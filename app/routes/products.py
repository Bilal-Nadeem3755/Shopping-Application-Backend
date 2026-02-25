from fastapi import APIRouter, Depends, HTTPException
from bson import ObjectId

from app.config.db import db
from app.schemas.product_schema import (
    ProductCreateSchema,
    ProductUpdateSchema
)
from app.middlewares.admin import require_admin

router = APIRouter(
    prefix="/products",
    tags=["Products"]
)

products_collection = db["products"]

# ------------------------
# USER ROUTES (PUBLIC)
# ------------------------

@router.get("/")
def list_products():
    products = []
    for product in products_collection.find():
        product["_id"] = str(product["_id"])
        products.append(product)

    return products


@router.get("/{product_id}")
def get_product(product_id: str):
    product = products_collection.find_one(
        {"_id": ObjectId(product_id)}
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    product["_id"] = str(product["_id"])
    return product


# ------------------------
# ADMIN ROUTES
# ------------------------

@router.post("/", dependencies=[Depends(require_admin)])
def create_product(data: ProductCreateSchema):
    result = products_collection.insert_one(data.dict())

    return {
        "message": "Product created successfully",
        "product_id": str(result.inserted_id)
    }


@router.put("/{product_id}", dependencies=[Depends(require_admin)])
def update_product(
    product_id: str,
    data: ProductUpdateSchema
):
    result = products_collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": data.dict(exclude_none=True)}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"message": "Product updated successfully"}


@router.delete("/{product_id}", dependencies=[Depends(require_admin)])
def delete_product(product_id: str):
    result = products_collection.delete_one(
        {"_id": ObjectId(product_id)}
    )

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"message": "Product deleted successfully"}
