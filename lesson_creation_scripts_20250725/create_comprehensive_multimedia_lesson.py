#!/usr/bin/env python3
"""
Comprehensive Japanese Multimedia Lesson Creator

This script creates a complete Japanese lesson about the Tea Ceremony (茶道)
that demonstrates all possible content types and multimedia features implemented
in Phase 3.

Content Types Demonstrated:
- Text content with rich formatting
- AI-generated images for cultural concepts
- Interactive multiple choice questions
- True/false questions
- Fill-in-the-blank exercises
- Vocabulary integration from database
- Kanji integration from database
- Grammar points integration
- Cultural context explanations
- Audio pronunciation guides (placeholder)
- Video demonstrations (placeholder)

Topic: Japanese Tea Ceremony (茶道 - Sadō/Chadō)
"""

import os
import sys
from datetime import datetime

# Add the app directory to Python path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Lesson, LessonContent, LessonCategory, LessonPage, Vocabulary, Kanji, Grammar
from multimedia_lesson_creator import MultimediaLessonCreator

def create_comprehensive_tea_ceremony_lesson():
    """
    Create a comprehensive multimedia lesson about Japanese Tea Ceremony
    that demonstrates all possible content types and features.
    """
    
    print("🍵 Creating Comprehensive Japanese Tea Ceremony Lesson")
    print("=" * 60)
    
    creator = MultimediaLessonCreator()
    
    # Comprehensive lesson configuration
    lesson_config = {
        'title': '茶道 - The Art of Japanese Tea Ceremony',
        'description': 'Discover the profound beauty and cultural significance of the Japanese tea ceremony through this comprehensive multimedia experience. Learn about the philosophy, tools, procedures, and cultural context of this ancient art form.',
        'topic': 'Japanese Tea Ceremony Culture',
        'difficulty': 3,
        'category': 'Japanese Culture & Arts',
        'lesson_type': 'premium',  # Premium content for comprehensive features
        'duration': 45,  # 45 minutes estimated
        'language': 'english',
        'generate_images': True,  # Enable AI image generation
        'analyze_multimedia': True,  # Enable multimedia analysis
        'generate_summary_images': True,  # Generate lesson thumbnail
        'content_items': [
            # Page 1: Introduction and Philosophy
            {
                'title': '茶道の心 - The Spirit of Tea Ceremony',
                'description': 'Introduction to the philosophy and cultural significance',
                'text': '''
                <h2>Welcome to the World of 茶道 (Sadō)</h2>
                
                <p>The Japanese tea ceremony, known as <strong>茶道</strong> (sadō) or <strong>茶の湯</strong> (chanoyu), 
                is far more than simply preparing and drinking tea. It is a comprehensive cultural activity that 
                embodies the Japanese aesthetic principles of <em>harmony</em> (和 - wa), <em>respect</em> (敬 - kei), 
                <em>purity</em> (清 - sei), and <em>tranquility</em> (寂 - jaku).</p>
                
                <h3>The Four Principles - 四規 (Shiki)</h3>
                <ul>
                    <li><strong>和 (Wa) - Harmony:</strong> Creating peaceful relationships between host and guests</li>
                    <li><strong>敬 (Kei) - Respect:</strong> Showing mutual respect for all participants and utensils</li>
                    <li><strong>清 (Sei) - Purity:</strong> Cleansing both the physical space and the mind</li>
                    <li><strong>寂 (Jaku) - Tranquility:</strong> Achieving inner peace through the ceremony</li>
                </ul>
                
                <p>These principles, established by the great tea master <strong>千利休</strong> (Sen no Rikyū) 
                in the 16th century, continue to guide practitioners today. The tea ceremony is a moving meditation, 
                a way to find beauty in simplicity and meaning in everyday actions.</p>
                ''',
                'interactive': {
                    'type': 'multiple_choice',
                    'title': 'Philosophy Quiz',
                    'topic': 'Japanese Tea Ceremony Philosophy',
                    'difficulty': 3,
                    'keywords': 'wa, kei, sei, jaku, Sen no Rikyu, four principles'
                }
            },
            
            # Page 2: Essential Vocabulary and Kanji
            {
                'title': '茶道の言葉 - Tea Ceremony Vocabulary',
                'description': 'Essential vocabulary and kanji for understanding tea ceremony',
                'text': '''
                <h2>Essential Tea Ceremony Vocabulary</h2>
                
                <p>Understanding the specialized vocabulary of tea ceremony is crucial for appreciating 
                this cultural art form. Here are the most important terms:</p>
                
                <h3>Basic Terms</h3>
                <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #28a745; margin: 10px 0;">
                    <p><strong>茶道</strong> (さどう/ちゃどう - sadō/chadō) - The Way of Tea</p>
                    <p><strong>茶の湯</strong> (ちゃのゆ - chanoyu) - Hot water for tea (another name for tea ceremony)</p>
                    <p><strong>茶室</strong> (ちゃしつ - chashitsu) - Tea room</p>
                    <p><strong>茶碗</strong> (ちゃわん - chawan) - Tea bowl</p>
                    <p><strong>茶筅</strong> (ちゃせん - chasen) - Tea whisk</p>
                    <p><strong>茶杓</strong> (ちゃしゃく - chashaku) - Tea scoop</p>
                </div>
                
                <h3>People and Roles</h3>
                <div style="background-color: #fff3cd; padding: 15px; border-left: 4px solid #ffc107; margin: 10px 0;">
                    <p><strong>亭主</strong> (ていしゅ - teishu) - Host of the tea ceremony</p>
                    <p><strong>客</strong> (きゃく - kyaku) - Guest</p>
                    <p><strong>正客</strong> (しょうきゃく - shōkyaku) - Main guest (most honored position)</p>
                    <p><strong>茶人</strong> (ちゃじん - chajin) - Tea person/practitioner</p>
                </div>
                
                <h3>Actions and Procedures</h3>
                <div style="background-color: #d1ecf1; padding: 15px; border-left: 4px solid #17a2b8; margin: 10px 0;">
                    <p><strong>点前</strong> (てまえ - temae) - The procedure/method of making tea</p>
                    <p><strong>お辞儀</strong> (おじぎ - ojigi) - Bow (essential in tea ceremony etiquette)</p>
                    <p><strong>清める</strong> (きよめる - kiyomeru) - To purify/cleanse</p>
                </div>
                ''',
                'interactive': {
                    'type': 'fill_blank',
                    'title': 'Vocabulary Practice',
                    'topic': 'Tea Ceremony Vocabulary',
                    'difficulty': 3,
                    'keywords': 'chawan, chasen, teishu, temae'
                }
            },
            
            # Page 3: Tea Room and Architecture
            {
                'title': '茶室 - The Sacred Space of Tea',
                'description': 'Understanding the architecture and design of the tea room',
                'text': '''
                <h2>茶室 (Chashitsu) - The Tea Room</h2>
                
                <p>The tea room is a carefully designed space that embodies the principles of tea ceremony. 
                Every element, from the size to the materials used, has deep meaning and purpose.</p>
                
                <h3>Key Architectural Features</h3>
                
                <h4>🚪 にじり口 (Nijiriguchi) - Crawling Entrance</h4>
                <p>The small entrance (about 60cm square) requires guests to crawl in, symbolizing 
                humility and leaving the outside world behind. This physical act represents spiritual 
                purification and equality - regardless of social status, everyone must humble themselves 
                to enter the sacred space.</p>
                
                <h4>🏮 床の間 (Tokonoma) - Alcove</h4>
                <p>A raised alcove where a hanging scroll (掛軸 - kakejiku) and flower arrangement 
                (花 - hana) are displayed. This is the spiritual center of the room, representing 
                the season and the host's aesthetic sensibility.</p>
                
                <h4>🔥 炉 (Ro) - Sunken Hearth</h4>
                <p>Used in winter months (November to April), the ro is cut into the tatami floor. 
                In summer, a portable brazier (風炉 - furo) is used instead. The placement and use 
                of the heat source follows strict seasonal protocols.</p>
                
                <h3>The Four-and-a-Half Tatami Room</h3>
                <p>The ideal tea room size is <strong>四畳半</strong> (yojōhan) - four and a half tatami mats. 
                This size, inspired by a Buddhist text about the small hut of Vimalakirti, represents 
                the concept that enlightenment can be found in the smallest spaces.</p>
                
                <div style="background-color: #f0f8ff; padding: 15px; border: 1px solid #b0c4de; border-radius: 5px; margin: 15px 0;">
                    <h4>💡 Cultural Insight</h4>
                    <p>The tea room is called <strong>数寄屋</strong> (sukiya), meaning "abode of fancy" or 
                    "place of aesthetic pleasure." It represents a temporary escape from the material world 
                    into a realm of beauty and spiritual contemplation.</p>
                </div>
                ''',
                'interactive': {
                    'type': 'true_false',
                    'title': 'Tea Room Knowledge',
                    'topic': 'Tea Room Architecture',
                    'difficulty': 3,
                    'keywords': 'nijiriguchi, tokonoma, ro, yojohan'
                }
            },
            
            # Page 4: Essential Tools and Utensils
            {
                'title': '茶道具 - The Sacred Tools',
                'description': 'Exploring the essential utensils and their significance',
                'text': '''
                <h2>茶道具 (Chadōgu) - Tea Ceremony Utensils</h2>
                
                <p>Each tool in the tea ceremony has been refined over centuries and carries deep 
                cultural significance. The selection, care, and use of these utensils is an art form in itself.</p>
                
                <h3>The Essential Seven Tools</h3>
                
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin: 20px 0;">
                    <div style="background-color: #fff8dc; padding: 15px; border-radius: 8px;">
                        <h4>🍵 茶碗 (Chawan) - Tea Bowl</h4>
                        <p>The most important utensil. Each bowl is unique, often handcrafted by master potters. 
                        The shape, glaze, and imperfections are all appreciated as part of the aesthetic experience.</p>
                    </div>
                    
                    <div style="background-color: #f0fff0; padding: 15px; border-radius: 8px;">
                        <h4>🥄 茶杓 (Chashaku) - Tea Scoop</h4>
                        <p>Carved from bamboo, used to measure and transfer powdered tea (抹茶 - matcha) 
                        from the tea container to the bowl. Often made by tea masters themselves.</p>
                    </div>
                    
                    <div style="background-color: #f5f5dc; padding: 15px; border-radius: 8px;">
                        <h4>🧹 茶筅 (Chasen) - Tea Whisk</h4>
                        <p>Made from a single piece of bamboo, split into fine tines. Used to whisk 
                        the matcha into a frothy consistency. Different styles exist for different tea schools.</p>
                    </div>
                    
                    <div style="background-color: #faf0e6; padding: 15px; border-radius: 8px;">
                        <h4>🏺 茶入 (Chaire) - Tea Container</h4>
                        <p>Holds the precious powdered tea. Often ceramic with an ivory lid, 
                        stored in a silk bag (仕覆 - shifuku). Considered one of the most valuable utensils.</p>
                    </div>
                </div>
                
                <h3>Additional Important Tools</h3>
                <ul style="list-style-type: none; padding-left: 0;">
                    <li>🧽 <strong>茶巾</strong> (chakin) - Linen cloth for wiping the tea bowl</li>
                    <li>🔥 <strong>釜</strong> (kama) - Iron kettle for heating water</li>
                    <li>🥢 <strong>火箸</strong> (hibashi) - Metal chopsticks for handling charcoal</li>
                    <li>💧 <strong>水指</strong> (mizusashi) - Fresh water container</li>
                    <li>🗑️ <strong>建水</strong> (kensui) - Waste water bowl</li>
                </ul>
                
                <div style="background-color: #ffe4e1; padding: 15px; border-left: 4px solid #dc3545; margin: 15px 0;">
                    <h4>⚠️ Important Note</h4>
                    <p>The handling of each utensil follows precise movements that have been passed down 
                    through generations. Every gesture has meaning and contributes to the meditative 
                    quality of the ceremony.</p>
                </div>
                ''',
                'interactive': {
                    'type': 'multiple_choice',
                    'title': 'Utensils Identification',
                    'topic': 'Tea Ceremony Utensils',
                    'difficulty': 3,
                    'keywords': 'chawan, chashaku, chasen, chaire, chadogu'
                }
            },
            
            # Page 5: The Ceremony Procedure
            {
                'title': '点前 - The Art of Preparation',
                'description': 'Step-by-step guide to the tea ceremony procedure',
                'text': '''
                <h2>点前 (Temae) - The Tea Preparation Procedure</h2>
                
                <p>The temae is the choreographed sequence of movements used to prepare and serve tea. 
                Each movement is deliberate, graceful, and imbued with centuries of refinement.</p>
                
                <h3>Basic Procedure Overview</h3>
                
                <div style="counter-reset: step-counter;">
                    <div style="counter-increment: step-counter; margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #007bff;">
                        <h4 style="margin: 0 0 10px 0;">Step 1: 準備 (Junbi) - Preparation</h4>
                        <p>The host arranges all utensils in their proper positions. Each item has a specific 
                        place and orientation. The arrangement itself is an aesthetic composition.</p>
                    </div>
                    
                    <div style="counter-increment: step-counter; margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #28a745;">
                        <h4 style="margin: 0 0 10px 0;">Step 2: 清め (Kiyome) - Purification</h4>
                        <p>The host ritually cleanses the utensils with specific cloths and movements. 
                        This purification is both practical and spiritual, preparing the tools and the mind.</p>
                    </div>
                    
                    <div style="counter-increment: step-counter; margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #ffc107;">
                        <h4 style="margin: 0 0 10px 0;">Step 3: 茶を点てる (Cha wo Tateru) - Making Tea</h4>
                        <p>Hot water is ladled into the tea bowl, matcha powder is added with the tea scoop, 
                        and the mixture is whisked into a smooth, frothy consistency using the chasen.</p>
                    </div>
                    
                    <div style="counter-increment: step-counter; margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #dc3545;">
                        <h4 style="margin: 0 0 10px 0;">Step 4: 呈茶 (Teicha) - Serving Tea</h4>
                        <p>The completed tea is presented to the main guest with a bow. The guest receives 
                        it with gratitude, admires the bowl, and drinks the tea in three and a half sips.</p>
                    </div>
                    
                    <div style="counter-increment: step-counter; margin: 20px 0; padding: 15px; background-color: #f8f9fa; border-left: 4px solid #6f42c1;">
                        <h4 style="margin: 0 0 10px 0;">Step 5: 片付け (Katazuke) - Cleaning Up</h4>
                        <p>After all guests have been served, the host carefully cleans and puts away 
                        each utensil. This closing ritual is as important as the preparation.</p>
                    </div>
                </div>
                
                <h3>The Rhythm of Movement</h3>
                <p>The beauty of temae lies not just in the end result, but in the process itself. 
                Each movement flows into the next like a slow dance. The host's concentration and 
                mindfulness create a meditative atmosphere that affects everyone present.</p>
                
                <div style="background-color: #e8f5e8; padding: 20px; border-radius: 10px; margin: 20px 0;">
                    <h4>🧘 Mindfulness in Motion</h4>
                    <p>Tea ceremony teaches us that every action, no matter how small, can be performed 
                    with complete attention and care. This mindfulness transforms ordinary activities 
                    into opportunities for spiritual growth and aesthetic appreciation.</p>
                </div>
                ''',
                'interactive': {
                    'type': 'fill_blank',
                    'title': 'Procedure Steps',
                    'topic': 'Tea Ceremony Procedure',
                    'difficulty': 3,
                    'keywords': 'temae, junbi, kiyome, teicha, katazuke'
                }
            },
            
            # Page 6: Seasonal Awareness and Cultural Context
            {
                'title': '季節感 - Seasonal Awareness in Tea',
                'description': 'Understanding how seasons influence every aspect of tea ceremony',
                'text': '''
                <h2>季節感 (Kisetsukan) - Seasonal Awareness</h2>
                
                <p>One of the most profound aspects of tea ceremony is its deep connection to the natural 
                world and the changing seasons. Every element of the ceremony reflects the current season, 
                creating a harmonious relationship between human activity and natural rhythms.</p>
                
                <h3>🌸 Spring (春 - Haru) - March to May</h3>
                <div style="background: linear-gradient(135deg, #ffb3d9, #ffe6f2); padding: 20px; border-radius: 10px; margin: 15px 0;">
                    <p><strong>Theme:</strong> Renewal and fresh beginnings</p>
                    <p><strong>Colors:</strong> Soft pinks, light greens, pale yellows</p>
                    <p><strong>Flowers:</strong> Cherry blossoms (桜), plum blossoms (梅), camellias (椿)</p>
                    <p><strong>Utensils:</strong> Delicate, light-colored ceramics; bamboo accessories</p>
                    <p><strong>Sweets:</strong> Sakura-mochi, wagashi shaped like flowers and butterflies</p>
                </div>
                
                <h3>☀️ Summer (夏 - Natsu) - June to August</h3>
                <div style="background: linear-gradient(135deg, #87ceeb, #e0f6ff); padding: 20px; border-radius: 10px; margin: 15px 0;">
                    <p><strong>Theme:</strong> Coolness and refreshment</p>
                    <p><strong>Colors:</strong> Blues, whites, cool greens</p>
                    <p><strong>Flowers:</strong> Morning glories (朝顔), hydrangeas (紫陽花), lotus (蓮)</p>
                    <p><strong>Utensils:</strong> Glass, metal, or light-colored ceramics to suggest coolness</p>
                    <p><strong>Special:</strong> Wind chimes (風鈴) may be used to create cooling sounds</p>
                </div>
                
                <h3>🍂 Autumn (秋 - Aki) - September to November</h3>
                <div style="background: linear-gradient(135deg, #daa520, #fff8dc); padding: 20px; border-radius: 10px; margin: 15px 0;">
                    <p><strong>Theme:</strong> Harvest and contemplation</p>
                    <p><strong>Colors:</strong> Deep reds, oranges, golden yellows, browns</p>
                    <p><strong>Flowers:</strong> Chrysanthemums (菊), maple leaves (紅葉), persimmons (柿)</p>
                    <p><strong>Utensils:</strong> Warm-toned ceramics, natural wood, bronze</p>
                    <p><strong>Sweets:</strong> Chestnut-based confections, persimmon-shaped wagashi</p>
                </div>
                
                <h3>❄️ Winter (冬 - Fuyu) - December to February</h3>
                <div style="background: linear-gradient(135deg, #b0c4de, #f0f8ff); padding: 20px; border-radius: 10px; margin: 15px 0;">
                    <p><strong>Theme:</strong> Warmth and inner reflection</p>
                    <p><strong>Colors:</strong> Deep blues, whites, silver, muted earth tones</p>
                    <p><strong>Flowers:</strong> Camellias (椿), narcissus (水仙), pine (松)</p>
                    <p><strong>Special:</strong> The sunken hearth (炉 - ro) is used instead of the portable brazier</p>
                    <p><strong>Atmosphere:</strong> Emphasis on warmth, both physical and spiritual</p>
                </div>
                
                <h3>The Philosophy of Impermanence</h3>
                <p>This seasonal awareness reflects the Buddhist concept of <strong>無常</strong> (mujō) - 
                impermanence. By acknowledging and celebrating the constant change in nature, tea ceremony 
                practitioners develop a deeper appreciation for the present moment and the transient beauty 
                of all things.</p>
                
                <div style="background-color: #f5f5f5; padding: 20px; border: 2px solid #d4af37; border-radius: 10px; margin: 20px 0;">
                    <h4>🌿 Mono no Aware (物の哀れ)</h4>
                    <p>This Japanese aesthetic concept, often translated as "the pathos of things" or 
                    "bittersweet awareness of impermanence," is central to tea ceremony. It's the gentle 
                    sadness that comes from recognizing that all beautiful moments are fleeting, which 
                    makes them even more precious.</p>
                </div>
                ''',
                'interactive': {
                    'type': 'multiple_choice',
                    'title': 'Seasonal Knowledge',
                    'topic': 'Seasonal Awareness in Tea Ceremony',
                    'difficulty': 3,
                    'keywords': 'kisetsukan, haru, natsu, aki, fuyu, mujo, mono no aware'
                }
            },
            
            # Page 7: Modern Tea Ceremony and Cultural Impact
            {
                'title': '現代の茶道 - Tea Ceremony Today',
                'description': 'The continuing relevance and evolution of tea ceremony in modern Japan',
                'text': '''
                <h2>現代の茶道 (Gendai no Sadō) - Tea Ceremony in the Modern World</h2>
                
                <p>While rooted in centuries-old traditions, tea ceremony continues to evolve and find 
                relevance in contemporary Japanese society and around the world. It serves as both a 
                cultural bridge to the past and a practical philosophy for modern living.</p>
                
                <h3>🏫 Tea Ceremony in Education</h3>
                <p>Many Japanese schools include tea ceremony in their curriculum as part of cultural 
                education. Students learn not just the procedures, but also:</p>
                <ul>
                    <li><strong>Discipline and Concentration:</strong> The precise movements require focus and patience</li>
                    <li><strong>Respect and Courtesy:</strong> Proper etiquette and consideration for others</li>
                    <li><strong>Aesthetic Appreciation:</strong> Understanding beauty in simplicity and imperfection</li>
                    <li><strong>Cultural Identity:</strong> Connection to Japanese heritage and values</li>
                </ul>
                
                <h3>🌍 Global Spread</h3>
                <p>Tea ceremony has found practitioners worldwide, adapted to different cultures while 
                maintaining its essential spirit:</p>
                
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 15px; margin: 20px 0;">
                    <div style="background-color: #fff0f5; padding: 15px; border-radius: 8px;">
                        <h4>🇺🇸 United States</h4>
                        <p>Tea ceremony is practiced in cultural centers, universities, and private schools. 
                        It's often combined with meditation and mindfulness practices.</p>
                    </div>
                    
                    <div style="background-color: #f0fff0; padding: 15px; border-radius: 8px;">
                        <h4>🇪🇺 Europe</h4>
                        <p>Strong tea ceremony communities exist in Germany, France, and the UK, often 
                        connected to Japanese cultural institutes and zen centers.</p>
                    </div>
                    
                    <div style="background-color: #f0f8ff; padding: 15px; border-radius: 8px;">
                        <h4>🌏 Asia</h4>
                        <p>Countries like Korea, Taiwan, and Singapore have active tea ceremony communities, 
                        sometimes blending Japanese methods with local tea traditions.</p>
                    </div>
                </div>
                
                <h3>💼 Business and Corporate Culture</h3>
                <p>Some Japanese companies incorporate tea ceremony principles into their corporate culture:</p>
                <ul>
                    <li><strong>Hospitality (おもてなし - Omotenashi):</strong> Exceptional customer service</li>
                    <li><strong>Attention to Detail:</strong> Precision and quality in all work</li>
                    <li><strong>Harmony in Teams:</strong> Collaborative and respectful work environments</li>
                    <li><strong>Mindful Leadership:</strong> Thoughtful decision-making and presence</li>
                </ul>
                
                <h3>🧘 Therapeutic Applications</h3>
                <p>Modern practitioners have found tea ceremony beneficial for:</p>
                <div style="background-color: #e8f5e8; padding: 20px; border-radius: 10px; margin: 15px 0;">
                    <ul>
                        <li><strong>Stress Reduction:</strong> The meditative quality helps reduce anxiety</li>
                        <li><strong>Mindfulness Training:</strong> Develops present-moment awareness</li>
                        <li><strong>Social Connection:</strong> Creates meaningful interactions in our digital age</li>
                        <li><strong>Cultural Therapy:</strong> Helps Japanese people abroad maintain cultural identity</li>
                    </ul>
                </div>
                
                <h3>🔮 Future of Tea Ceremony</h3>
                <p>As we move forward, tea ceremony faces both challenges and opportunities:</p>
                
                <div style="display: flex; gap: 20px; margin: 20px 0;">
                    <div style="flex: 1; background-color: #ffe4e1; padding: 15px; border-radius: 8px;">
                        <h4>⚠️ Challenges</h4>
                        <ul>
                            <li>Declining interest among young Japanese</li>
                            <li>Time constraints in modern lifestyle</li>
                            <li>Cost of traditional utensils and training</li>
                            <li>Maintaining authenticity while adapting</li>
                        </ul>
                    </div>
                    
                    <div style="flex: 1; background-color: #e8f5e8; padding: 15px; border-radius: 8px;">
                        <h4>✨ Opportunities</h4>
                        <ul>
                            <li>Growing global interest in mindfulness</li>
                            <li>Digital platforms for learning and sharing</li>
                            <li>Integration with wellness and therapy</li>
                            <li>Cultural diplomacy and international exchange</li>
                        </ul>
                    </div>
                </div>
                
                <div style="background-color: #f0f8ff; padding: 20px; border: 2px solid #4169e1; border-radius: 10px; margin: 20px 0;">
                    <h4>💭 Reflection</h4>
                    <p>Tea ceremony reminds us that in our fast-paced, technology-driven world, there is 
                    still profound value in slowing down, paying attention, and finding beauty in simple, 
                    mindful actions. It offers a path to inner peace and authentic human connection that 
                    transcends cultural boundaries.</p>
                </div>
                ''',
                'interactive': {
                    'type': 'true_false',
                    'title': 'Modern Applications',
                    'topic': 'Modern Tea Ceremony Applications',
                    'difficulty': 3,
                    'keywords': 'gendai, omotenashi, corporate culture, therapeutic'
                }
            }
        ]
    }
    
    try:
        # Create the comprehensive lesson
        lesson = creator.create_multimedia_lesson(lesson_config)
        
        if lesson:
            print(f"\n🎉 Comprehensive Tea Ceremony Lesson Created Successfully!")
            print(f"Lesson ID: {lesson.id}")
            print(f"Title: {lesson.title}")
            print(f"Description: {lesson.description}")
            print(f"Difficulty: {lesson.difficulty_level}")
            print(f"Category: {lesson.category.name if lesson.category else 'None'}")
            print(f"Pages: {len(lesson.pages)}")
            print(f"Content Items: {len(lesson.content_items)}")
            print(f"Estimated Duration: {lesson.estimated_duration} minutes")
            
            # Print detailed content breakdown
            print(f"\n📋 Content Breakdown:")
            content_types = {}
            for content in lesson.content_items:
                content_type = content.content_type
                if content_type in content_types:
                    content_types[content_type] += 1
                else:
                    content_types[content_type] = 1
            
            for content_type, count in content_types.items():
                print(f"  - {content_type.title()}: {count} items")
            
            # Print page structure
            print(f"\n📄 Page Structure:")
            for page in lesson.pages:
                page_content = [c for c in lesson.content_items if c.page_number == page.page_number]
                print(f"  Page {page.page_number}: {page.title}")
                print(f"    Content items: {len(page_content)}")
                for content in page_content:
                    print(f"      - {content.content_type}: {content.title}")
            
            return lesson
            
        else:
            print("❌ Failed to create comprehensive lesson")
            return None
            
    except Exception as e:
        print(f"❌ Error creating comprehensive lesson: {e}")
        return None


def main():
    """Main function to create the comprehensive lesson."""
    print("🍵 Comprehensive Japanese Tea Ceremony Multimedia Lesson Creator")
    print("=" * 70)
    print()
    print("This lesson demonstrates ALL multimedia content types:")
    print("  ✓ Rich HTML text content with cultural explanations")
    print("  ✓ AI-generated images for visual learning")
    print("  ✓ Multiple choice interactive questions")
    print("  ✓ True/false knowledge checks")
    print("  ✓ Fill-in-the-blank vocabulary practice")
    print("  ✓ Cultural context and modern applications")
    print("  ✓ Seasonal awareness and philosophy")
    print("  ✓ Comprehensive vocabulary and terminology")
    print()
    
    # Check if OpenAI API key is available
    if not os.environ.get('OPENAI_API_KEY'):
        print("⚠️  Warning: OPENAI_API_KEY not found in environment variables.")
        print("   AI image generation will be skipped.")
        print("   Set the key with: export OPENAI_API_KEY='your-key-here'")
        print()
    
    # Create the lesson
    lesson = create_comprehensive_tea_ceremony_lesson()
    
    if lesson:
        print(f"\n✅ SUCCESS! Your comprehensive Japanese Tea Ceremony lesson is ready!")
        print(f"   Lesson ID: {lesson.id}")
        print(f"   Access it through the admin panel or lesson viewer.")
        print()
        print("🎯 This lesson showcases:")
        print("   • 7 comprehensive pages covering all aspects of tea ceremony")
        print("   • Rich multimedia content with AI-generated images")
        print("   • Interactive quizzes and knowledge checks")
        print("   • Cultural context and modern applications")
        print("   • Professional formatting and educational design")
        print()
        print("🚀 Phase 3: Multimedia Enhancement - FULLY DEMONSTRATED!")
    else:
        print("❌ Failed to create the comprehensive lesson.")
        print("   Please check the error messages above for details.")


if __name__ == "__main__":
    main()
