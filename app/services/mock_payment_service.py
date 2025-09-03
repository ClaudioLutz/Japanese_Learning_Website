# app/services/mock_payment_service.py

from app.models import User, Lesson, Course, LessonPurchase, CoursePurchase
from app import db
from datetime import datetime
import logging
import random

class MockPaymentService:
    """
    Mock payment service for testing and development.
    Bypasses real payment processing and directly creates purchase records.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("MockPaymentService initialized - No real payments will be processed")

    def create_lesson_transaction(self, user: User, lesson: Lesson) -> dict:
        """
        Mock lesson purchase - immediately creates purchase record
        """
        try:
            # Check if user already owns this lesson
            existing_purchase = LessonPurchase.query.filter_by(
                user_id=user.id,
                lesson_id=lesson.id
            ).first()
            
            if existing_purchase:
                return {
                    'success': False,
                    'error': 'Lesson already purchased',
                    'error_type': 'DUPLICATE_PURCHASE'
                }
            
            # Create the purchase record directly
            lesson_purchase = LessonPurchase()
            lesson_purchase.user_id = user.id
            lesson_purchase.lesson_id = lesson.id
            lesson_purchase.price_paid = lesson.price
            lesson_purchase.purchased_at = datetime.utcnow()
            # Generate a mock transaction ID for consistency
            mock_transaction_id = random.randint(1000000, 9999999)
            lesson_purchase.postfinance_transaction_id = mock_transaction_id
            lesson_purchase.transaction_state = 'COMPLETED'  # Mock completion
            
            db.session.add(lesson_purchase)
            db.session.commit()
            
            # Generate a mock transaction ID for consistency
            mock_transaction_id = random.randint(1000000, 9999999)
            
            self.logger.info(f"Mock lesson purchase completed: User {user.id}, Lesson {lesson.id}, Mock Transaction {mock_transaction_id}")
            
            return {
                'success': True,
                'transaction_id': mock_transaction_id,
                'mock_purchase': True,
                'purchase_id': lesson_purchase.id
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Mock lesson purchase failed: {e}")
            return {
                'success': False,
                'error': 'Mock purchase creation failed',
                'error_type': 'SYSTEM_ERROR'
            }

    def create_course_transaction(self, user: User, course: Course) -> dict:
        """
        Mock course purchase - immediately creates purchase record
        """
        try:
            # Check if user already owns this course
            existing_purchase = CoursePurchase.query.filter_by(
                user_id=user.id,
                course_id=course.id
            ).first()
            
            if existing_purchase:
                return {
                    'success': False,
                    'error': 'Course already purchased',
                    'error_type': 'DUPLICATE_PURCHASE'
                }
            
            # Create the purchase record directly
            course_purchase = CoursePurchase()
            course_purchase.user_id = user.id
            course_purchase.course_id = course.id
            course_purchase.price_paid = course.price
            course_purchase.purchased_at = datetime.utcnow()
            # Generate a mock transaction ID for consistency
            mock_transaction_id = random.randint(1000000, 9999999)
            course_purchase.postfinance_transaction_id = mock_transaction_id
            course_purchase.transaction_state = 'COMPLETED'  # Mock completion
            
            db.session.add(course_purchase)
            db.session.commit()
            
            # Generate a mock transaction ID for consistency
            mock_transaction_id = random.randint(1000000, 9999999)
            
            self.logger.info(f"Mock course purchase completed: User {user.id}, Course {course.id}, Mock Transaction {mock_transaction_id}")
            
            return {
                'success': True,
                'transaction_id': mock_transaction_id,
                'mock_purchase': True,
                'purchase_id': course_purchase.id
            }
            
        except Exception as e:
            db.session.rollback()
            self.logger.error(f"Mock course purchase failed: {e}")
            return {
                'success': False,
                'error': 'Mock purchase creation failed',
                'error_type': 'SYSTEM_ERROR'
            }

    def generate_payment_page_url(self, transaction_id: int) -> dict:
        """
        Mock payment URL generation - returns success URL since payment is already "complete"
        """
        from flask import url_for, current_app
        
        try:
            # For mock payments, redirect to success page immediately
            success_url = url_for('routes.payment_success', _external=True)
            
            return {
                'success': True,
                'payment_url': success_url,
                'mock_payment': True
            }
            
        except Exception as e:
            self.logger.error(f"Error generating mock payment URL: {e}")
            return {
                'success': False,
                'error': 'Mock URL generation failed',
                'error_type': 'SYSTEM_ERROR'
            }

    def get_transaction_status(self, transaction_id: int) -> dict:
        """
        Mock transaction status - always returns completed for mock transactions
        """
        return {
            'success': True,
            'state': 'COMPLETED',
            'mock_transaction': True,
            'transaction_id': transaction_id
        }

class MockPaymentFactory:
    """Factory to determine which payment service to use"""
    
    @staticmethod
    def get_payment_service():
        """
        Return appropriate payment service based on configuration
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
            return MockPaymentService()
        else:
            # Try to import and use real PostFinance service
            try:
                from app.services.payment_service import get_payment_service as get_real_service
                current_app.logger.info("Using PostFinanceService - credentials configured")
                return get_real_service()
            except Exception as e:
                current_app.logger.warning(f"PostFinance service initialization failed, falling back to mock: {e}")
                return MockPaymentService()

def get_payment_service():
    """
    Get the appropriate payment service (mock or real)
    """
    return MockPaymentFactory.get_payment_service()
