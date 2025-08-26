from contextlib import asynccontextmanager
import os

from datetime import datetime

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message
from aiogram.filters import Command, CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from aiogram import Router

from src.database.models import User, MetaLog
from src.agentic_system.nodes_and_conditions import Graph
from src.client.utils_httpx import login
import asyncio
from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv("WISECOLLECT_BOT_TOKEN")
BACKEND_URL = os.getenv("BACKEND_URL")
FRONTEND_URL = os.getenv("FRONTEND_URL")
DATABASE_URL = os.getenv('DATABASE_URL')

workflow = Graph()

engine = create_async_engine(DATABASE_URL)
Session = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def get_session():
    session = Session()
    try:
        yield session
        await session.commit()
    except Exception as e:
        await session.rollback()
        raise e
    finally:
        await session.close()

start_router = Router(name = __name__)
class LoginStates(StatesGroup):
    is_registered = State()
    waiting_for_email = State()
    waiting_for_password = State()

@start_router.message(CommandStart())
async def start(message: Message, state: FSMContext):
    await state.set_state(LoginStates.is_registered)

    telegram_user_id = int(message.from_user.id)
    user_message = message.text
    user_id = user_message.split(' ')[1]

    async with get_session() as session:
        user = await session.scalar(select(User).where(User.id == user_id))
        if user:
            user.telegram_id = telegram_user_id
            is_act = user.is_active
            await session.commit()
        else:
            pass

    if user:
        await message.answer("Você já está logado.")
        if not is_act:
            async with get_session() as session:
                user = await session.scalar(select(User).where(User.id == user_id))
                user.is_active = True
                await session.commit()

    else:
        await message.answer(
            "Olá! Você já é registrado no nosso serviço? (sim/não)",
            reply_markup=ReplyKeyboardMarkup(
                keyboard=[
                    [KeyboardButton(text="Sim"), 
                    KeyboardButton(text="Não")]
                ],
                resize_keyboard=False
                ))

@start_router.message(LoginStates.is_registered, F.text.casefold() == "sim")
async def process_is_registered(message: Message, state: FSMContext):
    await message.reply("Redirecionando para o login...", reply_markup=ReplyKeyboardRemove())
    await process_login(message, state)

@start_router.message(LoginStates.is_registered, F.text.casefold() == "não")
async def process_is_not_registered(message: Message):
    await message.answer(f"Por favor, registre-se no nosso site: {FRONTEND_URL}/register", reply_markup=ReplyKeyboardRemove())

@start_router.message(Command("login"))
async def process_login(message: Message, state: FSMContext):
    await message.answer("Olá! Para começar, por favor, me informe seu e-mail ou /exit para sair:")
    await state.set_state(LoginStates.waiting_for_email)

@start_router.message(Command("exit"))
async def exit_login(message: Message, state: FSMContext):
    current_state = await state.get_state()
    if current_state in [LoginStates.waiting_for_email, LoginStates.waiting_for_password]:
        await state.clear()
        await message.answer("Sessão de login encerrada.")
    else:
        await message.answer("Nenhum processo de login ativo.")

@start_router.message(LoginStates.waiting_for_email)
async def process_email(message: Message, state: FSMContext):
    await state.update_data(email=message.text)
    await message.answer("Agora digite sua senha:")
    await state.set_state(LoginStates.waiting_for_password)

@start_router.message(LoginStates.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    user_data = await state.get_data()
    email = user_data['email']
    password = message.text
    telegram_user_id = message.from_user.id
    
    # Process login
    token_data = await login(email, password)
    
    
    if token_data:
        async with get_session() as session:
            user = await session.scalar(select(User).where(User.email == email))
            user.telegram_id = telegram_user_id
            await session.commit()
        fullname = f"{token_data['user']['first_name']} {token_data['user']['last_name']}"
        await message.answer(f"Bem-vindo {fullname}!")
    else:
        await message.answer("Login inválido, tente novamente com /start")
    
    await state.clear()


@start_router.message(Command("app"))
async def process_login(message: Message):
    telegram_user_id = message.from_user.id

    login_url = f"{FRONTEND_URL}/?telegram_id={telegram_user_id}"
    await message.answer(
        "🖥️ <b>Dashboard do Usuário</b>\n\n"
        '👉 <a href="{}">Clique aqui para acessar</a>'.format(login_url),
        parse_mode="HTML",
        disable_web_page_preview=True
    )

@start_router.message()
async def respond(message: Message, state: FSMContext):
    now = datetime.now()
    current_month = now.month
    current_year = now.year

    telegram_user_id = int(message.from_user.id)
    user_message = message.text

    async with get_session() as session:
        db_user = await session.scalar(
            select(User).where(User.telegram_id == telegram_user_id)
        )
        stmt = select(func.sum(MetaLog.n_tokens)).where(
    MetaLog.user_id == db_user.id,
    func.extract("month", MetaLog.created_at) == current_month,
    func.extract("year", MetaLog.created_at) == current_year
)
        total_tokens = await session.scalar(stmt)

    if total_tokens:
        if total_tokens > 100000:
            await message.answer(f'Numero total de tokens deste mês foi atingido: {total_tokens}.')
            return None

    if db_user:
        user_id = db_user.id
        thread = {'configurable': {'thread_id': user_id, 'user_id': user_id}}
        await workflow.async_invoking(message=user_message, config=thread)
        state = await workflow.async_state(config=thread)
        response_text = ''
        for i in reversed(state.values['messages']):
            if i.role == 'user':
                break
            response_text += i.content
        await message.answer(response_text)
    else:
        await message.answer(
                "Seu número de telegram não está cadastrado. Você já é registrado no nosso serviço? (sim/não)",
                reply_markup=ReplyKeyboardMarkup(
                    keyboard=[[KeyboardButton(text="Sim"), KeyboardButton(text="Não")]],
                    resize_keyboard=False
                )
            )
        await state.set_state(LoginStates.is_registered)


async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(start_router)

    print("BOT RUNNING")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())