import os

SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "change-me")
# Метаданные Superset (дашборды, чарты) — в SQLite внутри volume superset_home
SQLALCHEMY_DATABASE_URI = "sqlite:////app/superset_home/superset.db"
# Для локального пет-проекта отключаем строгие заголовки безопасности
TALISMAN_ENABLED = False
FEATURE_FLAGS = {
    "DASHBOARD_RBAC": False,
}
# Русский интерфейс можно включить так (по желанию):
# BABEL_DEFAULT_LOCALE = "ru"
