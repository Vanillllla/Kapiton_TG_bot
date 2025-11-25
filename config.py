import os
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()


class Config:
    """Класс для хранения конфигурации приложения"""

    # База данных
    BOT_TOKEN = os.getenv('BOT_TOKEN')
    SQL_SERVER = os.getenv("SQL_SERVER")
    SQL_DATABASE = os.getenv("SQL_DATABASE")
    SQL_USER = os.getenv("SQL_USER")
    SQL_PASSWORD = os.getenv("SQL_PASSWORD")


    @classmethod
    def validate_config(cls):
        """Проверка обязательных переменных окружения"""
        required_vars = ["BOT_TOKEN"]
        missing_vars = [var for var in required_vars if not getattr(cls, var)]

        if missing_vars:
            raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")


# Создаем экземпляр конфигурации
config = Config()