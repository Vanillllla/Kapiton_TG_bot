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

    async def execute_query(self, query: str, params: tuple = None) -> List[Tuple]:
        """Выполнение SELECT запроса"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    if params:
                        await cur.execute(query, params)
                    else:
                        await cur.execute(query)

                    result = await cur.fetchall()
                    return result
                except Exception as e:
                    print(f"Ошибка выполнения запроса: {e}")
                    raise

    async def execute_command(self, command: str, params: tuple = None) -> int:
        """Выполнение INSERT/UPDATE/DELETE команды"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    if params:
                        await cur.execute(command, params)
                    else:
                        await cur.execute(command)

                    # Возвращаем количество затронутых строк
                    return cur.rowcount
                except Exception as e:
                    print(f"Ошибка выполнения команды: {e}")
                    await conn.rollback()
                    raise

    async def execute_scalar(self, query: str, params: tuple = None) -> Any:
        """Выполнение запроса с возвратом одного значения"""
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cur:
                try:
                    if params:
                        await cur.execute(query, params)
                    else:
                        await cur.execute(query)

                    result = await cur.fetchone()
                    return result[0] if result else None
                except Exception as e:
                    print(f"Ошибка выполнения скалярного запроса: {e}")
                    raise

    async def get_columns(self, table_name: str) -> List[str]:
        """Получение списка колонок таблицы"""
        query = """
                SELECT COLUMN_NAME
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_NAME = ?
                ORDER BY ORDINAL_POSITION \
                """
        result = await self.execute_query(query, (table_name,))
        return [row[0] for row in result] if result else []