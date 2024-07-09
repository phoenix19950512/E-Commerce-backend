from pydantic import BaseModel
from typing import Optional, List
from decimal import Decimal

class ProductBase(BaseModel):

    product_name: Optional[str] = None
    model_name: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[Decimal] = None
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

    # admin_user: Optional[str] = None
    # part_number_key: Optional[str] = None
    # brand_name: Optional[str] = None
    # buy_button_rank: Optional[int] = None
    # category_id: Optional[int] = None
    # brand: Optional[str] = None
    # name: Optional[str] = None
    # part_number: Optional[str] = None
    # sale_price: Optional[Decimal] = None
    # currency: Optional[str] = None
    # description: Optional[str] = None
    # url: Optional[str] = None
    # warranty: Optional[int] = None
    # general_stock: Optional[int] = None
    # weight: Optional[Decimal] = None
    # status: Optional[int] = None
    # recommended_price: Optional[Decimal] = None
    # images: Optional[str] = None
    # attachments: Optional[str] = None
    # vat_id: Optional[int] = None
    # family: Optional[str] = None
    # reversible_vat_charging: Optional[bool] = None
    # min_sale_price: Optional[Decimal] = None
    # max_sale_price: Optional[Decimal] = None
    # offer_details: Optional[str] = None
    # availability: Optional[str] = None
    # stock: Optional[int] = None
    # handling_time: Optional[str] = None
    # ean: Optional[str] = None
    # commission: Optional[Decimal] = None
    # validation_status: Optional[str] = None
    # translation_validation_status: Optional[str] = None
    # offer_validation_status: Optional[str] = None
    # auto_translated: Optional[int] = None
    # ownership: Optional[bool] = None
    # best_offer_sale_price: Optional[Decimal] = None
    # best_offer_recommended_price: Optional[Decimal] = None
    # number_of_offers: Optional[int] = None
    # genius_eligibility: Optional[int] = None
    # recyclewarranties: Optional[int] = None

class ProductCreate(ProductBase):
    pass

class ProductRead(ProductBase):
    id: int

    class Config:
        orm_mode = True

class ProductUpdate(ProductBase):
    pass
