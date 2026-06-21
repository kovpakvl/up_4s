from pathlib import Path


APP_NAME = "SecureOffice"
PROJECT_NAME = "SecureOffice"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
BACKUP_DIR = BASE_DIR / "backups"
DB_PATH = DATA_DIR / "password_manager.db"

PBKDF2_ITERATIONS = 390_000
PASSWORD_REVEAL_SECONDS = 10
CLIPBOARD_CLEAR_SECONDS = 30
AUTO_LOCK_MINUTES = 5

DEFAULT_DEPARTMENTS = (
    "Финансы",
    "Продажи",
    "Маркетинг",
    "IT",
    "Руководство",
    "Бухгалтерия",
)

DEFAULT_SERVICE_TYPES = (
    "Банк",
    "Онлайн-касса",
    "Почта",
    "Сайт",
    "Соцсети",
    "Бухгалтерия",
)

FINANCIAL_SERVICE_TYPES = ("Банк", "Онлайн-касса", "Бухгалтерия")

EMPLOYEE_ROLES = (
    "Администратор",
    "Бухгалтер",
    "Менеджер",
    "Маркетолог",
    "Директор",
    "Сотрудник",
)

EMPLOYEE_STATUSES = ("Активен", "В отпуске", "Уволен")
