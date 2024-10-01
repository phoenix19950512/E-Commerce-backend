from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import func
from sqlalchemy import any_, text
from typing import List
from app.models.user import User
from app.routers.auth import get_current_user
from app.database import get_db
from app.models.shipment import Shipment
from app.models.supplier import Supplier
from app.models.internal_product import Internal_Product
from app.models.team_member import Team_member
from app.schemas.shipment import ShipmentCreate, ShipmentRead, ShipmentUpdate
import logging
import json
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

router = APIRouter()

@router.post("/", response_model=ShipmentRead)
async def create_shipment(shipment: ShipmentCreate, user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    if user.role != 4 and user.role != 2:
        raise HTTPException(status_code=401, detail="Authentication error")
    
    if user.role == 2:
        result = await db.execute(select(Team_member).where(Team_member.user == user.id))
        db_team = result.scalars().first()
        user_id = db_team.admin
    else:
        user_id = user.id
    db_shipment = Shipment(**shipment.dict())
    db.add(db_shipment)
    await db.commit()
    await db.refresh(db_shipment)
    return db_shipment

@router.get('/count')
async def get_shipments_count(db: AsyncSession = Depends(get_db)):
    result = await db.execute(func.count(Shipment.id))
    count = result.scalar()
    return count

@router.get("/new_count")
async def get_new_shipments(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shipment).where(Shipment.status == "New"))
    db_new_shipments = result.scalars().all()
    return len(db_new_shipments)

@router.get("/agent")
async def get_shipments_agent(
    agent: str,
    db:AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Shipment).where(Shipment.agent == agent))
    db_shipments = result.scalars().all()
    if db_shipments is None:
        raise HTTPException(status_code=404, detail="shipment not found")
    return db_shipments

@router.get("/", response_model=List[ShipmentRead])
async def get_shipments(
    page: int = Query(1, ge=1, description="Page number"),
    items_per_page: int = Query(50, ge=1, le=100, description="Number of items per page"),
    db: AsyncSession = Depends(get_db)
):
    
    offset = (page - 1) * items_per_page
    result = await db.execute(select(Shipment).offset(offset).limit(items_per_page))
    db_shipments = result.scalars().all()
    if db_shipments is None:
        raise HTTPException(status_code=404, detail="shipment not found")
    return db_shipments

@router.get("/new", response_model=List[ShipmentRead])
async def get_new_shipments(
    db: AsyncSession = Depends(get_db)
):
    result = await db.execute(select(Shipment).where(Shipment.status == "New"))
    db_new_shipments = result.scalars().all()
    if db_new_shipments is None:
        raise HTTPException(status_code=400, detail="New shipment not found")
    return db_new_shipments

@router.get("/extra") 
async def get_extra_info(
    db: AsyncSession = Depends(get_db)
):
    query = text("""
        SELECT id, title From shipments
    """)
    
    result = await db.execute(query)
    extra_info = result.fetchall()
    
    extra_info_list = [{"id": row[0], "title": row[1]} for row in extra_info]
    return extra_info_list

@router.get("/move", response_model=ShipmentRead)
async def move_products(shipment_id1: int, shipment_id2: int, ean: str, ship_id: int, db:AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shipment).where(Shipment.id == shipment_id1))
    shipment_1 = result.scalars().first()

    ean_list = shipment_1.ean

    for i in range(len(ean_list)):
        if ean_list[i] == ean and shipment_1.ship_id[i] == ship_id:
            index = i
            break
    quantity = shipment_1.quantity[index]
    item_per_box = shipment_1.item_per_box[index]
    pdf_sent = shipment_1.pdf_sent[index]
    pay_url = shipment_1.pay_url[index]
    tracking = shipment_1.tracking[index]
    arrive_agent = shipment_1.arrive_agent[index]
    wechat_group = shipment_1.wechat_group[index]
    pp = shipment_1.pp[index]
    each_status = shipment_1.each_status[index]
    box_number = shipment_1.box_number[index]
    document = shipment_1.document[index]
    date_added = shipment_1.date_added[index]
    date_agent = shipment_1.date_agent[index]

    before = shipment_1.before[index]
    if before:
        before = json.loads(before)
        before = before + [f"{ship_id}_{shipment_1.title}"]
        before = str(before)
    else:
        before = str([f"{ship_id}_{shipment_1.title}"])
    user = shipment_1.user[index]

    shipment_1.ean = shipment_1.ean[:index] + shipment_1.ean[index+1:]
    shipment_1.quantity = shipment_1.quantity[:index] + shipment_1.quantity[index+1:]
    shipment_1.item_per_box = shipment_1.item_per_box[:index] + shipment_1.item_per_box[index+1:]
    shipment_1.pdf_sent = shipment_1.pdf_sent[:index] + shipment_1.pdf_sent[index+1:]
    shipment_1.pay_url = shipment_1.pay_url[:index] + shipment_1.pay_url[index+1:]
    shipment_1.tracking = shipment_1.tracking[:index] + shipment_1.tracking[index+1:]
    shipment_1.arrive_agent = shipment_1.arrive_agent[:index] + shipment_1.arrive_agent[index+1:]
    shipment_1.wechat_group = shipment_1.wechat_group[:index] + shipment_1.wechat_group[index+1:]
    shipment_1.pp = shipment_1.pp[:index] + shipment_1.pp[index+1:]
    shipment_1.each_status = shipment_1.each_status[:index] + shipment_1.each_status[index+1:]
    shipment_1.box_number = shipment_1.box_number[:index] + shipment_1.box_number[index+1:]
    shipment_1.document = shipment_1.document[:index] + shipment_1.document[index+1:]
    shipment_1.date_added = shipment_1.date_added[:index] + shipment_1.date_added[index+1:]
    shipment_1.date_agent = shipment_1.date_agent[:index] + shipment_1.date_agent[index+1:]
    shipment_1.before = shipment_1.before[:index] + shipment_1.before[index+1:]
    shipment_1.user = shipment_1.user[:index] + shipment_1.user[index+1:]

    
    # await db.refresh(shipment_1)

    result = await db.execute(select(Shipment).where(Shipment.id == shipment_id2))
    shipment_2 = result.scalars().first()

    shipment_2.ean = shipment_2.ean + [ean]
    shipment_2.quantity = shipment_2.quantity + [quantity]
    shipment_2.item_per_box = shipment_2.item_per_box + [item_per_box]
    shipment_2.pdf_sent = shipment_2.pdf_sent + [pdf_sent]
    shipment_2.pay_url = shipment_2.pay_url + [pay_url]
    shipment_2.tracking = shipment_2.tracking + [tracking]
    shipment_2.arrive_agent = shipment_2.arrive_agent + [arrive_agent]
    shipment_2.wechat_group = shipment_2.wechat_group + [wechat_group]
    shipment_2.pp = shipment_2.pp + [""]
    shipment_2.each_status = shipment_2.each_status + [each_status]
    shipment_2.box_number = shipment_2.box_number + [box_number]
    shipment_2.document = shipment_2.document + [document]
    shipment_2.date_added = shipment_2.date_added + [date_added]
    shipment_2.date_agent = shipment_2.date_agent + [date_agent]
    shipment_2.before = shipment_2.before + [before]
    shipment_2.user = shipment_2.user + [user]
    shipment_2.ship_id = shipment_2.ship_id + [shipment_2.cnt + 1]
    shipment_2.cnt = shipment_2.cnt + 1

    await db.commit()
    await db.refresh(shipment_2)

    logging.info(f"@@@@@After update: {shipment_2}")

    return shipment_2

@router.get("/product_info")
async def get_info(ean: str, item_per_box: int, db:AsyncSession = Depends(get_db)):
    query = select(Shipment).where(ean == any_(Shipment.ean))
    result = await db.execute(query)

    shipments = result.scalars().all()

    imports_data = []

    for shipment in shipments:
        if shipment.status == "arrived":
            continue
        ean_list = shipment.ean
        quantity_list = shipment.quantity
        title = shipment.title
        index = ean_list.index(ean)
        quantity = quantity_list[index]

        imports_data.append({
            "title": title,
            "quantity": quantity
        })

    result = await db.execute(select(Internal_Product).where(Internal_Product.ean == ean))
    product = result.scalars().first()
 
    dimension = product.dimensions
    if dimension:
        numbers = dimension.split('*')
        # Ensure all parts are valid before conversion
        if len(numbers) == 3 and all(num.strip() for num in numbers):
            w, h, d = map(float, numbers)
        else:
            w, h, d = (0.0, 0.0, 0.0)
    else:
        w, h, d = (0.0, 0.0, 0.0)
    if item_per_box:
        volumetric_weight = w * h * d / 5000 / item_per_box
        if w == 0.0 or h == 0.0 or d == 0.0:
            type = -1
        elif product.weight < 0.35 and volumetric_weight < 0.35:
            type = 1
        elif product.battery:
            type = 2
        else:
            type = 3

        return {
            "type": type,
            "imports_data": imports_data
        }
    else:
        return {
            "type": 1,
            "imports_data": imports_data
        }

@router.get("/{shipment_id}")
async def get_shipment(shipment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shipment).where(Shipment.id == shipment_id))
    db_shipment = result.scalars().first()
    if db_shipment is None:
        raise HTTPException(status_code=404, detail="shipment not found")
    return db_shipment

@router.put("/{shipment_id}", response_model=ShipmentRead)
async def update_shipment(shipment_id: int, shipment: ShipmentUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shipment).filter(Shipment.id == shipment_id))
    db_shipment = result.scalars().first()
    if db_shipment is None:
        raise HTTPException(status_code=404, detail="shipment not found")
    update_data = shipment.dict(exclude_unset=True)  # Only update fields that are set
    for key, value in update_data.items():
        setattr(db_shipment, key, value) if value is not None else None
    await db.commit()
    await db.refresh(db_shipment)
    return db_shipment

@router.delete("/{shipment_id}", response_model=ShipmentRead)
async def delete_shipment(shipment_id: int, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Shipment).filter(Shipment.id == shipment_id))
    shipment = result.scalars().first()
    if shipment is None:
        raise HTTPException(status_code=404, detail="shipment not found")
    await db.delete(shipment)
    await db.commit()
    return shipment
