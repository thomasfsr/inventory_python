from pydantic import BaseModel, ConfigDict, EmailStr
from typing import Optional
from src.agentic_system.basemodels import UnitOptions
from uuid import UUID
class Message(BaseModel):
    message: str
    status: str
class UserSchema(BaseModel):
    email: EmailStr
    first_name: str
    last_name: str
    password: str

class UserPublic(BaseModel):
    id: UUID 
    first_name: str
    last_name: str
    email: EmailStr
    model_config = ConfigDict(from_attributes=True)

class StripeChecker(BaseModel):
    user: UserPublic

class UserList(BaseModel):
    users: list[UserPublic]

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserPublic

class TokenData(BaseModel):
    username: str | None = None

class ItemSchema(BaseModel):
    name: str
    description: str | None = None
    location: str | None = None
    quantity: float 
    unit: str
    category: str | None = None


class ItemPublic(ItemSchema):
    id: int

class ItemList(BaseModel):
    items: list[ItemPublic]

class ItemUpdate(BaseModel):
    name: Optional[str] = None
    quantity: Optional[float] = None
    location: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[UnitOptions] = None
    category: Optional[str] = None


class FilterPage(BaseModel):
    offset: int = 0
    limit: int = 100

class FilterItem(FilterPage):
    name: Optional[str] = None
    quantity: Optional[float] = None
    location: Optional[str] = None
    description: Optional[str] = None
    unit: Optional[str] = None    
    category: Optional[str] = None

class TelegramId(BaseModel):
    telegram_id: int