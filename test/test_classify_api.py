from fastapi.testclient import TestClient

from src.business.auth_service import AuthService
from src.business.classify_service import IssueCategory
from src.presentation.api import create_app


class InMemoryCategories:
    _CATEGORIES = {
        "MAN_HINH": IssueCategory(1, "MAN_HINH", "CAO"),
        "PIN": IssueCategory(2, "PIN", "TRUNG_BINH"),
        "SAC": IssueCategory(3, "SAC", "TRUNG_BINH"),
        "PHAN_MEM": IssueCategory(4, "PHAN_MEM", "TRUNG_BINH"),
        "NUOC_VAO": IssueCategory(5, "NUOC_VAO", "CAO"),
        "KHAC": IssueCategory(6, "KHAC", "THAP"),
    }

    def get_active_by_name(self, category_name: str) -> IssueCategory | None:
        return self._CATEGORIES.get(category_name)


auth_service = AuthService(
    "demo", "demo-password", "test-secret-key-that-is-at-least-32-chars"
)
client = TestClient(create_app(InMemoryCategories(), auth_service))


def authorization_headers() -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"username": "demo", "password": "demo-password"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def test_login_returns_bearer_token() -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "demo", "password": "demo-password"},
    )

    assert response.status_code == 200
    assert response.json()["token_type"] == "bearer"
    assert response.json()["expires_in"] == 1800


def test_login_rejects_invalid_credentials() -> None:
    response = client.post(
        "/api/auth/login",
        json={"username": "demo", "password": "incorrect"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_protected_endpoint_requires_access_token() -> None:
    response = client.post(
        "/api/classify", json={"issue_desc": "Máy sạc không vào"}
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_protected_endpoint_rejects_invalid_access_token() -> None:
    response = client.post(
        "/api/classify",
        json={"issue_desc": "Máy sạc không vào"},
        headers={"Authorization": "Bearer invalid-token"},
    )

    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"


def test_login_reports_missing_auth_configuration(monkeypatch) -> None:
    monkeypatch.setattr("src.presentation.api.auth_service_from_environment", lambda: None)

    response = TestClient(create_app()).post(
        "/api/auth/login",
        json={"username": "demo", "password": "demo-password"},
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "AUTH_NOT_CONFIGURED"


def test_classify_returns_category_and_default_priority() -> None:
    response = client.post(
        "/api/classify",
        json={"issue_desc": "Máy sạc không vào"},
        headers=authorization_headers(),
    )

    assert response.status_code == 200
    assert response.json() == {
        "category_id": 3,
        "category_name": "SAC",
        "priority": "TRUNG_BINH",
    }


def test_classify_falls_back_to_other_category() -> None:
    response = client.post(
        "/api/classify",
        json={"issue_desc": "Loa rè khi gọi điện thoại"},
        headers=authorization_headers(),
    )

    assert response.status_code == 200
    assert response.json()["category_name"] == "KHAC"


def test_classify_rejects_short_description_with_contract_status() -> None:
    response = client.post(
        "/api/classify",
        json={"issue_desc": "Máy hỏng"},
        headers=authorization_headers(),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"
    assert "issue_desc" in response.json()["error"]["fields"]


def test_classify_rejects_description_over_contract_limit() -> None:
    response = client.post(
        "/api/classify",
        json={"issue_desc": "x" * 2001},
        headers=authorization_headers(),
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_unconfigured_database_returns_standard_error_envelope(
    monkeypatch, tmp_path
) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setattr(
        "src.presentation.api.repository_from_environment", lambda: None
    )
    response = TestClient(create_app(auth_service=auth_service)).post(
        "/api/classify",
        json={"issue_desc": "Mô tả lỗi hợp lệ để phân loại"},
        headers=authorization_headers(),
    )

    assert response.status_code == 503
    assert response.json()["error"]["code"] == "DATABASE_NOT_CONFIGURED"


def test_health_check_remains_available() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_login_page_and_assets_are_served() -> None:
    page = client.get("/login")
    stylesheet = client.get("/static/login.css")
    script = client.get("/static/login.js")

    assert page.status_code == 200
    assert "id=\"login-form\"" in page.text
    assert "Kết quả đề xuất sẽ hiển thị ở đây sau khi gửi mô tả." in page.text
    assert 'class="result empty"' in page.text
    assert stylesheet.status_code == 200
    assert ".result.empty, .result.loading" in stylesheet.text
    assert script.status_code == 200