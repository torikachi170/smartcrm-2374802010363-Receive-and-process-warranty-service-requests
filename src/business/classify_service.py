from dataclasses import dataclass
from typing import Protocol
import unicodedata


@dataclass(frozen=True)
class IssueCategory:
    category_id: int
    category_name: str
    default_priority: str


class CategoryLookup(Protocol):
    def get_active_by_name(self, category_name: str) -> IssueCategory | None:
        ...


class CategoryNotConfigured(Exception):
    pass


class ClassifyService:
    _KEYWORDS = (
        ("NUOC_VAO", ("nuoc vao", "vao nuoc", "roi nuoc", "tham nuoc")),
        ("MAN_HINH", ("man hinh", "lcd", "display", "cam ung")),
        ("PHAN_MEM", ("phan mem", "ung dung", "app", "cap nhat", "treo may")),
        ("SAC", ("sac", "sac pin", "bo sac", "cap sac", "sac khong vao")),
        ("PIN", ("pin", "hao pin", "chai pin", "sut pin")),
    )

    def __init__(self, categories: CategoryLookup) -> None:
        self._categories = categories

    def classify(self, issue_desc: str) -> IssueCategory:
        normalized = self._normalize(issue_desc)
        category_name = "KHAC"
        for candidate, keywords in self._KEYWORDS:
            if any(keyword in normalized for keyword in keywords):
                category_name = candidate
                break

        category = self._categories.get_active_by_name(category_name)
        if category is None:
            raise CategoryNotConfigured(category_name)
        return category

    @staticmethod
    def _normalize(value: str) -> str:
        decomposed = unicodedata.normalize("NFKD", value)
        without_diacritics = "".join(
            character for character in decomposed if not unicodedata.combining(character)
        )
        return " ".join(without_diacritics.casefold().split())