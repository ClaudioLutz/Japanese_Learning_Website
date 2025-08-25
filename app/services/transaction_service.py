# app/services/transaction_service.py

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
        # Could implement cleanup, notifications, etc.
    
    def get_user_transactions(self, user_id: int, limit: int = 50):
        """
        Get payment transactions for a user
        """
        try:
            transactions = PaymentTransaction.query.filter_by(
                user_id=user_id
            ).order_by(PaymentTransaction.created_at.desc()).limit(limit).all()
            
            return transactions
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving user transactions: {e}")
            return []
    
    def get_transaction_by_id(self, transaction_id: int) -> PaymentTransaction:
        """
        Get a specific payment transaction by ID
        """
        try:
            return PaymentTransaction.query.filter_by(
                transaction_id=transaction_id
            ).first()
            
        except SQLAlchemyError as e:
            self.logger.error(f"Error retrieving transaction {transaction_id}: {e}")
            return None
