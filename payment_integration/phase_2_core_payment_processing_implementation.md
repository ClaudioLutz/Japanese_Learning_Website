# Phase 2: Core Payment Processing Implementation
## Detailed Step-by-Step Implementation Plan

### Overview
Phase 2 focuses on replacing the current mock payment system with fully functional PostFinance Checkout payment processing. This phase builds upon the foundation setup from Phase 1 and implements the core payment functionality required for lesson and course purchases.

### Prerequisites (Phase 1 Completed)
- ✅ PostFinance Checkout account configured
- ✅ Environment variables set up (space_id, user_id, api_secret)
- ✅ Database models updated with `postfinance_transaction_id` and `transaction_state` fields
- ✅ Basic PostFinanceService class created
- ✅ PaymentTransaction model implemented

---

## 2.1 Payment Service Layer Implementation

### 2.1.1 Enhance PostFinanceService Class
**Location**: `app/services/payment_service.py`
**Estimated Time**: 4-6 hours
**Priority**: Critical

#### Current State Analysis
```python
# Current implementation only has:
# - Basic configuration setup
# - get_transaction_status() method
```

#### Implementation Steps

**Step 1**: Add Required SDK Imports
```python
from postfinancecheckout import Configuration, ApiClient
from postfinancecheckout.api import (
    TransactionServiceApi, 
    TransactionPaymentPageServiceApi,
    RefundServiceApi
)
from postfinancecheckout.models import (
    TransactionCreate, 
    LineItem, 
    LineItemType,
    Address,
    AddressCreate
)
from postfinancecheckout.rest import ApiException
```

**Step 2**: Implement Transaction Creation Method
```python
def create_lesson_transaction(self, user: User, lesson: Lesson) -> dict:
    """
    Create a PostFinance transaction for lesson purchase
    
    API Endpoint: POST /api/transaction/create
    Required: spaceId (query parameter), Transaction Create object (body)
    Returns: Transaction object on success (HTTP 200)
    Error Responses: 442 Client Error, 542 Server Error
    """
    try:
        # Create line item using PostFinance API requirements
        line_item = LineItem(
            name=lesson.title[:150],  # Character limit: 1-150
            unique_id=f"lesson_{lesson.id}",  # Unique within transaction, 200 char limit
            sku=f"LESSON_{lesson.id}",  # SKU field, 200 char limit
            quantity=1,  # Positive decimal
            amount_including_tax=lesson.price,  # Price including tax
            type=LineItemType.PRODUCT  # PRODUCT, DISCOUNT, SHIPPING, FEE, or TIP
        )
        
        # Create transaction with metadata for linking
        transaction_create = TransactionCreate(
            line_items=[line_item],
            currency='CHF',  # ISO 4217 format
            auto_confirmation_enabled=True,
            success_url=current_app.config.get('PAYMENT_SUCCESS_URL'),
            failed_url=current_app.config.get('PAYMENT_FAILURE_URL'),
            # Use metaData field to store lesson_id for clean linking
            meta_data={
                'lesson_id': str(lesson.id),
                'user_id': str(user.id),
                'item_type': 'lesson'
            }
        )
        
        # Create transaction via API
        transaction = self.transaction_service.create(
            space_id=self.space_id, 
            transaction=transaction_create
        )
        
        # Log successful creation
        self.logger.info(f"Transaction created: ID {transaction.id} for user {user.id}, lesson {lesson.id}")
        
        return {
            'success': True,
            'transaction_id': transaction.id,
            'transaction': transaction
        }
        
    except ApiException as e:
        # Handle PostFinance API errors
        self.logger.error(f"PostFinance API error creating lesson transaction: {e.body}")
        error_data = self._parse_api_error(e)
        return {
            'success': False,
            'error': error_data['message'],
            'error_type': error_data['type']
        }
    except Exception as e:
        self.logger.error(f"Unexpected error creating lesson transaction: {e}")
        return {
            'success': False,
            'error': 'Transaction creation failed',
            'error_type': 'SYSTEM_ERROR'
        }
```

**Step 3**: Implement Course Transaction Creation
```python
def create_course_transaction(self, user: User, course: Course) -> dict:
    """
    Create a PostFinance transaction for course purchase
    Similar structure to lesson transaction but for courses
    """
    # Similar implementation with course-specific metadata
    # meta_data: {'course_id': str(course.id), 'user_id': str(user.id), 'item_type': 'course'}
```

**Step 4**: Implement Payment Page URL Generation
```python
def generate_payment_page_url(self, transaction_id: int) -> dict:
    """
    Generate payment page URL for transaction
    
    API Endpoint: GET /api/transaction-payment-page/payment-page-url
    Query Parameters: spaceId (Long), id (Long - transaction ID)
    Returns: URL as String on success (HTTP 200)
    Error Responses: 409 Conflict, 442 Client Error, 542 Server Error
    """
    try:
        from postfinancecheckout.api import TransactionPaymentPageServiceApi
        
        if not hasattr(self, 'payment_page_service'):
            self.payment_page_service = TransactionPaymentPageServiceApi(self.api_client)
        
        payment_url = self.payment_page_service.payment_page_url(
            space_id=self.space_id,
            id=transaction_id
        )
        
        self.logger.info(f"Payment URL generated for transaction {transaction_id}")
        
        return {
            'success': True,
            'payment_url': payment_url
        }
        
    except ApiException as e:
        self.logger.error(f"Error generating payment URL for transaction {transaction_id}: {e.body}")
        error_data = self._parse_api_error(e)
        return {
            'success': False,
            'error': error_data['message'],
            'error_type': error_data['type']
        }
```

**Step 5**: Enhance Transaction Status Checking
```python
def get_transaction_status(self, transaction_id: int) -> dict:
    """
    Enhanced transaction status checking with proper error handling
    
    API Endpoint: GET /api/transaction/read
    Query Parameters: spaceId (Long), id (Long)
    Returns: Transaction object with state field
    States: PENDING, CONFIRMED, PROCESSING, FAILED, AUTHORIZED, VOIDED, COMPLETED, FULFILL, DECLINE
    """
    try:
        transaction = self.transaction_service.read(
            space_id=self.space_id, 
            id=transaction_id
        )
        
        return {
            'success': True,
            'transaction': transaction,
            'state': transaction.state,
            'metadata': transaction.meta_data
        }
        
    except ApiException as e:
        self.logger.error(f"API error reading transaction {transaction_id}: {e.body}")
        error_data = self._parse_api_error(e)
        return {
            'success': False,
            'error': error_data['message'],
            'error_type': error_data['type']
        }
```

**Step 6**: Implement Error Parsing Helper
```python
def _parse_api_error(self, api_exception: ApiException) -> dict:
    """
    Parse PostFinance API errors into structured format
    
    Client Error fields: type, defaultMessage, id, message
    Server Error fields: date, id, message
    """
    try:
        import json
        error_body = json.loads(api_exception.body)
        
        if 'type' in error_body:
            # Client Error
            return {
                'type': error_body.get('type', 'CLIENT_ERROR'),
                'message': error_body.get('message', error_body.get('defaultMessage', 'Client error occurred')),
                'id': error_body.get('id'),
                'http_status': api_exception.status
            }
        else:
            # Server Error
            return {
                'type': 'SERVER_ERROR',
                'message': error_body.get('message', 'Server error occurred'),
                'id': error_body.get('id'),
                'date': error_body.get('date'),
                'http_status': api_exception.status
            }
    except:
        return {
            'type': 'UNKNOWN_ERROR',
            'message': 'Failed to parse error response',
            'http_status': api_exception.status
        }
```

### 2.1.2 Add Alternative Integration Methods (Future Enhancement)
**Priority**: Low (Phase 4)

```python
def get_iframe_javascript_url(self, transaction_id: int) -> dict:
    """
    Generate JavaScript URL for iframe integration
    API Endpoint: GET /api/transaction-iframe/javascript-url
    """
    
def get_lightbox_javascript_url(self, transaction_id: int) -> dict:
    """
    Generate JavaScript URL for lightbox integration  
    API Endpoint: GET /api/transaction-lightbox/javascript-url
    """
```

---

## 2.2 Database Transaction Management

### 2.2.1 Create PaymentTransactionService
**Location**: Create `app/services/transaction_service.py`
**Estimated Time**: 3-4 hours
**Priority**: Critical

```python
from app import db
from app.models import PaymentTransaction, LessonPurchase, CoursePurchase, User, Lesson, Course
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
import logging

class PaymentTransactionService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def create_payment_transaction(self, transaction_id: int, user: User, 
                                 item_type: str, item_id: int, amount: float) -> PaymentTransaction:
        """
        Create PaymentTransaction record for tracking
        Links PostFinance transaction with application data
        """
        try:
            payment_transaction = PaymentTransaction(
                transaction_id=transaction_id,
                user_id=user.id,
                item_type=item_type,  # 'lesson' or 'course'
                item_id=item_id,
                amount=amount,
                currency='CHF',
                state='PENDING',
                transaction_metadata={
                    'user_id': user.id,
                    'item_type': item_type,
                    'item_id': item_id
                }
            )
            
            db.session.add(payment_transaction)
            db.session.commit()
            
            self.logger.info(f"PaymentTransaction created: {transaction_id}")
            return payment_transaction
            
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"Error creating PaymentTransaction: {e}")
            raise
    
    def update_transaction_state(self, transaction_id: int, new_state: str, 
                               webhook_data: dict = None) -> bool:
        """
        Update transaction state from webhook or status check
        States: PENDING, CONFIRMED, PROCESSING, FAILED, AUTHORIZED, VOIDED, COMPLETED, FULFILL, DECLINE
        """
        try:
            payment_transaction = PaymentTransaction.query.filter_by(
                transaction_id=transaction_id
            ).first()
            
            if not payment_transaction:
                self.logger.error(f"PaymentTransaction not found: {transaction_id}")
                return False
            
            old_state = payment_transaction.state
            payment_transaction.state = new_state
            payment_transaction.updated_at = datetime.utcnow()
            
            if webhook_data:
                payment_transaction.webhook_data = webhook_data
            
            # Handle completion states
            if new_state in ['COMPLETED', 'FULFILL']:
                self._complete_purchase(payment_transaction)
            elif new_state in ['FAILED', 'DECLINE', 'VOIDED']:
                self._handle_failed_payment(payment_transaction)
            
            db.session.commit()
            
            self.logger.info(f"Transaction {transaction_id} state updated: {old_state} -> {new_state}")
            return True
            
        except SQLAlchemyError as e:
            db.session.rollback()
            self.logger.error(f"Error updating transaction state: {e}")
            return False
    
    def _complete_purchase(self, payment_transaction: PaymentTransaction):
        """
        Complete the purchase by creating LessonPurchase or CoursePurchase record
        """
        if payment_transaction.item_type == 'lesson':
            existing_purchase = LessonPurchase.query.filter_by(
                user_id=payment_transaction.user_id,
                lesson_id=payment_transaction.item_id
            ).first()
            
            if not existing_purchase:
                lesson_purchase = LessonPurchase(
                    user_id=payment_transaction.user_id,
                    lesson_id=payment_transaction.item_id,
                    price_paid=payment_transaction.amount,
                    postfinance_transaction_id=payment_transaction.transaction_id,
                    transaction_state=payment_transaction.state
                )
                db.session.add(lesson_purchase)
                
        elif payment_transaction.item_type == 'course':
            existing_purchase = CoursePurchase.query.filter_by(
                user_id=payment_transaction.user_id,
                course_id=payment_transaction.item_id
            ).first()
            
            if not existing_purchase:
                course_purchase = CoursePurchase(
                    user_id=payment_transaction.user_id,
                    course_id=payment_transaction.item_id,
                    price_paid=payment_transaction.amount,
                    postfinance_transaction_id=payment_transaction.transaction_id,
                    transaction_state=payment_transaction.state
                )
                db.session.add(course_purchase)
    
    def _handle_failed_payment(self, payment_transaction: PaymentTransaction):
        """
        Handle failed payment - cleanup or notification
        """
        self.logger.info(f"Payment failed for transaction {payment_transaction.transaction_id}")
        # Additional failure handling logic here
```

---

## 2.3 API Endpoint Updates

### 2.3.1 Replace Mock Payment Endpoints
**Location**: `app/routes.py`
**Estimated Time**: 4-5 hours
**Priority**: Critical

#### Step 1: Update Lesson Purchase Endpoint

**Replace the existing `/api/lessons/<int:lesson_id>/purchase` endpoint:**

```python
@bp.route('/api/lessons/<int:lesson_id>/purchase', methods=['POST'])
@login_required
def purchase_lesson(lesson_id):
    """
    Initiate lesson purchase with PostFinance Checkout
    
    Flow:
    1. Validate lesson and user eligibility
    2. Create PostFinance transaction
    3. Store transaction in database
    4. Return payment URL for redirect
    """
    from app.services.payment_service import get_payment_service
    from app.services.transaction_service import PaymentTransactionService
    
    # Validate CSRF token
    from flask_wtf.csrf import validate_csrf
    try:
        csrf_token = request.headers.get('X-CSRFToken')
        if not csrf_token:
            return jsonify({"error": "CSRF token missing"}), 400
        validate_csrf(csrf_token)
    except Exception:
        return jsonify({"error": "CSRF token invalid"}), 400
    
    lesson = Lesson.query.get_or_404(lesson_id)
    
    # Validate lesson is purchasable
    if not lesson.is_purchasable or lesson.price <= 0:
        return jsonify({"error": "This lesson is not available for purchase"}), 400
    
    # Check if user already owns this lesson
    existing_purchase = LessonPurchase.query.filter_by(
        user_id=current_user.id, 
        lesson_id=lesson_id
    ).first()
    
    if existing_purchase:
        return jsonify({"error": "You already own this lesson"}), 400
    
    try:
        # Initialize services
        payment_service = get_payment_service()
        transaction_service = PaymentTransactionService()
        
        # Create PostFinance transaction
        result = payment_service.create_lesson_transaction(current_user, lesson)
        
        if not result['success']:
            return jsonify({
                "error": result['error'],
                "error_type": result.get('error_type')
            }), 400
        
        transaction_id = result['transaction_id']
        
        # Store transaction in database
        payment_transaction = transaction_service.create_payment_transaction(
            transaction_id=transaction_id,
            user=current_user,
            item_type='lesson',
            item_id=lesson_id,
            amount=lesson.price
        )
        
        # Generate payment URL
        url_result = payment_service.generate_payment_page_url(transaction_id)
        
        if not url_result['success']:
            return jsonify({
                "error": "Failed to generate payment URL",
                "error_details": url_result['error']
            }), 500
        
        current_app.logger.info(f"Lesson purchase initiated: User {current_user.id}, Lesson {lesson_id}, Transaction {transaction_id}")
        
        return jsonify({
            "success": True,
            "transaction_id": transaction_id,
            "payment_url": url_result['payment_url'],
            "lesson_title": lesson.title,
            "amount": lesson.price,
            "currency": "CHF"
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error initiating lesson purchase: {e}")
        return jsonify({"error": "Purchase initiation failed"}), 500
```

#### Step 2: Update Course Purchase Endpoint

**Replace the existing `/api/courses/<int:course_id>/purchase` endpoint:**

```python
@bp.route('/api/courses/<int:course_id>/purchase', methods=['POST'])
@login_required
def purchase_course(course_id):
    """
    Initiate course purchase with PostFinance Checkout
    Similar structure to lesson purchase
    """
    # Similar implementation pattern to lesson purchase
    # Use payment_service.create_course_transaction()
```

#### Step 3: Add New Payment Status Endpoints

```python
@bp.route('/api/payment/status/<int:transaction_id>', methods=['GET'])
@login_required
def get_payment_status(transaction_id):
    """
    Check payment status for a transaction
    
    Returns current transaction state and details
    """
    from app.services.payment_service import get_payment_service
    
    # Verify user owns this transaction
    payment_transaction = PaymentTransaction.query.filter_by(
        transaction_id=transaction_id,
        user_id=current_user.id
    ).first_or_404()
    
    try:
        payment_service = get_payment_service()
        result = payment_service.get_transaction_status(transaction_id)
        
        if result['success']:
            # Update local state if different
            if result['state'] != payment_transaction.state:
                transaction_service = PaymentTransactionService()
                transaction_service.update_transaction_state(
                    transaction_id, 
                    result['state']
                )
            
            return jsonify({
                "success": True,
                "transaction_id": transaction_id,
                "state": result['state'],
                "item_type": payment_transaction.item_type,
                "item_id": payment_transaction.item_id,
                "amount": payment_transaction.amount
            })
        else:
            return jsonify({
                "error": result['error']
            }), 400
            
    except Exception as e:
        current_app.logger.error(f"Error checking payment status: {e}")
        return jsonify({"error": "Status check failed"}), 500

@bp.route('/api/payment/cancel/<int:transaction_id>', methods=['POST'])
@login_required
def cancel_payment(transaction_id):
    """
    Cancel a pending payment transaction
    
    Note: This is for user-initiated cancellation
    PostFinance handles timeout cancellation automatically
    """
    # Verify user owns this transaction
    payment_transaction = PaymentTransaction.query.filter_by(
        transaction_id=transaction_id,
        user_id=current_user.id,
        state='PENDING'
    ).first_or_404()
    
    try:
        transaction_service = PaymentTransactionService()
        success = transaction_service.update_transaction_state(
            transaction_id, 
            'CANCELLED'
        )
        
        if success:
            return jsonify({
                "success": True,
                "message": "Payment cancelled successfully"
            })
        else:
            return jsonify({"error": "Failed to cancel payment"}), 500
            
    except Exception as e:
        current_app.logger.error(f"Error cancelling payment: {e}")
        return jsonify({"error": "Cancellation failed"}), 500
```

---

## 2.4 Payment Flow Implementation

### 2.4.1 Frontend Integration Updates
**Location**: Templates and static files
**Estimated Time**: 3-4 hours
**Priority**: High

#### Step 1: Update Purchase Pages

**Update `templates/purchase.html`:**

```html
<!-- Add loading states and error handling -->
<div id="purchase-form">
    <div class="payment-summary">
        <h3>Purchase Summary</h3>
        <p><strong>{{ lesson.title }}</strong></p>
        <p>Price: CHF {{ "%.2f"|format(lesson.price) }}</p>
    </div>
    
    <button id="purchase-btn" class="btn btn-primary">
        <span class="btn-text">Purchase Lesson</span>
        <span class="btn-loading" style="display: none;">
            <i class="fa fa-spinner fa-spin"></i> Processing...
        </span>
    </button>
    
    <div id="error-message" class="alert alert-danger" style="display: none;"></div>
</div>

<script>
document.getElementById('purchase-btn').addEventListener('click', function() {
    const btn = this;
    const btnText = btn.querySelector('.btn-text');
    const btnLoading = btn.querySelector('.btn-loading');
    const errorDiv = document.getElementById('error-message');
    
    // Show loading state
    btn.disabled = true;
    btnText.style.display = 'none';
    btnLoading.style.display = 'inline';
    errorDiv.style.display = 'none';
    
    // Get CSRF token
    const csrfToken = document.querySelector('meta[name=csrf-token]').getAttribute('content');
    
    fetch(`/api/lessons/{{ lesson.id }}/purchase`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Redirect to PostFinance payment page
            window.location.href = data.payment_url;
        } else {
            // Show error
            errorDiv.textContent = data.error || 'Purchase failed';
            errorDiv.style.display = 'block';
        }
    })
    .catch(error => {
        console.error('Error:', error);
        errorDiv.textContent = 'Network error occurred';
        errorDiv.style.display = 'block';
    })
    .finally(() => {
        // Reset button state
        btn.disabled = false;
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
    });
});
</script>
```

#### Step 2: Create Payment Result Pages

**Create `templates/payment_success.html`:**

```html
{% extends "base.html" %}

{% block content %}
<div class="container mt-4">
    <div class="alert alert-success text-center">
        <h2><i class="fa fa-check-circle"></i> Payment Successful!</h2>
        <p>Your purchase has been completed successfully.</p>
    </div>
    
    <div class="card">
        <div class="card-body text-center">
            <h4>What's Next?</h4>
            <p>You can now access your purchased content.</p>
            <a href="{{ url_for('routes.my_lessons') }}" class="btn btn-primary">
                View My Lessons
            </a>
        </div>
    </div>
</div>

<script>
// Check payment status on page load
window.addEventListener('load', function() {
    const urlParams = new URLSearchParams(window.location.search);
    const transactionId = urlParams.get('transaction_id');
    
    if (transactionId) {
        // Verify payment status
        fetch(`/api/payment/status/${transactionId}`)
        .then(response => response.json())
        .then(data => {
            if (data.success && ['COMPLETED', 'FULFILL'].includes(data.state)) {
                console.log('Payment confirmed:', data);
            } else {
                console.warn('Payment status unclear:', data);
            }
        })
        .catch(error => console.error('Status check error:', error));
    }
});
</script>
{% endblock %}
```

**Create `templates/payment_failed.html`:**

```html
{% extends "base.html" %}

{% block content %}
<div class="container mt-4">
    <div class="alert alert-danger text-center">
        <h2><i class="fa fa-times-circle"></i> Payment Failed</h2>
        <p>Unfortunately, your payment could not be processed.</p>
    </div>
    
    <div class="card">
        <div class="card-body text-center">
            <h4>What Happened?</h4>
            <p>Your payment was not completed. This could be due to:</p>
            <ul class="text-left">
                <li>Payment method declined</li>
                <li>Insufficient funds</li>
                <li>Payment cancelled</li>
                <li>Technical issue</li>
            </ul>
            
            <div class="mt-3">
                <a href="javascript:history.back()" class="btn btn-secondary me-2">
                    Try Again
                </a>
                <a href="{{ url_for('routes.lessons') }}" class="btn btn-primary">
                    Browse Lessons
                </a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### 2.4.2 Configure Success/Failure URLs
**Location**: `instance/config.py`
**Estimated Time**: 30 minutes
**Priority**: Critical

```python
class Config:
    # Existing config...
    
    # Payment redirect URLs
    PAYMENT_SUCCESS_URL = os.environ.get('PAYMENT_SUCCESS_URL', 'http://localhost:5000/payment/success')
    PAYMENT_FAILURE_URL = os.environ.get('PAYMENT_FAILURE_URL', 'http://localhost:5000/payment/failed')
```

**Add corresponding routes:**

```python
@bp.route('/payment/success')
def payment_success():
    """Handle successful payment redirect from PostFinance"""
    return render_template('payment_success.html')

@bp.route('/payment/failed')
def payment_failed():
    """Handle failed payment redirect from PostFinance"""
    return render_template('payment_failed.html')
```

---

## 2.5 Error Handling and Recovery

### 2.5.1 Implement Comprehensive Error Handling
**Location**: `app/services/payment_service.py`
**Estimated Time**: 2-3 hours
**Priority**: High

```python
class PaymentErrorHandler:
    @staticmethod
    def handle_client_error(error_data: dict) -> dict:
        """
        Handle PostFinance Client Errors (442)
        Types: END_USER_ERROR, CONFIGURATION_ERROR, DEVELOPER_ERROR
        """
        error_type = error_data.get('type', 'CLIENT_ERROR')
        
        if error_type == 'END_USER_ERROR':
            return {
                'user_message': 'Please check your payment information and try again.',
                'severity': 'warning'
            }
        elif error_type == 'CONFIGURATION_ERROR':
            return {
                'user_message': 'Payment system temporarily unavailable. Please try again later.',
                'severity': 'error',
                'requires_admin': True
            }
        elif error_type == 'DEVELOPER_ERROR':
            return {
                'user_message': 'System error occurred. Support has been notified.',
                'severity': 'error',
                'requires_admin': True
            }
        else:
            return {
                'user_message': 'Payment processing error. Please try again.',
                'severity': 'error'
            }
    
    @staticmethod
    def handle_server_error(error_data: dict) -> dict:
        """
        Handle PostFinance Server Errors (542)
        """
        return {
            'user_message': 'Payment service temporarily unavailable. Please try again in a few minutes.',
            'severity': 'error',
            'retry_after': 300  # 5 minutes
        }
```

### 2.5.2 Add Transaction Timeout Handling
**Priority**: Medium

```python
def check_transaction_timeouts(self):
    """
    Check for transactions that have exceeded timeout
    Should be called periodically (cron job or background task)
    """
    from datetime import datetime, timedelta
    
    timeout_threshold = datetime.utcnow() - timedelta(hours=1)  # 1 hour timeout
    
    expired_transactions = PaymentTransaction.query.filter(
        PaymentTransaction.state == 'PENDING',
        PaymentTransaction.created_at < timeout_threshold
    ).all()
    
    for transaction in expired_transactions:
        # Check actual status with PostFinance
        status_result = self.get_transaction_status(transaction.transaction_id)
        
        if status_result['success']:
            # Update to actual state
            transaction_service = PaymentTransactionService()
            transaction_service.update_transaction_state(
                transaction.transaction_id,
                status_result['state']
            )
        else:
            # Mark as timeout if we can't reach PostFinance
            transaction_service = PaymentTransactionService()
            transaction_service.update_transaction_state(
                transaction.transaction_id,
                'TIMEOUT'
            )
```

---

## 2.6 Testing Strategy

### 2.6.1 Unit Tests for Payment Services
**Location**: `tests/test_payment_service.py`
**Estimated Time**: 4-5 hours
**Priority**: High

```python
import pytest
from unittest.mock import Mock, patch, MagicMock
from app.services.payment_service import PostFinanceService
from app.services.transaction_service import PaymentTransactionService
from app.models import User, Lesson, Course, PaymentTransaction
from postfinancecheckout.rest import ApiException

class TestPostFinanceService:
    def setup_method(self):
        self.mock_config = {
            'POSTFINANCE_SPACE_ID': 405,
            'POSTFINANCE_USER_ID': 512,
            'POSTFINANCE_API_SECRET': 'test_secret',
            'PAYMENT_SUCCESS_URL': 'http://localhost:5000/payment/success',
            'PAYMENT_FAILURE_URL': 'http://localhost:5000/payment/failed'
        }
    
    @patch('app.services.payment_service.current_app')
    def test_create_lesson_transaction_success(self, mock_app):
        mock_app.config = self.mock_config
        
        # Mock PostFinance API response
        mock_transaction = Mock()
        mock_transaction.id = 12345
        mock_transaction.state = 'PENDING'
        
        service = PostFinanceService()
        service.transaction_service = Mock()
        service.transaction_service.create.return_value = mock_transaction
        
        # Test data
        user = Mock()
        user.id = 1
        lesson = Mock()
        lesson.id = 100
        lesson.title = 'Test Lesson'
        lesson.price = 29.99
        
        # Execute
        result = service.create_lesson_transaction(user, lesson)
        
        # Assertions
        assert result['success'] is True
        assert result['transaction_id'] == 12345
        service.transaction_service.create.assert_called_once()
    
    @patch('app.services.payment_service.current_app')
    def test_create_lesson_transaction_api_error(self, mock_app):
        mock_app.config = self.mock_config
        
        service = PostFinanceService()
        service.transaction_service = Mock()
        
        # Mock API exception
        api_error = ApiException(status=442, reason="Client Error")
        api_error.body = '{"type": "END_USER_ERROR", "message": "Invalid payment data"}'
        service.transaction_service.create.side_effect = api_error
        
        user = Mock()
        lesson = Mock()
        lesson.title = 'Test Lesson'
        lesson.price = 29.99
        
        # Execute
        result = service.create_lesson_transaction(user, lesson)
        
        # Assertions
        assert result['success'] is False
        assert 'Invalid payment data' in result['error']
        assert result['error_type'] == 'END_USER_ERROR'
    
    def test_generate_payment_page_url_success(self):
        service = PostFinanceService()
        service.payment_page_service = Mock()
        service.payment_page_service.payment_page_url.return_value = 'https://checkout.postfinance.ch/pay/12345'
        
        result = service.generate_payment_page_url(12345)
        
        assert result['success'] is True
        assert 'https://checkout.postfinance.ch' in result['payment_url']

class TestPaymentTransactionService:
    def test_create_payment_transaction(self):
        service = PaymentTransactionService()
        
        user = Mock()
        user.id = 1
        
        with patch('app.services.transaction_service.db.session') as mock_session:
            transaction = service.create_payment_transaction(
                transaction_id=12345,
                user=user,
                item_type='lesson',
                item_id=100,
                amount=29.99
            )
            
            mock_session.add.assert_called_once()
            mock_session.commit.assert_called_once()
            assert transaction.transaction_id == 12345
            assert transaction.state == 'PENDING'
    
    def test_update_transaction_state_completed(self):
        service = PaymentTransactionService()
        
        # Mock existing transaction
        mock_transaction = Mock()
        mock_transaction.state = 'PENDING'
        mock_transaction.item_type = 'lesson'
        mock_transaction.user_id = 1
        mock_transaction.item_id = 100
        mock_transaction.amount = 29.99
        
        with patch.object(PaymentTransaction, 'query') as mock_query:
            mock_query.filter_by.return_value.first.return_value = mock_transaction
            
            with patch('app.services.transaction_service.db.session') as mock_session:
                with patch.object(service, '_complete_purchase') as mock_complete:
                    result = service.update_transaction_state(12345, 'COMPLETED')
                    
                    assert result is True
                    mock_complete.assert_called_once_with(mock_transaction)
                    mock_session.commit.assert_called_once()
```

### 2.6.2 Integration Tests
**Location**: `tests/test_payment_integration.py`
**Estimated Time**: 3-4 hours
**Priority**: High

```python
import pytest
from flask import url_for
from app import create_app, db
from app.models import User, Lesson, PaymentTransaction, LessonPurchase

class TestPaymentIntegration:
    def setup_method(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create test user
        self.user = User(username='testuser', email='test@example.com')
        self.user.set_password('password')
        db.session.add(self.user)
        
        # Create test lesson
        self.lesson = Lesson(
            title='Test Lesson',
            description='Test lesson for payment',
            lesson_type='paid',
            price=29.99,
            is_purchasable=True,
            is_published=True
        )
        db.session.add(self.lesson)
        db.session.commit()
        
        self.client = self.app.test_client()
    
    def teardown_method(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login_user(self):
        with self.client.session_transaction() as sess:
            sess['_user_id'] = str(self.user.id)
            sess['_fresh'] = True
    
    @patch('app.services.payment_service.PostFinanceService')
    def test_lesson_purchase_flow_success(self, mock_service_class):
        # Mock PostFinance service
        mock_service = Mock()
        mock_service.create_lesson_transaction.return_value = {
            'success': True,
            'transaction_id': 12345
        }
        mock_service.generate_payment_page_url.return_value = {
            'success': True,
            'payment_url': 'https://checkout.postfinance.ch/pay/12345'
        }
        mock_service_class.return_value = mock_service
        
        self.login_user()
        
        # Make purchase request
        response = self.client.post(
            f'/api/lessons/{self.lesson.id}/purchase',
            headers={'X-CSRFToken': 'test-token'},
            json={}
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['success'] is True
        assert data['transaction_id'] == 12345
        assert 'payment_url' in data
        
        # Verify PaymentTransaction was created
        transaction = PaymentTransaction.query.filter_by(transaction_id=12345).first()
        assert transaction is not None
        assert transaction.user_id == self.user.id
        assert transaction.item_type == 'lesson'
    
    def test_lesson_purchase_already_owned(self):
        # Create existing purchase
        purchase = LessonPurchase(
            user_id=self.user.id,
            lesson_id=self.lesson.id,
            price_paid=29.99
        )
        db.session.add(purchase)
        db.session.commit()
        
        self.login_user()
        
        response = self.client.post(
            f'/api/lessons/{self.lesson.id}/purchase',
            headers={'X-CSRFToken': 'test-token'},
            json={}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'already own' in data['error']
    
    def test_lesson_purchase_not_purchasable(self):
        self.lesson.is_purchasable = False
        db.session.commit()
        
        self.login_user()
        
        response = self.client.post(
            f'/api/lessons/{self.lesson.id}/purchase',
            headers={'X-CSRFToken': 'test-token'},
            json={}
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert 'not available for purchase' in data['error']
```

### 2.6.3 Manual Testing Checklist
**Priority**: High

**Phase 2 Testing Checklist:**

1. **Transaction Creation Tests**
   - [ ] Create lesson transaction with valid data
   - [ ] Create course transaction with valid data
   - [ ] Handle invalid lesson/course IDs
   - [ ] Handle user already owns item
   - [ ] Handle non-purchasable items
   - [ ] Test with different price values (including edge cases)

2. **Payment URL Generation Tests**
   - [ ] Generate valid payment URLs
   - [ ] Handle transaction ID not found
   - [ ] Handle PostFinance API errors

3. **Payment Flow Tests**
   - [ ] Complete successful payment flow
   - [ ] Handle payment cancellation
   - [ ] Handle payment failure
   - [ ] Test redirect URLs (success/failure)
   - [ ] Verify transaction state updates

4. **Error Handling Tests**
   - [ ] PostFinance API unavailable
   - [ ] Invalid API credentials
   - [ ] Network timeouts
   - [ ] Database connection issues
   - [ ] Invalid transaction states

5. **Security Tests**
   - [ ] CSRF token validation
   - [ ] User authorization checks
   - [ ] Transaction ownership verification
   - [ ] SQL injection prevention
   - [ ] XSS prevention in error messages

---

## 2.7 Security Considerations

### 2.7.1 Transaction Security
**Priority**: Critical

**Implementation Requirements:**

1. **Transaction Ownership Verification**
```python
def verify_transaction_ownership(user_id: int, transaction_id: int) -> bool:
    """Verify user owns the transaction"""
    transaction = PaymentTransaction.query.filter_by(
        transaction_id=transaction_id,
        user_id=user_id
    ).first()
    return transaction is not None
```

2. **Metadata Validation**
```python
def validate_transaction_metadata(transaction, expected_user_id: int) -> bool:
    """Validate transaction metadata matches expected user"""
    if not transaction.meta_data:
        return False
    
    metadata_user_id = transaction.meta_data.get('user_id')
    return str(metadata_user_id) == str(expected_user_id)
```

3. **Amount Validation**
```python
def validate_transaction_amount(transaction, expected_amount: float) -> bool:
    """Ensure transaction amount matches expected price"""
    tolerance = 0.01  # 1 cent tolerance for floating point precision
    return abs(transaction.amount - expected_amount) <= tolerance
```

### 2.7.2 API Security
**Priority**: Critical

1. **Rate Limiting** (Add to routes)
```python
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

limiter = Limiter(
    app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

@bp.route('/api/lessons/<int:lesson_id>/purchase', methods=['POST'])
@limiter.limit("5 per minute")  # Prevent purchase spam
@login_required
def purchase_lesson(lesson_id):
    # ... existing code
```

2. **Input Sanitization**
```python
def sanitize_transaction_input(data: dict) -> dict:
    """Sanitize input data for transaction creation"""
    sanitized = {}
    
    # Only allow expected fields
    allowed_fields = ['lesson_id', 'course_id', 'user_id']
    for field in allowed_fields:
        if field in data:
            sanitized[field] = int(data[field])  # Ensure integer
    
    return sanitized
```

### 2.7.3 Environment Security
**Priority**: High

**Environment Variables Checklist:**
```bash
# Production Environment (.env.production)
POSTFINANCE_SPACE_ID=your_production_space_id
POSTFINANCE_USER_ID=your_production_user_id
POSTFINANCE_API_SECRET=your_production_api_secret
PAYMENT_SUCCESS_URL=https://yourdomain.com/payment/success
PAYMENT_FAILURE_URL=https://yourdomain.com/payment/failed

# Security headers
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
SESSION_COOKIE_HTTPONLY=True
```

---

## 2.8 Database Migration Requirements

### 2.8.1 Migration Script for Existing Data
**Location**: Create `migrations/update_existing_purchases_phase2.py`
**Estimated Time**: 1-2 hours
**Priority**: High

```python
"""
Migration script to update existing purchase records for Phase 2 compatibility
This script should be run before deploying Phase 2 changes
"""

from app import db
from app.models import LessonPurchase, CoursePurchase
from sqlalchemy import text

def migrate_existing_purchases():
    """
    Update existing purchase records to be compatible with Phase 2
    - Set transaction_state to 'COMPLETED' for existing purchases
    - Ensure postfinance_transaction_id is properly set (will be None for old purchases)
    """
    
    try:
        # Update lesson purchases
        lesson_update_sql = text("""
            UPDATE lesson_purchase 
            SET transaction_state = 'COMPLETED'
            WHERE transaction_state IS NULL 
            AND purchased_at IS NOT NULL
        """)
        
        result = db.session.execute(lesson_update_sql)
        lesson_count = result.rowcount
        
        # Update course purchases
        course_update_sql = text("""
            UPDATE course_purchase 
            SET transaction_state = 'COMPLETED'
            WHERE transaction_state IS NULL 
            AND purchased_at IS NOT NULL
        """)
        
        result = db.session.execute(course_update_sql)
        course_count = result.rowcount
        
        db.session.commit()
        
        print(f"Migration completed successfully:")
        print(f"  - Updated {lesson_count} lesson purchases")
        print(f"  - Updated {course_count} course purchases")
        
        return True
        
    except Exception as e:
        db.session.rollback()
        print(f"Migration failed: {e}")
        return False

if __name__ == '__main__':
    migrate_existing_purchases()
```

### 2.8.2 Index Optimization
**Priority**: Medium

```sql
-- Add indexes for performance optimization
CREATE INDEX IF NOT EXISTS idx_payment_transaction_user_state 
ON payment_transaction(user_id, state);

CREATE INDEX IF NOT EXISTS idx_payment_transaction_created_state 
ON payment_transaction(created_at, state);

CREATE INDEX IF NOT EXISTS idx_lesson_purchase_transaction_id 
ON lesson_purchase(postfinance_transaction_id);

CREATE INDEX IF NOT EXISTS idx_course_purchase_transaction_id 
ON course_purchase(postfinance_transaction_id);
```

---

## 2.9 Deployment Checklist

### 2.9.1 Pre-Deployment Verification
**Priority**: Critical

**Environment Setup:**
- [ ] PostFinance Checkout production account configured
- [ ] Production API credentials verified
- [ ] Success/failure URLs configured for production domain
- [ ] SSL certificates installed and verified
- [ ] Database backup completed

**Code Deployment:**
- [ ] All Phase 2 code reviewed and tested
- [ ] Unit tests passing (>95% coverage)
- [ ] Integration tests passing
- [ ] Security audit completed
- [ ] Performance testing completed

**Configuration:**
- [ ] Environment variables set correctly
- [ ] Database migrations executed
- [ ] Existing purchase data migrated
- [ ] Monitoring and logging configured

### 2.9.2 Post-Deployment Monitoring
**Priority**: High

**Key Metrics to Monitor:**
1. **Transaction Success Rate**
   - Target: >95% success rate
   - Alert if rate drops below 90%

2. **Payment Processing Time**
   - Target: <30 seconds average
   - Alert if >60 seconds average

3. **Error Rates**
   - API errors: <1% of requests
   - Database errors: <0.1% of requests

4. **User Experience**
   - Payment abandonment rate
   - Support tickets related to payments
   - User feedback on payment process

**Monitoring Implementation:**
```python
# Add to payment service methods
import time
from flask import current_app

def monitor_payment_performance(func):
    """Decorator to monitor payment method performance"""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        try:
            result = func(*args, **kwargs)
            success = result.get('success', False)
            
            # Log performance metrics
            duration = time.time() - start_time
            current_app.logger.info(f"Payment method {func.__name__}: "
                                   f"duration={duration:.2f}s, success={success}")
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            current_app.logger.error(f"Payment method {func.__name__} failed: "
                                    f"duration={duration:.2f}s, error={e}")
            raise
    return wrapper
```

---

## 2.10 Risk Assessment and Mitigation

### 2.10.1 Technical Risks

**High Risk:**
1. **PostFinance API Unavailability**
   - **Impact**: Users cannot make purchases
   - **Mitigation**: Implement retry logic, graceful degradation, status page
   - **Fallback**: Temporary maintenance mode with clear communication

2. **Payment State Synchronization Issues**
   - **Impact**: Purchases not properly recorded
   - **Mitigation**: Webhook redundancy, periodic status checks, manual reconciliation tools
   - **Monitoring**: Alert on state mismatches

**Medium Risk:**
1. **Database Performance Impact**
   - **Impact**: Slow payment processing
   - **Mitigation**: Database indexes, query optimization, connection pooling
   - **Monitoring**: Query performance tracking

2. **Security Vulnerabilities**
   - **Impact**: Financial fraud, data breach
   - **Mitigation**: Regular security audits, input validation, rate limiting
   - **Prevention**: Automated security scanning

### 2.10.2 Business Risks

**High Risk:**
1. **Revenue Loss During Transition**
   - **Impact**: Temporary loss of sales
   - **Mitigation**: Thorough testing, gradual rollout, quick rollback plan
   - **Timeline**: Minimize downtime to <2 hours

2. **User Experience Degradation**
   - **Impact**: Customer dissatisfaction, support load
   - **Mitigation**: User testing, clear error messages, comprehensive support documentation
   - **Recovery**: Rapid issue resolution process

---

## 2.11 Implementation Timeline

### Week 1: Core Service Implementation
**Days 1-3: Payment Service Enhancement**
- Enhance PostFinanceService class (2.1.1)
- Implement transaction creation methods
- Add payment URL generation
- Create error handling framework

**Days 4-5: Database Service Implementation**
- Create PaymentTransactionService (2.2.1)
- Implement transaction state management
- Add purchase completion logic

### Week 2: API and Frontend Integration
**Days 1-2: API Endpoint Updates**
- Replace mock payment endpoints (2.3.1)
- Add payment status endpoints
- Implement security measures

**Days 3-4: Frontend Integration**
- Update purchase pages (2.4.1)
- Create payment result pages
- Add loading states and error handling

**Day 5: Configuration and Testing Setup**
- Configure success/failure URLs (2.4.2)
- Set up testing framework
- Create unit test foundation

### Week 3: Testing and Security
**Days 1-2: Comprehensive Testing**
- Unit tests implementation (2.6.1)
- Integration tests (2.6.2)
- Manual testing execution

**Days 3-4: Security Implementation**
- Security measures implementation (2.7)
- Rate limiting setup
- Input validation and sanitization

**Day 5: Performance and Monitoring**
- Performance optimization
- Monitoring setup (2.9.2)
- Error tracking implementation

### Week 4: Deployment Preparation
**Days 1-2: Migration and Database**
- Create migration scripts (2.8.1)
- Database optimization
- Backup and recovery procedures

**Days 3-4: Production Preparation**
- Production environment setup
- SSL and security configuration
- Performance testing in staging

**Day 5: Deployment and Go-Live**
- Production deployment
- Post-deployment verification
- Monitoring activation

---

## 2.12 Success Criteria

### Technical Success Metrics
- [ ] All unit tests pass with >95% coverage
- [ ] Integration tests complete successfully
- [ ] Payment success rate >95%
- [ ] Average payment processing time <30 seconds
- [ ] Zero critical security vulnerabilities
- [ ] Database performance within acceptable limits

### Business Success Metrics
- [ ] Zero payment-related revenue loss during transition
- [ ] User satisfaction maintained (>90% positive feedback)
- [ ] Support ticket volume increase <20%
- [ ] Payment abandonment rate <5%
- [ ] Admin can successfully manage all payment scenarios

### Operational Success Metrics
- [ ] Monitoring and alerting fully operational
- [ ] Documentation complete and accessible
- [ ] Team trained on new payment system
- [ ] Rollback procedure tested and verified
- [ ] Compliance requirements met

---

## 2.13 Next Steps After Phase 2

After successful completion of Phase 2, the following phases can be initiated:

**Phase 3: Webhook Integration** (Recommended Next)
- Real-time payment status updates
- Automated payment confirmation
- Enhanced reliability and user experience

**Phase 4: Advanced Features**
- Multiple payment methods
- Subscription management
- Advanced analytics and reporting

**Phase 5: Production Hardening**
- Load balancing
- Advanced security measures
- Disaster recovery procedures

---

## Summary

Phase 2 represents a critical transition from mock payment processing to a fully functional PostFinance Checkout integration. This implementation plan provides a structured approach to:

1. **Replace mock payment system** with real PostFinance API integration
2. **Maintain system reliability** through comprehensive error handling
3. **Ensure data integrity** with proper transaction management
4. **Provide excellent user experience** with clear payment flows
5. **Implement robust security** measures throughout the system

The estimated total implementation time is **3-4 weeks** with a team of 2-3 developers, assuming Phase 1 prerequisites are completed. Success depends on careful testing, security implementation, and thorough deployment preparation.

**Critical Success Factors:**
- Thorough testing at each implementation step
- Proper error handling and user feedback
- Secure transaction management
- Comprehensive monitoring and alerting
- Clear rollback procedures for any issues

This plan provides the foundation for a production-ready payment system that can scale with the business needs while maintaining security and reliability standards.
