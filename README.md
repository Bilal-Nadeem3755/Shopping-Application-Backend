# Shopping Application Backend

A RESTful e-commerce backend built with Python and FastAPI. The application provides APIs for authentication, product management, shopping carts, orders, payments, coupons, reviews, refunds, and returns.

## Features

### Authentication & Security

- User registration and login
- JWT access and refresh tokens
- Argon2 password hashing
- Email verification
- Resend email verification
- Forgot password functionality
- Password reset
- Protected API routes
- Role-based admin access
- Logout functionality

### Product Management

- Get all products
- Get a single product
- Create products
- Update products
- Delete products
- Product stock management
- Product images
- Product ratings and review counts

### Shopping Cart

- Add products to cart
- View cart
- Update product quantity
- Remove products from cart
- Clear cart

### Orders

- Create orders
- View personal orders
- View individual order details
- Admin order management
- Order status workflow
- Stock validation
- Automatic stock updates
- Multiple payment methods

### Payments

- Stripe Checkout integration
- Card payment processing
- Stripe webhook handling
- Payment confirmation
- Payment intent tracking
- Refund processing

### Coupons

- Admin coupon creation
- Percentage discounts
- Fixed discounts
- Coupon expiry dates
- Usage limits
- One-time coupon usage per user
- Coupon validation

### Reviews

- Customers can review purchased products
- 1–5 star ratings
- Review comments
- Admin review approval
- Admin review rejection
- Review editing while pending
- Admin review deletion
- Automatic product rating calculation

### Returns

- Customers can request product returns
- Seven-day return window
- Admin approval/rejection
- Refund initiation through Stripe
- Return status tracking

### Email Notifications

The backend sends email notifications for important events such as:

- Email verification
- Password reset
- Successful payments
- Refund processing

## Tech Stack

- Python
- FastAPI
- MongoDB
- PyMongo
- JWT
- Argon2
- Stripe
- Pydantic
- SMTP
- Uvicorn

## Project Structure

```text
Backend/
├── app/
│   ├── config/
│   │   └── db.py
│   │
│   ├── controllers/
│   │
│   ├── middlewares/
│   │   ├── admin.py
│   │   └── auth.py
│   │
│   ├── models/
│   │
│   ├── routes/
│   │   ├── admin.py
│   │   ├── auth.py
│   │   ├── cart.py
│   │   ├── checkout.py
│   │   ├── coupon.py
│   │   ├── orders.py
│   │   ├── products.py
│   │   ├── refund.py
│   │   ├── returns.py
│   │   ├── reviews.py
│   │   ├── stripe_payment.py
│   │   └── user.py
│   │
│   ├── schemas/
│   │
│   ├── services/
│   │   ├── email_service.py
│   │   └── order_service.py
│   │
│   ├── utils/
│   │   ├── auth.py
│   │   ├── jwt.py
│   │   ├── order_status.py
│   │   └── security.py
│   │
│   ├── webhooks/
│   │   └── stripe_webhook.py
│   │
│   └── main.py
│
├── .gitignore
└── README.md