# from fastapi import APIRouter, Depends, HTTPException
# from bson import ObjectId

# from app.middlewares.auth import get_current_user
# from app.config.db import db

# router = APIRouter(
#     prefix="/cart",
#     tags=["Cart"]
# )

# # add to cart

# @router.post("/add/{product_id}")
# def add_to_cart(product_id: str, current_user=Depends(get_current_user)):

#     user_id = str(current_user["_id"])

#     product = db["products"].find_one({"_id": ObjectId(product_id)})
#     if not product:
#         raise HTTPException(status_code=404, detail="Product not found")

#     cart_item = db["cart"].find_one({
#         "user_id": user_id,
#         "product_id": product_id
#     })

#     if cart_item:
#         db["cart"].update_one(
#             {"_id": cart_item["_id"]},
#             {"$inc": {"quantity": 1}}
#         )
#     else:
#         db["cart"].insert_one({
#             "user_id": user_id,
#             "product_id": product_id,
#             "quantity": 1
#         })

#     return {"message": "Product added to cart"}

# #get user cart

# @router.get("/")
# def get_cart(current_user=Depends(get_current_user)):

#     user_id = str(current_user["_id"])

#     cart_items = list(db["cart"].find({"user_id": user_id}))

#     response = []

#     for item in cart_items:
#         product = db["products"].find_one(
#             {"_id": ObjectId(item["product_id"])}
#         )

#         if product:
#             response.append({
#                 "cart_id": str(item["_id"]),
#                 "product_id": item["product_id"],
#                 "name": product["name"],
#                 "price": product["price"],
#                 "quantity": item["quantity"]
#             })

#     return response

# #remove item from cart

# @router.delete("/remove/{product_id}")
# def remove_from_cart(product_id: str, current_user=Depends(get_current_user)):

#     user_id = str(current_user["_id"])

#     result = db["cart"].delete_one({
#         "user_id": user_id,
#         "product_id": product_id
#     })

#     if result.deleted_count == 0:
#         raise HTTPException(status_code=404, detail="Item not found in cart")

#     return {"message": "Item removed from cart"}

# #update quantity

# @router.put("/update/{product_id}")
# def update_quantity(
#     product_id: str,
#     quantity: int,
#     current_user=Depends(get_current_user)
# ):

#     if quantity < 1:
#         raise HTTPException(status_code=400, detail="Quantity must be at least 1")

#     user_id = str(current_user["_id"])

#     result = db["cart"].update_one(
#         {
#             "user_id": user_id,
#             "product_id": product_id
#         },
#         {"$set": {"quantity": quantity}}
#     )

#     if result.matched_count == 0:
#         raise HTTPException(status_code=404, detail="Item not found in cart")

#     return {"message": "Cart updated"}

from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from app.middlewares.auth import get_current_user
from app.config.db import db

router = APIRouter(
    prefix="/cart",
    tags=["Cart"]
)

# -----------------------
# Add to cart / increment
# -----------------------
@router.post("/add/{product_id}")
def add_to_cart(product_id: str, current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])

    product = db["products"].find_one({"_id": ObjectId(product_id)})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    cart_item = db["cart"].find_one({
        "user_id": user_id,
        "product_id": product_id
    })

    if cart_item:
        # Increment quantity
        db["cart"].update_one(
            {"_id": cart_item["_id"]},
            {"$inc": {"quantity": 1}}
        )
    else:
        # First time add
        db["cart"].insert_one({
            "user_id": user_id,
            "product_id": product_id,
            "quantity": 1
        })

    return {"message": "Product added to cart"}


# -----------------------
# Get user cart
# -----------------------
@router.get("/")
def get_cart(current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])
    cart_items = list(db["cart"].find({"user_id": user_id}))
    response = []

    for item in cart_items:
        product = db["products"].find_one({"_id": ObjectId(item["product_id"])})
        if product:
            response.append({
                "cart_id": str(item["_id"]),
                "product_id": item["product_id"],
                "name": product["name"],
                "price": product["price"],
                "quantity": item["quantity"]
            })

    return response


# -----------------------
# Remove from cart
# -----------------------
@router.delete("/remove/{product_id}")
def remove_from_cart(product_id: str, current_user=Depends(get_current_user)):
    user_id = str(current_user["_id"])

    result = db["cart"].delete_one({
        "user_id": user_id,
        "product_id": product_id
    })

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found in cart")

    return {"message": "Item removed from cart"}


# -----------------------
# Update quantity
# -----------------------
@router.put("/update/{product_id}")
def update_quantity(
    product_id: str,
    quantity: int,
    current_user=Depends(get_current_user)
):
    user_id = str(current_user["_id"])

    if quantity < 1:
        # If quantity zero, remove item
        result = db["cart"].delete_one({
            "user_id": user_id,
            "product_id": product_id
        })
        if result.deleted_count == 0:
            raise HTTPException(status_code=404, detail="Item not found in cart")
        return {"message": "Item removed from cart"}

    # Otherwise, update quantity
    result = db["cart"].update_one(
        {"user_id": user_id, "product_id": product_id},
        {"$set": {"quantity": quantity}}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found in cart")

    return {"message": "Cart updated successfully"}