from config import Config
import asyncio
import aioodbc
from typing import List, Tuple, Any, Optional

class DataWork:
    def __init__(self):
        self.config = Config()
        self.connection_string = (
            f'DRIVER={{ODBC Driver 18 for SQL Server}};'
            f'SERVER={self.config.SQL_SERVER};'
            f'DATABASE={self.config.SQL_DATABASE};'
            f'UID={self.config.SQL_USER};'
            f'PWD={self.config.SQL_PASSWORD};'
            f'TrustServerCertificate=yes;'
            f'Encrypt=no;'
        )
        self.pool: Optional[aioodbc.Pool] = None

    async def connect(self, pool_size: int = 5):
        """Создание пула подключений"""
        try:
            self.pool = await aioodbc.create_pool(
                dsn=self.connection_string,
                minsize=1,
                maxsize=pool_size,
                autocommit=True
            )
            print("Пул подключений создан успешно")
        except Exception as e:
            print(f"Ошибка создания пула: {e}")
            raise

    async def close(self):
        """Закрытие пула подключений"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            print("Пул подключений закрыт")

    async def add_coins(self, amount: int, user_name: str) -> None:
        """Добавление койнов пользователю"""
        if not self.pool:
            raise ConnectionError("Пул подключений не инициализирован. Вызовите connect() перед использованием.")

        query = "UPDATE users SET coins = coins + ? WHERE user_name = ?"

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (amount, user_name))
                if cur.rowcount == 0:
                    raise ValueError(f"Пользователь '{user_name}' не найден")

    async def registration_user(self, user_name: str, telegram_id: int) -> None:
        """Регистрирует пользователя или обновляет telegram_id если user_name существует"""
        if not self.pool:
            raise ConnectionError("Пул подключений не инициализирован. Вызовите connect() перед использованием.")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Начинаем транзакцию
                await cur.execute("BEGIN TRANSACTION")

                try:
                    # Проверяем существование пользователя с таким user_name
                    await cur.execute(
                        "SELECT id, telegram_id FROM users WHERE user_name = ?",
                        (user_name,)
                    )
                    existing_user = await cur.fetchone()

                    if existing_user:
                        user_id, existing_telegram_id = existing_user

                        # Если у пользователя нет telegram_id, обновляем его
                        if existing_telegram_id is None:
                            await cur.execute(
                                "UPDATE users SET telegram_id = ? WHERE id = ?",
                                (telegram_id, user_id)
                            )
                            print(f"Обновлен telegram_id для пользователя {user_name}")
                        else:
                            print(f"Пользователь {user_name} уже зарегистрирован с telegram_id {existing_telegram_id}")
                    else:
                        # Создаем нового пользователя
                        await cur.execute(
                            "INSERT INTO users (user_name, telegram_id, coins, limits, lovers) VALUES (?, ?, 0, 10, '')",
                            (user_name, telegram_id)
                        )
                        print(f"Создан новый пользователь {user_name} с telegram_id {telegram_id}")

                    await cur.execute("COMMIT")

                except Exception as e:
                    await cur.execute("ROLLBACK")
                    raise e

    async def add_lovers(self, user_name_to_love: str, user_name: str) -> None:
        """Добавляет пользователя в список lovers с созданием при необходимости"""
        if not self.pool:
            raise ConnectionError("Пул подключений не инициализирован. Вызовите connect() перед использованием.")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Начинаем транзакцию для атомарности
                await cur.execute("BEGIN TRANSACTION")

                try:
                    # Проверяем существование пользователя user_name_to_love
                    await cur.execute("SELECT id FROM users WHERE user_name = ?", (user_name_to_love,))
                    target_user = await cur.fetchone()

                    if not target_user:
                        # Создаем нового пользователя если не существует
                        await cur.execute(
                            "INSERT INTO users (user_name, coins, limits, lovers) VALUES (?, 0, 10, '')",
                            (user_name_to_love,)
                        )
                        # Получаем ID нового пользователя
                        await cur.execute("SELECT SCOPE_IDENTITY()")
                        target_user_id = (await cur.fetchone())[0]
                    else:
                        target_user_id = target_user[0]

                    # Получаем текущих lovers для пользователя user_name
                    await cur.execute("SELECT lovers FROM users WHERE user_name = ?", (user_name,))
                    user_row = await cur.fetchone()

                    if not user_row:
                        raise ValueError(f"Пользователь с именем '{user_name}' не найден")

                    current_lovers = user_row[0] or ""

                    # Разделяем существующих lovers и проверяем дубликаты
                    lovers_list = current_lovers.split(',') if current_lovers else []
                    if str(target_user_id) in lovers_list:
                        # Уже есть в списке, выходим
                        await cur.execute("COMMIT")
                        return

                    # Добавляем нового lover с оптимальным разделителем
                    if current_lovers:
                        new_lovers = current_lovers + ',' + str(target_user_id)
                    else:
                        new_lovers = str(target_user_id)

                    # Обновляем запись
                    await cur.execute(
                        "UPDATE users SET lovers = ? WHERE user_name = ?",
                        (new_lovers, user_name)
                    )

                    await cur.execute("COMMIT")

                except Exception as e:
                    await cur.execute("ROLLBACK")
                    raise e

    async def get_lovers(self, telegram_id: int) -> dict:
        """Возвращает словарь всех lovers пользователя"""
        if not self.pool:
            raise ConnectionError("Пул подключений не инициализирован. Вызовите connect() перед использованием.")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                # Получаем список lovers для пользователя
                await cur.execute("SELECT lovers FROM users WHERE telegram_id = ?", (telegram_id,))
                user_row = await cur.fetchone()

                if not user_row:
                    raise ValueError(f"Пользователь с telegram_id {telegram_id} не найден")

                lovers_str = user_row[0]

                if not lovers_str:
                    return {}

                # Разделяем строку на отдельные ID
                lover_ids = lovers_str.split(',')

                # Получаем информацию о каждом lover
                if lover_ids:
                    # Создаем placeholders для запроса
                    placeholders = ','.join('?' * len(lover_ids))
                    query = f"""
                        SELECT telegram_id, user_name 
                        FROM users 
                        WHERE id IN ({placeholders})
                    """

                    await cur.execute(query, lover_ids)
                    lovers_data = await cur.fetchall()

                    # Формируем словарь {telegram_id: user_name}
                    return {row[0]: row[1] for row in lovers_data}

                return {}

    async def user_statistic(self, telegram_id: int) -> tuple:
        """Возвращает статистику пользователя (coins, limits) по telegram_id"""
        if not self.pool:
            raise ConnectionError("Пул подключений не инициализирован. Вызовите connect() перед использованием.")

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(
                    "SELECT coins, limits FROM users WHERE telegram_id = ?",
                    (telegram_id,)
                )
                user_data = await cur.fetchone()

                if not user_data:
                    raise ValueError(f"Пользователь с telegram_id {telegram_id} не найден")

                coins, limits = user_data
                return coins, limits