from datetime import datetime, timedelta
from http import HTTPStatus
from zoneinfo import ZoneInfo

from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer

from jwt import ExpiredSignatureError, decode, encode, DecodeError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.database import get_asession
from src.database.models import User
from src.api.schemas import TokenData
import bcrypt as bc

import os
from dotenv import load_dotenv
load_dotenv()

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(tz=ZoneInfo('UTC')) + timedelta(
        minutes= int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))
    )
    to_encode.update({'exp': expire})
    encoded_jwt = encode(
        to_encode, os.getenv("SECRET_KEY"), algorithm=os.getenv("ALGORITHM")
    )
    return encoded_jwt


def get_password_hash(password: str):
    return bc.hashpw(password.encode(), bc.gensalt()).decode()

def verify_password(plain_password: str, hashed_password: str):
    return bc.checkpw(plain_password.encode(), hashed_password.encode())

oauth2_schema = OAuth2PasswordBearer(tokenUrl='auth/token')

async def get_current_user(
    session: AsyncSession = Depends(get_asession),
    token: str = Depends(oauth2_schema),
):
    credentials_exception = HTTPException(
        status_code=HTTPStatus.UNAUTHORIZED,
        detail='Could not validate credentials',
        headers={'WWW-Authenticate': 'Bearer'},
    )

    try:
        payload = decode(
            token, os.getenv("SECRET_KEY"), algorithms=[os.getenv("ALGORITHM")]
        )
        username: str = payload.get('sub')
        if not username:
            raise credentials_exception
        token_data = TokenData(username=username)
    except DecodeError:
        raise credentials_exception
    except ExpiredSignatureError:
        raise credentials_exception

    user = await session.scalar(
        select(User).where(User.email == token_data.username)
    )

    if not user:
        raise credentials_exception

    return user