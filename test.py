from data_work import DataWork
import asyncio

db = DataWork()

async def main():
    await db.connect()
    users = await db.execute_query("SELECT id, telegram_id FROM users")

    users = await db.execute_query("SELECT id, telegram_id FROM users")
    print(users)

    users = await db.execute_query("SELECT id, telegram_id FROM users")
    print(users)
    users = await db.execute_query("SELECT id, telegram_id FROM users")
    print(users)
    users = await db.execute_query("SELECT id, telegram_id FROM users")
    print(users)
    await db.close()

if __name__ == "__main__":
    asyncio.run(main())

# import pyodbc
#
# # Посмотреть все доступные драйверы
# print(pyodbc.drivers())