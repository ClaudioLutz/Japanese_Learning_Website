# Clickable Kanji Audio Feature - Technical Analysis & Implementation Guide

## Project Overview

The Japanese Learning Website is a Flask-based educational platform that teaches Japanese language through interactive lessons. The system currently displays kanji characters in flip cards within lessons, but lacks audio pronunciation functionality. This document provides a comprehensive analysis for implementing clickable kanji audio features.

## Current System Architecture

### Technology Stack
- **Backend**: Flask (Python)
- **Database**: SQLAlchemy ORM with PostgreSQL
- **Frontend**: Bootstrap 5, Vanilla JavaScript
- **Templates**: Jinja2
- **Styling**: Custom CSS with CSS variables

### Current Kanji Implementation

#### Database Structure (app/models.py)
```python
class Kanji(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    character = db.Column(db.String(5), nullable=False, unique=True)
    meaning = db.Column(db.Text, nullable=False)
    onyomi = db.Column(db.String(100), nullable=True)
    kunyomi = db.Column(db.String(100), nullable=True)
    jlpt_level = db.Column(db.Integer, nullable=True)
    stroke_order_info = db.Column(db.String(255), nullable=True)
    radical = db.Column(db.String(10), nullable=True)
    stroke_count = db.Column(db.Integer, nullable=True)
    status = db.Column(db.String(20), default='approved', nullable=False)
    created_by_ai = db.Column(db.Boolean, default=False, nullable=False)
```

#### Current Display Implementation (lesson_view.html)
```html
{% elif content.content_type == 'kanji' %}
    <span class="kana-char">{{ content_data.character }}</span>
```

Kanji are displayed in 3D flip cards with:
- **Front**: Large kanji character (80px font)
- **Back**: Meaning, on'yomi, kun'yomi, JLPT level

#### Current CSS Styling (app/static/css/custom.css)
```css
.flip-card .kana-char {
    font-size: 80px;
    color: var(--primary-color);
    font-family: 'Noto Sans JP', sans-serif;
    font-weight: 500;
    text-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}
```

## Audio Implementation Options Analysis

### Option 1: Web Speech API (Text-to-Speech)
**Pros:**
- No external dependencies
- Works offline
- No storage requirements
- Supports multiple languages including Japanese
- Real-time generation

**Cons:**
- Browser compatibility varies
- Voice quality inconsistent across browsers
- Limited control over pronunciation accuracy
- May not handle kanji readings correctly (on'yomi vs kun'yomi)

**Implementation:**
```javascript
function speakKanji(character, reading) {
    if ('speechSynthesis' in window) {
        const utterance = new SpeechSynthesisUtterance(reading || character);
        utterance.lang = 'ja-JP';
        utterance.rate = 0.8;
        speechSynthesis.speak(utterance);
    }
}
```

### Option 2: External TTS API (Google Cloud Text-to-Speech)
**Pros:**
- High-quality Japanese voices
- Accurate pronunciation
- Supports SSML for pronunciation control
- Reliable and consistent

**Cons:**
- Requires API key and billing
- Internet dependency
- API rate limits
- Additional complexity

**Implementation:**
```python
from google.cloud import texttospeech

def generate_kanji_audio(character, reading):
    client = texttospeech.TextToSpeechClient()
    synthesis_input = texttospeech.SynthesisInput(text=reading)
    voice = texttospeech.VoiceSelectionParams(
        language_code="ja-JP",
        ssml_gender=texttospeech.SsmlVoiceGender.NEUTRAL
    )
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    response = client.synthesize_speech(
        input=synthesis_input, voice=voice, audio_config=audio_config
    )
    return response.audio_content
```

### Option 3: Pre-recorded Audio Files
**Pros:**
- Highest quality pronunciation
- Consistent across all users
- No API dependencies
- Fast playback

**Cons:**
- Large storage requirements
- Need to source/record audio for all kanji
- Difficult to scale
- Static content

### Option 4: Hybrid Approach (Recommended)
**Pros:**
- Fallback mechanism ensures functionality
- Best user experience when available
- Scalable and maintainable

**Implementation Strategy:**
1. Check for pre-recorded audio file
2. Fallback to Web Speech API
3. Cache generated audio for future use

## Recommended Implementation Plan - Automated Approach

### Phase 1: Automated Japanese Text Detection & Audio Integration

#### Automatic Text Detection Strategy
Instead of manually adding audio controls to each kanji, we'll implement an automated system that:
1. **Scans all lesson content** for Japanese characters (kanji, hiragana, katakana)
2. **Automatically wraps detected text** with clickable audio elements
3. **Uses Google Text-to-Speech API** for high-quality pronunciation
4. **Caches generated audio** for performance

#### Database Schema Updates (Simplified)
```python
class LessonContent(db.Model):
    # ... existing fields ...
    auto_audio_enabled = db.Column(db.Boolean, default=True, nullable=False)
    audio_cache_enabled = db.Column(db.Boolean, default=True, nullable=False)

class AudioCache(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    text_content = db.Column(db.String(500), nullable=False, unique=True)
    audio_url = db.Column(db.String(255), nullable=False)
    language = db.Column(db.String(10), default='ja-JP', nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    access_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime, default=datetime.utcnow)
```

#### Migration Script
```python
def upgrade():
    op.add_column('lesson_content', sa.Column('auto_audio_enabled', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('lesson_content', sa.Column('audio_cache_enabled', sa.Boolean(), nullable=False, server_default='true'))
    
    op.create_table('audio_cache',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('text_content', sa.String(500), nullable=False),
        sa.Column('audio_url', sa.String(255), nullable=False),
        sa.Column('language', sa.String(10), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('access_count', sa.Integer(), nullable=True),
        sa.Column('last_accessed', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('text_content')
    )
```

### Phase 2: Backend API Development - Automated Text-to-Speech

#### Universal Text-to-Speech API Endpoint
```python
@bp.route('/api/text-to-speech', methods=['POST'])
def generate_text_to_speech():
    """
    Universal endpoint for generating audio from any Japanese text
    Supports automatic caching and Google TTS integration
    """
    data = request.json
    if not data or not data.get('text'):
        return jsonify({'error': 'Text is required'}), 400
    
    text = data['text'].strip()
    language = data.get('language', 'ja-JP')
    
    # Check cache first
    cached_audio = AudioCache.query.filter_by(text_content=text).first()
    if cached_audio:
        # Update access statistics
        cached_audio.access_count += 1
        cached_audio.last_accessed = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'audio_url': cached_audio.audio_url,
            'method': 'cached',
            'text': text
        })
    
    # Generate new audio using Google TTS
    try:
        audio_service = GoogleTTSService()
        audio_url = audio_service.generate_audio(text, language)
        
        # Cache the result
        new_cache = AudioCache(
            text_content=text,
            audio_url=audio_url,
            language=language,
            access_count=1
        )
        db.session.add(new_cache)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'audio_url': audio_url,
            'method': 'generated',
            'text': text
        })
        
    except Exception as e:
        current_app.logger.error(f"TTS generation failed: {e}")
        return jsonify({
            'success': False,
            'error': 'Audio generation failed',
            'fallback_text': text
        }), 500

@bp.route('/api/detect-japanese-text', methods=['POST'])
def detect_japanese_text():
    """
    Detect and extract Japanese text from HTML content
    Returns positions and text for automatic audio integration
    """
    data = request.json
    if not data or not data.get('html_content'):
        return jsonify({'error': 'HTML content is required'}), 400
    
    detector = JapaneseTextDetector()
    japanese_segments = detector.extract_japanese_text(data['html_content'])
    
    return jsonify({
        'success': True,
        'segments': japanese_segments,
        'count': len(japanese_segments)
    })
```

#### Google Text-to-Speech Service
```python
import hashlib
import os
from google.cloud import texttospeech
from flask import current_app, url_for

class GoogleTTSService:
    def __init__(self):
        self.client = texttospeech.TextToSpeechClient()
        self.audio_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'tts_audio')
        os.makedirs(self.audio_dir, exist_ok=True)
    
    def generate_audio(self, text, language='ja-JP'):
        """Generate audio file using Google TTS and return URL"""
        # Create unique filename based on text hash
        text_hash = hashlib.md5(text.encode('utf-8')).hexdigest()
        filename = f"tts_{text_hash}.mp3"
        filepath = os.path.join(self.audio_dir, filename)
        
        # Check if file already exists
        if os.path.exists(filepath):
            return url_for('routes.uploaded_file', filename=f'tts_audio/{filename}')
        
        # Configure TTS request
        synthesis_input = texttospeech.SynthesisInput(text=text)
        
        # Select voice (prefer female Japanese voice)
        voice = texttospeech.VoiceSelectionParams(
            language_code=language,
            name="ja-JP-Wavenet-A",  # High-quality Japanese female voice
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        
        # Configure audio output
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=0.9,  # Slightly slower for learning
            pitch=0.0
        )
        
        # Generate audio
        response = self.client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )
        
        # Save audio file
        with open(filepath, 'wb') as f:
            f.write(response.audio_content)
        
        return url_for('routes.uploaded_file', filename=f'tts_audio/{filename}')

class JapaneseTextDetector:
    def __init__(self):
        # Unicode ranges for Japanese characters
        self.hiragana_range = (0x3040, 0x309F)
        self.katakana_range = (0x30A0, 0x30FF)
        self.kanji_range = (0x4E00, 0x9FAF)
        self.japanese_punctuation = (0x3000, 0x303F)
    
    def is_japanese_char(self, char):
        """Check if character is Japanese (hiragana, katakana, or kanji)"""
        code = ord(char)
        return (
            self.hiragana_range[0] <= code <= self.hiragana_range[1] or
            self.katakana_range[0] <= code <= self.katakana_range[1] or
            self.kanji_range[0] <= code <= self.kanji_range[1] or
            self.japanese_punctuation[0] <= code <= self.japanese_punctuation[1]
        )
    
    def extract_japanese_text(self, html_content):
        """Extract Japanese text segments from HTML content"""
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(html_content, 'html.parser')
        segments = []
        
        # Find all text nodes
        for element in soup.find_all(text=True):
            text = element.strip()
            if not text:
                continue
            
            # Find Japanese text segments
            japanese_segments = self.find_japanese_segments(text)
            
            for segment in japanese_segments:
                if len(segment['text']) > 0:
                    segments.append({
                        'text': segment['text'],
                        'start': segment['start'],
                        'end': segment['end'],
                        'parent_tag': element.parent.name if element.parent else None,
                        'context': text
                    })
        
        return segments
    
    def find_japanese_segments(self, text):
        """Find continuous Japanese text segments within a string"""
        segments = []
        current_segment = ""
        start_pos = 0
        in_japanese = False
        
        for i, char in enumerate(text):
            if self.is_japanese_char(char):
                if not in_japanese:
                    # Starting new Japanese segment
                    start_pos = i
                    in_japanese = True
                    current_segment = char
                else:
                    # Continuing Japanese segment
                    current_segment += char
            else:
                if in_japanese:
                    # Ending Japanese segment
                    if len(current_segment.strip()) > 0:
                        segments.append({
                            'text': current_segment.strip(),
                            'start': start_pos,
                            'end': i
                        })
                    in_japanese = False
                    current_segment = ""
        
        # Handle segment at end of string
        if in_japanese and len(current_segment.strip()) > 0:
            segments.append({
                'text': current_segment.strip(),
                'start': start_pos,
                'end': len(text)
            })
        
        return segments
```

### Phase 3: Frontend JavaScript Implementation - Automated Audio Integration

#### Automated Japanese Text Audio System
```javascript
class AutoJapaneseAudioSystem {
    constructor() {
        this.audioCache = new Map();
        this.currentAudio = null;
        this.supportsTTS = 'speechSynthesis' in window;
        this.isProcessing = false;
        this.processedElements = new WeakSet();
        
        // Japanese character detection regex
        this.japaneseRegex = /[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF\u3000-\u303F]/g;
        
        // Initialize system
        this.init();
    }
    
    init() {
        // Process existing content on page load
        document.addEventListener('DOMContentLoaded', () => {
            this.processAllContent();
        });
        
        // Set up mutation observer for dynamic content
        this.setupMutationObserver();
        
        // Add global click handler for audio elements
        document.addEventListener('click', this.handleAudioClick.bind(this));
    }
    
    setupMutationObserver() {
        const observer = new MutationObserver((mutations) => {
            mutations.forEach((mutation) => {
                if (mutation.type === 'childList') {
                    mutation.addedNodes.forEach((node) => {
                        if (node.nodeType === Node.ELEMENT_NODE) {
                            this.processElement(node);
                        }
                    });
                }
            });
        });
        
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    processAllContent() {
        if (this.isProcessing) return;
        this.isProcessing = true;
        
        // Process all lesson content areas
        const contentAreas = document.querySelectorAll(
            '.content-item, .rich-text-content, .text-content-container, .details, .flip-card'
        );
        
        contentAreas.forEach(area => {
            if (!this.processedElements.has(area)) {
                this.processElement(area);
                this.processedElements.add(area);
            }
        });
        
        this.isProcessing = false;
    }
    
    processElement(element) {
        // Skip if already processed or if it's an audio control
        if (this.processedElements.has(element) || 
            element.classList.contains('japanese-audio-text') ||
            element.classList.contains('audio-btn')) {
            return;
        }
        
        // Process text nodes within the element
        this.processTextNodes(element);
        this.processedElements.add(element);
    }
    
    processTextNodes(element) {
        const walker = document.createTreeWalker(
            element,
            NodeFilter.SHOW_TEXT,
            {
                acceptNode: (node) => {
                    // Skip if parent already has audio functionality
                    if (node.parentElement.classList.contains('japanese-audio-text') ||
                        node.parentElement.classList.contains('audio-btn')) {
                        return NodeFilter.FILTER_REJECT;
                    }
                    
                    // Only process nodes with Japanese text
                    return this.japaneseRegex.test(node.textContent) ? 
                        NodeFilter.FILTER_ACCEPT : NodeFilter.FILTER_REJECT;
                }
            }
        );
        
        const textNodes = [];
        let node;
        while (node = walker.nextNode()) {
            textNodes.push(node);
        }
        
        // Process each text node
        textNodes.forEach(textNode => {
            this.wrapJapaneseText(textNode);
        });
    }
    
    wrapJapaneseText(textNode) {
        const text = textNode.textContent;
        const segments = this.findJapaneseSegments(text);
        
        if (segments.length === 0) return;
        
        const fragment = document.createDocumentFragment();
        let lastIndex = 0;
        
        segments.forEach(segment => {
            // Add text before Japanese segment
            if (segment.start > lastIndex) {
                fragment.appendChild(
                    document.createTextNode(text.slice(lastIndex, segment.start))
                );
            }
            
            // Create clickable Japanese text element
            const audioSpan = document.createElement('span');
            audioSpan.className = 'japanese-audio-text';
            audioSpan.textContent = segment.text;
            audioSpan.setAttribute('data-japanese-text', segment.text);
            audioSpan.setAttribute('title', 'Click to hear pronunciation');
            audioSpan.style.cursor = 'pointer';
            
            fragment.appendChild(audioSpan);
            lastIndex = segment.end;
        });
        
        // Add remaining text
        if (lastIndex < text.length) {
            fragment.appendChild(
                document.createTextNode(text.slice(lastIndex))
            );
        }
        
        // Replace original text node
        textNode.parentNode.replaceChild(fragment, textNode);
    }
    
    findJapaneseSegments(text) {
        const segments = [];
        let match;
        let currentSegment = null;
        
        // Reset regex
        this.japaneseRegex.lastIndex = 0;
        
        for (let i = 0; i < text.length; i++) {
            const char = text[i];
            const isJapanese = this.isJapaneseChar(char);
            
            if (isJapanese) {
                if (!currentSegment) {
                    currentSegment = {
                        text: char,
                        start: i,
                        end: i + 1
                    };
                } else {
                    currentSegment.text += char;
                    currentSegment.end = i + 1;
                }
            } else {
                if (currentSegment) {
                    if (currentSegment.text.trim().length > 0) {
                        segments.push(currentSegment);
                    }
                    currentSegment = null;
                }
            }
        }
        
        // Handle segment at end
        if (currentSegment && currentSegment.text.trim().length > 0) {
            segments.push(currentSegment);
        }
        
        return segments;
    }
    
    isJapaneseChar(char) {
        const code = char.charCodeAt(0);
        return (
            (code >= 0x3040 && code <= 0x309F) || // Hiragana
            (code >= 0x30A0 && code <= 0x30FF) || // Katakana
            (code >= 0x4E00 && code <= 0x9FAF) || // Kanji
            (code >= 0x3000 && code <= 0x303F)    // Japanese punctuation
        );
    }
    
    handleAudioClick(event) {
        const target = event.target;
        
        if (target.classList.contains('japanese-audio-text')) {
            event.preventDefault();
            const text = target.getAttribute('data-japanese-text');
            this.playTextAudio(text, target);
        }
    }
    
    async playTextAudio(text, element) {
        try {
            // Add visual feedback
            element.classList.add('playing-audio');
            
            // Stop any currently playing audio
            this.stopCurrentAudio();
            
            // Check cache first
            if (this.audioCache.has(text)) {
                const audio = this.audioCache.get(text);
                this.playAudio(audio, element);
                return;
            }
            
            // Request audio from server
            const response = await fetch('/api/text-to-speech', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify({
                    text: text,
                    language: 'ja-JP'
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                if (data.audio_url) {
                    // Play generated/cached audio file
                    const audio = new Audio(data.audio_url);
                    this.audioCache.set(text, audio);
                    this.playAudio(audio, element);
                } else if (data.fallback_text && this.supportsTTS) {
                    // Fallback to Web Speech API
                    this.speakText(data.fallback_text, element);
                }
            } else {
                // Final fallback to Web Speech API
                if (this.supportsTTS) {
                    this.speakText(text, element);
                } else {
                    throw new Error('No audio method available');
                }
            }
            
        } catch (error) {
            console.error('Error playing text audio:', error);
            this.showAudioError();
            element.classList.remove('playing-audio');
        }
    }
    
    playAudio(audio, element) {
        this.currentAudio = audio;
        this.currentElement = element;
        
        audio.addEventListener('ended', () => {
            element.classList.remove('playing-audio');
            this.currentAudio = null;
            this.currentElement = null;
        });
        
        audio.addEventListener('error', () => {
            element.classList.remove('playing-audio');
            this.showAudioError();
        });
        
        audio.play().catch(error => {
            console.error('Audio playback failed:', error);
            element.classList.remove('playing-audio');
            this.showAudioError();
        });
    }
    
    speakText(text, element) {
        if (!this.supportsTTS) return;
        
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.lang = 'ja-JP';
        utterance.rate = 0.8;
        utterance.pitch = 1.0;
        
        // Try to use a Japanese voice if available
        const voices = speechSynthesis.getVoices();
        const japaneseVoice = voices.find(voice => voice.lang.startsWith('ja'));
        if (japaneseVoice) {
            utterance.voice = japaneseVoice;
        }
        
        utterance.addEventListener('end', () => {
            element.classList.remove('playing-audio');
        });
        
        utterance.addEventListener('error', () => {
            element.classList.remove('playing-audio');
            this.showAudioError();
        });
        
        speechSynthesis.speak(utterance);
    }
    
    stopCurrentAudio() {
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
        }
        
        if (this.currentElement) {
            this.currentElement.classList.remove('playing-audio');
            this.currentElement = null;
        }
        
        if (speechSynthesis.speaking) {
            speechSynthesis.cancel();
        }
    }
    
    getCSRFToken() {
        const tokenElement = document.querySelector('meta[name="csrf-token"]');
        return tokenElement ? tokenElement.getAttribute('content') : '';
    }
    
    showAudioError() {
        // Remove any existing error messages
        const existingError = document.querySelector('.audio-error-toast');
        if (existingError) {
            existingError.remove();
        }
        
        // Show user-friendly error message
        const errorMsg = document.createElement('div');
        errorMsg.className = 'audio-error-toast';
        errorMsg.innerHTML = `
            <i class="fas fa-exclamation-triangle"></i>
            Audio not available
        `;
        document.body.appendChild(errorMsg);
        
        setTimeout(() => {
            errorMsg.remove();
        }, 3000);
    }
    
    // Public method to manually process new content
    processNewContent(container) {
        if (container) {
            this.processElement(container);
        } else {
            this.processAllContent();
        }
    }
}

// Initialize the automated audio system
const autoJapaneseAudio = new AutoJapaneseAudioSystem();

// Legacy support for existing kanji cards
class KanjiAudioPlayer {
    constructor() {
        this.audioSystem = autoJapaneseAudio;
    }
    
    async playKanjiAudio(kanjiId, readingType = 'character') {
        // For backward compatibility with existing kanji cards
        // This would need to be adapted based on the specific kanji data
        console.log(`Playing kanji audio for ID: ${kanjiId}, type: ${readingType}`);
        // Implementation would depend on how kanji data is structured
    }
}

// Initialize legacy player for backward compatibility
const kanjiAudioPlayer = new KanjiAudioPlayer();
```

### Phase 4: Template Updates

#### Enhanced Kanji Display with Audio Controls
```html
{% elif content.content_type == 'kanji' %}
<div class="flip-card">
    <button class="card-scene" 
            aria-label="Flip card for {{ content_data.character }} to see details"
            tabindex="0">
        <div class="card-flipper">
            <div class="card-face card-face--front">
                <div class="kanji-display-container">
                    <span class="kana-char">{{ content_data.character }}</span>
                    <div class="kanji-audio-controls">
                        <button class="audio-btn main-audio" 
                                onclick="event.stopPropagation(); kanjiAudioPlayer.playKanjiAudio({{ content_data.id }}, 'character')"
                                title="Play pronunciation">
                            <i class="fas fa-volume-up"></i>
                        </button>
                    </div>
                </div>
                <div class="flip-hint">Click to flip</div>
            </div>
            
            <div class="card-face card-face--back">
                <div class="details">
                    <p><strong>Meaning:</strong> {{ content_data.meaning }}</p>
                    {% if content_data.onyomi %}
                    <p class="reading-row">
                        <strong>On'yomi:</strong> 
                        <span class="reading-text">{{ content_data.onyomi }}</span>
                        <button class="audio-btn reading-audio" 
                                onclick="event.stopPropagation(); kanjiAudioPlayer.playKanjiAudio({{ content_data.id }}, 'onyomi')"
                                title="Play on'yomi">
                            <i class="fas fa-volume-up"></i>
                        </button>
                    </p>
                    {% endif %}
                    {% if content_data.kunyomi %}
                    <p class="reading-row">
                        <strong>Kun'yomi:</strong> 
                        <span class="reading-text">{{ content_data.kunyomi }}</span>
                        <button class="audio-btn reading-audio" 
                                onclick="event.stopPropagation(); kanjiAudioPlayer.playKanjiAudio({{ content_data.id }}, 'kunyomi')"
                                title="Play kun'yomi">
                            <i class="fas fa-volume-up"></i>
                        </button>
                    </p>
                    {% endif %}
                    {% if content_data.jlpt_level %}
                    <p><strong>JLPT Level:</strong> N{{ content_data.jlpt_level }}</p>
                    {% endif %}
                </div>
            </div>
        </div>
    </button>
</div>
{% endif %}
```

### Phase 5: CSS Styling for Audio Controls

#### Audio Button Styling
```css
/* Kanji Audio Controls */
.kanji-display-container {
    position: relative;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
}

.kanji-audio-controls {
    position: absolute;
    top: 10px;
    right: 10px;
    opacity: 0;
    transition: opacity 0.3s ease;
}

.card-scene:hover .kanji-audio-controls {
    opacity: 1;
}

.audio-btn {
    background: rgba(74, 144, 226, 0.9);
    color: white;
    border: none;
    border-radius: 50%;
    width: 35px;
    height: 35px;
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    transition: all 0.3s ease;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    font-size: 0.9rem;
}

.audio-btn:hover {
    background: var(--secondary-color);
    transform: scale(1.1);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
}

.audio-btn:active {
    transform: scale(0.95);
}

.audio-btn.playing {
    background: var(--secondary-color);
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0% { box-shadow: 0 0 0 0 rgba(80, 227, 194, 0.7); }
    70% { box-shadow: 0 0 0 10px rgba(80, 227, 194, 0); }
    100% { box-shadow: 0 0 0 0 rgba(80, 227, 194, 0); }
}

/* Reading row styling */
.reading-row {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 8px;
}

.reading-text {
    flex: 1;
}

.reading-audio {
    width: 25px;
    height: 25px;
    font-size: 0.75rem;
    flex-shrink: 0;
}

/* Audio error toast */
.audio-error-toast {
    position: fixed;
    top: 20px;
    right: 20px;
    background: #dc3545;
    color: white;
    padding: 0.75rem 1rem;
    border-radius: 8px;
    font-size: 0.875rem;
    z-index: 9999;
    animation: slideIn 0.3s ease;
}

@keyframes slideIn {
    from {
        transform: translateX(100%);
        opacity: 0;
    }
    to {
        transform: translateX(0);
        opacity: 1;
    }
}

/* Automated Japanese Text Audio Styling */
.japanese-audio-text {
    color: var(--primary-color);
    cursor: pointer;
    position: relative;
    transition: all 0.3s ease;
    border-radius: 4px;
    padding: 1px 2px;
    margin: 0 1px;
    display: inline-block;
    font-weight: 500;
}

.japanese-audio-text:hover {
    background-color: rgba(74, 144, 226, 0.1);
    color: var(--secondary-color);
    transform: translateY(-1px);
    box-shadow: 0 2px 8px rgba(74, 144, 226, 0.2);
}

.japanese-audio-text:active {
    transform: translateY(0);
    box-shadow: 0 1px 4px rgba(74, 144, 226, 0.3);
}

.japanese-audio-text.playing-audio {
    background-color: var(--secondary-color);
    color: white;
    animation: audioPlaying 1.5s infinite;
    box-shadow: 0 0 0 2px rgba(80, 227, 194, 0.3);
}

@keyframes audioPlaying {
    0%, 100% { 
        background-color: var(--secondary-color);
        transform: scale(1);
    }
    50% { 
        background-color: var(--primary-color);
        transform: scale(1.05);
    }
}

/* Audio loading indicator */
.japanese-audio-text.loading-audio {
    background: linear-gradient(90deg, 
        rgba(74, 144, 226, 0.1) 0%, 
        rgba(74, 144, 226, 0.3) 50%, 
        rgba(74, 144, 226, 0.1) 100%);
    background-size: 200% 100%;
    animation: loadingShimmer 1.5s infinite;
}

@keyframes loadingShimmer {
    0% { background-position: -200% 0; }
    100% { background-position: 200% 0; }
}

/* Enhanced audio error toast */
.audio-error-toast {
    position: fixed;
    top: 20px;
    right: 20px;
    background: linear-gradient(135deg, #dc3545, #c82333);
    color: white;
    padding: 1rem 1.5rem;
    border-radius: 12px;
    font-size: 0.875rem;
    z-index: 9999;
    animation: slideInBounce 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    box-shadow: 0 8px 25px rgba(220, 53, 69, 0.3);
    display: flex;
    align-items: center;
    gap: 0.75rem;
    max-width: 300px;
}

.audio-error-toast i {
    font-size: 1.1rem;
    flex-shrink: 0;
}

@keyframes slideInBounce {
    0% {
        transform: translateX(100%) scale(0.8);
        opacity: 0;
    }
    60% {
        transform: translateX(-10%) scale(1.05);
        opacity: 1;
    }
    100% {
        transform: translateX(0) scale(1);
        opacity: 1;
    }
}

/* Audio success feedback */
.audio-success-toast {
    position: fixed;
    top: 20px;
    right: 20px;
    background: linear-gradient(135deg, var(--secondary-color), #28a745);
    color: white;
    padding: 0.75rem 1.25rem;
    border-radius: 12px;
    font-size: 0.875rem;
    z-index: 9999;
    animation: slideInBounce 0.5s cubic-bezier(0.68, -0.55, 0.265, 1.55);
    box-shadow: 0 8px 25px rgba(80, 227, 194, 0.3);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

/* Global audio control panel (optional) */
.global-audio-controls {
    position: fixed;
    bottom: 20px;
    right: 20px;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(74, 144, 226, 0.2);
    border-radius: 50px;
    padding: 0.75rem 1.25rem;
    box-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
    display: none;
    align-items: center;
    gap: 1rem;
    z-index: 1000;
    transition: all 0.3s ease;
}

.global-audio-controls.active {
    display: flex;
}

.global-audio-controls .control-btn {
    background: none;
    border: none;
    color: var(--primary-color);
    font-size: 1.1rem;
    cursor: pointer;
    padding: 0.5rem;
    border-radius: 50%;
    transition: all 0.3s ease;
}

.global-audio-controls .control-btn:hover {
    background: rgba(74, 144, 226, 0.1);
    transform: scale(1.1);
}

.global-audio-controls .audio-info {
    font-size: 0.875rem;
    color: var(--text-color);
    font-weight: 500;
}

/* Mobile responsive adjustments */
@media (max-width: 768px) {
    .kanji-audio-controls {
        opacity: 1; /* Always visible on mobile */
        top: 5px;
        right: 5px;
    }
    
    .audio-btn {
        width: 30px;
        height: 30px;
        font-size: 0.8rem;
    }
    
    .reading-audio {
        width: 22px;
        height: 22px;
        font-size: 0.7rem;
    }
    
    .japanese-audio-text {
        padding: 2px 4px;
        margin: 0 2px;
        font-size: 1rem;
        line-height: 1.4;
    }
    
    .japanese-audio-text:hover {
        background-color: rgba(74, 144, 226, 0.15);
    }
    
    .audio-error-toast,
    .audio-success-toast {
        right: 10px;
        left: 10px;
        max-width: none;
        font-size: 0.8rem;
        padding: 0.75rem 1rem;
    }
    
    .global-audio-controls {
        bottom: 10px;
        right: 10px;
        left: 10px;
        justify-content: center;
        padding: 0.5rem 1rem;
    }
}

/* High contrast mode support */
@media (prefers-contrast: high) {
    .japanese-audio-text {
        border: 1px solid var(--primary-color);
        background-color: transparent;
    }
    
    .japanese-audio-text:hover {
        background-color: var(--primary-color);
        color: white;
    }
    
    .japanese-audio-text.playing-audio {
        border-color: var(--secondary-color);
        background-color: var(--secondary-color);
    }
}

/* Reduced motion support */
@media (prefers-reduced-motion: reduce) {
    .japanese-audio-text,
    .audio-error-toast,
    .audio-success-toast,
    .global-audio-controls {
        animation: none;
        transition: none;
    }
    
    .japanese-audio-text:hover {
        transform: none;
    }
    
    .japanese-audio-text.playing-audio {
        animation: none;
        background-color: var(--secondary-color);
    }
}

/* Print styles - hide audio controls */
@media print {
    .japanese-audio-text {
        color: inherit;
        cursor: default;
        background: none;
        box-shadow: none;
        padding: 0;
        margin: 0;
    }
    
    .audio-btn,
    .kanji-audio-controls,
    .global-audio-controls,
    .audio-error-toast,
    .audio-success-toast {
        display: none !important;
    }
}
```

## Implementation Considerations

### Performance Optimization
1. **Audio Caching**: Cache audio files in browser memory
2. **Lazy Loading**: Only load audio when requested
3. **Compression**: Use compressed audio formats (MP3, OGG)
4. **CDN**: Serve audio files from CDN for faster delivery

### Accessibility
1. **Screen Reader Support**: Proper ARIA labels and descriptions
2. **Keyboard Navigation**: Audio controls accessible via keyboard
3. **Visual Indicators**: Clear visual feedback for audio state
4. **Alternative Text**: Fallback text for audio content

### Browser Compatibility
1. **Feature Detection**: Check for Web Speech API support
2. **Graceful Degradation**: Fallback options when audio unavailable
3. **Cross-browser Testing**: Test across major browsers
4. **Mobile Support**: Ensure functionality on mobile devices

### Security Considerations
1. **Input Validation**: Validate kanji IDs and reading types
2. **Rate Limiting**: Prevent audio API abuse
3. **File Security**: Secure audio file storage and access
4. **CSRF Protection**: Protect audio generation endpoints

## Testing Strategy

### Unit Tests
```python
def test_kanji_audio_api():
    """Test kanji audio API endpoint"""
    response = client.get('/api/kanji/1/audio/character')
    assert response.status_code == 200
    data = response.get_json()
    assert data['success'] is True

def test_audio_file_generation():
    """Test audio file generation service"""
    service = KanjiAudioService()
    # Test audio generation logic
```

### Integration Tests
```javascript
describe('KanjiAudioPlayer', () => {
    test('should play audio for valid kanji', async () => {
        const player = new KanjiAudioPlayer();
        await player.playKanjiAudio(1, 'character');
        // Assert audio playback
    });
    
    test('should handle audio errors gracefully', async () => {
        const player = new KanjiAudioPlayer();
        await player.playKanjiAudio(999, 'invalid');
        // Assert error handling
    });
});
```

### User Acceptance Testing
1. **Functionality**: Audio plays correctly for all kanji
2. **Usability**: Controls are intuitive and accessible
3. **Performance**: Audio loads and plays quickly
4. **Compatibility**: Works across different browsers and devices

## Deployment Considerations

### Database Migration
```bash
# Run migration to add audio fields
flask db upgrade

# Optional: Populate existing kanji with audio URLs
python scripts/populate_kanji_audio.py
```

### Static File Management
```python
# Update upload folder structure
UPLOAD_FOLDER/
├── lessons/
│   ├── audio/
│   ├── image/
│   └── video/
└── kanji_audio/
    ├── kanji_1_character.mp3
    ├── kanji_1_onyomi.mp3
    └── kanji_1_kunyomi.mp3
```

### Configuration Updates
```python
# Add audio-related configuration
KANJI_AUDIO_ENABLED = True
KANJI_AUDIO_CACHE_DURATION = 3600  # 1 hour
MAX_AUDIO_FILE_SIZE = 1024 * 1024  # 1MB
SUPPORTED_AUDIO_FORMATS = ['mp3', 'ogg', 'wav']
```

## Future Enhancements

### Phase 2 Features
1. **Vocabulary Audio**: Extend to vocabulary words
2. **Sentence Audio**: Audio for example sentences
3. **Speed Control**: Adjustable playback speed
4. **Voice Selection**: Multiple voice options

### Advanced Features
1. **Pronunciation Practice**: Record and compare user pronunciation
2. **Audio Quizzes**: Audio-based quiz questions
3. **Offline Support**: Cache audio for offline use
4. **Analytics**: Track audio usage patterns

## Conclusion

This implementation plan provides a comprehensive approach to adding clickable kanji audio functionality to the Japanese Learning Website. The hybrid approach ensures reliability while maintaining good user experience across different browsers and devices. The modular design allows for future enhancements and easy maintenance.

The key success factors are:
1. **Robust fallback mechanisms** for audio delivery
2. **Intuitive user interface** with clear visual feedback
3. **Performance optimization** for fast audio loading
4. **Accessibility compliance** for all users
5. **Comprehensive testing** across platforms and browsers

By following this implementation guide, the development team can successfully add high-quality audio pronunciation features that enhance the learning experience for Japanese language students.
