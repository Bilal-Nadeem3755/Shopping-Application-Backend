from fastapi import APIRouter, Depends, HTTPException
from bson.objectid import ObjectId
from datetime import datetime
from app.schemas.review_schema import ReviewCreate
from app.config.db import db
from app.middlewares.auth import get_current_user
from app.middlewares.admin import get_admin_user

router = APIRouter(prefix="/reviews", tags=["Reviews"])


# ===============================
# ADD REVIEW
# ===============================
@router.post("/")
def add_review(data: ReviewCreate, current_user=Depends(get_current_user)):

    user_id = str(current_user["_id"])
    product_id = data.product_id

    #  Check product exists
    product = db["products"].find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    #  Check user purchased AND delivered
    print("USER:", user_id)
    print("PRODUCT:", product_id)
    delivered_order = db["orders"].find_one(
        {
            "user_id": ObjectId(user_id),
            "status": "delivered",
            "items.product_id": ObjectId(product_id),
        }
    )
    print("ORDER FOUND:", delivered_order)

    if not delivered_order:
        raise HTTPException(
            status_code=403,
            detail="You can only review delivered products you purchased",
        )

    #  Prevent duplicate review
    existing_review = db["reviews"].find_one(
        {"user_id": user_id, "product_id": product_id}
    )

    if existing_review:
        raise HTTPException(status_code=400, detail="You already reviewed this product")

    review = {
        "product_id": product_id,
        "user_id": user_id,
        "rating": data.rating,
        "comment": data.comment,
        "status": "pending",
        "created_at": datetime.utcnow(),
    }

    db["reviews"].insert_one(review)

    return {
        "message": "Review submitted and waiting for admin approval",
        "status": "pending",
    }


# ===============================
# DELETE REVIEW (ADMIN)
# ===============================
@router.delete("/{review_id}")
def delete_review(review_id: str, admin=Depends(get_admin_user)):

    review = db["reviews"].find_one({"_id": ObjectId(review_id)})

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    product_id = review["product_id"]

    db["reviews"].delete_one({"_id": ObjectId(review_id)})

    update_product_rating(product_id)

    return {"message": "Review deleted by admin"}


# ===============================
# APPROVE REVIEW (ADMIN)
# ===============================
@router.put("/{review_id}/approve")
def approve_review(review_id: str, admin=Depends(get_admin_user)):

    review = db["reviews"].find_one({"_id": ObjectId(review_id)})

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review["status"] == "approved":
        raise HTTPException(status_code=400, detail="Review already approved")

    db["reviews"].update_one(
        {"_id": ObjectId(review_id)}, {"$set": {"status": "approved"}}
    )

    update_product_rating(review["product_id"])

    return {"message": "Review approved successfully"}


# ===============================
# REJECT REVIEW (ADMIN)
# ===============================
@router.put("/{review_id}/reject")
def reject_review(review_id: str, admin=Depends(get_admin_user)):

    review = db["reviews"].find_one({"_id": ObjectId(review_id)})

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review["status"] == "rejected":
        raise HTTPException(status_code=400, detail="Review already rejected")

    db["reviews"].update_one(
        {"_id": ObjectId(review_id)}, {"$set": {"status": "rejected"}}
    )

    update_product_rating(review["product_id"])

    return {"message": "Review rejected successfully"}


# ===============================
# GET PENDING REVIEWS (ADMIN)
# ===============================
@router.get("/pending")
def get_pending_reviews(admin=Depends(get_admin_user)):

    reviews = list(db["reviews"].find({"status": "pending"}))

    for r in reviews:
        r["_id"] = str(r["_id"])

    return reviews


# ===============================
# EDIT OWN PENDING REVIEW
# ===============================
@router.put("/{review_id}")
def edit_review(
    review_id: str, data: ReviewCreate, current_user=Depends(get_current_user)
):

    review = db["reviews"].find_one({"_id": ObjectId(review_id)})

    if not review:
        raise HTTPException(status_code=404, detail="Review not found")

    if review["user_id"] != str(current_user["_id"]):
        raise HTTPException(status_code=403, detail="Not authorized")

    if review["status"] != "pending":
        raise HTTPException(status_code=400, detail="Only pending review can be edited")

    db["reviews"].update_one(
        {"_id": ObjectId(review_id)},
        {
            "$set": {
                "rating": data.rating,
                "comment": data.comment,
                "created_at": datetime.utcnow(),
            }
        },
    )

    return {"message": "Review updated successfully (waiting for approval)"}


# ===============================
# HELPER FUNCTION
# ===============================
def update_product_rating(product_id: str):

    reviews = list(db["reviews"].find({"product_id": product_id, "status": "approved"}))

    if not reviews:
        db["products"].update_one(
            {"_id": ObjectId(product_id)},
            {"$set": {"average_rating": 0, "review_count": 0}},
        )
        return

    total_rating = sum(r["rating"] for r in reviews)
    avg_rating = total_rating / len(reviews)

    db["products"].update_one(
        {"_id": ObjectId(product_id)},
        {
            "$set": {
                "average_rating": round(avg_rating, 2),
                "review_count": len(reviews),
            }
        },
    )
