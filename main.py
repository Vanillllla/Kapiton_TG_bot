import asyncio

from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from config import config


class BotStates(StatesGroup):
    """Состояния бота"""
    choosing = State()


class ButtonBot:
    def __init__(self):
        self.config = config.validate_config()
        self.bot = Bot(token=config.BOT_TOKEN)
        self.dp = Dispatcher()
        self.router = Router()
        self.user_sessions = {}  # Хранение сессий пользователей

        self.setup_handlers()
        self.dp.include_router(self.router)

        # Клавиатуры:


        self.keyboard_kapiton = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Выдать 3 капитона", callback_data="give_3")],
                [InlineKeyboardButton(text="Выдать 1 капитон", callback_data="give_1")],
                [InlineKeyboardButton(text="Отмена", callback_data="otmena")],
                [InlineKeyboardButton(text="Забрать 1 капитон", callback_data="take_1")],
                [InlineKeyboardButton(text="Забрать 2 капитон", callback_data="take_2")],
                # [InlineKeyboardButton(text="", url="https://vk.com/video-229719551_456239389")],
            ]
        )

        self.keyboard_main = ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text="Моя статистика"), KeyboardButton(text="Избранные")],
                [KeyboardButton(text="Общая статистика"), KeyboardButton(text="Информация")],
            ],
            resize_keyboard=True,  # Подгонка под размер
            one_time_keyboard=False  # Скрыть после нажатия
        )


    def setup_handlers(self):
        """Настраивает обработчики сообщений"""
        # Команда /start
        self.router.message.register(self.start, Command("start"))

        # Обработка кнопок в состоянии choosing
        self.router.message.register(self.info, F.text == "Информация", StateFilter(BotStates.choosing))
        self.router.message.register(self.teg_input, StateFilter(BotStates.choosing))


        # Любое сообщение без состояния
        self.router.message.register(self.any_message)

    async def start(self, message: types.Message, state: FSMContext):
        """Обработчик команды /start"""

        await message.answer("Я РЫЦАРЬ!",reply_markup=self.keyboard_main)
        await state.set_state(BotStates.choosing)

    async def teg_input(self, message: types.Message, state: FSMContext):
        text = message.text
        if text[0] == "@":
            print(text, message.from_user.full_name)
            await message.answer(f"Что сделать с этим {text} ?", reply_markup=self.keyboard_kapiton)
        else:
            await message.answer("Что ты несёшь!?")

    async def info(self, message: types.Message, state: FSMContext):
        """Обработчик кнопки Информация"""

    async def any_message(self, message: types.Message):
        """Обработчик любого сообщения без состояния"""
        await message.answer("Используйте /start для начала работы")

    async def run(self):
        """Запускает бота"""
        print("Бот запущен на aiogram...")
        await self.dp.start_polling(self.bot)

    async def handle_callback(self, callback: types.CallbackQuery):
        """Обработчик нажатий на инлайн-кнопки"""
        if callback.data == "button1":
            await callback.message.edit_text("Вы нажали Кнопку 1! ✅")
        elif callback.data == "button2":
            await callback.message.edit_text("Вы выбрали Кнопку 2! 🚀")
        elif callback.data == "info":
            await callback.message.edit_text("Это асинхронный бот на aiogram с инлайн-кнопками!")

        await callback.answer()



if __name__ == '__main__':
    # Выберите одну из версий бота:

    # Версия с обычными кнопками
    bot = ButtonBot()

    # Или версия с инлайн-кнопками
    # bot = InlineButtonBot()

    asyncio.run(bot.run())