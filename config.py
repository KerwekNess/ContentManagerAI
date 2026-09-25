import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    API_KEY = os.getenv('GONKA_BROKER_API_KEY', '').strip()
    BASE_URL = (os.getenv('GONKA_BROKER_URL') or '').strip().rstrip('/')
    
    DB_PATH = os.getenv('DB_PATH', './data/history.db')
    DEBUG = os.getenv('DEBUG', 'True').lower() == 'true'

    def validate(self):
        if not self.API_KEY or not self.BASE_URL:
            raise RuntimeError(
                'Missing configuration in .env: GONKA_BROKER_URL or GONKA_BROKER_API_KEY.'
            )
        
        # Создаем папку для БД, если её нет
        db_dir = os.path.dirname(self.DB_PATH)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
