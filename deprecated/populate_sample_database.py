#!/usr/bin/env python3
"""
Database Population Script for Testing Database-Aware Lesson Creation

This script populates the database with sample Japanese learning content
to test the database-aware lesson creation system functionality.

Content includes:
- Basic Hiragana and Katakana characters
- Essential Kanji with JLPT levels
- Common vocabulary words
- Basic grammar points
"""

import os
import sys
from dotenv import load_dotenv

# Add the app directory to Python path
sys.path.insert(0, os.path.dirname(__file__))

# Load environment variables
load_dotenv()

from app import create_app, db
from app.models import Kana, Kanji, Vocabulary, Grammar

def populate_kana():
    """Populate basic Hiragana and Katakana characters."""
    print("📝 Populating Kana characters...")
    
    # Basic Hiragana characters
    hiragana_data = [
        ('あ', 'a'), ('い', 'i'), ('う', 'u'), ('え', 'e'), ('お', 'o'),
        ('か', 'ka'), ('き', 'ki'), ('く', 'ku'), ('け', 'ke'), ('こ', 'ko'),
        ('さ', 'sa'), ('し', 'shi'), ('す', 'su'), ('せ', 'se'), ('そ', 'so'),
        ('た', 'ta'), ('ち', 'chi'), ('つ', 'tsu'), ('て', 'te'), ('と', 'to'),
        ('な', 'na'), ('に', 'ni'), ('ぬ', 'nu'), ('ね', 'ne'), ('の', 'no'),
        ('は', 'ha'), ('ひ', 'hi'), ('ふ', 'fu'), ('へ', 'he'), ('ほ', 'ho'),
        ('ま', 'ma'), ('み', 'mi'), ('む', 'mu'), ('め', 'me'), ('も', 'mo'),
        ('や', 'ya'), ('ゆ', 'yu'), ('よ', 'yo'),
        ('ら', 'ra'), ('り', 'ri'), ('る', 'ru'), ('れ', 're'), ('ろ', 'ro'),
        ('わ', 'wa'), ('を', 'wo'), ('ん', 'n')
    ]
    
    # Basic Katakana characters
    katakana_data = [
        ('ア', 'a'), ('イ', 'i'), ('ウ', 'u'), ('エ', 'e'), ('オ', 'o'),
        ('カ', 'ka'), ('キ', 'ki'), ('ク', 'ku'), ('ケ', 'ke'), ('コ', 'ko'),
        ('サ', 'sa'), ('シ', 'shi'), ('ス', 'su'), ('セ', 'se'), ('ソ', 'so'),
        ('タ', 'ta'), ('チ', 'chi'), ('ツ', 'tsu'), ('テ', 'te'), ('ト', 'to'),
        ('ナ', 'na'), ('ニ', 'ni'), ('ヌ', 'nu'), ('ネ', 'ne'), ('ノ', 'no'),
        ('ハ', 'ha'), ('ヒ', 'hi'), ('フ', 'fu'), ('ヘ', 'he'), ('ホ', 'ho'),
        ('マ', 'ma'), ('ミ', 'mi'), ('ム', 'mu'), ('メ', 'me'), ('モ', 'mo'),
        ('ヤ', 'ya'), ('ユ', 'yu'), ('ヨ', 'yo'),
        ('ラ', 'ra'), ('リ', 'ri'), ('ル', 'ru'), ('レ', 're'), ('ロ', 'ro'),
        ('ワ', 'wa'), ('ヲ', 'wo'), ('ン', 'n')
    ]
    
    # Add Hiragana
    for char, rom in hiragana_data:
        existing = Kana.query.filter_by(character=char).first()
        if not existing:
            kana = Kana(
                character=char,
                romanization=rom,
                type='hiragana'
            )
            db.session.add(kana)
    
    # Add Katakana
    for char, rom in katakana_data:
        existing = Kana.query.filter_by(character=char).first()
        if not existing:
            kana = Kana(
                character=char,
                romanization=rom,
                type='katakana'
            )
            db.session.add(kana)
    
    db.session.commit()
    
    hiragana_count = Kana.query.filter_by(type='hiragana').count()
    katakana_count = Kana.query.filter_by(type='katakana').count()
    print(f"✅ Added {hiragana_count} Hiragana and {katakana_count} Katakana characters")

def populate_kanji():
    """Populate essential Kanji characters with JLPT levels."""
    print("📝 Populating Kanji characters...")
    
    kanji_data = [
        # JLPT N5 Kanji
        ('人', 'person, people', 'じん、にん', 'ひと', 5, 2),
        ('日', 'day, sun', 'にち、じつ', 'ひ、か', 5, 4),
        ('本', 'book, origin', 'ほん', 'もと', 5, 5),
        ('水', 'water', 'すい', 'みず', 5, 4),
        ('火', 'fire', 'か', 'ひ', 5, 4),
        ('木', 'tree, wood', 'もく、ぼく', 'き', 5, 4),
        ('金', 'gold, money', 'きん', 'かね', 5, 8),
        ('土', 'earth, soil', 'ど、と', 'つち', 5, 3),
        ('一', 'one', 'いち、いつ', 'ひと', 5, 1),
        ('二', 'two', 'に', 'ふた', 5, 2),
        ('三', 'three', 'さん', 'み', 5, 3),
        ('四', 'four', 'し', 'よん', 5, 5),
        ('五', 'five', 'ご', 'いつ', 5, 4),
        ('六', 'six', 'ろく', 'む', 5, 4),
        ('七', 'seven', 'しち', 'なな', 5, 2),
        ('八', 'eight', 'はち', 'や', 5, 2),
        ('九', 'nine', 'きゅう、く', 'ここの', 5, 2),
        ('十', 'ten', 'じゅう', 'とお', 5, 2),
        ('大', 'big, large', 'だい、たい', 'おお', 5, 3),
        ('小', 'small, little', 'しょう', 'ちい、こ', 5, 3),
        ('中', 'middle, inside', 'ちゅう', 'なか', 5, 4),
        ('上', 'up, above', 'じょう', 'うえ、あ', 5, 3),
        ('下', 'down, below', 'か、げ', 'した、さ', 5, 3),
        ('左', 'left', 'さ', 'ひだり', 5, 5),
        ('右', 'right', 'う、ゆう', 'みぎ', 5, 5),
        ('前', 'front, before', 'ぜん', 'まえ', 5, 9),
        ('後', 'back, after', 'ご、こう', 'うし、あと', 5, 9),
        ('今', 'now', 'こん、きん', 'いま', 5, 4),
        ('年', 'year', 'ねん', 'とし', 5, 6),
        ('月', 'month, moon', 'げつ、がつ', 'つき', 5, 4),
        
        # JLPT N4 Kanji (sample)
        ('家', 'house, family', 'か、け', 'いえ、や', 4, 10),
        ('学', 'study, learning', 'がく', 'まな', 4, 8),
        ('校', 'school', 'こう', '', 4, 10),
        ('先', 'previous, ahead', 'せん', 'さき', 4, 6),
        ('生', 'life, birth', 'せい、しょう', 'い、う、なま', 4, 5),
        ('時', 'time', 'じ', 'とき', 4, 10),
        ('間', 'interval, space', 'かん、けん', 'あいだ、ま', 4, 12),
        ('食', 'eat, food', 'しょく', 'た、く', 4, 9),
        ('飲', 'drink', 'いん', 'の', 4, 12),
        ('買', 'buy', 'ばい', 'か', 4, 12)
    ]
    
    for char, meaning, onyomi, kunyomi, jlpt, strokes in kanji_data:
        existing = Kanji.query.filter_by(character=char).first()
        if not existing:
            kanji = Kanji(
                character=char,
                meaning=meaning,
                onyomi=onyomi,
                kunyomi=kunyomi,
                jlpt_level=jlpt,
                stroke_count=strokes
            )
            db.session.add(kanji)
    
    db.session.commit()
    
    n5_count = Kanji.query.filter_by(jlpt_level=5).count()
    n4_count = Kanji.query.filter_by(jlpt_level=4).count()
    total_count = Kanji.query.count()
    print(f"✅ Added {total_count} Kanji characters (N5: {n5_count}, N4: {n4_count})")

def populate_vocabulary():
    """Populate common vocabulary words."""
    print("📝 Populating Vocabulary...")
    
    vocabulary_data = [
        # JLPT N5 Vocabulary
        ('こんにちは', 'konnichiwa', 'hello, good afternoon', 5, 'こんにちは、田中さん。', 'Hello, Mr. Tanaka.'),
        ('ありがとう', 'arigatou', 'thank you', 5, 'ありがとうございます。', 'Thank you very much.'),
        ('すみません', 'sumimasen', 'excuse me, sorry', 5, 'すみません、駅はどこですか。', 'Excuse me, where is the station?'),
        ('はい', 'hai', 'yes', 5, 'はい、そうです。', 'Yes, that\'s right.'),
        ('いいえ', 'iie', 'no', 5, 'いいえ、違います。', 'No, that\'s wrong.'),
        ('私', 'watashi', 'I, me', 5, '私は学生です。', 'I am a student.'),
        ('あなた', 'anata', 'you', 5, 'あなたの名前は何ですか。', 'What is your name?'),
        ('名前', 'namae', 'name', 5, '私の名前は田中です。', 'My name is Tanaka.'),
        ('学生', 'gakusei', 'student', 5, '私は大学生です。', 'I am a university student.'),
        ('先生', 'sensei', 'teacher', 5, '田中先生は親切です。', 'Teacher Tanaka is kind.'),
        ('友達', 'tomodachi', 'friend', 5, '友達と映画を見ました。', 'I watched a movie with my friend.'),
        ('家族', 'kazoku', 'family', 5, '家族と一緒に住んでいます。', 'I live with my family.'),
        ('お父さん', 'otousan', 'father', 5, 'お父さんは会社員です。', 'My father is a company employee.'),
        ('お母さん', 'okaasan', 'mother', 5, 'お母さんは料理が上手です。', 'My mother is good at cooking.'),
        ('食べ物', 'tabemono', 'food', 5, '日本の食べ物が好きです。', 'I like Japanese food.'),
        ('飲み物', 'nomimono', 'drink, beverage', 5, '何か飲み物はいかがですか。', 'Would you like something to drink?'),
        ('水', 'mizu', 'water', 5, '水を一杯ください。', 'Please give me a glass of water.'),
        ('お茶', 'ocha', 'tea', 5, 'お茶を飲みませんか。', 'Would you like to drink tea?'),
        ('コーヒー', 'koohii', 'coffee', 5, '朝はコーヒーを飲みます。', 'I drink coffee in the morning.'),
        ('パン', 'pan', 'bread', 5, '朝食にパンを食べます。', 'I eat bread for breakfast.'),
        ('ご飯', 'gohan', 'rice, meal', 5, 'ご飯を食べましょう。', 'Let\'s eat rice/meal.'),
        ('肉', 'niku', 'meat', 5, '肉が好きです。', 'I like meat.'),
        ('魚', 'sakana', 'fish', 5, '魚を食べますか。', 'Do you eat fish?'),
        ('野菜', 'yasai', 'vegetables', 5, '野菜は体にいいです。', 'Vegetables are good for your body.'),
        ('果物', 'kudamono', 'fruit', 5, '果物が大好きです。', 'I love fruit.'),
        ('りんご', 'ringo', 'apple', 5, '赤いりんごを買いました。', 'I bought a red apple.'),
        ('みかん', 'mikan', 'mandarin orange', 5, 'みかんは甘いです。', 'Mandarin oranges are sweet.'),
        ('一', 'ichi', 'one', 5, '一つください。', 'Please give me one.'),
        ('二', 'ni', 'two', 5, '二人で行きます。', 'Two people will go.'),
        ('三', 'san', 'three', 5, '三時に会いましょう。', 'Let\'s meet at three o\'clock.'),
        ('四', 'yon/shi', 'four', 5, '四月は春です。', 'April is spring.'),
        ('五', 'go', 'five', 5, '五分待ってください。', 'Please wait five minutes.'),
        ('赤', 'aka', 'red', 5, '赤い花がきれいです。', 'The red flowers are beautiful.'),
        ('青', 'ao', 'blue', 5, '青い空が好きです。', 'I like the blue sky.'),
        ('白', 'shiro', 'white', 5, '白いシャツを着ています。', 'I\'m wearing a white shirt.'),
        ('黒', 'kuro', 'black', 5, '黒い猫がいます。', 'There is a black cat.'),
        ('時間', 'jikan', 'time', 5, '時間がありません。', 'I don\'t have time.'),
        ('今日', 'kyou', 'today', 5, '今日は暑いです。', 'It\'s hot today.'),
        ('明日', 'ashita', 'tomorrow', 5, '明日は雨です。', 'It will rain tomorrow.'),
        ('昨日', 'kinou', 'yesterday', 5, '昨日は忙しかったです。', 'I was busy yesterday.'),
        
        # JLPT N4 Vocabulary (sample)
        ('天気', 'tenki', 'weather', 4, '今日の天気はいいです。', 'Today\'s weather is good.'),
        ('季節', 'kisetsu', 'season', 4, '日本には四つの季節があります。', 'Japan has four seasons.'),
        ('春', 'haru', 'spring', 4, '春は花が咲きます。', 'Flowers bloom in spring.'),
        ('夏', 'natsu', 'summer', 4, '夏は暑いです。', 'Summer is hot.'),
        ('秋', 'aki', 'autumn', 4, '秋は紅葉がきれいです。', 'The autumn leaves are beautiful.'),
        ('冬', 'fuyu', 'winter', 4, '冬は雪が降ります。', 'It snows in winter.'),
        ('旅行', 'ryokou', 'travel', 4, '来月、旅行に行きます。', 'I\'m going on a trip next month.'),
        ('電車', 'densha', 'train', 4, '電車で学校に行きます。', 'I go to school by train.'),
        ('バス', 'basu', 'bus', 4, 'バスが来ました。', 'The bus has come.'),
        ('飛行機', 'hikouki', 'airplane', 4, '飛行機で日本に来ました。', 'I came to Japan by airplane.')
    ]
    
    for word, reading, meaning, jlpt, jp_example, en_example in vocabulary_data:
        existing = Vocabulary.query.filter_by(word=word).first()
        if not existing:
            vocab = Vocabulary(
                word=word,
                reading=reading,
                meaning=meaning,
                jlpt_level=jlpt,
                example_sentence_japanese=jp_example,
                example_sentence_english=en_example
            )
            db.session.add(vocab)
    
    db.session.commit()
    
    n5_count = Vocabulary.query.filter_by(jlpt_level=5).count()
    n4_count = Vocabulary.query.filter_by(jlpt_level=4).count()
    total_count = Vocabulary.query.count()
    print(f"✅ Added {total_count} Vocabulary words (N5: {n5_count}, N4: {n4_count})")

def populate_grammar():
    """Populate basic grammar points."""
    print("📝 Populating Grammar points...")
    
    grammar_data = [
        # JLPT N5 Grammar
        ('です/である', 'Copula (to be)', 'Used to state that something "is" something else. です is polite form, である is plain form.', 5, 
         '私は学生です。(I am a student.) / 彼は医者である。(He is a doctor.)'),
        
        ('は (topic particle)', 'Topic marker', 'Marks the topic of the sentence. What the sentence is about.', 5,
         '私は田中です。(As for me, I am Tanaka.) / 今日は暑いです。(As for today, it is hot.)'),
        
        ('を (object particle)', 'Object marker', 'Marks the direct object of a transitive verb.', 5,
         'りんごを食べます。(I eat an apple.) / 本を読みます。(I read a book.)'),
        
        ('に (direction/time particle)', 'Direction/Time marker', 'Indicates direction, destination, or specific time.', 5,
         '学校に行きます。(I go to school.) / 三時に会います。(I will meet at 3 o\'clock.)'),
        
        ('で (location/method particle)', 'Location/Method marker', 'Indicates location of action or method/means.', 5,
         '図書館で勉強します。(I study at the library.) / 電車で行きます。(I go by train.)'),
        
        ('が (subject particle)', 'Subject marker', 'Marks the grammatical subject of the sentence.', 5,
         '犬がいます。(There is a dog.) / 雨が降っています。(It is raining.)'),
        
        ('の (possessive particle)', 'Possessive marker', 'Shows possession or relationship between nouns.', 5,
         '私の本 (my book) / 日本の文化 (Japanese culture)'),
        
        ('と (and/with particle)', 'And/With marker', 'Connects nouns (and) or indicates accompaniment (with).', 5,
         'パンとバター (bread and butter) / 友達と映画を見ます。(I watch a movie with my friend.)'),
        
        ('ます form', 'Polite verb form', 'Polite present/future tense form of verbs.', 5,
         '食べます (eat/will eat) / 行きます (go/will go) / 見ます (see/will see)'),
        
        ('ません', 'Polite negative', 'Polite negative form of verbs.', 5,
         '食べません (don\'t eat/won\'t eat) / 行きません (don\'t go/won\'t go)'),
        
        # JLPT N4 Grammar (sample)
        ('たことがある', 'Experience', 'Expresses experience - "have done something before".', 4,
         '日本に行ったことがあります。(I have been to Japan before.)'),
        
        ('ながら', 'While doing', 'Indicates doing two actions simultaneously.', 4,
         '音楽を聞きながら勉強します。(I study while listening to music.)'),
        
        ('ばかり', 'Just/Only', 'Indicates "just did" or "only/nothing but".', 4,
         '来たばかりです。(I just came.) / ゲームばかりしています。(I do nothing but play games.)'),
        
        ('そうです (hearsay)', 'I heard that', 'Indicates information received from others.', 4,
         '雨が降るそうです。(I heard it will rain.)'),
        
        ('つもり', 'Intention', 'Expresses intention or plan to do something.', 4,
         '明日、映画を見るつもりです。(I intend to watch a movie tomorrow.)')
    ]
    
    for title, structure, explanation, jlpt, examples in grammar_data:
        existing = Grammar.query.filter_by(title=title).first()
        if not existing:
            grammar = Grammar(
                title=title,
                explanation=explanation,
                structure=structure,
                jlpt_level=jlpt,
                example_sentences=examples
            )
            db.session.add(grammar)
    
    db.session.commit()
    
    n5_count = Grammar.query.filter_by(jlpt_level=5).count()
    n4_count = Grammar.query.filter_by(jlpt_level=4).count()
    total_count = Grammar.query.count()
    print(f"✅ Added {total_count} Grammar points (N5: {n5_count}, N4: {n4_count})")

def main():
    """Main function to populate the database."""
    print("🚀 Starting Database Population for Testing Database-Aware Lesson Creation")
    print("=" * 70)
    
    # Create Flask app and context
    app = create_app()
    
    with app.app_context():
        print("📊 Current database state:")
        print(f"   Kana: {Kana.query.count()}")
        print(f"   Kanji: {Kanji.query.count()}")
        print(f"   Vocabulary: {Vocabulary.query.count()}")
        print(f"   Grammar: {Grammar.query.count()}")
        print()
        
        # Populate each content type
        populate_kana()
        populate_kanji()
        populate_vocabulary()
        populate_grammar()
        
        print()
        print("📊 Final database state:")
        print(f"   Kana: {Kana.query.count()}")
        print(f"   Kanji: {Kanji.query.count()}")
        print(f"   Vocabulary: {Vocabulary.query.count()}")
        print(f"   Grammar: {Grammar.query.count()}")
        
        print()
        print("✅ Database population completed successfully!")
        print()
        print("🎯 Next steps:")
        print("1. Test content discovery:")
        print("   python -c \"from create_jlpt_lesson_database_aware import demonstrate_content_discovery; demonstrate_content_discovery()\"")
        print()
        print("2. Create a database-aware lesson:")
        print("   python -c \"from create_jlpt_lesson_database_aware import create_jlpt_lesson; create_jlpt_lesson(5)\"")
        print()
        print("3. View lessons in frontend:")
        print("   python run.py")
        print("   Navigate to: http://localhost:5000/lessons")

if __name__ == "__main__":
    main()
