from fastapi import APIRouter, Depends, HTTPException, Query
from bson import ObjectId

from app.config.db import db
from app.schemas.product_schema import (
    ProductCreateSchema,
    ProductUpdateSchema,
)
from app.middlewares.admin import require_admin

router = APIRouter(
    prefix="/products",
    tags=["Products"],
)

products_collection = db["products"]


# ------------------------
# USER ROUTES (PUBLIC)
# ------------------------

@router.get("/")
def list_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
):
    cursor = (
        products_collection
        .find()
        .skip(skip)
        .limit(limit)
    )

    products = []

    for product in cursor:
        product["_id"] = str(product["_id"])
        products.append(product)

    return products


@router.get("/{product_id}")
def get_product(product_id: str):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid product ID",
        )

    product = products_collection.find_one(
        {"_id": ObjectId(product_id)}
    )

    if not product:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

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
        "product_id": str(result.inserted_id),
    }


@router.put("/{product_id}", dependencies=[Depends(require_admin)])
def update_product(
    product_id: str,
    data: ProductUpdateSchema,
):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid product ID",
        )

    result = products_collection.update_one(
        {"_id": ObjectId(product_id)},
        {"$set": data.dict(exclude_none=True)},
    )

    if result.matched_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return {"message": "Product updated successfully"}


@router.delete(
    "/{product_id}",
    dependencies=[Depends(require_admin)],
)
def delete_product(product_id: str):
    if not ObjectId.is_valid(product_id):
        raise HTTPException(
            status_code=400,
            detail="Invalid product ID",
        )

    result = products_collection.delete_one(
        {"_id": ObjectId(product_id)}
    )

    if result.deleted_count == 0:
        raise HTTPException(
            status_code=404,
            detail="Product not found",
        )

    return {"message": "Product deleted successfully"}