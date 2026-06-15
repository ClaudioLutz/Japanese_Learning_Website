# app/models.py
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from dataclasses import dataclass
import enum
import json
import re
from typing import List
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import ForeignKey, Table, Column, Integer, String, Text, Boolean, DateTime, JSON, event, BigInteger, true as sa_true


class AccessDenialReason(enum.Enum):
    """Strukturierter Grund, warum eine Lektion (nicht) zugaenglich ist.

    Ersetzt die fruehere String-als-Steuerlogik (Substring-Match auf
    'Login required'). NONE bedeutet: Zugriff gewaehrt.
    """
    NONE = "none"
    LOGIN_REQUIRED = "login_required"
    PREREQUISITE = "prerequisite"
    PURCHASE_REQUIRED = "purchase_required"
    PREMIUM_REQUIRED = "premium_required"


@dataclass(frozen=True)
class AccessResult:
    """Ergebnis von Lesson.access_check: Zugriff + User-Message + Grund."""
    accessible: bool
    message: str
    reason: AccessDenialReason


@dataclass(frozen=True)
class AccessContext:
    """Vorberechnete Batch-Daten fuer Lesson.access_check (N+1-Vermeidung).

    Bei Listen-Ansichten (z.B. module_detail mit vielen Lessons fuer denselben
    User) loesen die Per-Row-Queries in access_check (LessonPurchase,
    CoursePurchase, UserLessonProgress) eine echte, lesson-skalierende N+1 aus.
    Diese Struktur traegt die drei Mengen vorab — in je EINER Query geladen —
    und access_check liest nur noch daraus. Die ENTSCHEIDUNGSLOGIK bleibt
    bit-identisch (Set-Membership ist aequivalent zur `... .first()`-Wahrheit).

    Default-Pfad (access_ctx=None) bleibt das heutige Per-Row-Verhalten, damit
    alle anderen Aufrufer von access_check/is_accessible_to_user unveraendert
    und risikofrei bleiben.
    """
    purchased_lesson_ids: frozenset[int]
    purchased_course_ids: frozenset[int]
    completed_lesson_ids: frozenset[int]

    @classmethod
    def build_for_user(cls, user, lessons) -> 'AccessContext':
        """Laedt die Batch-Mengen fuer `user` ueber die gegebenen Lessons.

        - purchased_lesson_ids: gekaufte Lessons aus der Lesson-Menge
        - purchased_course_ids: gekaufte Courses, die eine dieser Lessons
          enthalten (deckt den Course-Kauf-Zweig ab)
        - completed_lesson_ids: abgeschlossene Lessons des Users, die als
          Lesson ODER als Voraussetzung einer dieser Lessons relevant sind
        Drei Queries, unabhaengig von der Lesson-Anzahl.
        """
        lesson_list = list(lessons)
        lesson_ids = {lsn.id for lsn in lesson_list}

        # Voraussetzungs-Lesson-IDs einsammeln (deren Completion wird geprueft)
        prereq_ids: set[int] = set()
        course_ids: set[int] = set()
        for lsn in lesson_list:
            for prereq in lsn.get_prerequisites():
                if prereq is not None:
                    prereq_ids.add(prereq.id)
            for course in lsn.courses:
                course_ids.add(course.id)

        relevant_lesson_ids = lesson_ids | prereq_ids

        if not user or not getattr(user, 'is_authenticated', False):
            return cls(frozenset(), frozenset(), frozenset())

        purchased_lessons: frozenset[int] = frozenset()
        if lesson_ids:
            rows = (
                db.session.query(LessonPurchase.lesson_id)
                .filter(
                    LessonPurchase.user_id == user.id,
                    LessonPurchase.lesson_id.in_(lesson_ids),
                )
                .all()
            )
            purchased_lessons = frozenset(r[0] for r in rows)

        purchased_courses: frozenset[int] = frozenset()
        if course_ids:
            rows = (
                db.session.query(CoursePurchase.course_id)
                .filter(
                    CoursePurchase.user_id == user.id,
                    CoursePurchase.course_id.in_(course_ids),
                )
                .all()
            )
            purchased_courses = frozenset(r[0] for r in rows)

        completed_lessons: frozenset[int] = frozenset()
        if relevant_lesson_ids:
            rows = (
                db.session.query(UserLessonProgress.lesson_id)
                .filter(
                    UserLessonProgress.user_id == user.id,
                    UserLessonProgress.lesson_id.in_(relevant_lesson_ids),
                    UserLessonProgress.is_completed.is_(True),
                )
                .all()
            )
            completed_lessons = frozenset(r[0] for r in rows)

        return cls(purchased_lessons, purchased_courses, completed_lessons)


class User(UserMixin, db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(80), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(120), unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    subscription_level: Mapped[str] = mapped_column(String(50), default='free')
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Account Lockout
    failed_login_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default='0')
    locked_until: Mapped[datetime] = mapped_column(DateTime, nullable=True)

    # Streak-System
    current_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default='0')
    longest_streak: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default='0')
    last_activity_date = db.Column(db.Date, nullable=True)
    total_xp: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default='0')

    # Phase 6: Gamification
    level: Mapped[int] = mapped_column(Integer, default=1, nullable=False, server_default='1')
    total_reviews: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default='0')
    total_mastered: Mapped[int] = mapped_column(Integer, default=0, nullable=False, server_default='0')

    # Phase 3 (Kana-Spiel): Web-Push-Subscription (opt-in via Service Worker)
    push_subscription: Mapped[dict] = mapped_column(JSON, nullable=True)

    lesson_progress: Mapped[List['UserLessonProgress']] = relationship('UserLessonProgress', backref='user', lazy=True, cascade='all, delete-orphan')
    course_purchases: Mapped[List['CoursePurchase']] = relationship('CoursePurchase', backref='user', lazy=True, cascade='all, delete-orphan')

    LOCKOUT_THRESHOLD = 5
    LOCKOUT_DURATION_MINUTES = 15

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def is_locked(self):
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False

    def record_failed_login(self):
        from datetime import timedelta
        self.failed_login_count = (self.failed_login_count or 0) + 1
        if self.failed_login_count >= self.LOCKOUT_THRESHOLD:
            self.locked_until = datetime.utcnow() + timedelta(minutes=self.LOCKOUT_DURATION_MINUTES)

    def record_successful_login(self):
        self.failed_login_count = 0
        self.locked_until = None
        self.update_streak()

    def update_streak(self):
        """Aktualisiert den Tages-Streak bei Aktivitaet mit Streak-Freeze-Unterstuetzung."""
        # Tagesgrenze in CH-Lokalzeit (Europe/Zurich), NICHT UTC: bei UTC wuerde eine
        # spaetabendliche Session (z.B. 23:30 CH = 22:30/21:30 UTC ist noch ok, aber
        # 00:30 CH = 23:30 UTC des Vortags) auf den falschen Kalendertag fallen und den
        # Streak faelschlich brechen. Europe/Zurich = der Tag, den der Nutzer sieht.
        from zoneinfo import ZoneInfo
        today = datetime.now(ZoneInfo("Europe/Zurich")).date()
        if self.last_activity_date == today:
            return  # Bereits heute aktiv
        from datetime import timedelta

        # Streak-Freeze-Nachfuellung (1x pro Woche)
        settings = getattr(self, 'srs_settings', None)
        if settings:
            if not settings.last_freeze_replenish or (today - settings.last_freeze_replenish).days >= 7:
                settings.streak_freezes_available = 1
                settings.last_freeze_replenish = today

        if self.last_activity_date == today - timedelta(days=1):
            # Gestern gelernt → Streak weiter
            self.current_streak = (self.current_streak or 0) + 1
        elif (self.last_activity_date
              and self.last_activity_date == today - timedelta(days=2)
              and settings
              and (settings.streak_freezes_available or 0) > 0):
            # Vorgestern gelernt, gestern verpasst, Freeze verfuegbar
            settings.streak_freezes_available -= 1
            # Streak bleibt (kein +1, aber kein Reset)
        else:
            self.current_streak = 1
        if self.current_streak > (self.longest_streak or 0):
            self.longest_streak = self.current_streak
        self.last_activity_date = today

    def add_xp(self, amount):
        """Fuegt XP hinzu und prueft Level-Up."""
        self.total_xp = (self.total_xp or 0) + amount
        while self.total_xp >= self.xp_for_next_level:
            self.level = (self.level or 1) + 1

    @property
    def xp_for_next_level(self):
        """XP-Schwelle fuer das naechste Level (polynomiale Kurve)."""
        return int(100 * ((self.level or 1) ** 1.5))

    @property
    def level_title(self):
        """Japanisch-thematischer Level-Titel."""
        lvl = self.level or 1
        if lvl <= 5:
            return 'Anfänger (初心者)'
        elif lvl <= 10:
            return 'Schüler (学生)'
        elif lvl <= 15:
            return 'Lehrling (見習い)'
        elif lvl <= 25:
            return 'Fortgeschritten (上級者)'
        elif lvl <= 40:
            return 'Experte (達人)'
        elif lvl <= 50:
            return 'Meister (師匠)'
        return 'Grossmeister (名人)'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'

class Kana(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    character = db.Column(db.String(5), nullable=False, unique=True)
    romanization = db.Column(db.String(10), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'hiragana' or 'katakana'
    stroke_order_info = db.Column(db.String(255), nullable=True)
    example_sound_url = db.Column(db.String(255), nullable=True)
    mnemonic = db.Column(db.Text, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Kana {self.character}>'

class Kanji(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    character = db.Column(db.String(5), nullable=False, unique=True)
    meaning = db.Column(db.Text, nullable=False)
    onyomi = db.Column(db.String(100), nullable=True)
    kunyomi = db.Column(db.String(100), nullable=True)
    jlpt_level = db.Column(db.Integer, nullable=True)
    stroke_order_info = db.Column(db.String(255), nullable=True)
    radical = db.Column(db.String(10), nullable=True)
    stroke_count = db.Column(db.Integer, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), default='approved', nullable=False)  # 'approved', 'pending_approval'
    created_by_ai = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Kanji {self.character}>'

class Vocabulary(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    word = db.Column(db.String(100), nullable=False, unique=True)
    reading = db.Column(db.String(100), nullable=False)
    romaji = db.Column(db.String(200), nullable=True)
    meaning = db.Column(db.Text, nullable=False)
    meaning_de = db.Column(db.Text, nullable=True)
    jlpt_level = db.Column(db.Integer, nullable=True)
    example_sentence_japanese = db.Column(db.Text, nullable=True)
    # Format: "Romaji-Satz — Deutsche Uebersetzung". Wird auf der Backseite
    # zerlegt in zwei Zeilen (Romaji, Deutsch). Felder mit altem englischem
    # Inhalt werden weiterhin gerendert, gehoeren aber langfristig auf
    # Deutsch umgestellt (instruction_language=german auf der Plattform).
    example_sentence_english = db.Column(db.Text, nullable=True)
    audio_url = db.Column(db.String(255), nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    status = db.Column(db.String(20), default='approved', nullable=False)  # 'approved', 'pending_approval'
    created_by_ai = db.Column(db.Boolean, default=False, nullable=False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Vocabulary {self.word}>'

    def _split_example_translation(self) -> tuple[str | None, str | None]:
        """Zerlegt example_sentence_english in (Romaji, Uebersetzung).

        Pflicht-Format laut SKILL.md ist "Romaji — Translation" mit em-dash.
        Tolerant gegenueber dem ASCII-Bindestrich " - " als Trenner. Wenn kein
        Trenner gefunden, gilt der Inhalt komplett als Uebersetzung (Romaji = None).
        """
        raw = (self.example_sentence_english or '').strip()
        if not raw:
            return None, None
        for sep in (' — ', ' – ', ' - '):
            if sep in raw:
                left, right = raw.split(sep, 1)
                left = left.strip()
                right = right.strip()
                return (left or None), (right or None)
        return None, raw or None

    @property
    def example_sentence_romaji(self) -> str | None:
        return self._split_example_translation()[0]

    @property
    def example_sentence_translation(self) -> str | None:
        return self._split_example_translation()[1]


# Zeilen, die mit "(" bzw. einem Gedankenstrich beginnen, setzen den
# vorherigen Beispiel-Eintrag fort (Romaji-Klammer- bzw. Uebersetzungszeile).
_EXAMPLE_CONTINUATION_RE = re.compile(r'^[(（—–\-→:>]')
# Fuehrende Aufzaehlungsmarker (①–⑩, "1." / "1)", Bullet) am Eintragsanfang.
_EXAMPLE_MARKER_RE = re.compile(r'^(?:[①②③④⑤⑥⑦⑧⑨⑩]|[0-9]+[.)]|[•*])\s*')
# Trennzeichen vor der Uebersetzung (—, –, ->, :, >).
_TRANSLATION_LEAD_RE = re.compile(r'^[\s—–\-→:>]+')


def parse_example_sentences(raw: str | None) -> list[dict[str, str]]:
    """Normalisiert ``Grammar.example_sentences`` in eine Liste von
    Beispielsaetzen ``{'japanese', 'romaji', 'translation'}``.

    Unterstuetzt beide in der DB vorkommenden Formate:

    1. **JSON-Liste**::

         [{"japanese": "...", "romanization"/"romaji": "...",
           "german"/"english"/"translation": "..."}, ...]

    2. **Nummerierter Plaintext**::

         ① わたしは マイク・ミラーです。
           (Watashi wa Maiku Miraa desu.)
           — Ich bin Mike Miller.

       inklusive einzeiliger Inline-Variante ``JP。 (Romaji) — Uebersetzung``
       und "…"-Antwortzeilen.

    Fehlende Teile werden als leerer String geliefert (nie ``None``), damit
    das Rendering ohne Sonderfaelle bleibt. Nicht parsebarer Input → ``[]``.
    """
    raw = (raw or '').strip()
    if not raw:
        return []

    # --- Format 1: JSON-Liste ---
    if raw.startswith('['):
        try:
            data = json.loads(raw)
        except (ValueError, TypeError):
            data = None
        if isinstance(data, list):
            examples: list[dict[str, str]] = []
            for entry in data:
                if not isinstance(entry, dict):
                    continue
                jp = str(entry.get('japanese') or '').strip()
                if not jp:
                    continue
                examples.append({
                    'japanese': jp,
                    'romaji': str(entry.get('romanization')
                                  or entry.get('romaji') or '').strip(),
                    'translation': str(entry.get('german') or entry.get('de')
                                       or entry.get('english')
                                       or entry.get('translation') or '').strip(),
                })
            return examples

    # --- Format 2: nummerierter / Inline-Plaintext ---
    # Zeilen zu Eintraegen gruppieren: Fortsetzungszeilen (Romaji/Uebersetzung)
    # haengen am aktuellen Eintrag, jede andere nicht-leere Zeile beginnt einen
    # neuen Eintrag.
    records: list[str] = []
    current: list[str] = []
    for line in raw.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if current and not _EXAMPLE_CONTINUATION_RE.match(stripped):
            records.append(' '.join(current))
            current = []
        current.append(stripped)
    if current:
        records.append(' '.join(current))

    examples = []
    for record in records:
        record = _EXAMPLE_MARKER_RE.sub('', record).strip()
        if not record:
            continue
        japanese, romaji, translation = record, '', ''
        open_candidates = [i for i in (record.find('('), record.find('（')) if i != -1]
        if open_candidates:
            open_idx = min(open_candidates)
            japanese = record[:open_idx].strip()
            rest = record[open_idx + 1:]
            close_candidates = [i for i in (rest.find(')'), rest.find('）')) if i != -1]
            if close_candidates:
                close_idx = min(close_candidates)
                romaji = rest[:close_idx].strip()
                translation = _TRANSLATION_LEAD_RE.sub('', rest[close_idx + 1:]).strip()
            else:
                romaji = rest.strip()  # unbalancierte/abgeschnittene Klammer
        examples.append({'japanese': japanese, 'romaji': romaji,
                         'translation': translation})
    return examples


# Lauf japanischer Zeichen (Hiragana/Katakana/Kanji) — ein „Grammatik-Marker"
# im structure-Feld ist genau so ein Lauf (Platzhalter wie N/S/V sind Latein).
_CLOZE_JP_RUN = re.compile(r'[ぁ-んァ-ヶーゝゞ一-鿿々]+')
# Satz-Endungen/Kopula, die nur Fallback-Lückenkandidaten sind (selten DER
# Lernpunkt). Distinktive Marker (Partikeln wie は/が/を/に/で, Konjugations-
# formen) haben Vorrang — sonst würde z.B. „N は N です" das です statt は testen.
_CLOZE_COMMON_MARKERS = {'です', 'だ', 'ます', 'ません', 'ました', 'でした',
                         'でしょう', 'だった', 'では', 'じゃ'}

# Kompakte Hiragana→Romaji-Umschrift, um die Cloze-Antwort auch im Satz-Romaji
# maskieren zu können (Lesehilfe ohne Spoiler).
_KANA_DIGRAPHS = {
    'きゃ': 'kya', 'きゅ': 'kyu', 'きょ': 'kyo', 'ぎゃ': 'gya', 'ぎゅ': 'gyu', 'ぎょ': 'gyo',
    'しゃ': 'sha', 'しゅ': 'shu', 'しょ': 'sho', 'じゃ': 'ja', 'じゅ': 'ju', 'じょ': 'jo',
    'ちゃ': 'cha', 'ちゅ': 'chu', 'ちょ': 'cho', 'にゃ': 'nya', 'にゅ': 'nyu', 'にょ': 'nyo',
    'ひゃ': 'hya', 'ひゅ': 'hyu', 'ひょ': 'hyo', 'びゃ': 'bya', 'びゅ': 'byu', 'びょ': 'byo',
    'ぴゃ': 'pya', 'ぴゅ': 'pyu', 'ぴょ': 'pyo', 'みゃ': 'mya', 'みゅ': 'myu', 'みょ': 'myo',
    'りゃ': 'rya', 'りゅ': 'ryu', 'りょ': 'ryo',
}
_KANA_BASIC = {
    'あ': 'a', 'い': 'i', 'う': 'u', 'え': 'e', 'お': 'o',
    'か': 'ka', 'き': 'ki', 'く': 'ku', 'け': 'ke', 'こ': 'ko',
    'が': 'ga', 'ぎ': 'gi', 'ぐ': 'gu', 'げ': 'ge', 'ご': 'go',
    'さ': 'sa', 'し': 'shi', 'す': 'su', 'せ': 'se', 'そ': 'so',
    'ざ': 'za', 'じ': 'ji', 'ず': 'zu', 'ぜ': 'ze', 'ぞ': 'zo',
    'た': 'ta', 'ち': 'chi', 'つ': 'tsu', 'て': 'te', 'と': 'to',
    'だ': 'da', 'ぢ': 'ji', 'づ': 'zu', 'で': 'de', 'ど': 'do',
    'な': 'na', 'に': 'ni', 'ぬ': 'nu', 'ね': 'ne', 'の': 'no',
    'は': 'ha', 'ひ': 'hi', 'ふ': 'fu', 'へ': 'he', 'ほ': 'ho',
    'ば': 'ba', 'び': 'bi', 'ぶ': 'bu', 'べ': 'be', 'ぼ': 'bo',
    'ぱ': 'pa', 'ぴ': 'pi', 'ぷ': 'pu', 'ぺ': 'pe', 'ぽ': 'po',
    'ま': 'ma', 'み': 'mi', 'む': 'mu', 'め': 'me', 'も': 'mo',
    'や': 'ya', 'ゆ': 'yu', 'よ': 'yo',
    'ら': 'ra', 'り': 'ri', 'る': 'ru', 'れ': 're', 'ろ': 'ro',
    'わ': 'wa', 'を': 'o', 'ん': 'n',
}


def _romanize_kana(text: str) -> str:
    """Grobe Hiragana→Romaji-Umschrift für kurze Marker. Leerer String, sobald
    ein Zeichen nicht abbildbar ist (z.B. Kanji/Katakana) → kein maskiertes Romaji."""
    out: list[str] = []
    i, n, geminate = 0, len(text), False
    while i < n:
        ch = text[i]
        if ch in (' ', '　'):
            out.append(' ')
            i += 1
            continue
        if ch == 'ー':  # Langvokal-Zeichen überspringen
            i += 1
            continue
        if ch == 'っ':  # kleiner tsu → nächsten Konsonanten verdoppeln
            geminate = True
            i += 1
            continue
        pair = text[i:i + 2]
        if pair in _KANA_DIGRAPHS:
            rom, i = _KANA_DIGRAPHS[pair], i + 2
        elif ch in _KANA_BASIC:
            rom, i = _KANA_BASIC[ch], i + 1
        else:
            return ''  # nicht abbildbar
        if geminate and rom:
            rom, geminate = rom[0] + rom, False
        out.append(rom)
    return ''.join(out)


# Lange Vokale (Makron) im Satz-Romaji → Vokal-Verdopplung, damit die
# Maskierung gegen die Kana-Umschrift der Antwort (die "ou"/"uu" liefert, nie
# "ō"/"ū") matcht. Schreibweise "ou" passt zum Site-Stil ("Toukyou", "Kyou").
_ROMAJI_MACRON = {
    'ā': 'aa', 'ī': 'ii', 'ū': 'uu', 'ē': 'ee', 'ō': 'ou',
    'â': 'aa', 'î': 'ii', 'û': 'uu', 'ê': 'ee', 'ô': 'ou',
    'Ā': 'Aa', 'Ī': 'Ii', 'Ū': 'Uu', 'Ē': 'Ee', 'Ō': 'Ou',
    'Â': 'Aa', 'Î': 'Ii', 'Û': 'Uu', 'Ê': 'Ee', 'Ô': 'Ou',
}


def _expand_macrons(s: str) -> str:
    return ''.join(_ROMAJI_MACRON.get(ch, ch) for ch in s)


def _answer_romaji_candidates(answer: str) -> list[str]:
    """Romaji-Kandidaten für die Cloze-Antwort inkl. Partikel-Sonderlesungen.

    Liefert für mehrteilige Antworten (z.B. ``わたしは``) zusätzlich die Variante
    mit phonetischer Partikel-Lesung (は=wa, へ=e, を=o), damit ``Watashi wa`` im
    Satz-Romaji gefunden wird und nicht das (kana-wörtliche) ``watashiha``.
    Kanji-Antworten ohne Kana-Umschrift liefern ``[]`` → kein maskiertes Romaji.
    """
    a = (answer or '').strip()
    specials = {'は': ['wa', 'ha'], 'へ': ['e', 'he'], 'を': ['o', 'wo']}
    if a in specials:
        return specials[a]
    cands: list[str] = []
    base = _romanize_kana(a)
    if base:
        cands.append(base)
        # Partikel-Variante: は→wa, へ→e (を ist im Kana-Mapping bereits 'o').
        particle = _romanize_kana(a.replace('は', 'わ').replace('へ', 'え'))
        if particle and particle != base:
            cands.append(particle)
    return cands


def _mask_romaji(full: str, candidates: list[str], gap: str = '＿＿') -> str:
    """Ersetzt die Antwort-Lesung im Satz-Romaji durch die Lücke ``gap``.

    Robust gegen die Unterschiede zwischen Kana-Umschrift und Satz-Romaji:
    Makron (``dō``↔``dou``) und Leerzeichen (``desuka``↔``desu ka``) werden beim
    Suchen ignoriert. Sehr kurze Lesungen (≤2 Zeichen, z.B. ``wa``/``mo``) nur an
    Wortgrenzen, um Treffer mitten im Wort zu vermeiden.

    Findet sich die Lesung NICHT (Kanji-Antwort ohne Umschrift o.ä.), kommt ``''``
    zurück — die Karte zeigt dann keine Romaji-Zeile, aber die Lösung wird NIE
    unmaskiert gespoilert. Leer auch ohne jedes Satz-Romaji.
    """
    if not full or not candidates:
        return ''

    def _skip(ch: str) -> bool:
        return ch.isspace() or ch in '-‐'

    # Normalisierte Suchform `s` (lowercase + Makron→Vokaldopplung) mit Rückbezug
    # `m2o` jedes s-Zeichens auf seinen Index in `full`. Gesucht wird auf `s`,
    # gerendert wird aus `full` — so bleibt der NICHT maskierte Rest exakt 1:1
    # erhalten (inkl. Makron/Bindestrich), nur die Lücke wird ersetzt.
    s_chars: list[str] = []
    m2o: list[int] = []
    for i, ch in enumerate(full):
        frag = (_ROMAJI_MACRON.get(ch) or _ROMAJI_MACRON.get(ch.lower())
                or ch).lower()
        for c in frag:
            s_chars.append(c)
            m2o.append(i)
    s = ''.join(s_chars)
    # Kompaktform ohne Leerzeichen/Bindestriche (Romaji trennt Zähl-Lesungen
    # mit '-': "nan-ji", "hachi-gatsu") + Rückbezug auf s-Indizes.
    cidx = [k for k, c in enumerate(s) if not _skip(c)]
    compact = ''.join(s[k] for k in cidx)

    for cand in sorted({c for c in candidates if c}, key=len, reverse=True):
        nc = ''.join(c for c in _expand_macrons(cand).lower() if not _skip(c))
        if not nc:
            continue
        if len(nc) <= 2:
            # Kurze Lesungen (wa/mo/ni/o …) nur an Wortgrenzen.
            mt = re.search(r'\b' + re.escape(nc) + r'\b', s)
            if mt:
                o0, o1 = m2o[mt.start()], m2o[mt.end() - 1] + 1
                return full[:o0] + gap + full[o1:]
            continue
        pos = compact.find(nc)
        if pos != -1:
            o0 = m2o[cidx[pos]]
            o1 = m2o[cidx[pos + len(nc) - 1]] + 1
            return full[:o0] + gap + full[o1:]
    return ''


def _pyk_romaji(text: str) -> str:
    """Romanisiert beliebigen japanischen Text (inkl. Kanji) via pykakasi zu
    Hepburn. Leerer String, wenn pykakasi fehlt oder nichts uebrig bleibt.

    Wird nur fuer den Cloze-Fallback gebraucht, wenn die Antwort ein Kanji ist
    und sich darum nicht im kuratierten Romaji lokalisieren laesst — dann wird
    die Romaji-Zeile aus den Satzteilen vor/nach der Luecke neu gebaut.

    Bewusst FRISCHE pykakasi-Instanz pro Aufruf: eine global wiederverwendete
    Instanz lieferte nach vielen ``convert``-Aufrufen fuer denselben Satz
    abgeschnittene Ergebnisse (z.B. nur ``desu`` statt des ganzen Satzes). Der
    Pfad laeuft nur fuer die wenigen Kanji-Luecken-Karten, darum unkritisch."""
    text = (text or '').strip()
    if not text:
        return ''
    try:
        import pykakasi
        kks = pykakasi.kakasi()
    except Exception:  # noqa: BLE001  (pykakasi optional → Fallback auf '')
        return ''
    parts = [(_t.get('hepburn') or '').strip() for _t in kks.convert(text)]
    out = ' '.join(p for p in parts if p)
    # Standalone-Partikel-Norm (は→wa, へ→e am Wort-/Satzanfang ohne Kontext)
    out = re.sub(r'\bha\b', 'wa', out)
    out = re.sub(r'\bhe\b', 'e', out)
    # Japanische Satzzeichen + Whitespace glaetten
    out = out.replace('、', ', ').replace('。', '.')
    out = re.sub(r'\s+([,.!?])', r'\1', out)
    out = re.sub(r'\s{2,}', ' ', out).strip(' ')
    return out


def _romaji_with_gap(before: str, after: str, gap: str = '＿＿') -> str:
    """Baut die Satz-Romaji-Zeile aus den Teilen VOR und NACH der Luecke neu auf
    und setzt ``gap`` dazwischen. Die Antwort selbst wird nie romanisiert →
    garantiert spoilerfrei. Fuer Kanji-Luecken, die ``_mask_romaji`` nicht
    auffindet. Leer nur, wenn beide Teile kein Romaji ergeben."""
    rb = _pyk_romaji(before)
    ra = _pyk_romaji(after)
    if not rb and not ra:
        return ''
    out = ' '.join(p for p in (rb, gap, ra) if p)
    out = re.sub(r'\s+([,.!?])', r'\1', out)
    out = re.sub(r'\s{2,}', ' ', out).strip(' ')
    if out and out[0].islower():
        out = out[0].upper() + out[1:]
    return out


def make_grammar_cloze(examples: list[dict[str, str]],
                       structure: str | None) -> dict[str, str] | None:
    """Erzeugt eine Lückentext-Karte: blendet den für diese Grammatik typischen
    Marker (Partikel/Form aus `structure`) im ersten passenden Beispielsatz aus.

    Vorgehen: die japanischen Marker aus `structure` werden in zwei Stufen
    gesucht — zuerst distinktive (Partikeln/Formen), dann erst Allerwelts-Kopula.
    Das Matching ist leerzeichentolerant, weil der Datensatz Satzglieder mit
    Leerzeichen trennt (z.B. „学生じゃ ありません").

    Liefert ``{'before', 'after', 'answer', 'japanese', 'romaji', 'translation'}``
    oder ``None``, wenn kein Marker in einem Beispiel vorkommt (z.B. reine
    Konjugations-/Lesungstabellen) — dann faellt das UI auf den Titel zurueck.
    """
    markers = set(_CLOZE_JP_RUN.findall(
        re.sub(r'[(（][^)）]*[)）]', '', structure or '')))
    if not markers:
        return None
    tiers = (
        sorted((m for m in markers if m not in _CLOZE_COMMON_MARKERS),
               key=len, reverse=True),
        sorted((m for m in markers if m in _CLOZE_COMMON_MARKERS),
               key=len, reverse=True),
    )
    for tier in tiers:
        for ex in examples:
            jp = ex.get('japanese', '')
            for marker in tier:
                pattern = r'\s*'.join(re.escape(c) for c in marker)
                m = re.search(pattern, jp)
                if m:
                    answer = jp[m.start():m.end()]
                    before, after = jp[:m.start()], jp[m.end():]
                    romaji = ex.get('romaji', '')
                    # 1) Antwort-Lesung im kuratierten Satz-Romaji maskieren.
                    masked = _mask_romaji(
                        romaji, _answer_romaji_candidates(answer))
                    # 2) Fallback (z.B. Kanji-Lücke, im Romaji nicht auffindbar):
                    #    Zeile aus before/after neu romanisieren — der Rest steht
                    #    als Romaji, nur die Lücke bleibt leer (nie gespoilert).
                    if not masked:
                        masked = _romaji_with_gap(before, after)
                    return {
                        'before': before,
                        'after': after,
                        'answer': answer,
                        'japanese': jp,
                        'romaji': romaji,
                        # Satz-Romaji mit ausgeblendeter Lücke (Lesehilfe ohne
                        # Spoiler). Leer nur, wenn weder kuratiertes Romaji noch
                        # der pykakasi-Fallback etwas liefern.
                        'romaji_masked': masked,
                        'translation': ex.get('translation', ''),
                    }
    return None


class Grammar(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False, unique=True)
    explanation = db.Column(db.Text, nullable=False)
    structure = db.Column(db.Text, nullable=True)
    romaji = db.Column(db.String(500), nullable=True)
    jlpt_level = db.Column(db.Integer, nullable=True)
    example_sentences = db.Column(db.Text, nullable=True)
    # Genau EIN japanischer Satz pro Grammatik-Karte fuer den Audio-Button.
    # Pflicht-Format: rein japanisch (kein Romaji, keine Uebersetzung), so dass
    # die ja-JP-Stimme niemals deutschen Text liest. Wenn leer, faellt der
    # Audio-Button auf den Titel zurueck.
    tts_example_jp = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default='approved', nullable=False)  # 'approved', 'pending_approval'
    created_by_ai = db.Column(db.Boolean, default=False, nullable=False)
    # Kurze didaktische Notiz: Nuance/Formalität/„nicht verwechseln mit …".
    # Kuratiert, v.a. für verwechselbare Punkte (は/が/も …). Optional.
    nuance = db.Column(db.Text, nullable=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Grammar {self.title}>'

    def _extract_tts_example_parts(self) -> tuple[str | None, str | None]:
        """Liefert (Romaji, Uebersetzung) zum Satz in ``tts_example_jp``.

        Sucht in :meth:`parsed_examples` den Eintrag, dessen japanischer Satz
        ``tts_example_jp`` entspricht (exakt oder als Teilstring), und liefert
        dessen Romaji + Uebersetzung. Findet sich nichts, kommt (None, None)
        zurueck — der Audio-Button funktioniert weiterhin.
        """
        if not self.tts_example_jp:
            return None, None
        target = self.tts_example_jp.strip().rstrip('。！？')
        if not target:
            return None, None
        for ex in self.parsed_examples():
            jp = ex['japanese'].strip().rstrip('。！？')
            if jp and (jp == target or target in jp or jp in target):
                return (ex['romaji'] or None), (ex['translation'] or None)
        return None, None

    def parsed_examples(self) -> list[dict[str, str]]:
        """Beispielsaetze dieser Karte als normalisierte Liste
        ``{'japanese', 'romaji', 'translation'}`` (siehe Modulfunktion
        :func:`parse_example_sentences`)."""
        return parse_example_sentences(self.example_sentences)

    def cloze(self) -> dict[str, str] | None:
        """Lückentext-Variante eines Beispielsatzes für den Cloze-Review —
        der typische Marker (Partikel/Form) ist ausgeblendet. ``None``, wenn
        kein Marker passt (siehe :func:`make_grammar_cloze`)."""
        return make_grammar_cloze(self.parsed_examples(), self.structure)

    @property
    def tts_example_romaji(self) -> str | None:
        return self._extract_tts_example_parts()[0]

    @property
    def tts_example_translation(self) -> str | None:
        return self._extract_tts_example_parts()[1]

class LessonCategory(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    color_code = db.Column(db.String(7), default='#007bff')  # hex color for UI
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Lernpfad-Felder (Mayuko-Direktive 2026-04-25: JLPT-strukturierter Pfad)
    # Eine Kategorie wirkt als Modul innerhalb eines JLPT-Levels.
    slug = db.Column(db.String(80), unique=True, nullable=True)  # z.B. 'n5-hiragana'
    jlpt_level = db.Column(db.Integer, nullable=True)             # 5, 4, 3, 2, 1
    display_order = db.Column(db.Integer, default=0, nullable=False)  # Reihenfolge innerhalb Level
    icon_emoji = db.Column(db.String(8), nullable=True)           # z.B. 'あ' oder '🔢'
    prerequisite_category_id = db.Column(
        db.Integer, db.ForeignKey('lesson_category.id'), nullable=True
    )

    # Relationship
    lessons = db.relationship('Lesson', backref='category', lazy=True)
    prerequisite = db.relationship(
        'LessonCategory', remote_side=[id], foreign_keys=[prerequisite_category_id]
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<LessonCategory {self.name}>'

    def completion_for_user(self, user, languages: list[str] | None = None) -> tuple[int, int]:
        """Returns (completed_lessons, total_published_lessons) fuer Pfad-Anzeige.

        Wenn `languages` gesetzt ist (z.B. ['german']), werden nur Lessons mit
        passender instruction_language gezaehlt — fuer den Sprach-Filter aus
        app.config['CONTENT_LANGUAGES'].
        """
        from app.models import Lesson, UserLessonProgress
        published = [l for l in self.lessons if l.is_published]
        if languages is not None:
            published = [l for l in published if l.instruction_language in languages]
        total = len(published)
        if not user or not getattr(user, 'is_authenticated', False) or total == 0:
            return 0, total
        progress = UserLessonProgress.query.filter(
            UserLessonProgress.user_id == user.id,
            UserLessonProgress.lesson_id.in_([l.id for l in published]),
            UserLessonProgress.is_completed == True,  # noqa: E712
        ).count()
        return progress, total

    def is_unlocked_for_user(self, user, threshold: float = 0.8) -> bool:
        """Modul ist freigeschaltet, wenn Vorgaenger-Modul zu >=threshold complete ist.
        Ohne Voraussetzung: immer unlocked. Anonyme User: unlocked wenn Modul kostenlose
        Inhalte hat (Detail-Pruefung erfolgt bei Lektion-Zugriff)."""
        if self.prerequisite_category_id is None:
            return True
        if not user or not getattr(user, 'is_authenticated', False):
            return True  # Anonyme User sehen alles, harte Pruefung beim Lesson-Zugriff
        done, total = self.prerequisite.completion_for_user(user)
        if total == 0:
            return True
        return (done / total) >= threshold

class Lesson(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    lesson_type: Mapped[str] = mapped_column(String(20), nullable=False)
    category_id: Mapped[int] = mapped_column(Integer, ForeignKey('lesson_category.id'), nullable=True)
    difficulty_level: Mapped[int] = mapped_column(Integer, nullable=True)
    estimated_duration: Mapped[int] = mapped_column(Integer, nullable=True)
    order_index: Mapped[int] = mapped_column(Integer, default=0)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    allow_guest_access: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    instruction_language: Mapped[str] = mapped_column(String(10), default='english', nullable=False)
    show_romaji_on_front: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, server_default=sa_true())
    thumbnail_url: Mapped[str] = mapped_column(String(255), nullable=True)
    background_image_url: Mapped[str] = mapped_column(String(1000), nullable=True)
    background_image_path: Mapped[str] = mapped_column(String(500), nullable=True)
    video_intro_url: Mapped[str] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Pricing fields
    price: Mapped[float] = mapped_column(db.Float, nullable=False, default=0.0)
    is_purchasable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    # Relationships
    content_items: Mapped[List['LessonContent']] = relationship('LessonContent', backref='lesson', lazy=True, cascade='all, delete-orphan')
    prerequisites: Mapped[List['LessonPrerequisite']] = relationship('LessonPrerequisite', 
                                  foreign_keys='LessonPrerequisite.lesson_id',
                                  backref='lesson', lazy=True, cascade='all, delete-orphan')
    required_by: Mapped[List['LessonPrerequisite']] = relationship('LessonPrerequisite',
                                foreign_keys='LessonPrerequisite.prerequisite_lesson_id',
                                lazy=True)
    user_progress: Mapped[List['UserLessonProgress']] = relationship('UserLessonProgress', lazy=True, cascade='all, delete-orphan')
    pages_metadata: Mapped[List['LessonPage']] = relationship('LessonPage', backref='lesson', lazy=True, cascade='all, delete-orphan')
    courses: Mapped[List['Course']] = relationship('Course', secondary='course_lessons', back_populates='lessons')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<Lesson {self.title}>'
    
    def get_prerequisites(self) -> List['Lesson']:
        """Get list of prerequisite lessons"""
        return [prereq.prerequisite_lesson for prereq in self.prerequisites]

    @property
    def progress_visible_content_items(self) -> List['LessonContent']:
        """Content-Items, die im Lesson-View tatsaechlich sichtbar gerendert
        werden — und damit fuer den Fortschritt zaehlen.

        Bisheriger Bug: audio-Items wurden ausgeblendet, wenn auf derselben
        Page ein dialog_slideshow existiert (Slideshow hat eigenes Audio).
        Der User konnte sie also nie als erledigt markieren, der Progress
        blieb bei 96% statt 100%.

        is_optional-Items (z.B. dekorative Seitenbilder) zaehlen nicht zum
        Fortschritt — sie haben keinen Erledigt-Button und duerfen den
        Lektionsabschluss nicht blockieren.
        """
        items = list(self.content_items)
        slideshow_pages = {
            c.page_number for c in items if c.content_type == 'dialog_slideshow'
        }
        return [
            c for c in items
            if not (c.content_type == 'audio' and c.page_number in slideshow_pages)
            and not c.is_optional
        ]
    
    def access_check(self, user, access_ctx=None) -> 'AccessResult':
        """Strukturierte Zugriffspruefung: liefert AccessResult(accessible,
        message, reason).

        Loest die fruehere String-als-Steuerlogik ab: statt im Aufrufer per
        Substring auf 'Login required' zu matchen, liefert jeder Zweig den
        passenden AccessDenialReason. Messages bleiben deutsch und
        user-facing (flash()/Template).

        `access_ctx` (optional, AccessContext): vorberechnete Batch-Mengen fuer
        Listen-Ansichten (N+1-Vermeidung). Default None = Per-Row-Queries wie
        bisher. Die Entscheidungslogik ist in beiden Pfaden bit-identisch.
        """
        # --- Per-Row vs. Batch: Helfer kapseln die einzige Datenquellen-Differenz ---
        def _has_lesson_purchase(lesson_id):
            if access_ctx is not None:
                return lesson_id in access_ctx.purchased_lesson_ids
            return LessonPurchase.query.filter_by(
                user_id=user.id, lesson_id=lesson_id
            ).first() is not None

        def _has_course_purchase(course_id):
            if access_ctx is not None:
                return course_id in access_ctx.purchased_course_ids
            return CoursePurchase.query.filter_by(
                user_id=user.id, course_id=course_id
            ).first() is not None

        def _prereq_completed(prereq_id):
            if access_ctx is not None:
                return prereq_id in access_ctx.completed_lesson_ids
            progress = UserLessonProgress.query.filter_by(
                user_id=user.id, lesson_id=prereq_id
            ).first()
            return bool(progress and progress.is_completed)

        def _first_unmet_prereq():
            """Erste nicht erfuellte Voraussetzung (oder None) — identische
            Reihenfolge wie zuvor (get_prerequisites)."""
            for prereq in self.get_prerequisites():  # type: ignore
                if not _prereq_completed(prereq.id):
                    return prereq
            return None

        # Handle guest users (not authenticated)
        if user is None or not hasattr(user, 'is_authenticated') or not user.is_authenticated:
            # Free lessons with guest access
            if self.price == 0.0 and self.allow_guest_access:
                return AccessResult(True, "Als Gast zugänglich", AccessDenialReason.NONE)
            else:
                return AccessResult(
                    False,
                    "Anmeldung erforderlich, um auf diese Lektion zuzugreifen.",
                    AccessDenialReason.LOGIN_REQUIRED,
                )

        # Admin-Bypass: Admins sehen alle Lessons (Dogfood + Content-Verwaltung)
        if getattr(user, 'is_admin', False):
            return AccessResult(True, "Admin", AccessDenialReason.NONE)

        # For authenticated users, check pricing first
        if self.price == 0.0:
            # Free lesson - check prerequisites only
            unmet = _first_unmet_prereq()
            if unmet is not None:
                return AccessResult(
                    False, f"Schliesse zuerst „{unmet.title}\" ab",
                    AccessDenialReason.PREREQUISITE,
                )
            return AccessResult(True, "Kostenlose Lektion", AccessDenialReason.NONE)

        # Paid lesson - check if user purchased it
        if self.is_purchasable:
            if _has_lesson_purchase(self.id):
                # User owns the lesson - check prerequisites
                unmet = _first_unmet_prereq()
                if unmet is not None:
                    return AccessResult(
                        False, f"Schliesse zuerst „{unmet.title}\" ab",
                        AccessDenialReason.PREREQUISITE,
                    )
                return AccessResult(True, "Gekauft", AccessDenialReason.NONE)

            # Check if the lesson is part of a purchased course
            for course in self.courses:
                if _has_course_purchase(course.id):
                    # User owns the course, so grant access to the lesson
                    unmet = _first_unmet_prereq()
                    if unmet is not None:
                        return AccessResult(
                            False, f"Schliesse zuerst „{unmet.title}\" ab",
                            AccessDenialReason.PREREQUISITE,
                        )
                    return AccessResult(
                        True, f"Zugriff über „{course.title}\"",
                        AccessDenialReason.NONE,
                    )

            return AccessResult(
                False, f"Kauf erforderlich (CHF {self.price:.2f})",
                AccessDenialReason.PURCHASE_REQUIRED,
            )

        # Legacy subscription check (for existing premium lessons)
        if self.lesson_type == 'premium' and user.subscription_level != 'premium':
            return AccessResult(
                False, "Premium-Abo erforderlich",
                AccessDenialReason.PREMIUM_REQUIRED,
            )

        # Check prerequisites for other cases
        unmet = _first_unmet_prereq()
        if unmet is not None:
            return AccessResult(
                False, f"Schliesse zuerst „{unmet.title}\" ab",
                AccessDenialReason.PREREQUISITE,
            )

        return AccessResult(True, "Zugänglich", AccessDenialReason.NONE)

    def is_accessible_to_user(self, user):
        """Legacy-Wrapper: liefert das alte 2-Tupel (accessible, message).

        Bestehende ~10 Aufrufer bleiben unveraendert. Neue Logik, die den
        Ablehnungsgrund braucht, nutzt access_check() direkt.
        Messages auf Deutsch (User-facing — via flash() oder Template).
        """
        result = self.access_check(user)
        return result.accessible, result.message

    @property
    def pages(self):
        """Groups content items by page number for rendering and includes page metadata."""
        from collections import defaultdict
        from typing import DefaultDict, List, Dict, Any, Optional

        if not self.content_items:
            return []

        pages_dict: DefaultDict[int, Dict[str, Any]] = defaultdict(lambda: {'content': [], 'metadata': None})
        
        # Create a lookup for page metadata
        metadata_lookup = {pm.page_number: pm for pm in self.pages_metadata}

        # Sort all content items first by page, then by their order within the page
        sorted_content = sorted(self.content_items, key=lambda c: (c.page_number, c.order_index))
        
        for item in sorted_content:
            pages_dict[item.page_number]['content'].append(item)
        
        # Add metadata to each page
        for p_num, page_data in pages_dict.items():
            page_data['metadata'] = metadata_lookup.get(p_num)

        # Return a list of page objects, sorted by page number
        return [pages_dict[p_num] for p_num in sorted(pages_dict.keys())]

    def get_background_url(self):
        """Get URL for background image, handling GCS if enabled"""
        from flask import url_for, current_app
        
        # If we have a path, try to resolve it
        if self.background_image_path:
            # Check if GCS is enabled
            bucket_name = current_app.config.get('GCS_BUCKET_NAME')
            if bucket_name:
                # Remove leading slashes if any
                clean_path = self.background_image_path.lstrip('/')
                return f"https://storage.googleapis.com/{bucket_name}/{clean_path}"
            
            # Fallback to local serving
            return url_for('routes.uploaded_file', filename=self.background_image_path)
            
        # Fallback to the URL field if path is not set
        return self.background_image_url

    def get_thumbnail_url(self):
        """Get URL for thumbnail, handling GCS if enabled"""
        from flask import url_for, current_app
        
        if self.thumbnail_url:
            if self.thumbnail_url.startswith('http'):
                return self.thumbnail_url
            
            # Check if GCS is enabled
            bucket_name = current_app.config.get('GCS_BUCKET_NAME')
            if bucket_name:
                clean_path = self.thumbnail_url.lstrip('/')
                return f"https://storage.googleapis.com/{bucket_name}/{clean_path}"
            
            # Fallback to local serving
            return url_for('routes.uploaded_file', filename=self.thumbnail_url)
            
        return None

class LessonPrerequisite(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey('lesson.id'), nullable=False)
    prerequisite_lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey('lesson.id'), nullable=False)
    
    prerequisite_lesson: Mapped["Lesson"] = relationship(foreign_keys=[prerequisite_lesson_id], overlaps="required_by")
    
    __table_args__ = (db.UniqueConstraint('lesson_id', 'prerequisite_lesson_id'),)
    
    def __repr__(self):
        return f'<LessonPrerequisite {self.lesson_id} requires {self.prerequisite_lesson_id}>'

class LessonPage(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    page_number = db.Column(db.Integer, nullable=False)
    title = db.Column(db.String(200), nullable=True)
    description = db.Column(db.Text, nullable=True)
    page_type = db.Column(db.String(20), default='normal', nullable=False)  # 'normal' or 'quiz_carousel'

    __table_args__ = (db.UniqueConstraint('lesson_id', 'page_number'),)

    def __repr__(self):
        return f'<LessonPage {self.title} for lesson {self.lesson_id}>'

class LessonContent(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    content_type = db.Column(db.String(20), nullable=False)  # 'kana', 'kanji', 'vocabulary', 'grammar', 'text', 'image', 'video', 'audio'
    content_id = db.Column(db.Integer)  # NULL for multimedia content
    title = db.Column(db.String(200))  # for multimedia content
    content_text = db.Column(db.Text)  # for text content
    media_url = db.Column(db.String(255))  # for multimedia content
    order_index = db.Column(db.Integer, default=0)  # order within the lesson
    page_number = db.Column(db.Integer, default=1, nullable=False)  # Add page number
    is_optional = db.Column(db.Boolean, default=False)  # whether this content is optional
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # File-related fields
    file_path = db.Column(db.String(500))  # Relative path to uploaded file
    file_size = db.Column(db.Integer)      # File size in bytes
    file_type = db.Column(db.String(50))   # MIME type
    original_filename = db.Column(db.String(255))  # Original filename

    # Interactive content fields
    is_interactive = db.Column(db.Boolean, default=False)
    quiz_type = db.Column(db.String(50), default='standard') # 'standard', 'adaptive'
    max_attempts = db.Column(db.Integer, default=3)
    passing_score = db.Column(db.Integer, default=70)  # Percentage
    
    # AI generation tracking fields
    generated_by_ai = db.Column(db.Boolean, default=False, nullable=False)
    ai_generation_details = db.Column(db.JSON, nullable=True)
    
    # Relationships
    quiz_questions = db.relationship('QuizQuestion', backref='content', lazy=True, cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<LessonContent {self.content_type} in lesson {self.lesson_id}>'
    
    def get_file_url(self):
        """Get URL for accessing uploaded file"""
        from flask import url_for
        if self.file_path:
            # If it's a full URL (already migrated or external), return it
            if self.file_path.startswith('http'):
                return self.file_path
            
            # If it's a relative path, construct the GCS URL
            # Assuming the file_path stored in DB is relative to 'uploads/'
            # e.g. 'lessons/image/lesson_1/file.jpg'
            
            # Check if GCS is enabled (bucket name is set)
            from flask import current_app
            bucket_name = current_app.config.get('GCS_BUCKET_NAME')
            if bucket_name:
                # Remove leading slashes if any
                clean_path = self.file_path.lstrip('/')
                return f"https://storage.googleapis.com/{bucket_name}/{clean_path}"
            
            # Fallback to local serving (for development if GCS not set)
            return url_for('routes.uploaded_file', filename=self.file_path)
        return self.media_url  # Fallback to URL-based media
    
    def delete_file(self):
        """Delete associated file from filesystem"""
        if self.file_path:
            from flask import current_app
            import os
            file_full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], self.file_path)
            try:
                if os.path.exists(file_full_path):
                    os.remove(file_full_path)
                    current_app.logger.info(f"Successfully deleted file: {file_full_path}")
                return True # File deleted or did not exist
            except OSError as e: # D1
                current_app.logger.error(f"Error deleting file {file_full_path} for LessonContent {self.id}: {e}")
                return False # Deletion failed
    
    def get_content_data(self):
        """Get the actual content data based on content_type and content_id"""
        if self.content_type == 'kana' and self.content_id:
            return Kana.query.get(self.content_id)
        elif self.content_type == 'kanji' and self.content_id:
            return Kanji.query.get(self.content_id)
        elif self.content_type == 'vocabulary' and self.content_id:
            return Vocabulary.query.get(self.content_id)
        elif self.content_type == 'grammar' and self.content_id:
            return Grammar.query.get(self.content_id)
        elif self.content_type in ['text', 'image', 'video', 'audio']:
            return {
                'title': self.title,
                'content_text': self.content_text,
                'media_url': self.get_file_url() if self.file_path else self.media_url,
                'file_path': self.file_path,
                'file_size': self.file_size,
                'original_filename': self.original_filename
            }
        return None

    def is_quiz_fully_resolved(self, user_id) -> bool:
        """True, wenn ALLE Quiz-Fragen dieses Items fuer den User aufgeloest sind —
        jede Frage entweder korrekt beantwortet ODER alle Versuche aufgebraucht.

        Verhindert den Verfrueht-100%-Bug (2026-06-14): Frueher markierte das
        Frontend ein ganzes Quiz-Content-Item schon nach der ERSTEN beantworteten
        Frage als erledigt. Eine 14-Fragen-Uebung galt damit nach einer Antwort als
        fertig und die Lektion sprang verfrueht auf 100%.

        Ein Item ohne Fragen (kein echtes Quiz) gilt als aufgeloest (nichts zu tun).
        Bei unbegrenzten Versuchen (max_attempts None/0) ist eine falsch beantwortete
        Frage NICHT aufgeloest — sie muss korrekt beantwortet werden.
        """
        question_ids = [q.id for q in self.quiz_questions]
        if not question_ids:
            return True
        max_attempts = self.max_attempts or 0  # 0/None => unbegrenzt
        answers = {
            a.question_id: a
            for a in UserQuizAnswer.query.filter(
                UserQuizAnswer.user_id == user_id,
                UserQuizAnswer.question_id.in_(question_ids),
            ).all()
        }
        for qid in question_ids:
            a = answers.get(qid)
            if a is None:
                return False  # nie beantwortet
            if a.is_correct:
                continue
            # Falsch beantwortet: nur aufgeloest, wenn alle Versuche aufgebraucht
            if max_attempts and a.attempts >= max_attempts:
                continue
            return False
        return True

class QuizQuestion(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    lesson_content_id = db.Column(db.Integer, db.ForeignKey('lesson_content.id'), nullable=False)
    question_type = db.Column(db.String(50), nullable=False)  # 'multiple_choice', 'fill_blank', 'true_false', 'matching'
    question_text = db.Column(db.Text, nullable=False)
    explanation = db.Column(db.Text)  # Explanation for the answer
    hint = db.Column(db.Text) # Progressive hint
    difficulty_level = db.Column(db.Integer, default=1) # 1-5 for adaptive quizzes
    points = db.Column(db.Integer, default=1)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    options = db.relationship('QuizOption', backref='question', lazy=True, cascade='all, delete-orphan')
    user_answers = db.relationship('UserQuizAnswer', backref='question', lazy=True, cascade='all, delete-orphan')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class QuizOption(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_question.id'), nullable=False)
    option_text = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, default=False)
    order_index = db.Column(db.Integer, default=0)
    feedback = db.Column(db.Text)  # Specific feedback for this option

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class UserQuizAnswer(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    question_id = db.Column(db.Integer, db.ForeignKey('quiz_question.id'), nullable=False)
    selected_option_id = db.Column(db.Integer, db.ForeignKey('quiz_option.id'))
    text_answer = db.Column(db.Text)  # For fill-in-the-blank questions
    is_correct = db.Column(db.Boolean, default=False)
    answered_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    attempts = db.Column(db.Integer, default=0, nullable=False)

    __table_args__ = (db.UniqueConstraint('user_id', 'question_id'),)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class UserLessonProgress(db.Model):
    __allow_unmapped__ = True
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lesson.id'), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    is_completed = db.Column(db.Boolean, default=False)
    progress_percentage = db.Column(db.Integer, default=0)
    time_spent = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
    content_progress = db.Column(db.Text)
    
    lesson: Mapped['Lesson'] = relationship(foreign_keys=[lesson_id], overlaps="user_progress")

    __table_args__ = (db.UniqueConstraint('user_id', 'lesson_id'),)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __repr__(self):
        return f'<UserLessonProgress user:{self.user_id} lesson:{self.lesson_id}>'
    
    def get_content_progress(self):
        """Get content progress as dictionary"""
        if self.content_progress:
            return json.loads(self.content_progress)
        return {}
    
    def set_content_progress(self, progress_dict):
        """Set content progress from dictionary"""
        self.content_progress = json.dumps(progress_dict)
    
    def mark_content_completed(self, content_id):
        """Mark a specific content item as completed"""
        progress = self.get_content_progress()
        progress[str(content_id)] = True
        self.set_content_progress(progress)
        self.update_progress_percentage()

    def mark_passive_items_completed(self):
        """Markiert alle sichtbaren, NICHT-interaktiven Content-Items als erledigt.

        Robustes Sicherheitsnetz fuer den Lektionsabschluss: Wird am Lektions-Ende
        ausgeloest (letzte Seite erreicht / Scroll-Ende / Single-Page-Verweildauer).
        Damit zaehlen passive Inhalte ALLER Typen zuverlaessig zum 100%-Abschluss —
        auch solche, die im Frontend keinen eigenen "Als erledigt"-Button haben und
        sich darum bisher nie selbst melden konnten (dialog_slideshow, standalone
        audio, isolierte Einzel-Flipcards).

        Interaktive Items (Quiz via is_interactive, kana_grid_game) bleiben bewusst
        ausgenommen — sie muessen weiterhin aktiv geloest werden und melden ihren
        Abschluss ueber den jeweils eigenen Pfad (korrekte Antwort bzw. SRS-Rating).

        Returns True, wenn mindestens ein Item neu als erledigt markiert wurde.
        """
        progress = self.get_content_progress()
        changed = False
        for c in self.lesson.progress_visible_content_items:  # type: ignore
            if c.is_interactive or c.content_type == 'kana_grid_game':
                continue
            if not progress.get(str(c.id)):
                progress[str(c.id)] = True
                changed = True
        if changed:
            self.set_content_progress(progress)
        # Immer neu berechnen — auch bei changed=False: heilt Altbestand-Zeilen,
        # in denen content_progress bereits vollstaendig ist, is_completed wegen
        # des alten Nenner-Bugs aber noch False steht (Self-Healing beim Revisit).
        self.update_progress_percentage()
        return changed

    def update_progress_percentage(self):
        """Update overall progress percentage based on completed content.

        Zaehlt nur UI-sichtbare Items (siehe Lesson.progress_visible_content_items),
        sonst koennen 'audio'-Eintraege auf Slideshow-Pages nie completed werden
        und der Progress bleibt unter 100% trotz vollstaendiger Lektion.

        Eine Lektion ganz ohne sichtbare Items (z.B. nur dekorative is_optional-
        Bilder) gilt als sofort 100% abgeschlossen. WICHTIG: Der is_completed-Block
        unten MUSS in beiden Zweigen laufen — frueher gab es bei 0 Items ein
        return VOR dem Setzen von is_completed, sodass solche Lektionen zwar 100%
        zeigten, aber nie als "fertig" galten.
        """
        visible_items = self.lesson.progress_visible_content_items  # type: ignore
        total_content = len(visible_items)
        if total_content == 0:
            self.progress_percentage = 100
        else:
            visible_ids = {str(c.id) for c in visible_items}
            cp = self.get_content_progress()
            completed_content = sum(
                1 for cid in visible_ids if cp.get(cid)
            )
            self.progress_percentage = int((completed_content / total_content) * 100)

        if self.progress_percentage == 100 and not self.is_completed:
            self.is_completed = True
            self.completed_at = datetime.utcnow()

    def reset(self):
        """Reset the progress for this lesson."""
        self.completed_at = None
        self.is_completed = False
        self.progress_percentage = 0
        self.time_spent = 0
        self.content_progress = json.dumps({})
        
        # Delete all quiz answers for this lesson for the user
        content_ids = [content.id for content in self.lesson.content_items if content.is_interactive]
        if content_ids:
            question_ids = [q.id for q in QuizQuestion.query.filter(QuizQuestion.lesson_content_id.in_(content_ids)).all()]
            if question_ids:
                UserQuizAnswer.query.filter(
                    UserQuizAnswer.user_id == self.user_id,
                    UserQuizAnswer.question_id.in_(question_ids)
                ).delete(synchronize_session=False)

class LessonPurchase(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey('lesson.id', ondelete='RESTRICT'), nullable=False)
    price_paid: Mapped[float] = mapped_column(db.Float, nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    provider_transaction_id: Mapped[int] = mapped_column(BigInteger, nullable=True, index=True)
    transaction_state: Mapped[str] = mapped_column(String(50), nullable=True)

    # Relationships
    user: Mapped['User'] = relationship('User', backref='lesson_purchases')
    # Hinweis: ORM-Cascade entfernt — DB-FK ist RESTRICT, Loeschungen werden geblockt.
    lesson: Mapped['Lesson'] = relationship('Lesson', backref=db.backref('purchases'))

    __table_args__ = (db.UniqueConstraint('user_id', 'lesson_id'),)

    def __repr__(self):
        return f'<LessonPurchase user:{self.user_id} lesson:{self.lesson_id} price:{self.price_paid}>'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

course_lessons = Table('course_lessons', db.metadata,
    Column('course_id', Integer, ForeignKey('course.id'), primary_key=True),
    Column('lesson_id', Integer, ForeignKey('lesson.id'), primary_key=True)
)

class Course(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    background_image_url: Mapped[str] = mapped_column(String(255), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Pricing fields
    price: Mapped[float] = mapped_column(db.Float, nullable=False, default=0.0)
    is_purchasable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    
    lessons: Mapped[List['Lesson']] = relationship('Lesson', secondary=course_lessons, lazy='subquery',
                              back_populates='courses')

    def __repr__(self):
        return f'<Course {self.title}>'

class CoursePurchase(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    course_id: Mapped[int] = mapped_column(Integer, ForeignKey('course.id', ondelete='RESTRICT'), nullable=False)
    price_paid: Mapped[float] = mapped_column(db.Float, nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    provider_transaction_id: Mapped[int] = mapped_column(BigInteger, nullable=True, index=True)
    transaction_state: Mapped[str] = mapped_column(String(50), nullable=True)

    # Hinweis: ORM-Cascade entfernt — DB-FK ist RESTRICT, Loeschungen werden geblockt.
    course: Mapped['Course'] = relationship('Course', backref=db.backref('purchases'))

    __table_args__ = (db.UniqueConstraint('user_id', 'course_id'),)

    def __repr__(self):
        return f'<CoursePurchase user:{self.user_id} course:{self.course_id} price:{self.price_paid}>'


class CardReviewState(db.Model):
    """SRS-Zustand pro User + Content-Item (FSRS-Algorithmus)."""
    __tablename__ = 'card_review_state'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    content_id = db.Column(db.Integer, db.ForeignKey('lesson_content.id'), nullable=False)

    # FSRS Card State (kompletter State als JSON via Card.to_json())
    fsrs_card_state = db.Column(db.Text, nullable=False)

    # Denormalisierte Felder fuer Queries
    due_date = db.Column(db.DateTime, nullable=False, index=True)
    status = db.Column(db.String(20), nullable=False, default='new')
    # Werte: 'new', 'learning', 'review', 'relearning', 'suspended'

    # Statistiken
    reps = db.Column(db.Integer, default=0, nullable=False)
    lapses = db.Column(db.Integer, default=0, nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Beziehungen
    user = db.relationship('User', backref=db.backref('card_states', lazy='dynamic'))
    content = db.relationship('LessonContent', backref=db.backref('review_states', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'content_id', name='uq_user_content_review'),
        db.Index('ix_card_review_due', 'user_id', 'due_date', 'status'),
    )

    def __repr__(self):
        return f'<CardReviewState user:{self.user_id} content:{self.content_id} status:{self.status}>'


class ReviewLog(db.Model):
    """Protokoll jeder Bewertung — Basis fuer FSRS-Optimizer."""
    __tablename__ = 'review_log'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    content_id = db.Column(db.Integer, db.ForeignKey('lesson_content.id'), nullable=False)

    rating = db.Column(db.Integer, nullable=False)  # 1=Again, 2=Hard, 3=Good, 4=Easy
    reviewed_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False, index=True)
    time_taken_ms = db.Column(db.Integer)

    # FSRS ReviewLog State (fuer Optimizer)
    fsrs_review_log = db.Column(db.Text)

    # Denormalisiert fuer Statistiken
    scheduled_days = db.Column(db.Integer)
    elapsed_days = db.Column(db.Integer)
    # SRS-Stufe (0..9 aus get_card_stage) VOR diesem Review — fuer „Genauigkeit
    # nach Reife"-Statistik (/api/dashboard/acc-by-stage). Nullable: Altdaten vor
    # Einfuehrung haben keinen Wert, fuellt sich ab Einfuehrung pro Review.
    stage_at_review = db.Column(db.Integer, nullable=True)

    # Beziehungen
    user = db.relationship('User', backref=db.backref('review_logs', lazy='dynamic'))
    content = db.relationship('LessonContent')

    def __repr__(self):
        return f'<ReviewLog user:{self.user_id} content:{self.content_id} rating:{self.rating}>'


class KanaConfusion(db.Model):
    """Per-User-Verwechslungssignal: welches FALSCHE Kana wurde fuer ein
    Ziel-Kana platziert (Fehl-Drop im Kana-Grid).

    Heute wird beim Grid-Fehler nur die korrekte Zielkarte ans SRS bewertet —
    *welches* falsche Zeichen der User ablegte, ging verloren. Diese Tabelle
    sammelt genau dieses Signal und speist den gezielten Verwechslungs-Drill
    (datengetriebene Distraktoren statt nur statischer Aehnlichkeitsmatrix).
    """
    __tablename__ = 'kana_confusion'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    target_kana_id = db.Column(db.Integer, db.ForeignKey('kana.id'), nullable=False)
    confused_kana_id = db.Column(db.Integer, db.ForeignKey('kana.id'), nullable=False)
    count = db.Column(db.Integer, nullable=False, default=1, server_default='1')
    last_seen = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        db.UniqueConstraint(
            'user_id', 'target_kana_id', 'confused_kana_id', name='uq_kana_confusion'
        ),
    )

    def __repr__(self):
        return (f'<KanaConfusion u:{self.user_id} '
                f'{self.target_kana_id}<-{self.confused_kana_id} x{self.count}>')


class KanaStormScore(db.Model):
    """Eine beendete Kana-Storm-Runde eines EINGELOGGTEN Nutzers.

    Speist die persoenliche Storm-Statistik auf /review/stats (Bester Score,
    Spiele, Beste Combo, Genauigkeit, Kana getippt) und die Konto-Bestmarke im
    End-Screen. Gaeste spielen weiter rein clientseitig (localStorage) — diese
    Tabelle existiert nur fuer eingeloggte Spieler. Bewusst EINE Zeile pro Runde
    (kein Upsert), damit Aggregat UND spaeterer Verlauf moeglich bleiben.

    mode = 'storm' (Arcade gegen die Uhr) | 'daily' (Wordle-Tagesbrett). Die
    /review/stats-Sektion aggregiert NUR mode='storm'; Daily-Runden werden
    mitgeschrieben (XP) und sind fuer spaetere Auswertungen da. score/combo/
    counts kommen vom Client und werden im Endpoint hart geclamped (Anti-Cheat).
    """
    __tablename__ = 'kana_storm_score'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    mode = db.Column(db.String(16), nullable=False, default='storm', server_default='storm')
    schrift = db.Column(db.String(16), nullable=False, default='hiragana', server_default='hiragana')
    duration = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    score = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    best_combo = db.Column(db.Integer, nullable=False, default=1, server_default='1')
    correct_count = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    miss_count = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    xp_awarded = db.Column(db.Integer, nullable=False, default=0, server_default='0')
    daily_date = db.Column(db.Date, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    user = db.relationship('User', backref=db.backref('kana_storm_scores', lazy='dynamic'))

    def __repr__(self):
        return (f'<KanaStormScore u:{self.user_id} {self.mode} '
                f'score:{self.score} combo:{self.best_combo}>')


class UserSRSSettings(db.Model):
    """Persoenliche SRS-Einstellungen pro User."""
    __tablename__ = 'user_srs_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)

    desired_retention = db.Column(db.Float, default=0.9)
    daily_new_cards = db.Column(db.Integer, default=20)
    daily_review_limit = db.Column(db.Integer, default=100)

    # FSRS Optimizer Parameters (21 Floats als JSON, nach ~1000 Reviews)
    fsrs_parameters = db.Column(db.Text)

    # Phase 6: Streak-Freeze + Leech-Schwelle
    streak_freezes_available = db.Column(db.Integer, default=1, nullable=False, server_default='1')
    last_freeze_replenish = db.Column(db.Date, nullable=True)
    leech_threshold = db.Column(db.Integer, default=8, nullable=False, server_default='8')

    user = db.relationship('User', backref=db.backref('srs_settings', uselist=False))

    def __repr__(self):
        return f'<UserSRSSettings user:{self.user_id} retention:{self.desired_retention}>'


class UserAchievement(db.Model):
    """Freigeschaltete Achievements pro User."""
    __tablename__ = 'user_achievement'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    achievement_key = db.Column(db.String(50), nullable=False)
    unlocked_at = db.Column(db.DateTime, default=datetime.utcnow)
    notified = db.Column(db.Boolean, default=False, nullable=False)

    user = db.relationship('User', backref=db.backref('achievements', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'achievement_key', name='uq_user_achievement'),
    )

    def __repr__(self):
        return f'<UserAchievement user:{self.user_id} key:{self.achievement_key}>'


class DailyReviewAggregate(db.Model):
    """Taeglich aggregierte Review-Statistiken (Heatmap, Performance)."""
    __tablename__ = 'daily_review_aggregate'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False, index=True)
    review_date = db.Column(db.Date, nullable=False, index=True)

    total_reviews = db.Column(db.Integer, default=0, nullable=False)
    correct_reviews = db.Column(db.Integer, default=0, nullable=False)
    again_count = db.Column(db.Integer, default=0, nullable=False)
    hard_count = db.Column(db.Integer, default=0, nullable=False)
    good_count = db.Column(db.Integer, default=0, nullable=False)
    easy_count = db.Column(db.Integer, default=0, nullable=False)
    total_time_ms = db.Column(db.BigInteger, default=0, nullable=False)
    xp_earned = db.Column(db.Integer, default=0, nullable=False)
    new_cards_learned = db.Column(db.Integer, default=0, nullable=False)
    cards_leveled_up = db.Column(db.Integer, default=0, nullable=False)
    cards_leveled_down = db.Column(db.Integer, default=0, nullable=False)

    user = db.relationship('User', backref=db.backref('daily_aggregates', lazy='dynamic'))

    __table_args__ = (
        db.UniqueConstraint('user_id', 'review_date', name='uq_user_daily_agg'),
    )

    def __repr__(self):
        return f'<DailyReviewAggregate user:{self.user_id} date:{self.review_date}>'


class KanaGridConfig(db.Model):
    """Konfiguration eines Kana-Grid-Spiels, gekoppelt an einen LessonContent.

    1:1-Beziehung: jeder LessonContent mit content_type='kana_grid_game' hat
    genau eine KanaGridConfig. Loeschen des LessonContents kaskadiert auf
    die Config.
    """
    __tablename__ = 'kana_grid_config'

    id = db.Column(db.Integer, primary_key=True)
    lesson_content_id = db.Column(
        db.Integer,
        db.ForeignKey('lesson_content.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
    )

    # Welche Kana-IDs spielen mit (JSON-Array von Kana.id)
    kana_ids = db.Column(db.JSON, nullable=False)

    # Modus + Layout
    default_mode = db.Column(
        db.String(20), nullable=False, default='schreiben', server_default='schreiben'
    )  # 'schreiben' | 'lesen' | 'blind'
    allow_mode_switch = db.Column(
        db.Boolean, nullable=False, default=True, server_default=sa_true()
    )
    grid_layout = db.Column(
        db.String(20), nullable=False, default='rows', server_default='rows'
    )  # 'rows' = 5xn nach Kana-Reihe, 'free' = flach
    shuffle_pool = db.Column(
        db.Boolean, nullable=False, default=True, server_default=sa_true()
    )
    timer_enabled = db.Column(
        db.Boolean, nullable=False, default=False, server_default=db.text('false')
    )
    # Forschungsbasierte Anfaenger-Hilfe (Bjork Desirable Difficulties, Fading Scaffolding):
    # - max_hints: Anzahl Hint-Klicks pro Runde. Pre-Testing-Gate: Hint erst nach 1 Fehlversuch.
    #   Hint setzt Rating auf 2 (Hard) — sichtbare metakognitive Kosten.
    # - show_romaji_hint_on_pool: Pool-Karten zeigen kleines Romaji unter Hiragana.
    #   Beide Werte sinken ueber die Lesson-Reihenfolge (Fading-Scaffolding):
    #   Lesson 1 → max_hints=3, romaji=True. Lesson 4+ → max_hints=0, romaji=False.
    max_hints = db.Column(
        db.Integer, nullable=False, default=0, server_default='0'
    )
    show_romaji_hint_on_pool = db.Column(
        db.Boolean, nullable=False, default=False, server_default=db.text('false')
    )

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    content = db.relationship(
        'LessonContent',
        backref=db.backref('kana_grid_config', uselist=False, cascade='all, delete-orphan'),
    )

    def __repr__(self):
        return f'<KanaGridConfig content:{self.lesson_content_id} mode:{self.default_mode}>'


class PaymentTransaction(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    # Use BigInteger for the transaction_id as per API documentation
    transaction_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=True)
    item_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'lesson' or 'course'
    item_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[float] = mapped_column(db.Float, nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default='CHF')
    state: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Use JSON for efficient querying of webhook data
    webhook_data: Mapped[dict] = mapped_column(JSON, nullable=True)
    transaction_metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

    def __repr__(self):
        return f'<PaymentTransaction {self.transaction_id} - {self.state}>'


# SQLAlchemy event listeners to automatically maintain lesson type consistency
@event.listens_for(Lesson, 'before_insert')
@event.listens_for(Lesson, 'before_update')
def update_lesson_type_on_price_change(mapper, connection, target):
    """
    Automatically set lesson_type based on price before insert/update operations.
    This ensures consistency between lesson_type and pricing.
    
    - lesson_type = "free" when price = 0.00
    - lesson_type = "paid" when price > 0.00
    """
    if target.price == 0.0:
        target.lesson_type = "free"
    else:
        target.lesson_type = "paid"
