from functools import lru_cache
from typing import Union
from uuid import UUID
from contextlib import asynccontextmanager
from sqlalchemy import select
from sqlalchemy.sql import text

from langchain_core.prompts import ChatPromptTemplate

from src.database.models import InventoryItem, User, MetaLog

from pydantic import BaseModel

from sqlalchemy.ext.asyncio import (create_async_engine, 
                                    async_sessionmaker)

from decimal import Decimal
import os
from dotenv import load_dotenv
load_dotenv()

@lru_cache
def get_uri():
    return os.getenv('DATABASE_URL')

def format_as_table(data: list) -> str:
    if not data:
        return """Resultado não encontrado. """
    
    rows = [", ".join(map(str, row)) for row in data]
    return "\n".join(rows)

class DatabaseHandler:
    def __init__(self):
        uri = get_uri()
        self.engine = create_async_engine(uri)
        self.Session = async_sessionmaker(self.engine, expire_on_commit=False)
    @asynccontextmanager
    async def _get_session(self):
        session = self.Session()
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise e
        finally:
            await session.close()

    async def user_name(self, user_id:Union[str, UUID]):
        async with self._get_session() as session:
            user = await session.scalar(
                select(User).where(User.id == user_id))
            return f'{user.first_name} {user.last_name}'


    async def check_existing_item(self, user_id:Union[str, UUID], item_name:str):
        item_name = item_name.lower()
        async with self._get_session() as session:
            try:
                existing_item = await session.scalar(
                    select(InventoryItem).where((InventoryItem.user_id==user_id) & 
                    (InventoryItem.name == item_name)))
            except:
                existing_item = None
            if existing_item:
                message = f"""Item '{item_name}' já existe no banco de dados. """
                is_in_db = True
            else:
                message = f"""Item '{item_name}' não existe no banco de dados. """
                is_in_db = False
        return is_in_db, message
    
    async def renaming_existing_item(self, user_id:Union[str, UUID], old_item_name:str, new_item_name:str):
        old_item_name = old_item_name.lower()
        new_item_name = new_item_name.lower()
        async with self._get_session() as session:
            existing_old_item = await session.scalar(
                select(InventoryItem).where((InventoryItem.user_id==user_id) & 
                (InventoryItem.name == old_item_name)))
        
            existing_new_item = await session.scalar(
                select(InventoryItem).where((InventoryItem.user_id==user_id) &
                (InventoryItem.name == new_item_name)))
            
            if existing_old_item and not existing_new_item:
                existing_old_item.name = new_item_name
                await session.commit()
                await session.refresh(existing_old_item)
                message = f"""Item:{old_item_name} renomeado para: {existing_old_item.name}. """

            elif existing_old_item and existing_new_item:
                existing_new_item.quantity += Decimal(existing_old_item.quantity)
                await session.commit()
                await session.refresh(existing_new_item)
                
                message = f"""Item: {old_item_name} quantidade: ({existing_old_item.quantity}) 
                foi encorporado pelo nome correto do item: {new_item_name} - {existing_new_item.quantity}. """
            
            else:
                message = f"""Item {old_item_name} não encontrado. """
        return message

    async def add_to_existing_item(self, user_id:Union[str, UUID], item_name:str, quantity:int|float):
        item_name = item_name.lower()
        async with self._get_session() as session:
            item = await session.scalar(
                select(InventoryItem).where((InventoryItem.user_id ==user_id) &
                                                    (InventoryItem.name == item_name)))
            current_quantity = Decimal(item.quantity)
            plus_quantity = Decimal(quantity)
            item.quantity = current_quantity + plus_quantity
            await session.commit()
            await session.refresh(item)
            message = f"""Adicionado {quantity} {item.unit} ao item {item_name}, quantidade atual: {item.quantity}. """
        return message

    async def subtract_to_existing_item(self, user_id:Union[str, UUID], item_name:str, quantity:int|float):
        item_name = item_name.lower()
        async with self._get_session() as session:
            item = await session.scalar(
                select(InventoryItem).where((InventoryItem.user_id ==user_id) &
                                                    (InventoryItem.name == item_name)))
            if item.quantity >= Decimal(quantity):
                item.quantity-= Decimal(quantity)
                await session.commit()
                await session.refresh(item)
                
                message = f"""Subtraido {quantity} {item.unit} do item {item_name}, quantidade atual: {item.quantity}. """
            else:
                message = f"""Quantidade {quantity} {item.unit} é maior que a quantidade do item 
                {item_name}: quantidade Total {item.quantity} {item.unit}. """
        return message

    async def discard_all_to_existing_item(self, user_id:Union[str, UUID], item_name:str):
        item_name = item_name.lower()
        async with self._get_session() as session:
            item = await session.scalar(
                select(InventoryItem).where((InventoryItem.user_id ==user_id) &
                                                    (InventoryItem.name == item_name)))
            if item.quantity >= 0:
                item.quantity = 0
                await session.commit()
                await session.refresh(item)
                
                message = f"Descartar todas as unidades do item {item_name}. "
            else:
                message = f"Quantidade de {item_name} já é 0. "
        return message
    
    
    async def change_unit(self, user_id:Union[str, UUID], item_name:str, unit: str):
        item_name = item_name.lower()
        async with self._get_session() as session:
            item = await session.scalar(
                select(InventoryItem).where((InventoryItem.user_id ==user_id) &
                                                    (InventoryItem.name == item_name)))
            if item:
                item.unit = unit
                await session.commit()
                await session.refresh(item)
                message = f"""Unidade de {item_name} definido como {item.unit}. """
            else:
                message = f"""Item {item_name} não encontrado. """
        return message
    
    async def creating_new_item(self, user_id:Union[str, UUID], 
                                item_name:str, 
                                quantity:int|float,
                                category:str|None,
                                desc:str|None, 
                                loc:str|None, 
                                unit=str|None):
        item_name = item_name.lower()
        if desc:
            desc = desc.lower()
        if loc:
            loc = loc.lower()
        if unit:
            unit = unit.lower()
        if not quantity:
            quantity = 0
        if not category:
            category = "geral"
        async with self._get_session() as session:
            created_item = InventoryItem(
                    user_id=user_id,
                    name=item_name,
                    description=desc,
                    location= loc,
                    quantity=quantity,
                    unit=unit,
                    category=category
                    )
            session.add(created_item)
            await session.commit()
            await session.refresh(created_item)
            message = f"""Item {created_item.name} criado com sucesso, quantidade atual: {created_item.quantity} {created_item.unit}. """
        return message

    async def add_total_tokens(self, user_id:Union[str,UUID], n_tokens: int):
        async with self._get_session() as session:
            token_usage = MetaLog(
                    user_id=user_id,
                    n_tokens=n_tokens)
            session.add(token_usage)
            await session.commit()
            await session.refresh(token_usage)
            message = f"""Number of tokens used: {token_usage.n_tokens}. """
        return message
   
    async def query(self, query: str):
        async with self._get_session() as session:
            try:
                result = await session.execute(text(query))
                rows = result.fetchall()
                formated_result = format_as_table(rows)
                return formated_result
            except Exception as e:
                raise e


from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage

async def struct_output_call(system:str, human:str, llm:BaseChatModel, basemodel: BaseModel):
    check_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", human),
            ]
        )
    structured_llm = llm.with_structured_output(basemodel, include_raw=True)
    chain = check_prompt | structured_llm
    response = await chain.ainvoke({})

    return response

async def llm_chain_call(system:str, human:str, llm:BaseChatModel) -> AIMessage:
    check_prompt = ChatPromptTemplate.from_messages(
            [
                ("system", system),
                ("human", human),
            ]
        )
    chain = check_prompt | llm
    response = await chain.ainvoke({})

    return response