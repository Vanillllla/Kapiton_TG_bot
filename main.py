import asyncio

from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
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

    def create_main_keyboard(self) -> ReplyKeyboardMarkup:
        """Создает основную клавиатуру"""
        builder = ReplyKeyboardBuilder()
        builder.add(
            KeyboardButton(text="Кнопка 1"),
            KeyboardButton(text="Кнопка 2"),
            KeyboardButton(text="Информация"),
            KeyboardButton(text="Закрыть")
        )
        return builder.as_markup(resize_keyboard=True)

    def setup_handlers(self):
        """Настраивает обработчики сообщений"""
        # Команда /start
        self.router.message.register(self.start, Command("start"))

        # Обработка кнопок в состоянии choosing
        self.router.message.register(self.button1, F.text == "Кнопка 1", StateFilter(BotStates.choosing))
        self.router.message.register(self.button2, F.text == "Кнопка 2", StateFilter(BotStates.choosing))
        self.router.message.register(self.info, F.text == "Информация", StateFilter(BotStates.choosing))
        self.router.message.register(self.close, F.text == "Закрыть", StateFilter(BotStates.choosing))

        # Команда /cancel
        self.router.message.register(self.cancel, Command("cancel"))

        # Любое сообщение без состояния
        self.router.message.register(self.any_message)

    async def start(self, message: types.Message, state: FSMContext):
        """Обработчик команды /start"""
        user_id = message.from_user.id
        self.user_sessions[user_id] = {
            "start_time": message.date,
            "button1_clicks": 0
        }

        await message.answer(
            "Выберите действие:",
            reply_markup=self.create_main_keyboard()
        )
        await state.set_state(BotStates.choosing)

    async def button1(self, message: types.Message, state: FSMContext):
        """Обработчик кнопки 1"""
        user_id = message.from_user.id
        click_count = self.user_sessions[user_id].get("button1_clicks", 0) + 1
        self.user_sessions[user_id]["button1_clicks"] = click_count

        await message.answer(f'Кнопка 1 нажата {click_count} раз! ✅')

    async def button2(self, message: types.Message, state: FSMContext):
        """Обработчик кнопки 2"""
        await message.answer('Вы выбрали Кнопку 2! 🚀')

    async def info(self, message: types.Message, state: FSMContext):
        """Обработчик кнопки Информация"""
        user_count = len(self.user_sessions)
        await message.answer(f'Бот работает на aiogram! Активных пользователей: {user_count}')

    async def close(self, message: types.Message, state: FSMContext):
        """Обработчик кнопки Закрыть"""
        await message.answer(
            'Клавиатура закрыта. Используйте /start чтобы открыть снова.',
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()

    async def cancel(self, message: types.Message, state: FSMContext):
        """Обработчик команды /cancel"""
        await message.answer(
            'До свидания!',
            reply_markup=ReplyKeyboardRemove()
        )
        await state.clear()

    async def any_message(self, message: types.Message):
        """Обработчик любого сообщения без состояния"""
        await message.answer("Используйте /start для начала работы")

    async def run(self):
        """Запускает бота"""
        print("Бот запущен на aiogram...")
        await self.dp.start_polling(self.bot)


# Альтернативная версия с инлайн-кнопками
class InlineButtonBot:
    def __init__(self):
        self.config = config.validate_config()
        self.bot = Bot(token=config.BOT_TOKEN)
        self.dp = Dispatcher()
        self.router = Router()

        self.setup_handlers()
        self.dp.include_router(self.router)

    def create_inline_keyboard(self):
        """Создает инлайн-клавиатуру"""
        buttons = [
            [
                types.InlineKeyboardButton(text="Кнопка 1", callback_data="button1"),
                types.InlineKeyboardButton(text="Кнопка 2", callback_data="button2")
            ],
            [types.InlineKeyboardButton(text="Информация", callback_data="info")]
        ]
        return types.InlineKeyboardMarkup(inline_keyboard=buttons)

    def setup_handlers(self):
        """Настраивает обработчики"""
        self.router.message.register(self.start, Command("start"))
        self.router.callback_query.register(self.handle_callback, StatesGroup)

    async def start(self, message: types.Message):
        """Обработчик команды /start"""
        await message.answer(
            "Выберите действие:",
            reply_markup=self.create_inline_keyboard()
        )

    async def handle_callback(self, callback: types.CallbackQuery):
        """Обработчик нажатий на инлайн-кнопки"""
        if callback.data == "button1":
            await callback.message.edit_text("Вы нажали Кнопку 1! ✅")
        elif callback.data == "button2":
            await callback.message.edit_text("Вы выбрали Кнопку 2! 🚀")
        elif callback.data == "info":
            await callback.message.edit_text("Это асинхронный бот на aiogram с инлайн-кнопками!")

        await callback.answer()

    async def run(self):
        """Запускает бота"""
        print("Инлайн-бот запущен на aiogram...")
        await self.dp.start_polling(self.bot)


if __name__ == '__main__':
    # Выберите одну из версий бота:

    # Версия с обычными кнопками
    bot = ButtonBot()

    # Или версия с инлайн-кнопками
    # bot = InlineButtonBot()

    asyncio.run(bot.run())