from http import HTTPStatus
from typing import Annotated
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.database import get_asession
from src.database.models import User, InventoryItem
from src.api.schemas import (
    FilterItem,
    Message,
    ItemList,
    ItemPublic,
    ItemSchema,
    ItemUpdate,
)
from src.api.security import get_current_user

router = APIRouter()

T_Session = Annotated[AsyncSession, Depends(get_asession)]
CurrentUser = Annotated[User, Depends(get_current_user)]

router = APIRouter(prefix='/items', tags=['items'])


@router.post('/', response_model=ItemPublic)
async def create_item(
    item: ItemSchema,
    user: CurrentUser,
    session: T_Session,
):
    db_item: InventoryItem = InventoryItem(
        user_id=user.id,
        name=item.name,
        description=item.description,
        location= item.location,
        quantity=item.quantity,
        unit= item.unit,
        category=item.category,
    )
    session.add(db_item)
    await session.commit()
    await session.refresh(db_item)

    return db_item


@router.get('/', response_model=ItemList)
async def list_items(
    session: T_Session,
    user: CurrentUser,
    item_filter: Annotated[FilterItem, Query()],
):
    query = select(InventoryItem).where(InventoryItem.user_id == user.id)

    if item_filter.name:
        query = query.filter(
            InventoryItem.name.contains(item_filter.name))
    if item_filter.quantity:
        query = query.filter(
            InventoryItem.quantity.contains(item_filter.quantity))
    if item_filter.location:
        query = query.filter(
            InventoryItem.location.contains(item_filter.location))
    if item_filter.description:
        query = query.filter(
            InventoryItem.description.contains(item_filter.description))
    if item_filter.category:
        query = query.filter(
            InventoryItem.category.contains(item_filter.category))

    result = await session.scalars(
        query.offset(item_filter.offset).limit(item_filter.limit)
    )
    items = result.all()

    return {'items': items}


@router.patch('/{item_id}', response_model=ItemPublic)
async def patch_item(
    item_id: int, session: T_Session, user: CurrentUser, item: ItemUpdate
):
    db_item = await session.scalar(
        select(InventoryItem).where(InventoryItem.user_id == user.id, 
                                    InventoryItem.id == item_id)
    )

    if not db_item:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Item not found.'
        )

    for key, value in item.model_dump(exclude_unset=True).items():
        if key == 'unit':
            value = value.value
        setattr(db_item, key, value)
    await session.commit()
    await session.refresh(db_item)

    return db_item


@router.delete('/{item_id}', response_model=Message)
async def delete_item(item_id: int, session: T_Session, user: CurrentUser):
    item = await session.scalar(
        select(InventoryItem).where(InventoryItem.user_id == user.id, 
                                    InventoryItem.id == item_id)
    )
    if not item:
        raise HTTPException(
            status_code=HTTPStatus.NOT_FOUND, detail='Item not found.'
        )
    await session.delete(item)
    await session.flush()
    await session.commit()
    return {'message': f'Item {item.name} has been deleted successfully.'}