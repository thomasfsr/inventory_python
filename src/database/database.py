from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from src.database.models import User
import bcrypt as bc
import asyncio
from dotenv import load_dotenv
import os
load_dotenv()

url = os.getenv("DATABASE_URL")
telegram_id = os.getenv("MY_USER_ID")

engine = create_async_engine(url=url)
asyncsession = async_sessionmaker(engine, expire_on_commit=False)

@asynccontextmanager
async def get_async_session():
    async_session = asyncsession()
    try:
        yield async_session
        await async_session.commit()
    except Exception as e:
        await async_session.rollback()
        raise e
    finally:
        await async_session.close()

async def get_asession():
    instance_session = asyncsession()
    async with instance_session as session:
        yield session

async def create_user(first_name, last_name, email, password, telegram_id):
    hashed_password = bc.hashpw(password.encode('utf-8'), bc.gensalt())
    user = User(
        first_name=first_name,
        last_name=last_name,
        email=email,
        hashed_password=hashed_password.decode('utf-8'),
        telegram_id = int(telegram_id),
        is_active=True
    )
    async with get_async_session() as session:
        session.add(user)
        await session.commit()

async def main():
    await create_user(
        first_name='Thomás',
        last_name='Freire da Silva Reis',
        email='thomas.fsr@gmail.com',
        password='feliz1989',
        telegram_id=telegram_id,
        )
    await create_user(
        first_name='Priscila',
        last_name='Plácido da Silva',
        email='priscilaplacidoricci132@gmail.com',
        password='fuba0603',
        telegram_id=int(1025568783)
    )

if __name__ == '__main__':
    # import sys
    # if sys.platform.startswith("win"):
    #     asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())