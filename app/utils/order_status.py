# app/utils/order_status.py

ALLOWED_TRANSITIONS = {
    "pending_payment": ["placed"],
    "placed": ["processing"],
    "processing": ["packed"],
    "packed": ["shipped"],
    "shipped": ["delivered"],
    "delivered": [],
    "refunded": []
}


def can_update_status(current_status: str, new_status: str) -> bool:

    if current_status not in ALLOWED_TRANSITIONS:
        return False

    return new_status in ALLOWED_TRANSITIONS[current_status]
