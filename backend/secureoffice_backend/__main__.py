from .app import create_app
from .config import AppConfig
from .db import Database


def main() -> None:
    config = AppConfig.from_env()
    database = Database(config.database_url)
    database.wait_until_ready()
    database.initialize()

    app = create_app(config=config, database=database)
    app.run(host=config.host, port=config.port)


if __name__ == "__main__":
    main()
