# app/services/payment_service.py

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
from flask import current_app
from app.models import User, Lesson, Course, PaymentTransaction
from datetime import datetime, timedelta
import logging
import json

class PostFinanceService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        try:
            self.configuration = self._create_configuration()
            # Pass configuration directly to service APIs, not ApiClient
            self.transaction_service = TransactionServiceApi(configuration=self.configuration)
            self.space_id = current_app.config['POSTFINANCE_SPACE_ID']
            self.logger.info("PostFinanceService initialized successfully.")
        except ValueError as e:
            self.logger.error(f"Failed to initialize PostFinanceService: {e}")
            raise
        except Exception as e:
            self.logger.error(f"An unexpected error occurred during PostFinanceService initialization: {e}")
            raise

    def _create_configuration(self):
        """Creates the API configuration object from Flask app config."""
        user_id = current_app.config.get('POSTFINANCE_USER_ID')
        api_secret = current_app.config.get('POSTFINANCE_API_SECRET')
        
        if not user_id or not api_secret:
            raise ValueError("PostFinance User ID or API Secret is not configured.")

        # Ensure user_id is a string (PostFinance SDK expects string)
        user_id_str = str(user_id)

        return Configuration(
            user_id=user_id_str,
            api_secret=api_secret,
            request_timeout=30  # Set a reasonable timeout
        )

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

    def create_course_transaction(self, user: User, course: Course) -> dict:
        """
        Create a PostFinance transaction for course purchase
        Similar structure to lesson transaction but for courses
        """
        try:
            # Create line item using PostFinance API requirements
            line_item = LineItem(
                name=course.title[:150],  # Character limit: 1-150
                unique_id=f"course_{course.id}",  # Unique within transaction, 200 char limit
                sku=f"COURSE_{course.id}",  # SKU field, 200 char limit
                quantity=1,  # Positive decimal
                amount_including_tax=course.price,  # Price including tax
                type=LineItemType.PRODUCT  # PRODUCT, DISCOUNT, SHIPPING, FEE, or TIP
            )
            
            # Create transaction with metadata for linking
            transaction_create = TransactionCreate(
                line_items=[line_item],
                currency='CHF',  # ISO 4217 format
                auto_confirmation_enabled=True,
                success_url=current_app.config.get('PAYMENT_SUCCESS_URL'),
                failed_url=current_app.config.get('PAYMENT_FAILURE_URL'),
                # Use metaData field to store course_id for clean linking
                meta_data={
                    'course_id': str(course.id),
                    'user_id': str(user.id),
                    'item_type': 'course'
                }
            )
            
            # Create transaction via API
            transaction = self.transaction_service.create(
                space_id=self.space_id, 
                transaction=transaction_create
            )
            
            # Log successful creation
            self.logger.info(f"Transaction created: ID {transaction.id} for user {user.id}, course {course.id}")
            
            return {
                'success': True,
                'transaction_id': transaction.id,
                'transaction': transaction
            }
            
        except ApiException as e:
            # Handle PostFinance API errors
            self.logger.error(f"PostFinance API error creating course transaction: {e.body}")
            error_data = self._parse_api_error(e)
            return {
                'success': False,
                'error': error_data['message'],
                'error_type': error_data['type']
            }
        except Exception as e:
            self.logger.error(f"Unexpected error creating course transaction: {e}")
            return {
                'success': False,
                'error': 'Transaction creation failed',
                'error_type': 'SYSTEM_ERROR'
            }

    def generate_payment_page_url(self, transaction_id: int) -> dict:
        """
        Generate payment page URL for transaction
        
        API Endpoint: GET /api/transaction-payment-page/payment-page-url
        Query Parameters: spaceId (Long), id (Long - transaction ID)
        Returns: URL as String on success (HTTP 200)
        Error Responses: 409 Conflict, 442 Client Error, 542 Server Error
        """
        try:
            if not hasattr(self, 'payment_page_service'):
                self.payment_page_service = TransactionPaymentPageServiceApi(configuration=self.configuration)
            
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

    def _parse_api_error(self, api_exception: ApiException) -> dict:
        """
        Parse PostFinance API errors into structured format
        
        Client Error fields: type, defaultMessage, id, message
        Server Error fields: date, id, message
        """
        try:
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

    @staticmethod
    def check_transaction_timeouts(payment_service):
        """
        Check for transactions that have exceeded timeout
        Should be called periodically (cron job or background task)
        """
        timeout_hours = current_app.config.get('PAYMENT_TIMEOUT_HOURS', 1)
        timeout_threshold = datetime.utcnow() - timedelta(hours=timeout_hours)
        
        from app import db
        expired_transactions = PaymentTransaction.query.filter(
            PaymentTransaction.state == 'PENDING',
            PaymentTransaction.created_at < timeout_threshold
        ).all()
        
        for transaction in expired_transactions:
            # Check actual status with PostFinance
            status_result = payment_service.get_transaction_status(transaction.transaction_id)
            
            if status_result['success']:
                # Update to actual state
                from app.services.transaction_service import PaymentTransactionService
                transaction_service = PaymentTransactionService()
                transaction_service.update_transaction_state(
                    transaction.transaction_id,
                    status_result['state']
                )
            else:
                # Mark as timeout if we can't reach PostFinance
                from app.services.transaction_service import PaymentTransactionService
                transaction_service = PaymentTransactionService()
                transaction_service.update_transaction_state(
                    transaction.transaction_id,
                    'TIMEOUT'
                )

# Add enhanced PostFinanceService with timeout checking
class EnhancedPostFinanceService(PostFinanceService):
    def __init__(self):
        super().__init__()
        self.error_handler = PaymentErrorHandler()
    
    def create_lesson_transaction_with_timeout(self, user: User, lesson: Lesson) -> dict:
        """Create transaction with automatic timeout configuration"""
        result = self.create_lesson_transaction(user, lesson)
        
        if result['success']:
            # Set timeout for the transaction
            timeout_hours = current_app.config.get('PAYMENT_TIMEOUT_HOURS', 1)
            # Note: PostFinance handles timeouts automatically, but we track locally
            self.logger.info(f"Transaction {result['transaction_id']} will timeout after {timeout_hours} hours")
        
        return result
    
    def create_course_transaction_with_timeout(self, user: User, course: Course) -> dict:
        """Create course transaction with automatic timeout configuration"""
        result = self.create_course_transaction(user, course)
        
        if result['success']:
            # Set timeout for the transaction
            timeout_hours = current_app.config.get('PAYMENT_TIMEOUT_HOURS', 1)
            # Note: PostFinance handles timeouts automatically, but we track locally
            self.logger.info(f"Transaction {result['transaction_id']} will timeout after {timeout_hours} hours")
        
        return result
    
    def get_enhanced_error_message(self, error_data: dict) -> str:
        """Get user-friendly error message"""
        if error_data.get('type') in ['END_USER_ERROR', 'CONFIGURATION_ERROR', 'DEVELOPER_ERROR']:
            handled_error = self.error_handler.handle_client_error(error_data)
        else:
            handled_error = self.error_handler.handle_server_error(error_data)
        
        return handled_error.get('user_message', 'Payment processing error occurred.')

# You can add a simple function to get a service instance
def get_payment_service():
    """
    Get the appropriate payment service (PostFinance or Mock) based on configuration
    """
    from flask import current_app
    
    # Check if PostFinance credentials are properly configured
    postfinance_configured = all([
        current_app.config.get('POSTFINANCE_USER_ID'),
        current_app.config.get('POSTFINANCE_API_SECRET'),
        current_app.config.get('POSTFINANCE_SPACE_ID'),
    ])
    
    # Also check if we're explicitly in mock mode
    force_mock_mode = current_app.config.get('MOCK_PAYMENTS_ENABLED', False)
    
    if not postfinance_configured or force_mock_mode:
        current_app.logger.info("Using MockPaymentService - PostFinance not configured or mock mode enabled")
        from app.services.mock_payment_service import MockPaymentService
        return MockPaymentService()
    else:
        # Try to use real PostFinance service
        try:
            current_app.logger.info("Using PostFinanceService - credentials configured")
            return EnhancedPostFinanceService()
        except Exception as e:
            current_app.logger.warning(f"PostFinance service initialization failed, falling back to mock: {e}")
            from app.services.mock_payment_service import MockPaymentService
            return MockPaymentService()

# Backward compatibility
def get_basic_payment_service():
    return PostFinanceService()
