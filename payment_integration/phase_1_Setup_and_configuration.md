# Phase 1: Foundation Setup and Configuration

This document provides a detailed, step-by-step guide for completing Phase 1 of the PostFinance Checkout integration. It incorporates information from the initial plan, the official API documentation, the Python SDK, and an analysis of the existing application codebase.

---

## 1.1: Account Setup and Credentials

**Objective**: Establish the PostFinance Checkout account and securely configure API credentials.

**Action Items**:

1.  **Create PostFinance Account**:
    *   [x] Access the PostFinance Checkout portal and create a merchant account.
    *   [x] Within the account, create a new "Space". This `spaceId` will be required for nearly all API calls.

2.  **Generate API Credentials**:
    *   [x] In the account dashboard, navigate to **Account > Users > Application Users**.
    *   [x] Create a new Application User.
    *   [x] **Securely store the following credentials**:
        *   `user_id`: The ID of the Application User (visible in the user list). This will be used for the `x-mac-userid` header.
        *   `api_secret`: A 32-byte, Base64 encoded authentication key. **This is shown only once.** It must be saved immediately and securely.

3.  **Configure Webhook Endpoint in Dashboard**:
    *   [x] In the PostFinance dashboard for your Space, navigate to the Webhooks section.
    *   [x] Create a new **Webhook URL**. Set the URL to `https://<your_domain>/webhook/postfinance`.
    *   [x] Create a new **Webhook Listener** and subscribe it to the `Transaction` entity.
    *   [x] Configure the listener to trigger on the following states initially: `COMPLETED`, `FAILED`, `FULFILL`. This can be expanded later.
    *   [x] Ensure the `enablePayloadSignatureAndState` flag is enabled for enhanced security.

---

## 1.2: Environment Configuration

**Objective**: Integrate PostFinance credentials and settings into the application's configuration management.

**Action Items**:

1.  **Update `.env` file**:
    *   Add the following keys to your `.env` file with the credentials obtained in step 1.1.

    ```dotenv
    # PostFinance Checkout Credentials
    POSTFINANCE_SPACE_ID="<your_space_id>"
    POSTFINANCE_USER_ID="<your_user_id>"
    POSTFINANCE_API_SECRET="<your_api_secret>"

    # PostFinance URLs and Webhook Secret
    PAYMENT_SUCCESS_URL="https://<your_domain>/payment/success"
    PAYMENT_FAILURE_URL="https://<your_domain>/payment/failure"
    ```

2.  **Update `instance/config.py`**:
    *   Modify the file to load the PostFinance credentials from the environment variables.

    ```python
    # instance/config.py

    import os

    # Grabs the folder where the script runs.
    basedir = os.path.abspath(os.path.dirname(__file__))

    # Enable debug mode.
    DEBUG = True

    # Secret key for session management.
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'mysecretkey'

    # Connect to the database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'postgresql://postgres:E8BnuCBpWKP@localhost:5433/japanese_learning'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # PostFinance Checkout Configuration
    POSTFINANCE_SPACE_ID = os.environ.get('POSTFINANCE_SPACE_ID')
    POSTFINANCE_USER_ID = os.environ.get('POSTFINANCE_USER_ID')
    POSTFINANCE_API_SECRET = os.environ.get('POSTFINANCE_API_SECRET')
    PAYMENT_SUCCESS_URL = os.environ.get('PAYMENT_SUCCESS_URL')
    PAYMENT_FAILURE_URL = os.environ.get('PAYMENT_FAILURE_URL')

    # Basic validation to ensure payment config is loaded
    if not all([POSTFINANCE_SPACE_ID, POSTFINANCE_USER_ID, POSTFINANCE_API_SECRET]):
        raise ValueError("PostFinance Checkout credentials are not fully configured in the environment.")

    ```

---

## 1.3: Database Model Updates

**Objective**: Modify the existing database schema to support PostFinance transaction data and states.

**Action Items**:

1.  **Create a New Migration File**:
    *   Use `flask db migrate -m "Add PostFinance payment integration fields"` to generate a new migration script.

2.  **Modify `app/models.py`**:
    *   Update the `LessonPurchase` and `CoursePurchase` models.
    *   Create a new `PaymentTransaction` model for detailed logging.

    ```python
    # app/models.py

    # ... imports ...
    from sqlalchemy import BigInteger

    # ... (existing models) ...

    class LessonPurchase(db.Model):
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
        lesson_id: Mapped[int] = mapped_column(Integer, ForeignKey('lesson.id', ondelete='CASCADE'), nullable=False)
        price_paid: Mapped[float] = mapped_column(db.Float, nullable=False)
        purchased_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
        # Rename stripe_payment_intent_id and add state tracking
        postfinance_transaction_id: Mapped[int] = mapped_column(BigInteger, nullable=True, index=True)
        transaction_state: Mapped[str] = mapped_column(String(50), nullable=True)

        # Relationships
        user: Mapped['User'] = relationship('User', backref='lesson_purchases')
        lesson: Mapped['Lesson'] = relationship('Lesson', backref=db.backref('purchases', cascade='all, delete-orphan'))

        __table_args__ = (db.UniqueConstraint('user_id', 'lesson_id'),)

        def __repr__(self):
            return f'<LessonPurchase user:{self.user_id} lesson:{self.lesson_id} price:{self.price_paid}>'


    class CoursePurchase(db.Model):
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=False)
        course_id: Mapped[int] = mapped_column(Integer, ForeignKey('course.id', ondelete='CASCADE'), nullable=False)
        price_paid: Mapped[float] = mapped_column(db.Float, nullable=False)
        purchased_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
        # Rename stripe_payment_intent_id and add state tracking
        postfinance_transaction_id: Mapped[int] = mapped_column(BigInteger, nullable=True, index=True)
        transaction_state: Mapped[str] = mapped_column(String(50), nullable=True)

        course: Mapped['Course'] = relationship('Course', backref=db.backref('purchases', cascade='all, delete-orphan'))

        __table_args__ = (db.UniqueConstraint('user_id', 'course_id'),)

        def __repr__(self):
            return f'<CoursePurchase user:{self.user_id} course:{self.course_id} price:{self.price_paid}>'


    class PaymentTransaction(db.Model):
        id: Mapped[int] = mapped_column(Integer, primary_key=True)
        # Use BigInteger for the transaction_id as per API documentation
        transaction_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
        user_id: Mapped[int] = mapped_column(Integer, ForeignKey('user.id'), nullable=True)
        item_type: Mapped[str] = mapped_column(String(20), nullable=False)  # 'lesson' or 'course'
        item_id: Mapped[int] = mapped_column(Integer, nullable=False)
        amount: Mapped[float] = mapped_column(db.Float, nullable=False)
        currency: Mapped[str] = mapped_column(String(3), default='CHF')
        state: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
        created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
        updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
        # Use JSONB for efficient querying of webhook data
        webhook_data: Mapped[dict] = mapped_column(JSON, nullable=True)
        metadata: Mapped[dict] = mapped_column(JSON, nullable=True)

        def __repr__(self):
            return f'<PaymentTransaction {self.transaction_id} - {self.state}>'

    ```

3.  **Update the Migration Script**:
    *   Edit the generated migration file in `migrations/versions/`.
    *   Use `op.rename_table` and `op.add_column` to reflect the changes from the old `stripe_payment_intent_id` to the new fields.
    *   Add `op.create_table` for the `payment_transaction` model.
    *   Ensure you create indexes for performance.

4.  **Apply the Migration**:
    *   Run `flask db upgrade` to apply the changes to the database.

---

## 1.4: SDK Integration Setup

**Objective**: Install the PostFinance Checkout SDK and create a dedicated service class for all payment operations.

**Action Items**:

1.  **Install the SDK**:
    *   Add `postfinancecheckout` to your `requirements.txt` file.
    *   Run `pip install -r requirements.txt`.

    ```text
    # requirements.txt
    # ... other packages
    postfinancecheckout
    ```

2.  **Create `app/services/payment_service.py`**:
    *   Create a new file to house the `PostFinanceService` class. This encapsulates all interaction with the PostFinance API.

    ```python
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
            
            if not all([user_id, api_secret]):
                raise ValueError("PostFinance User ID or API Secret is not configured.")

            return Configuration(
                user_id=int(user_id),
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

    ```

3.  **Update `app/__init__.py`**:
    *   Ensure the application context is available for the service. No changes are likely needed here if using `current_app`, but it's good to verify.

4.  **Create Unit Tests**:
    *   Create a new test file `tests/test_payment_service.py`.
    *   Add initial tests to verify:
        *   The service initializes correctly with proper configuration.
        *   The service raises a `ValueError` if configuration is missing.
        *   (Optional/Advanced) Mock the API and test that the `get_transaction_status` method handles both success and `ApiException` correctly.

### **Key Technical Considerations from Documentation**:

*   **Optimistic Locking**: The SDK handles the `version` property automatically. When you fetch an object, modify it, and send it back, the SDK includes the version. If a `409 Conflict` occurs, the SDK will raise an `ApiException`. Your higher-level application logic (in Phase 2) will need to catch this, re-fetch, and retry.
*   **Timestamp Tolerance**: The server running the Flask app must have its clock synchronized (e.g., via NTP) to avoid authentication errors, as the API allows a maximum of 600 seconds of clock skew.
*   **Error Handling**: The `ApiException` from the SDK contains a `body` attribute with the detailed JSON error message from the API. The service class should log this for debugging.
*   **IDs as `Long`**: The use of `BigInteger` in the database models correctly reflects the 64-bit integer type used for IDs in the PostFinance API.

---

### **Expected Deliverables for Phase 1**:

*   A configured PostFinance Checkout account with API credentials stored securely in the application's environment.
*   An updated database schema with the necessary tables and fields to support payment processing, confirmed via a successful `flask db upgrade`.
*   A foundational `PostFinanceService` class that is initialized and ready for building out payment logic in Phase 2.
*   Basic unit tests confirming the correct initialization and configuration of the payment service.
