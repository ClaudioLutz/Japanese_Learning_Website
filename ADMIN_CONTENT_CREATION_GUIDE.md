# Admin Content Creation Guide

## Quick Start

1. **Login as Admin**
   - Go to: `http://localhost:5000/login`
   - Email: `admin@example.com`
   - Password: `admin123`
   - You'll be automatically redirected to the admin panel

2. **Access Content Management**
   - Click on any "Manage [Content Type]" link in the navigation
   - Available content types: Kana, Kanji, Vocabulary, Grammar

## Content Creation Process

### Creating Kana Characters
1. Go to **Manage Kana**
2. Click **"Add New Kana"** button
3. Fill out the form:
   - **Character**: The hiragana or katakana character (e.g., あ, ア)
   - **Romanization**: Roman alphabet equivalent (e.g., a, ka, shi)
   - **Type**: Select "hiragana" or "katakana"
   - **Stroke Order Info**: (Optional) URL or description of stroke order
   - **Example Sound URL**: (Optional) Link to audio pronunciation
4. Click **"Add Kana"** to save

### Creating Kanji Characters
1. Go to **Manage Kanji**
2. Click **"Add New Kanji"** button
3. Fill out the form:
   - **Character**: The kanji character (e.g., 水, 火, 木)
   - **Meaning**: English meanings (e.g., "water, liquid")
   - **On'yomi**: Chinese reading (e.g., スイ)
   - **Kun'yomi**: Japanese reading (e.g., みず)
   - **JLPT Level**: Difficulty level (1-5, where 5 is easiest)
   - **Stroke Order Info**: (Optional) Stroke order information
   - **Radical**: (Optional) Kanji radical
   - **Stroke Count**: (Optional) Number of strokes
4. Click **"Add Kanji"** to save

### Creating Vocabulary Words
1. Go to **Manage Vocabulary**
2. Click **"Add New Vocabulary"** button
3. Fill out the form:
   - **Word**: Japanese word (e.g., 水, こんにちは)
   - **Reading**: Hiragana/katakana reading (e.g., みず, こんにちは)
   - **Meaning**: English translation (e.g., "water", "hello")
   - **JLPT Level**: Difficulty level (1-5)
   - **Example Sentence (Japanese)**: (Optional) Example usage
   - **Example Sentence (English)**: (Optional) Translation of example
   - **Audio URL**: (Optional) Link to pronunciation audio
4. Click **"Add Vocabulary"** to save

### Creating Grammar Points
1. Go to **Manage Grammar**
2. Click **"Add New Grammar"** button
3. Fill out the form:
   - **Title**: Grammar point name (e.g., "Past tense with た")
   - **Explanation**: Detailed explanation of the grammar rule
   - **Structure**: Pattern or formula (e.g., "Verb stem + た")
   - **JLPT Level**: Difficulty level (1-5)
   - **Example Sentences**: (Optional) JSON format examples
4. Click **"Add Grammar"** to save

## Managing Existing Content

### Viewing Content
- All existing content is displayed in tables on each management page
- Tables show all relevant information for each content type
- Content loads automatically when you visit the page

### Editing Content
1. Click the **"Edit"** link next to any item
2. Modify the fields in the popup form
3. Click **"Save Changes"** to update

### Deleting Content
1. Click the **"Delete"** link next to any item
2. Confirm the deletion in the popup dialog
3. The item will be permanently removed

## Technical Features

### Real-Time Updates
- All changes are saved immediately to the database
- Tables refresh automatically after create/edit/delete operations
- No page reloads required

### Data Validation
- Required fields are enforced
- Duplicate entries are prevented
- Error messages provide clear feedback

### User Interface
- Modal dialogs for clean content creation/editing
- Responsive design works on different screen sizes
- Intuitive navigation between content types

## API Access (Advanced)

For programmatic access, the following API endpoints are available:

### Kana API
- `GET /api/admin/kana` - List all kana
- `POST /api/admin/kana/new` - Create new kana
- `GET /api/admin/kana/{id}` - Get specific kana
- `PUT /api/admin/kana/{id}/edit` - Update kana
- `DELETE /api/admin/kana/{id}/delete` - Delete kana

### Similar endpoints exist for:
- `/api/admin/kanji/*` - Kanji management
- `/api/admin/vocabulary/*` - Vocabulary management  
- `/api/admin/grammar/*` - Grammar management

All API endpoints require admin authentication and accept/return JSON data.

## Security Notes

- Only users with `is_admin = True` can access admin functions
- All admin routes are protected with authentication
- API endpoints validate admin permissions on every request
- Session-based authentication ensures secure access

## Troubleshooting

### Common Issues
1. **Can't access admin panel**: Ensure you're logged in with admin credentials
2. **Templates not loading**: Admin templates are in `app/templates/admin/`
3. **API errors**: Check browser console for detailed error messages
4. **Form validation**: Ensure all required fields are filled

### Getting Help
- Check browser console for JavaScript errors
- Verify admin user exists with `is_admin = True`
- Ensure all dependencies are installed (`pip install -r requirements.txt`)
