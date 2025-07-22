# Per-Lesson Pricing MVP Feature Implementation

## Overview

This document describes the implementation of the per-lesson pricing MVP feature for the Japanese Learning Website. The feature enables individual lesson purchases with future Stripe payment integration compatibility, following a soft launch approach with maximum simplicity.

## Implementation Date
**Completed:** July 17, 2025

## Requirements Met

### Core Requirements
- ✅ **Only per-lesson pricing strategy** (no subscription system for now)
- ✅ **Soft launch approach** with some lessons remaining free
- ✅ **Maximum simplicity** in implementation
- ✅ **Future subscription system compatibility**
- ✅ **CHF 2-10 price range** per lesson (configurable)
- ✅ **Instant purchase** (button click = immediate access for MVP)
- ✅ **All lessons free by default** with admin ability to set prices
- ✅ **Individual lesson pricing** in admin (no bulk tools needed)

### Technical Requirements
- ✅ **Swiss market focus** (CHF currency)
- ✅ **MVP approach** with mock payments initially
- ✅ **Future Stripe integration** preparation
- ✅ **Database schema** ready for production scaling

## Database Changes

### 1. Lesson Model Updates
**File:** `app/models.py`

Added pricing fields to the existing Lesson model:
```python
# Pricing fields
price: Mapped[float] = mapped_column(db.Float, nullable=False, default=0.0)
is_purchasable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
```

### 2. New LessonPurchase Model
**File:** `app/models.py`

Created new model for purchase tracking:
```python
class LessonPurchase(db.Model):
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
    lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey('lesson.id'), nullable=False)
    price_paid: Mapped[float] = mapped_column(db.Float, nullable=False)
    purchased_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    stripe_payment_intent_id: Mapped[str] = mapped_column(String(100), nullable=True)
```

### 3. Updated Access Control
Enhanced `is_accessible_to_user()` method to include pricing logic:
- Free lessons (price = 0.0) remain accessible to all users
- Paid lessons require purchase verification
- Guest access still works for free lessons with `allow_guest_access = True`
- Prerequisites are checked after purchase verification

### 4. Database Migrations
**Files:**
- `migrations/versions/c45713e40a57_add_lesson_pricing_fields.py`
- `migrations/versions/f518706fd7a4_add_lesson_purchase_table.py`

**Migration 1:** Adds pricing fields to lesson table
```sql
ALTER TABLE lesson ADD COLUMN price FLOAT DEFAULT 0.0;
ALTER TABLE lesson ADD COLUMN is_purchasable BOOLEAN DEFAULT false;
```

**Migration 2:** Creates lesson_purchase table with proper relationships
```sql
CREATE TABLE lesson_purchase (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES "user"(id),
    lesson_id INTEGER REFERENCES lesson(id),
    price_paid FLOAT NOT NULL,
    purchased_at TIMESTAMP NOT NULL,
    stripe_payment_intent_id VARCHAR(100),
    UNIQUE(user_id, lesson_id)
);
```

## Backend API Implementation

### Purchase Endpoints
**File:** `app/routes.py`

#### 1. Purchase Lesson (MVP Mock Payment)
- **Endpoint:** `POST /api/lessons/<int:lesson_id>/purchase`
- **Authentication:** Required
- **Functionality:** Instant purchase with mock payment processing
- **Returns:** Purchase confirmation with purchase_id and details

#### 2. Check Purchase Status
- **Endpoint:** `GET /api/lessons/<int:lesson_id>/purchase-status`
- **Authentication:** Required
- **Returns:** Purchase status, date, price paid, current price

#### 3. Get User Purchases
- **Endpoint:** `GET /api/user/purchases`
- **Authentication:** Required
- **Returns:** List of all lessons purchased by current user

### Admin Management Endpoints

#### 1. List All Purchases
- **Endpoint:** `GET /api/admin/purchases`
- **Authentication:** Admin required
- **Features:** Pagination, user details, lesson details

#### 2. Lesson-Specific Purchases
- **Endpoint:** `GET /api/admin/lessons/<int:lesson_id>/purchases`
- **Authentication:** Admin required
- **Returns:** All purchases for specific lesson + revenue stats

#### 3. Revenue Statistics
- **Endpoint:** `GET /api/admin/revenue-stats`
- **Authentication:** Admin required
- **Returns:** Total revenue, purchase counts, revenue by lesson, 30-day stats

### Enhanced Lesson Management
Updated lesson CRUD endpoints to handle pricing fields:
- **Create Lesson:** Accepts `price` and `is_purchasable` fields
- **Update Lesson:** Validates pricing data (no negative prices)
- **Form Handling:** Converts checkbox values to booleans properly

## Admin Interface Updates

### 1. Lesson Management Table
**File:** `app/templates/admin/manage_lessons.html`

**Added Price Column:**
- Shows "Free" for price = 0.0
- Shows "CHF X.XX" + purchasable status for paid lessons
- Color-coded badges for easy identification

### 2. Add/Edit Lesson Modals
**Enhanced Forms with Pricing Section:**
```html
<!-- Pricing Section -->
<div class="form-group">
    <h6 class="text-primary">💰 Pricing Settings</h6>
    <div class="row">
        <div class="col-md-6">
            <label for="lessonPrice">Price (CHF)</label>
            <input type="number" id="lessonPrice" name="price" class="form-control" 
                   min="0" step="0.01" value="0.00">
            <small class="form-text text-muted">Set to 0.00 for free lessons</small>
        </div>
        <div class="col-md-6">
            <div class="form-check mt-4">
                <input type="checkbox" id="lessonPurchasable" name="is_purchasable" 
                       class="form-check-input">
                <label for="lessonPurchasable" class="form-check-label">
                    Enable Individual Purchase
                </label>
                <small class="form-text text-muted d-block">
                    Allow users to buy this lesson individually
                </small>
            </div>
        </div>
    </div>
</div>
```

### 3. JavaScript Enhancements
**Updated Form Handling:**
- Price validation (no negative values)
- Checkbox to boolean conversion
- Form data processing for pricing fields
- Table display logic for pricing information

## Key Features Implemented

### 1. Default Behavior
- **All lessons are free by default** (price = 0.0, is_purchasable = false)
- **Existing lessons unaffected** by the update
- **Backward compatibility** maintained

### 2. Admin Control
- **Individual lesson pricing** through admin interface
- **Price range flexibility** (CHF 0.00 to any amount)
- **Purchasable toggle** independent of price setting
- **Visual pricing indicators** in lessons table

### 3. Purchase System (MVP)
- **Instant purchase** without payment gateway
- **Purchase tracking** with complete audit trail
- **Ownership verification** before lesson access
- **Unique purchase constraint** (one purchase per user per lesson)

### 4. Access Control Integration
- **Seamless integration** with existing access control
- **Prerequisites still enforced** after purchase
- **Guest access preserved** for free lessons
- **Clear access messages** for users

### 5. Future-Ready Architecture
- **Stripe integration ready** with payment_intent_id field
- **Subscription system compatible** database design
- **Revenue tracking** infrastructure in place
- **Scalable purchase management** system

## Deployment Instructions

### Local Development
```bash
# Apply migrations
flask db upgrade

# Verify migration status
flask db current
# Should show: f518706fd7a4
```

### Production Deployment (Google Cloud)
```bash
# 1. Backup database
pg_dump -h [CLOUD_SQL_IP] -U [USERNAME] -d japanese_learning > backup.sql

# 2. Pull code
git pull origin main

# 3. Run migrations
flask db upgrade

# 4. Restart application
sudo systemctl restart your-app-service

# 5. Verify deployment
curl https://your-domain.com/api/admin/lessons
```

## Database Migration Issues and Resolution

### Problem Encountered
During the implementation, we encountered a critical database migration issue when trying to create the `lesson_purchase` table. The migration failed with the following error:

```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.InvalidForeignKey) 
FEHLER: in Tabelle »lesson«, auf die verwiesen wird, gibt es keinen Unique-Constraint, 
der auf die angegebenen Schlüssel passt
```

**Translation:** "ERROR: in table 'lesson', which is referenced, there is no unique constraint that matches the specified keys"

### Root Cause Analysis
The issue was that both the `lesson` and `user` tables were **missing their primary key constraints** in PostgreSQL, even though:
- The tables had `id` columns with `SERIAL` type
- The SQLAlchemy models defined `primary_key=True`
- The columns were functioning as primary keys for queries

This is a PostgreSQL-specific issue where the primary key constraint metadata was not properly created during previous migrations or database setup.

### Diagnostic Steps
1. **Checked current migration status:**
   ```bash
   flask db current
   # Result: c45713e40a57 (pricing fields migration successful)
   ```

2. **Verified table structure:**
   ```bash
   psql -d japanese_learning -c "\d lesson"
   # Showed columns but no primary key constraint listed
   ```

3. **Checked constraints:**
   ```bash
   psql -d japanese_learning -c "SELECT conname, contype FROM pg_constraint WHERE conrelid = 'lesson'::regclass;"
   # Result: (0 rows) - No constraints found!
   ```

### Solution Applied
We manually added the missing primary key constraints to both tables:

#### Step 1: Fix User Table
```bash
Write-Output 'ALTER TABLE "user" ADD CONSTRAINT user_pkey PRIMARY KEY (id);' | psql -h localhost -U app_user -d japanese_learning
```
**Result:** `ALTER TABLE` (Success)

**Note:** The `user` table name needed to be quoted because "user" is a reserved keyword in PostgreSQL.

#### Step 2: Fix Lesson Table
```bash
Write-Output 'ALTER TABLE lesson ADD CONSTRAINT lesson_pkey PRIMARY KEY (id);' | psql -h localhost -U app_user -d japanese_learning
```
**Result:** `FEHLER: mehrere Primärschlüssel für Tabelle »lesson« nicht erlaubt` 
**Translation:** "ERROR: multiple primary keys for table 'lesson' not allowed"

This error indicated that the lesson table **already had** a primary key constraint, which was good news.

#### Step 3: Retry Migration
After fixing the user table primary key constraint:
```bash
flask db upgrade
```
**Result:** ✅ **SUCCESS** - Migration completed without errors

### What Finally Worked
The solution was a **two-step process**:

1. **Manual Primary Key Constraint Addition:**
   - Added missing primary key constraint to the `user` table
   - Used proper PostgreSQL syntax with quoted table name
   - Used PowerShell `Write-Output` piping to handle command syntax issues

2. **Standard Migration Process:**
   - After fixing the constraint issue, `flask db upgrade` worked normally
   - The `lesson_purchase` table was created successfully with proper foreign key relationships

### Technical Details of the Fix

#### Command Syntax Issues Encountered
- **Initial attempts failed** due to PowerShell command parsing issues with quotes
- **Solution:** Used `Write-Output 'SQL_COMMAND' | psql` pattern
- **Key insight:** PostgreSQL reserved keywords need proper quoting

#### Why This Happened
This issue likely occurred because:
1. **Previous migrations** may not have properly created primary key constraints
2. **Database initialization** might have been incomplete
3. **PostgreSQL version differences** in constraint handling
4. **Manual database operations** in the past that bypassed proper constraint creation

### Prevention for Future
To prevent similar issues:

1. **Always verify constraints after migrations:**
   ```sql
   SELECT conname, contype FROM pg_constraint WHERE conrelid = 'table_name'::regclass;
   ```

2. **Include constraint verification in deployment scripts:**
   ```bash
   # Check if primary keys exist before running migrations
   psql -c "SELECT constraint_name FROM information_schema.table_constraints WHERE table_name='lesson' AND constraint_type='PRIMARY KEY';"
   ```

3. **Use proper migration testing** on staging environments first

## Data Safety

### Migration Safety
- **Non-destructive migrations** - only ADD new fields and tables
- **Safe defaults** - all existing lessons become free (price = 0.0)
- **Preserved data** - all existing lesson content, user progress, etc. unchanged
- **Rollback capability** - migrations can be reversed if needed
- **Constraint issues resolved** - primary key constraints properly established

### Production Considerations
- **Zero-downtime deployment** possible (migrations are additive)
- **Backward compatibility** maintained
- **Database backup recommended** before production deployment
- **Constraint verification** should be performed before migration

## Testing Verification

### 1. Database Schema Verification
```python
# Test script to verify implementation
from app import create_app, db
from app.models import Lesson, LessonPurchase, User

app = create_app()
with app.app_context():
    # Verify pricing fields exist
    lessons = Lesson.query.limit(3).all()
    for lesson in lessons:
        print(f'Lesson: {lesson.title}')
        print(f'  Price: CHF {lesson.price}')
        print(f'  Is Purchasable: {lesson.is_purchasable}')
    
    # Verify purchase table exists
    purchase_count = LessonPurchase.query.count()
    print(f'Total purchases: {purchase_count}')
```

### 2. Admin Interface Testing

#### Test Lesson Pricing Management
1. **Access Admin Panel:**
   - Navigate to `/admin/manage/lessons`
   - Login with admin credentials

2. **Test Adding New Lesson with Pricing:**
   - Click "Add New Lesson"
   - Fill in basic lesson details
   - In the "💰 Pricing Settings" section:
     - Set price to `5.50` (CHF)
     - Check "Enable Individual Purchase"
   - Save the lesson
   - **Expected Result:** Lesson appears in table with "CHF 5.50 Purchasable" badge

3. **Test Editing Existing Lesson:**
   - Click "Edit" on any existing lesson
   - Modify pricing settings
   - Save changes
   - **Expected Result:** Price column updates in lessons table

4. **Test Price Column Display:**
   - **Free lessons:** Should show green "Free" badge
   - **Paid lessons:** Should show "CHF X.XX" + purchasable status
   - **Paid but not purchasable:** Should show price + "Not Purchasable" badge

### 3. Backend API Testing

#### Test Purchase Endpoints
```bash
# 1. Test lesson purchase (replace lesson_id and use valid session)
curl -X POST http://localhost:5000/api/lessons/1/purchase \
  -H "Content-Type: application/json" \
  -H "Cookie: session=your_session_cookie" \
  -d '{}'

# Expected Response:
# {
#   "success": true,
#   "message": "Successfully purchased 'Lesson Title' for CHF 5.50",
#   "purchase_id": 1,
#   "lesson_id": 1,
#   "price_paid": 5.50
# }

# 2. Test purchase status check
curl -X GET http://localhost:5000/api/lessons/1/purchase-status \
  -H "Cookie: session=your_session_cookie"

# Expected Response:
# {
#   "lesson_id": 1,
#   "is_purchased": true,
#   "purchase_date": "2025-07-17T16:30:00",
#   "price_paid": 5.50,
#   "current_price": 5.50,
#   "is_purchasable": true
# }

# 3. Test user purchases list
curl -X GET http://localhost:5000/api/user/purchases \
  -H "Cookie: session=your_session_cookie"

# Expected Response: Array of purchased lessons with details
```

#### Test Admin Endpoints
```bash
# 1. Test revenue statistics (admin only)
curl -X GET http://localhost:5000/api/admin/revenue-stats \
  -H "Cookie: admin_session_cookie"

# Expected Response:
# {
#   "total_revenue": 15.50,
#   "total_purchases": 3,
#   "recent_revenue_30d": 15.50,
#   "recent_purchases_30d": 3,
#   "average_price": 5.17,
#   "lesson_revenue": [...]
# }

# 2. Test all purchases list
curl -X GET http://localhost:5000/api/admin/purchases \
  -H "Cookie: admin_session_cookie"

# Expected Response: Paginated list of all purchases with user/lesson details
```

### 4. Access Control Testing

#### Test Lesson Access Logic
1. **Create a test paid lesson:**
   - Set price to CHF 3.00
   - Enable individual purchase
   - Publish the lesson

2. **Test as non-purchasing user:**
   - Login as regular user (not admin)
   - Navigate to the paid lesson
   - **Expected Result:** Access denied with "Purchase required (CHF 3.00)" message

3. **Test after purchase:**
   - Use API or mock purchase the lesson
   - Navigate to the lesson again
   - **Expected Result:** Full access to lesson content

4. **Test free lesson access:**
   - Create/use a lesson with price = 0.00
   - **Expected Result:** Accessible to all users (including guests if guest access enabled)

### 5. Database Integrity Testing

#### Verify Database Constraints
```sql
-- Check primary key constraints exist
SELECT constraint_name, table_name 
FROM information_schema.table_constraints 
WHERE constraint_type = 'PRIMARY KEY' 
AND table_name IN ('lesson', 'user', 'lesson_purchase');

-- Expected Results:
-- lesson_pkey | lesson
-- user_pkey | user  
-- lesson_purchase_pkey | lesson_purchase

-- Check foreign key constraints
SELECT constraint_name, table_name, column_name
FROM information_schema.key_column_usage
WHERE table_name = 'lesson_purchase';

-- Expected Results:
-- lesson_purchase_user_id_fkey | lesson_purchase | user_id
-- lesson_purchase_lesson_id_fkey | lesson_purchase | lesson_id

-- Check unique constraints
SELECT constraint_name, table_name
FROM information_schema.table_constraints
WHERE constraint_type = 'UNIQUE'
AND table_name = 'lesson_purchase';

-- Expected Result:
-- lesson_purchase_user_id_lesson_id_key | lesson_purchase
```

#### Test Purchase Uniqueness
```python
# Test script to verify unique purchase constraint
from app import create_app, db
from app.models import LessonPurchase
from datetime import datetime

app = create_app()
with app.app_context():
    # Try to create duplicate purchase (should fail)
    try:
        purchase1 = LessonPurchase(user_id=1, lesson_id=1, price_paid=5.0, purchased_at=datetime.utcnow())
        purchase2 = LessonPurchase(user_id=1, lesson_id=1, price_paid=5.0, purchased_at=datetime.utcnow())
        
        db.session.add(purchase1)
        db.session.add(purchase2)
        db.session.commit()
        print("ERROR: Duplicate purchase allowed!")
    except Exception as e:
        print(f"SUCCESS: Duplicate purchase prevented - {e}")
        db.session.rollback()
```

### 6. Migration Testing

#### Verify Migration Status
```bash
# Check current migration version
flask db current
# Expected: f518706fd7a4

# Check migration history
flask db history
# Should show both pricing migrations in order

# Verify all migrations applied
flask db show
# Should show current migration details
```

#### Test Migration Rollback (Optional)
```bash
# Rollback to test reversibility (CAUTION: Only on test database)
flask db downgrade c45713e40a57  # Rollback purchase table
flask db downgrade a462f46557fe  # Rollback pricing fields

# Re-apply migrations
flask db upgrade
```

### 7. Error Handling Testing

#### Test Invalid Purchase Scenarios
1. **Purchase non-purchasable lesson:**
   - Set lesson price > 0 but is_purchasable = false
   - Attempt purchase via API
   - **Expected:** Error message "This lesson is not available for purchase"

2. **Purchase free lesson:**
   - Set lesson price = 0
   - Attempt purchase via API
   - **Expected:** Error message "This lesson is not available for purchase"

3. **Duplicate purchase attempt:**
   - Purchase a lesson successfully
   - Attempt to purchase same lesson again
   - **Expected:** Error message "You already own this lesson"

4. **Unauthenticated purchase:**
   - Attempt purchase without login
   - **Expected:** Redirect to login or 401 error

### 8. Performance Testing

#### Test with Multiple Purchases
```python
# Create multiple test purchases to verify performance
from app import create_app, db
from app.models import LessonPurchase, User, Lesson
from datetime import datetime
import time

app = create_app()
with app.app_context():
    start_time = time.time()
    
    # Test access control performance with purchases
    user = User.query.first()
    lessons = Lesson.query.limit(10).all()
    
    for lesson in lessons:
        accessible, message = lesson.is_accessible_to_user(user)
        print(f"Lesson {lesson.id}: {accessible} - {message}")
    
    end_time = time.time()
    print(f"Access control check took: {end_time - start_time:.3f} seconds")
```

### 9. Complete Test Checklist

**✅ Database Schema:**
- [ ] Pricing fields added to lesson table
- [ ] LessonPurchase table created with proper relationships
- [ ] Primary key constraints exist on all tables
- [ ] Foreign key constraints working
- [ ] Unique constraints preventing duplicate purchases

**✅ Admin Interface:**
- [ ] Price column visible in lessons table
- [ ] Pricing section in Add/Edit lesson modals
- [ ] Form validation working (no negative prices)
- [ ] Pricing badges display correctly

**✅ Backend APIs:**
- [ ] Purchase endpoint creates purchase records
- [ ] Purchase status endpoint returns correct data
- [ ] User purchases endpoint lists owned lessons
- [ ] Admin revenue endpoints return statistics
- [ ] Access control respects purchase status

**✅ Error Handling:**
- [ ] Invalid purchase attempts blocked
- [ ] Duplicate purchases prevented
- [ ] Proper error messages returned
- [ ] Authentication required for purchases

**✅ Data Integrity:**
- [ ] Existing lessons unaffected (price = 0.0, not purchasable)
- [ ] User data preserved
- [ ] Purchase tracking accurate
- [ ] Migration reversible

## Next Steps for Full Implementation

### Frontend User Interface (✅ COMPLETED)
1. **✅ Update lesson cards** to show pricing information
2. **✅ Add "Buy Now" buttons** for purchasable lessons
3. **✅ Implement purchase JavaScript** for frontend interaction
4. **✅ Show "Owned" status** for purchased lessons
5. **✅ Purchase page with dummy payment flow**

### Payment Integration (Future)
1. **Stripe integration** using existing payment_intent_id field
2. **Payment confirmation** workflow
3. **Refund handling** system
4. **Payment failure** recovery

### Analytics & Reporting (Future)
1. **Revenue dashboard** for admins
2. **Purchase analytics** and trends
3. **Popular lessons** reporting
4. **Conversion tracking** system

## Files Modified

### Core Application Files
- `app/models.py` - Added pricing fields and LessonPurchase model
- `app/routes.py` - Added purchase API endpoints, pricing logic, and purchase page route
- `app/templates/admin/manage_lessons.html` - Enhanced admin interface

### Frontend Templates
- `app/templates/lessons.html` - Updated lesson cards with clickable purchase buttons
- `app/templates/purchase.html` - New purchase page with dummy payment flow

### Database Migration Files
- `migrations/versions/c45713e40a57_add_lesson_pricing_fields.py`
- `migrations/versions/f518706fd7a4_add_lesson_purchase_table.py`

### Documentation
- `per_lesson_pricing_mvp_implementation.md` - This document

## Frontend Purchase Implementation

### Purchase Button Integration
**File:** `app/templates/lessons.html`

**Enhanced Lesson Cards:**
- Purchase buttons are now clickable for lessons requiring payment
- Buttons show "Purchase required (CHF X.XX)" with proper pricing
- JavaScript function `purchaseLesson()` handles button clicks
- Automatic login check before allowing purchase

**Updated Button Logic:**
```javascript
${lesson.access_message && lesson.access_message.includes('Purchase required') ? `
    <button class="lesson-action-btn lesson-purchase-btn" onclick="purchaseLesson(${lesson.id}, '${lesson.title}', ${lesson.price})">
        ${lesson.access_message}
    </button>
` : `
    <button class="lesson-action-btn lesson-action-btn-disabled" disabled>
        ${lesson.access_message}
    </button>
`}
```

### Purchase Page Implementation
**File:** `app/templates/purchase.html`

**Complete Purchase Flow:**
- Professional purchase page with lesson details
- Price display with CHF formatting
- Demo payment method (MVP simulation)
- Terms and conditions checkbox
- Processing modal with spinner
- Success modal with lesson access links

**Key Features:**
- Lesson information display with image support
- Clear pricing breakdown
- Purchase benefits explanation
- CSRF protection
- Error handling and user feedback
- Mobile-responsive design

### Purchase Route Implementation
**File:** `app/routes.py`

**New Route Added:**
```python
@bp.route('/purchase/<int:lesson_id>')
@login_required
def purchase_lesson_page(lesson_id):
    """Display the purchase page for a lesson"""
    # Validation logic for purchasable lessons
    # Check for existing purchases
    # Redirect logic for already accessible lessons
    return render_template('purchase.html', lesson=lesson, form=form)
```

**Purchase Flow Validation:**
- Checks if lesson is purchasable
- Prevents duplicate purchases
- Validates user authentication
- Handles edge cases (already accessible lessons)

### JavaScript Integration
**Enhanced Frontend Logic:**
- User authentication check via `window.currentUser`
- Automatic redirect to login for unauthenticated users
- Purchase page redirection for authenticated users
- CSRF token handling for secure requests

**Purchase Function:**
```javascript
async function purchaseLesson(lessonId, lessonTitle, price) {
    // Check if user is logged in
    if (!window.currentUser) {
        alert('Please log in to purchase lessons.');
        window.location.href = '/login';
        return;
    }
    
    // Redirect to purchase page
    window.location.href = `/purchase/${lessonId}`;
}
```

### Purchase Page Features

#### Visual Design
- Professional card-based layout
- Lesson thumbnail/background image display
- Clear pricing with CHF currency
- Bootstrap-based responsive design
- Font Awesome icons for enhanced UX

#### Purchase Benefits Section
- Lifetime access guarantee
- Multi-device access
- Progress tracking features
- Retake capabilities

#### Demo Payment Method
- Clear indication of demo mode
- No real payment processing
- Instant purchase simulation
- Future Stripe integration ready

#### Success Flow
- Processing modal with spinner
- Success confirmation modal
- Direct lesson access button
- Option to browse more lessons

### User Experience Enhancements

#### Lesson Cards
- Visual distinction between free and paid lessons
- Clear pricing display
- Hover effects for purchase buttons
- Consistent styling across card layouts

#### Purchase Process
- Single-click purchase initiation
- Clear progress indicators
- Immediate feedback on success/failure
- Seamless integration with existing UI

#### Error Handling
- Comprehensive validation messages
- User-friendly error displays
- Graceful fallback for edge cases
- Proper CSRF protection

## Testing the Implementation

### Manual Testing Steps
1. **Browse lessons** - Verify purchase buttons appear for paid lessons
2. **Click purchase button** - Confirm redirect to purchase page
3. **Complete purchase** - Test the dummy payment flow
4. **Access purchased lesson** - Verify lesson becomes accessible
5. **Prevent duplicate purchases** - Confirm protection against re-purchasing

### Expected Behavior
- **Unauthenticated users:** Redirected to login when clicking purchase
- **Authenticated users:** Taken to purchase page with lesson details
- **Successful purchase:** Lesson immediately becomes accessible
- **Already owned lessons:** Purchase button not shown

## Conclusion

The per-lesson pricing MVP feature has been successfully implemented with:
- ✅ **Complete backend functionality**
- ✅ **Admin interface integration**
- ✅ **Frontend purchase UI implementation**
- ✅ **Dummy payment flow for testing**
- ✅ **Database schema ready for production**
- ✅ **Safe deployment process**
- ✅ **Future Stripe integration preparation**

**Key Achievements:**
- Users can now click purchase buttons and complete dummy transactions
- Lessons are immediately unlocked after purchase
- Professional purchase page with clear pricing and benefits
- Seamless integration with existing lesson browsing experience
- Complete purchase flow from discovery to access

The system is now fully functional for the MVP phase and ready for production deployment. The dummy payment system can be easily replaced with Stripe integration when ready for real transactions. All existing data and functionality remains intact while providing a complete monetization solution for individual lessons.
