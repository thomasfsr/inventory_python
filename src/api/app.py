from http import HTTPStatus

from fastapi import FastAPI

from src.api.routers import auth, items, users
from src.api.schemas import Message

app = FastAPI()

app.include_router(users.router)
app.include_router(auth.router)
app.include_router(items.router)