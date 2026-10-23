from sqlalchemy import Engine, create_engine, text
from dotenv import load_dotenv

from src.business.classify_service import IssueCategory


class IssueCategoryRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def get_active_by_name(self, category_name: str) -> IssueCategory | None:
        statement = text(
            "SELECT category_id, category_name, default_priority "
            "FROM issue_category "
            "WHERE category_name = :category_name AND is_active = TRUE"
        )
        with self._engine.connect() as connection:
            row = connection.execute(
                statement, {"category_name": category_name}
            ).mappings().first()

        if row is None:
            return None
        return IssueCategory(
            category_id=row["category_id"],
            category_name=row["category_name"],
            default_priority=row["default_priority"],
        )


def repository_from_environment() -> IssueCategoryRepository | None:
    import os

    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return None
    return IssueCategoryRepository(create_engine(database_url, pool_pre_ping=True))