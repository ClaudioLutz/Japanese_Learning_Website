"""
Pydantic-Schema fuer MNN-Lektions-JSON-Dateien.

Validiert alle JSON-Dateien bevor sie importiert werden.
Ein Schema fuer alle 50 Lektionen — optionale Felder fuer spaetere Lektionen.

Nutzung:
    from scripts.schema import LessonData
    data = LessonData.model_validate(json.load(open("lesson01.json")))
"""

from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional


class VocabularyItem(BaseModel):
    """Einzelne Vokabel."""
    word: str = Field(..., min_length=1)
    reading: str = Field(..., min_length=1)
    meaning: str = Field(..., min_length=1)
    kanji: Optional[str] = None
    part_of_speech: Optional[str] = Field(
        None,
        pattern=r"^(noun|verb|i-adjective|na-adjective|adverb|particle|expression|counter|conjunction|prefix|suffix)$",
    )
    verb_group: Optional[int] = Field(None, ge=1, le=3)
    adjective_type: Optional[str] = Field(None, pattern=r"^(i|na)$")

    @field_validator("verb_group")
    @classmethod
    def verb_group_needs_verb(cls, v, info):
        if v is not None and info.data.get("part_of_speech") != "verb":
            raise ValueError("verb_group nur bei part_of_speech='verb' erlaubt")
        return v

    @field_validator("adjective_type")
    @classmethod
    def adjective_type_needs_adjective(cls, v, info):
        if v is not None and info.data.get("part_of_speech") not in ("i-adjective", "na-adjective"):
            raise ValueError("adjective_type nur bei Adjektiven erlaubt")
        return v


class GrammarPoint(BaseModel):
    """Einzelner Grammatikpunkt."""
    title: str = Field(..., min_length=1, max_length=200)
    structure: str = Field(..., min_length=1)
    jlpt_level: int = Field(..., ge=1, le=5)
    explanation: str = Field(..., min_length=10)
    example_sentences: str = Field(..., min_length=5)


class ConversationLine(BaseModel):
    """Einzelne Dialogzeile."""
    speaker: str = Field(..., min_length=1)
    japanese: str = Field(..., min_length=1)
    romaji: str = Field(..., min_length=1)
    english: str = Field(..., min_length=1)


class Conversation(BaseModel):
    """Konversation/Dialog."""
    title: str = Field(..., min_length=1)
    title_ja: str = Field(..., min_length=1)
    lines: list[ConversationLine] = Field(..., min_length=2)

    @field_validator("lines")
    @classmethod
    def at_least_two_speakers(cls, v):
        speakers = {line.speaker for line in v}
        if len(speakers) < 2:
            raise ValueError(f"Konversation braucht mindestens 2 Sprecher, hat nur: {speakers}")
        return v


class LessonData(BaseModel):
    """Komplettes Schema fuer eine MNN-Lektion (L1-50)."""
    source: str = Field(..., min_length=1)
    lesson_number: int = Field(..., ge=1, le=50)
    title: str = Field(..., min_length=1)
    title_ja: str = Field(..., min_length=1)
    jlpt_level: int = Field(..., ge=1, le=5)
    description: str = Field(..., min_length=1)
    vocabulary: list[VocabularyItem] = Field(..., min_length=1)
    vocabulary_countries: list[VocabularyItem] = Field(default_factory=list)
    grammar: list[GrammarPoint] = Field(..., min_length=1)
    conversation: Conversation

    @model_validator(mode="after")
    def jlpt_matches_lesson(self):
        """JLPT-Level muss zur Lektionsnummer passen."""
        if self.lesson_number <= 25 and self.jlpt_level != 5:
            raise ValueError(
                f"Lektion {self.lesson_number} (Book 1) muss JLPT N5 sein, nicht N{self.jlpt_level}"
            )
        if 26 <= self.lesson_number <= 50 and self.jlpt_level != 4:
            raise ValueError(
                f"Lektion {self.lesson_number} (Book 2) muss JLPT N4 sein, nicht N{self.jlpt_level}"
            )
        return self

    @field_validator("vocabulary")
    @classmethod
    def no_duplicate_words(cls, v):
        """Keine doppelten Vokabeln innerhalb einer Lektion."""
        words = [item.word for item in v]
        dupes = [w for w in words if words.count(w) > 1]
        if dupes:
            raise ValueError(f"Doppelte Vokabeln: {set(dupes)}")
        return v
