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

    async def add_coins(self, amount: int, telegram_id: int) -> None:
        """Добавление койнов пользователю"""
        if not self.pool:
            raise ConnectionError("Пул подключений не инициализирован. Вызовите connect() перед использованием.")

        query = "UPDATE users SET coins = coins + ? WHERE telegram_id = ?"

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (amount, telegram_id))
                if cur.rowcount == 0:
                    raise ValueError(f"Пользователь '{telegram_id}' не найден")

    async def registration_user(self, user_name: str, telegram_id: int) -> None:
        """Проверяет наличие пользователя по telegram_id и добавляет если не найден"""
        if not self.pool:
            raise ConnectionError("Пул подключений не инициализирован. Вызовите connect() перед использованием.")

        query = """
            MERGE users AS target
            USING (SELECT ? AS user_name, ? AS telegram_id) AS source
            ON target.telegram_id = source.telegram_id
            WHEN NOT MATCHED THEN
                INSERT (user_name, telegram_id) 
                VALUES (source.user_name, source.telegram_id);
        """

        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                await cur.execute(query, (user_name, telegram_id))