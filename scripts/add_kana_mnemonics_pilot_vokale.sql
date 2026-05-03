-- Pilot: Mnemonics fuer die 5 Vokale (Hiragana + Katakana)
-- Stil: Tofugu-inspirierte Bildmnemonics, deutsche Lautanker (DE-Buchstabe = JA-Laut, ohne englischen Umweg)
-- Format: 1-2 Saetze, Bild im Zeichen wiedererkennbar, Lautanker im Schluesselwort
-- Erwartete Zeilen pro UPDATE: 1
-- Datum: 2026-05-03
SET client_encoding = 'UTF8';

BEGIN;

-- =====================================================
-- HIRAGANA-Vokale (id 1-5)
-- =====================================================

UPDATE kana SET mnemonic='Sieht aus wie ein Apfel-Maennchen: oben ein waagerechter Hut, in der Mitte ein Kreuz (Koerper) und rechts eine Schleife (der Apfel im Arm). Es ruft laut: "A!" wenn es in den Apfel beisst.' WHERE id=1;

UPDATE kana SET mnemonic='Zwei senkrechte Striche nebeneinander — wie zwei stehende Igel, die sich anschauen: der linke gross, der rechte klein. Beide piepsen: "I!"' WHERE id=2;

UPDATE kana SET mnemonic='Erinnert an ein liegendes U-Boot von der Seite: kleines Periskop oben, darunter der flache Rumpf, der nach rechts schwimmt. Aus dem Periskop kommt ein langgezogenes "Uuuu".' WHERE id=3;

UPDATE kana SET mnemonic='Ein Elch im Profil: oben das Horn, darunter der lange Hals, am Ende der Bart unten rechts. Der Elch ruft: "E!"' WHERE id=4;

UPDATE kana SET mnemonic='Eine kleine Oma mit Dutt: das Kreuz in der Mitte ist ihr Koerper, links steht sie aufrecht, der Punkt rechts oben ist ihr Dutt. Sie ruft erstaunt: "Oh!"' WHERE id=5;

-- =====================================================
-- KATAKANA-Vokale (id 105-109)
-- =====================================================

UPDATE kana SET mnemonic='Wie ein Axt-Kopf von der Seite: oben der diagonale Schnitt der Klinge, rechts der kurze Stiel. Wer die Axt schwingt, ruft: "A!"' WHERE id=105;

UPDATE kana SET mnemonic='Ein I-Schild aus zwei Latten: lange senkrechte Latte rechts, kurze schraege Stuetze oben links. So steht das I auf einem Igel-Pfahl im Garten.' WHERE id=106;

UPDATE kana SET mnemonic='Wie eine U-Boot-Bruecke: kleines Huetchen (Periskop) oben, darunter der breite Bogen mit Strich nach unten. Aus dem Bogen kommt ein "U!"' WHERE id=107;

UPDATE kana SET mnemonic='Wie der Buchstabe E auf der Seite: drei waagerechte Striche, der mittlere und der untere bilden den Boden. Stell dir den Esel vor, der "E!" schreit.' WHERE id=108;

UPDATE kana SET mnemonic='Wie ein Schluessel zum Ofen: ein Kreuz mit einem kleinen Haken nach rechts unten. "Ohne Schluessel kein Ofen — Oh!"' WHERE id=109;

-- =====================================================
-- Verifikation
-- =====================================================
SELECT id, character, romanization, type, LEFT(mnemonic, 80) AS mnemonic_preview
FROM kana
WHERE id IN (1,2,3,4,5,105,106,107,108,109)
ORDER BY type, id;

COMMIT;
