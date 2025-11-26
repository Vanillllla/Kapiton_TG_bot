import asyncio

from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, InlineKeyboardMarkup, \
    InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

from config import config
from data_work import DataWork
db = DataWork()

class BotStates(StatesGroup):
    """Состояния бота"""
    choosing = State()
    lovers = State()


class ButtonBot:
    def __init__(self):
        self.config = config.validate_config()
        self.bot = Bot(token=config.BOT_TOKEN)
        self.dp = Dispatcher()
        self.router = Router()
        self.user_sessions = {}  # Хранение сессий пользователей

        self.setup_handlers()
        self.dp.include_router(self.router)

        self.last_message = None

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

        self.keyboard_lovers = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Добавить", callback_data="plus"),
                 InlineKeyboardButton(text="Удалить", callback_data="minus")],
                [InlineKeyboardButton(text="Закрыть меню", callback_data="home")],
            ]
        )

        self.keyboard_to_home = InlineKeyboardMarkup(
            inline_keyboard=[
                [InlineKeyboardButton(text="Закрыть меню", callback_data="to_home")],
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
        self.router.message.register(self.lovers, F.text == "Избранные", StateFilter(BotStates.choosing))
        self.router.message.register(self.teg_input, StateFilter(BotStates.choosing))

        self.router.callback_query.register(self.handle_callback, StateFilter(BotStates.choosing))

        # Обработчик избранного

        self.router.message.register(self.lovers_work, StateFilter(BotStates.lovers))

        self.router.callback_query.register(self.to_home, F.data == "to_home", StateFilter(BotStates.lovers))
        self.router.callback_query.register(self.handle_callback_lovers, StateFilter(BotStates.lovers))


        # Любое сообщение без состояния

        self.router.message.register(self.any_message)

    async def start(self, message: types.Message, state: FSMContext):
        """Обработчик команды /start"""
        await message.answer("Я РЫЦАРЬ!", reply_markup=self.keyboard_main)
        await db.registration_user(message.from_user.username, message.from_user.id)
        await state.set_state(BotStates.choosing)

    async def to_home(self, callback: types.CallbackQuery, state: FSMContext):
        print(123)
        await state.clear()
        await state.set_state(BotStates.choosing)
        await callback.answer("Вы в главном меню:", reply_markup=self.keyboard_main)
        await callback.message.delete()

    async def lovers(self, message: types.Message, state: FSMContext):
        await message.answer("Тут список", reply_markup=self.keyboard_lovers)
        await state.update_data(act=0)

    async def handle_callback_lovers(self, callback: types.CallbackQuery, state: FSMContext):
        if callback.data == "plus":
            await callback.message.edit_text(text="Ведите персонажа которого хотите добавить в избранные :", reply_markup=self.keyboard_to_home)
            await state.set_state(BotStates.lovers)
            await state.update_data(act=1)
        elif callback.data == "minus":
            await callback.message.edit_text(text="Ведите персонажа которого хотите удалить из избранных :", reply_markup=self.keyboard_to_home)
            await state.set_state(BotStates.lovers)
            await state.update_data(act=2)
        elif callback.data == "home":
            await callback.message.delete()
            await state.set_state(BotStates.choosing)
        await callback.answer()

    async def lovers_work(self, message: types.Message, state: FSMContext):

        data = await state.get_data()
        if data["act"] == 0 or message.text[0] != "@":
            await message.answer("И чё ты хочешь? Напиши телеграм ник пользователя, например: \"@Kapiton_TG_bot\"")
        elif data["act"] == 1:
            await message.answer(f"Пользователь {message.text} добавлен в избранные", reply_markup=self.keyboard_main)
            await state.set_state(BotStates.choosing)
        elif data["act"] == 2:
            await message.answer(f"Пользователь {message.text} удалён из избранных.", reply_markup=self.keyboard_main)
            await state.set_state(BotStates.choosing)


    async def solo_statistic(self, message: types.Message, state: FSMContext):
        """показ статистики для одного пользователя"""
        print(123)

    async def full_statistic(self, message: types.Message, state: FSMContext):
        """показывает весь рейтинг и место пользователя в нём"""
        print(321)

    async def teg_input(self, message: types.Message, state: FSMContext):
        text = message.text
        if text[0] == "@":
            print(text, message.from_user.full_name)
            await message.answer(f"Что сделать с этим {text} ?", reply_markup=self.keyboard_kapiton)
        else:
            await message.answer("Что ты несёшь!?")

    async def handle_callback(self, callback: types.CallbackQuery):
        """Обработчик нажатий на инлайн-кнопки"""
        if callback.data == "give_1":
            await callback.message.edit_text("<b>Выдан</b> 1 капитон! ", parse_mode="html")
            await db.add_coins(1, callback.message.chat.id)
        elif callback.data == "give_3":
            await callback.message.edit_text("<b>Выдано</b> 3 капитона! ", parse_mode="html")

        elif callback.data == "take_1":
            await callback.message.edit_text("<b>Изнят</b> 1 капитон!", parse_mode="html")

        elif callback.data == "take_2":
            await callback.message.edit_text("<b>Изнято</b> 2 капитона!", parse_mode="html")

        elif callback.data == "otmena":
            await callback.message.edit_text("ок...")

        await callback.answer()

    async def info(self, message: types.Message, state: FSMContext):
        """Обработчик кнопки Информация"""
        await message.answer("*ПОЛЕЗНАЯ ИНФОРМАЦИЯ*")
        print("info")

    async def any_message(self, message: types.Message):
        """Обработчик любого сообщения без состояния"""
        await message.answer("Используйте /start для начала работы")

    async def run(self):
        """Запускает бота"""
        await db.connect()

        print("Бот запущен на aiogram...")
        await self.dp.start_polling(self.bot)

        await db.close()

if __name__ == '__main__':
    bot = ButtonBot()
    asyncio.run(bot.run())
