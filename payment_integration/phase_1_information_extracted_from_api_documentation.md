### **Information for Phase 1: Foundation Setup and Configuration**

Here is the detailed information extracted from "complete pfp documentation.txt" to complement each task in Phase 1 of your "initial_payment_integration_plan.md".

---

### **For Task 1.1: Account Setup and Credentials**

* **Account & Space Creation**: To get started, you will need to create an "Account" and within that, a "Space". Nearly every API call requires a `spaceId` as a query parameter. Think of a Space as a self-contained environment for your transactions.
* **API Credentials**:
    * **`user_id` (`x-mac-userid`)**: This is the ID of an "Application User". You can create one in your account by navigating to **Account > Users > Application Users**. The ID will be visible in the user list after creation.
    * **`api_secret` (`application_user_key`)**: This is a 32-byte, Base64 encoded authentication key. It is displayed **only once** when you create a new Application User. You must save this key securely, as it cannot be retrieved later.
* **Programmatic Webhook Setup**: While you can configure webhook endpoints in the dashboard, the documentation provides API endpoints to do this programmatically, which is useful for automating your environment setup:
    * **Webhook URL Service (`POST /api/webhook-url/create`)**: Use this to register your endpoint URL (`/webhook/postfinance`).
    * **Webhook Listener Service (`POST /api/webhook-listener/create`)**: Use this to subscribe to specific events for an entity (e.g., when a `Transaction` state changes).

---

### **For Task 1.2: Environment Configuration**

* **Authentication Headers**: Every single request to the API must include four custom HTTP headers:
    * `x-mac-version`: Always set to `1`.
    * `x-mac-userid`: Your Application User ID.
    * `x-mac-timestamp`: The current Unix timestamp in seconds.
    * `x-mac-value`: The Base64 encoded HMAC-SHA512 signature.
* **MAC Authentication (Signature Calculation)**: The `x-mac-value` is the most critical part. It is calculated by:
    1.  Creating a single string by concatenating the following values, separated by a `|` character:
        * The version (`1`)
        * Your user ID
        * The timestamp
        * The uppercase HTTP Method (`GET`, `POST`, etc.)
        * The full request path including the query string (e.g., `/api/transaction/read?spaceId=12&id=1`)
    2.  Creating an HMAC-SHA512 hash of this string using your `api_secret` as the key.
    3.  Base64 encoding the resulting binary hash.
* **Code Examples**: Section 2.5 of the documentation provides ready-to-use code examples for generating this signature in **PHP, Java, and Python**, which will be invaluable for building and testing your `PostFinanceService`.
* **Timestamp Tolerance**: The server allows a maximum difference of **600 seconds** between its time and the `x-mac-timestamp` you send. Ensure your server's clock is accurately synchronized with an NTP server.

---

### **For Task 1.3: Database Model Updates**

* **Data Type for IDs**: The documentation's "Type System" (Section 1.1) specifies that IDs are of type `Long`, which is a 64-bit integer. Your `postfinance_transaction_id` column should therefore be a `BIGINT` or equivalent in your database to prevent overflow.
* **`transaction_state` Enum**: The documentation defines a comprehensive list of states for a transaction in the `Transaction State` model (Section 4.11.121). Your database enum should include all of them:
    * `CREATE`
    * `PENDING`
    * `CONFIRMED`
    * `PROCESSING`
    * `FAILED`
    * `AUTHORIZED`
    * `VOIDED`
    * `COMPLETED`
    * `FULFILL`
    * `DECLINE`
* **Metadata Limitations**: The `Transaction` object has a `metaData` property which is ideal for storing your `lesson_id` and `course_id`. However, it has specific limits (Section 1.6):
    * A maximum of **25 key/value pairs**.
    * Keys cannot be longer than **40 characters**.
    * Values cannot be longer than **512 characters**.
    * Keys must match the regex: `[a-zA-Z]{1}[a-zA-Z0-9_]{0,39}`.

---

### **For Task 1.4: SDK Integration Setup**

* **Critical - Optimistic Locking**: Section 1.2, "Object Versioning / Locking," describes a mandatory optimistic locking mechanism that you must implement.
    * Most objects returned by the API (including `Transaction`) have a `version` property (an integer).
    * When you perform an **update** on an object, you **must** include the `version` number from the object you last fetched.
    * If the version has changed on the server in the meantime, the API will reject your update with a **`409 Conflict`** status code.
    * **Your `PostFinanceService` must handle this**. The recommended logic is to catch the `409` error, re-fetch the latest version of the object, re-apply your changes to the new version, and then retry the update.
* **Detailed Error Models**: The documentation provides the exact JSON structure for `Client Error` and `Server Error` responses (Section 4.6). This allows you to build specific error handling in your `PostFinanceService` to parse the error `id`, `message`, and `type` for better logging and user feedback.
* **Logging**: You can add an `x-wallee-logtoken` header to your requests with a unique ID per request. This token will be included in the service's logs, which can help their support team trace a specific request if you encounter issues.
* **Swagger / OpenAPI Specification**: Section 1.4 mentions that a machine-readable API definition is available in **Swagger** format. This is a highly valuable resource for exploring the API, understanding all available endpoints and models, and potentially generating a client library stub.
* **Available SDKs**: The documentation states that official SDKs for several programming languages are available on their GitHub Repository, which could simplify the integration process.