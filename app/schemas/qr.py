from pydantic import BaseModel, ConfigDict


class QRCodeResponse(BaseModel):
    product_id: int
    product_name: str
    qr_code: str

    model_config = ConfigDict(from_attributes=True)
