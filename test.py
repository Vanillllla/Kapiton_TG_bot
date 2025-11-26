from data_work import DataWork
import asyncio

db = DataWork()

async def main():
    await db.connect()

    await db.registration_user("Kapiton_TG_bot",8561660959)

    await db.close()

if __name__ == "__main__":
    asyncio.run(main())

# import pyodbc
#
# # Посмотреть все доступные драйверы
# print(pyodbc.drivers())