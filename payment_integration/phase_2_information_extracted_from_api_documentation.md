Based on the provided documentation, here is the information relevant to **Phase 2: Core Payment Processing Implementation** of the initial payment integration plan.

### 2.1 Payment Service Layer

#### **Transaction Creation (`create_transaction`)**
[cite_start]The service for creating a transaction is available at `POST /api/transaction/create`[cite: 1410].

* [cite_start]**Endpoint**: `POST /api/transaction/create`[cite: 1410].
* [cite_start]**Query Parameters**: Requires `spaceId` of type `Long`[cite: 1410].
* [cite_start]**Message Body**: The request body should contain the `Transaction Create` object[cite: 1410].
* [cite_start]**Success Response**: On success (HTTP 200), it returns a `Transaction` object[cite: 1411].
* **Error Responses**:
    * [cite_start]`442 Client Error`: Indicates a client-side error, preventing the request from being processed[cite: 1412].
    * [cite_start]`542 Server Error`: Indicates an unexpected server condition prevented the request's fulfillment[cite: 1413].

#### **Payment Page URL Generation (`generate_payment_page_url`)**
[cite_start]This functionality creates the URL for redirecting the user to the payment page[cite: 1370].

* [cite_start]**Endpoint**: `GET /api/transaction-payment-page/payment-page-url`[cite: 1370].
* **Query Parameters**:
    * [cite_start]`spaceId` (`Long`): The ID of the space[cite: 1371].
    * [cite_start]`id` (`Long`): The ID of the transaction for which the URL is being created[cite: 1371].
* [cite_start]**Success Response**: On success (HTTP 200), it returns the URL as a `String`[cite: 1372].
* **Error Responses**:
    * [cite_start]`409 Error`: Indicates a conflict with the current version of the data[cite: 1373].
    * [cite_start]`442 Error`: Client-side error[cite: 1374].
    * [cite_start]`542 Error`: Unexpected server error[cite: 1375].

#### **Transaction Status Checking (`GET /api/transaction/read`)**
[cite_start]This endpoint reads and returns a transaction entity by its ID[cite: 1451].

* [cite_start]**Endpoint**: `GET /api/transaction/read`[cite: 1451].
* **Query Parameters**:
    * [cite_start]`spaceId` (`Long`)[cite: 1452].
    * [cite_start]`id` (`Long`): The ID of the transaction to be returned[cite: 1452].
* [cite_start]**Success Response**: On success (HTTP 200), it returns the full `Transaction` object[cite: 1453].
* **Error Responses**:
    * [cite_start]`442 Error`: Client-side error[cite: 1454].
    * [cite_start]`542 Error`: Unexpected server error[cite: 1455].
* [cite_start]**Transaction State**: The current state of the transaction is available in the `state` field of the returned `Transaction` object[cite: 3576]. [cite_start]Possible states include `PENDING`, `CONFIRMED`, `PROCESSING`, `FAILED`, `AUTHORIZED`, `VOIDED`, `COMPLETED`, `FULFILL`, and `DECLINE`[cite: 3617].

#### **Refund Processing**
[cite_start]The documentation includes a `Refund Service` to create and execute refunds for a transaction[cite: 1075].

* [cite_start]**Endpoint**: `POST /api/refund/refund`[cite: 1075].
* [cite_start]**Query Parameters**: `spaceId` (`Long`)[cite: 1076].
* [cite_start]**Message Body**: Requires a `Refund Create` object[cite: 1076].
* [cite_start]**Success Response**: Returns a `Refund` object[cite: 1077].

#### **Error Handling Models**
The API returns two main types of errors:

* [cite_start]**Client Error**: Returned as a result of a bad user request or misconfiguration[cite: 2654].
    * [cite_start]`type`: Categorizes the error as `END_USER_ERROR`, `CONFIGURATION_ERROR`, or `DEVELOPER_ERROR`[cite: 2659, 2660].
    * [cite_start]`defaultMessage`: An error message in English[cite: 2656].
    * [cite_start]`id`: A unique identifier for the error[cite: 2657].
    * [cite_start]`message`: A translated error message in the client's language[cite: 2658].
* [cite_start]**Server Error**: Thrown when an unexpected issue occurs on the server side[cite: 2664]. [cite_start]It contains a `date`, unique `id`, and a descriptive `message`[cite: 2665, 2666, 2667].

#### **Alternative Integration Modes (Iframe and Lightbox)**
* [cite_start]**Iframe Integration**: An endpoint at `GET /api/transaction-iframe/javascript-url` creates the URL needed to embed the JavaScript for the iFrame checkout flow[cite: 1251]. [cite_start]It requires `spaceId` and the transaction `id` as parameters[cite: 1252].
* [cite_start]**Lightbox Integration**: An endpoint at `GET /api/transaction-lightbox/javascript-url` creates the URL for the JavaScript to handle the Lightbox checkout flow[cite: 1338]. [cite_start]It requires `spaceId` and the transaction `id` as parameters[cite: 1339].

### 2.3 Transaction Management

#### **Transaction Creation with Line Items**
[cite_start]When creating a transaction, the `Transaction Create` object includes a `lineItems` field[cite: 3560]. Each line item has the following relevant properties:
* [cite_start]**`name`**: The product name, with a character limit of 1 to 150[cite: 2748].
* [cite_start]**`quantity`**: The number of items purchased (a positive decimal)[cite: 2749].
* [cite_start]**`uniqueId`**: A unique identifier for the line item within the set, with a 200-character limit[cite: 2760].
* [cite_start]**`unitPriceIncludingTax`**: The calculated price per unit, including taxes (read-only virtual field)[cite: 2762].
* [cite_start]**`sku`**: The stock-keeping unit of the product, with a 200-character limit[cite: 2751].
* [cite_start]**`type`**: The type of line item, which can be `PRODUCT`, `DISCOUNT`, `SHIPPING`, `FEE`, or `TIP`[cite: 2755].

#### **Transaction Metadata (`metaData`)**
* [cite_start]The `Transaction` object has a `metaData` field, which allows for storing additional information[cite: 3563].
* [cite_start]This field functions as a key-value store[cite: 71].
* **Limitations**:
    * [cite_start]A maximum of 25 key-value pairs can be provided per object[cite: 72].
    * Keys are limited to 40 characters and can only contain alphabetic characters, numeric characters, and underscores. [cite_start]Keys cannot start with an underscore or a number[cite: 73, 74, 75]. [cite_start]The validation regex is `[a-zA-Z]{1}[a-zA-Z0-9_]{0,39}`[cite: 76].
    * [cite_start]Values are limited to 512 characters and can contain any printable UTF-8 characters[cite: 73, 77].

#### **Transaction Currency**
* [cite_start]The `currency` field in the `Transaction Create` object sets the transaction's currency[cite: 3539].
* [cite_start]It must be the three-letter code in ISO 4217 format[cite: 3539].

#### **Success and Failed URLs**
* [cite_start]The `Transaction` object contains fields for `successUrl` and `failedUrl`[cite: 3577, 3551].
* [cite_start]**`successUrl`**: The URL to which the customer is redirected after a successful payment authentication[cite: 3577].
* [cite_start]**`failedUrl`**: The URL to which the customer is redirected after a canceled or failed payment authentication[cite: 3551].

#### **Timeout Handling**
The `Transaction` object includes several fields for managing timeouts:
* [cite_start]**`authorizationTimeoutOn`**: The date and time when the transaction must be authorized, after which it will be canceled[cite: 3526].
* [cite_start]**`completionTimeoutOn`**: The date and time for when a transaction is automatically completed[cite: 3534].

### 2.4 Payment Flow Implementation

#### **Payment Initiation**
[cite_start]The payment flow is initiated by creating a transaction via `POST /api/transaction/create` with all necessary details, including line items, currency, and success/failure URLs[cite: 1410].

#### **Redirect to Payment Page**
[cite_start]After successfully creating a transaction, the application generates the payment page URL using the transaction ID with the `GET /api/transaction-payment-page/payment-page-url` endpoint and redirects the customer to this URL[cite: 1370].

#### **Handling Completion Redirects**
[cite_start]The `successUrl` and `failedUrl` properties provided during transaction creation are used to redirect the customer back to the merchant's site after the payment process is completed[cite: 3577, 3551].

#### **Payment Cancellation**
* [cite_start]If a transaction is not authorized by the `authorizationTimeoutOn` date, it will be canceled[cite: 3526].
* [cite_start]The `Transaction Void Service` can be used to explicitly cancel a transaction before it is completed[cite: 1489, 1495].
    * [cite_start]**`voidOnline`**: Forwards the void to the processor[cite: 1495].
    * [cite_start]**`voidOffline`**: Manually fixes the transaction state without notifying the processor[cite: 1489].