import os
from dotenv import load_dotenv
import requests


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

    GIT_OWNER = os.getenv("GIT_OWNER")
    GIT_REPO = os.getenv("GIT_REPO")

    url = f"https://api.github.com/repos/{GIT_OWNER}/{GIT_REPO}/commits"

    try:
        response = requests.get(url)
        response.raise_for_status()

        commits = response.json()
        if commits:
            GIT_LAST_COMMIT_NAME = commits[0]['commit']['message']
        else:
            print("Репозиторий не содержит коммитов")


    except:
        print(f"Ошибка при запросе к GitHub API: {{}}")


    @classmethod
    def validate_config(cls):
        """Проверка обязательных переменных окружения"""
        required_vars = ["BOT_TOKEN"]
        missing_vars = [var for var in required_vars if not getattr(cls, var)]

        if missing_vars:
            raise ValueError(f"Отсутствуют обязательные переменные окружения: {', '.join(missing_vars)}")


# Создаем экземпляр конфигурации
config = Config()