# app/utils/awb.py
import uuid

def generate_awb_number() -> str:
    return str(uuid.uuid4())
