from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal

class ProductBase(BaseModel):
    id: int
    product_name: Optional[str] = None
    model_name: Optional[str] = None
    price: Optional[Decimal] = None
    ean: str
    image_link: Optional[str] = None
    barcode_title: Optional[str] = None
    masterbox_title: Optional[str] = None
    link_address_1688: Optional[str] = None
    price_1688: Optional[Decimal] = None
    variation_name_1688: Optional[str] = None
    pcs_ctn: Optional[str] = None
    weight: Optional[Decimal] = None
    volumetric_weight: Optional[Decimal] = None
    dimensions: Optional[str] = None
    supplier_id: Optional[int] = None
    english_name: Optional[str] = None
    romanian_name: Optional[str] = None
    material_name_en: Optional[str] = None
    material_name_ro: Optional[str] = None
    hs_code: Optional[str] = None
    battery: Optional[bool] = None
    default_usage: Optional[str] = None
    production_time: Optional[Decimal] = None
    discontinued: Optional[bool] = None
    stock: Optional[int] = None
    internal_shipping_price: Optional[Decimal] = None
    market_places: Optional[List[str]] = None

class ProductCreate(ProductBase):
    pass

class ProductRead(ProductBase):
    id: int

    class Config:
        orm_mode = True

class ProductUpdate(ProductBase):
    pass
