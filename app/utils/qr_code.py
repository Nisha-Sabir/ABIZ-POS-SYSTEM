from uuid import uuid4


def generate_product_qr_code() -> str:
    return f"ABIZ-PROD-{uuid4().hex[:12].upper()}"
