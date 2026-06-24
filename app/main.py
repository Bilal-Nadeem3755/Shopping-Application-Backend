from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import (
    auth,
    user,
    admin,
    products,
    cart,
    checkout,
    orders,
    stripe_payment,
    refund,
    returns,
    coupon,
    reviews
)

from app.webhooks import stripe_webhook

app = FastAPI(title="Online Shop API")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ROUTERS
app.include_router(auth.router)
app.include_router(user.router)
app.include_router(admin.router)
app.include_router(products.router)
app.include_router(cart.router)
app.include_router(checkout.router)
app.include_router(orders.router)
app.include_router(stripe_payment.router)
app.include_router(stripe_webhook.router)
app.include_router(refund.router)
app.include_router(returns.router)
app.include_router(coupon.router)
app.include_router(reviews.router)

# TEST
@app.get("/")
async def test():
    return {"message": "working"}