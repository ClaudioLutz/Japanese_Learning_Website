/* Romaji → Hiragana (Hepburn + gaengige Tipp-Varianten).
 *
 * Kleiner, abhaengigkeitsfreier Konverter fuer das Eingabefeld des
 * Rollenspiel-Tutors. Regeln:
 *   - Standardtabelle inkl. Yoon (kya, sha, cho, ...), shi/chi/tsu/fu/ji
 *     und die Nihon-shiki-Varianten (si, ti, tu, hu, zi)
 *   - Doppelkonsonant → っ (kitte → きって, matcha → まっちゃ)
 *   - n → ん vor Konsonant / am Ende, "nn" und "n'" → ん
 *     (Hepburn: konnichiwa → こんにちわ, konna → こんな)
 *   - Langvokale: ou/oo/uu/ei werden silbenweise (おう/おお/うう/えい)
 *     umgesetzt, Makron-Vokale ebenso (tō → とう, ē → えい)
 *   - Kana, Kanji, Katakana und alles Nicht-Lateinische bleiben unveraendert
 *
 * convert(text, {partial: true}) laesst ein unvollstaendiges Ende stehen
 * ("k", "sh", "n"), damit die Live-Umwandlung beim Tippen nicht vorgreift.
 */
(function (root) {
    'use strict';

    var BASE = {
        a: 'あ', i: 'い', u: 'う', e: 'え', o: 'お',
        ka: 'か', ki: 'き', ku: 'く', ke: 'け', ko: 'こ',
        ga: 'が', gi: 'ぎ', gu: 'ぐ', ge: 'げ', go: 'ご',
        sa: 'さ', si: 'し', shi: 'し', su: 'す', se: 'せ', so: 'そ',
        za: 'ざ', zi: 'じ', ji: 'じ', zu: 'ず', ze: 'ぜ', zo: 'ぞ',
        ta: 'た', ti: 'ち', chi: 'ち', tu: 'つ', tsu: 'つ', te: 'て', to: 'と',
        da: 'だ', di: 'ぢ', du: 'づ', de: 'で', do: 'ど',
        na: 'な', ni: 'に', nu: 'ぬ', ne: 'ね', no: 'の',
        ha: 'は', hi: 'ひ', hu: 'ふ', fu: 'ふ', he: 'へ', ho: 'ほ',
        ba: 'ば', bi: 'び', bu: 'ぶ', be: 'べ', bo: 'ぼ',
        pa: 'ぱ', pi: 'ぴ', pu: 'ぷ', pe: 'ぺ', po: 'ぽ',
        ma: 'ま', mi: 'み', mu: 'む', me: 'め', mo: 'も',
        ya: 'や', yu: 'ゆ', yo: 'よ',
        ra: 'ら', ri: 'り', ru: 'る', re: 'れ', ro: 'ろ',
        la: 'ら', li: 'り', lu: 'る', le: 'れ', lo: 'ろ',
        wa: 'わ', wi: 'うぃ', we: 'うぇ', wo: 'を',
        va: 'ゔぁ', vi: 'ゔぃ', vu: 'ゔ', ve: 'ゔぇ', vo: 'ゔぉ',
        fa: 'ふぁ', fi: 'ふぃ', fe: 'ふぇ', fo: 'ふぉ',
        je: 'じぇ', che: 'ちぇ', she: 'しぇ',
        // Kleine Kana (explizit)
        xa: 'ぁ', xi: 'ぃ', xu: 'ぅ', xe: 'ぇ', xo: 'ぉ',
        xya: 'ゃ', xyu: 'ゅ', xyo: 'ょ', xtu: 'っ', xtsu: 'っ', ltu: 'っ', xwa: 'ゎ'
    };

    // Yoon: <Konsonant>y + a/u/o
    var YOON = {
        ky: 'き', gy: 'ぎ', sy: 'し', zy: 'じ', jy: 'じ', ty: 'ち', cy: 'ち', dy: 'ぢ',
        ny: 'に', hy: 'ひ', by: 'び', py: 'ぴ', my: 'み', ry: 'り',
        sh: 'し', ch: 'ち', j: 'じ'
    };
    var SMALL_Y = { a: 'ゃ', u: 'ゅ', o: 'ょ' };
    Object.keys(YOON).forEach(function (k) {
        Object.keys(SMALL_Y).forEach(function (v) { BASE[k + v] = YOON[k] + SMALL_Y[v]; });
    });

    var PUNCT = { '.': '。', ',': '、', '?': '？', '!': '！', '-': 'ー', '~': '〜' };
    // Makron-/Zirkumflex-Vokale: Grundvokal + Verlaengerung (Hepburn ō = おう, ē = えい)
    var MACRON = {
        'ā': ['a', 'あ'], 'â': ['a', 'あ'], 'ī': ['i', 'い'], 'î': ['i', 'い'],
        'ū': ['u', 'う'], 'û': ['u', 'う'], 'ē': ['e', 'い'], 'ê': ['e', 'い'],
        'ō': ['o', 'う'], 'ô': ['o', 'う']
    };
    var VOWELS = 'aiueo';
    var KEYS = Object.keys(BASE);

    function isLatin(ch) { return ch >= 'a' && ch <= 'z'; }
    function isVowel(ch) { return !!ch && VOWELS.indexOf(ch) !== -1; }
    function isPrefixOfKey(rest) {
        for (var i = 0; i < KEYS.length; i++) {
            if (KEYS[i].length > rest.length && KEYS[i].indexOf(rest) === 0) return true;
        }
        return false;
    }

    function convert(text, opts) {
        var partial = !!(opts && opts.partial);
        var src = String(text == null ? '' : text);
        var lower = src.toLowerCase();
        var out = '';
        var i = 0;
        while (i < src.length) {
            var raw = src[i];
            var ch = lower[i];

            if (MACRON[ch]) {
                out += BASE[MACRON[ch][0]] + MACRON[ch][1];
                i += 1;
                continue;
            }
            if (!isLatin(ch) && ch !== "'") {
                out += PUNCT[raw] || raw;
                i += 1;
                continue;
            }
            if (ch === "'") { i += 1; continue; }  // Silbentrenner (kin'en) faellt weg

            var next = lower[i + 1] || '';

            if (ch === 'n') {
                if (!next) {
                    out += partial ? raw : 'ん';
                    i += 1;
                    continue;
                }
                if (next === "'") { out += 'ん'; i += 2; continue; }
                if (next === 'n') {
                    var after = lower[i + 2] || '';
                    // Hepburn "konna"/"konnichiwa": erstes n = ん, dann "na"/"ni".
                    if (isVowel(after) || after === 'y') { out += 'ん'; i += 1; continue; }
                    if (!after && partial) { out += src.slice(i); break; }
                    out += 'ん';
                    i += 2;
                    continue;
                }
                if (!isVowel(next) && next !== 'y' && !MACRON[next]) { out += 'ん'; i += 1; continue; }
            }

            // Doppelkonsonant → っ (nicht bei Vokalen und n)
            if (!isVowel(ch) && ch !== 'n' && next === ch) { out += 'っ'; i += 1; continue; }
            if (ch === 't' && next === 'c' && lower[i + 2] === 'h') { out += 'っ'; i += 1; continue; }

            var matched = false;
            for (var len = 4; len >= 1 && !matched; len--) {
                var chunk = lower.substr(i, len);
                if (chunk.length < len) continue;
                var last = chunk[chunk.length - 1];
                if (MACRON[last]) {
                    // Silbe mit Makron (tō → とう, kyō → きょう)
                    var syl = BASE[chunk.slice(0, -1) + MACRON[last][0]];
                    if (len > 1 && syl) {
                        out += syl + MACRON[last][1];
                        i += len;
                        matched = true;
                    }
                    continue;
                }
                if (BASE[chunk]) {
                    out += BASE[chunk];
                    i += len;
                    matched = true;
                }
            }
            if (matched) continue;

            if (partial && isPrefixOfKey(lower.slice(i))) {
                out += src.slice(i);
                break;
            }
            out += raw;
            i += 1;
        }
        return out;
    }

    var api = { convert: convert };
    if (typeof module === 'object' && module.exports) {
        module.exports = api;
    } else {
        root.RomajiToKana = api;
    }
})(typeof window !== 'undefined' ? window : this);
