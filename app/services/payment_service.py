# app/services/payment_service.py

from postfinancecheckout import Configuration, ApiClient, TransactionServiceApi
from postfinancecheckout.rest import ApiException
from flask import current_app
import logging

class PostFinanceService:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        try:
            config = self._create_configuration()
            self.api_client = ApiClient(config)
            self.transaction_service = TransactionServiceApi(self.api_client)
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

        try:
            user_id_int = int(user_id)
        except (ValueError, TypeError):
            raise ValueError(f"PostFinance User ID must be a valid integer, got: {user_id}")

        return Configuration(
            user_id=user_id_int,
            api_secret=api_secret,
            request_timeout=30  # Set a reasonable timeout
        )

    def get_transaction_status(self, transaction_id: int):
        """Reads the status of a given transaction."""
        try:
            transaction = self.transaction_service.read(space_id=self.space_id, id=transaction_id)
            return transaction
        except ApiException as e:
            self.logger.error(f"API error when reading transaction {transaction_id}: {e.body}")
            return None
        except Exception as e:
            self.logger.error(f"Unexpected error reading transaction {transaction_id}: {e}")
            return None

# You can add a simple function to get a service instance
def get_payment_service():
    return PostFinanceService()
