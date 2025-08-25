import os
from http import HTTPStatus
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.security import OAuth2PasswordRequestForm
from fastapi import Query  
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.database import get_asession
from src.database.models import User
from src.api.schemas import Token, Message, StripeChecker, TelegramId
from src.api.security import (
    create_access_token,
    get_current_user,
    verify_password,
)


router = APIRouter(prefix='/auth', tags=['auth'])

OAuth2Form = Annotated[OAuth2PasswordRequestForm, Depends()]
T_Session = Annotated[AsyncSession, Depends(get_asession)]

@router.post('/token', response_model=Token)
async def login_for_access_token(form_data: OAuth2Form, session: T_Session, response: Response): 
    user = await session.scalar(select(User).where(User.email == form_data.username))
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Incorrect email or password',
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Incorrect email or password',
        )

    access_token = create_access_token(data={'sub': user.email})

    return {'access_token': access_token, 
            'token_type': 'bearer', 
            'user':user}


@router.post('/refresh_token', response_model=Token)
def refresh_access_token(
    user: User = Depends(get_current_user),
):
    new_access_token = create_access_token(data={'sub': user.email})

    return {'access_token': new_access_token, 'token_type': 'bearer'}

@router.post('/telegram_access_token', response_model=Token)
async def telegram_access_token(form_data: OAuth2Form, session: T_Session, response: Response): 
    user = await session.scalar(select(User).where(User.telegram_id == int(form_data.username)))
    if not user:
        raise HTTPException(
            status_code=HTTPStatus.BAD_REQUEST,
            detail='Incorrect email or password',
        )

    access_token = create_access_token(data={'sub': user.email})

    return {'access_token': access_token, 
            'token_type': 'bearer', 
            'user':user}