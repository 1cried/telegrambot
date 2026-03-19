import os
import sys
from pathlib import Path

# Определяем правильный путь к директории (для exe и для обычного запуска)
def get_base_dir():
    """Получить директорию, где находится скрипт/exe"""
    if getattr(sys, 'frozen', False):
        # Запущен как exe
        return os.path.dirname(sys.executable)
    else:
        # Запущен как скрипт
        return os.path.dirname(os.path.abspath(__file__))

BASE_DIR = get_base_dir()

# Загружаем .env файл если он есть
env_path = Path(__file__).parent / '.env'
if env_path.exists():
    with open(env_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                os.environ[key.strip()] = value.strip()

class Config:
    """Конфигурация бота"""
    
    def __init__(self):
        self.BOT_TOKEN = os.getenv('BOT_TOKEN', '')
        self.DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')
        self.DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'

config = Config()
