from fastapi import Depends, FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator
from pathlib import Path

from src.business.auth_service import (
    AuthService,
    InvalidAccessToken,
    InvalidCredentials,
    auth_service_from_environment,
)
from src.business.classify_service import (
    CategoryNotConfigured,
    CategoryLookup,
    ClassifyService,
)
from src.data_access.issue_category_repository import repository_from_environment


class ClassifyRequest(BaseModel):
    issue_desc: str = Field(min_length=10, max_length=2000)

    @field_validator("issue_desc", mode="before")
    @classmethod
    def trim_issue_description(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value


class ClassifyResponse(BaseModel):
    category_id: int
    category_name: str
    priority: str


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AuthenticationRequired(Exception):
    pass


def create_app(
    categories: CategoryLookup | None = None,
    auth_service: AuthService | None = None,
) -> FastAPI:
    app = FastAPI(title="Smart CRM API", version="0.1.0")
    static_directory = Path(__file__).with_name("static")
    app.mount("/static", StaticFiles(directory=static_directory), name="static")
    category_lookup = categories or repository_from_environment()
    classifier = ClassifyService(category_lookup) if category_lookup else None
    authenticator = auth_service or auth_service_from_environment()
    bearer_scheme = HTTPBearer(auto_error=False)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        request, exc: RequestValidationError
    ) -> JSONResponse:
        fields: dict[str, list[str]] = {}
        for error in exc.errors():
            location = [
                str(part)
                for part in error["loc"]
                if part not in {"body", "query", "path"}
            ]
            field = ".".join(location) or "body"
            fields.setdefault(field, []).append(error["msg"])
        return JSONResponse(
            status_code=400,
            content={
                "error": {
                    "code": "VALIDATION_FAILED",
                    "message": "Dữ liệu yêu cầu không hợp lệ",
                    "fields": fields,
                }
            },
        )

    @app.exception_handler(AuthenticationRequired)
    async def authentication_error_handler(request, exc) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Phiên đăng nhập không hợp lệ hoặc đã hết hạn",
                    "fields": {},
                }
            },
            headers={"WWW-Authenticate": "Bearer"},
        )

    def require_authentication(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> dict[str, object]:
        if authenticator is None:
            raise AuthenticationRequired
        if credentials is None:
            raise AuthenticationRequired
        try:
            return authenticator.verify_access_token(credentials.credentials)
        except InvalidAccessToken as error:
            raise AuthenticationRequired from error

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/login", include_in_schema=False)
    def login_page() -> FileResponse:
        return FileResponse(static_directory / "login.html")

    @app.post("/api/auth/login", response_model=LoginResponse)
    def login(request: LoginRequest) -> LoginResponse | JSONResponse:
        if authenticator is None:
            return JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "code": "AUTH_NOT_CONFIGURED",
                        "message": "Chưa cấu hình tài khoản demo và JWT_SECRET_KEY",
                        "fields": {},
                    }
                },
            )
        try:
            token = authenticator.login(request.username, request.password)
        except InvalidCredentials:
            return JSONResponse(
                status_code=401,
                content={
                    "error": {
                        "code": "INVALID_CREDENTIALS",
                        "message": "Tên đăng nhập hoặc mật khẩu không đúng",
                        "fields": {},
                    }
                },
                headers={"WWW-Authenticate": "Bearer"},
            )
        return LoginResponse(
            access_token=token,
            expires_in=authenticator.token_lifetime_seconds,
        )

    @app.post(
        "/api/classify",
        response_model=ClassifyResponse,
        dependencies=[Depends(require_authentication)],
    )
    def classify(request: ClassifyRequest) -> ClassifyResponse | JSONResponse:
        if classifier is None:
            return JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "code": "DATABASE_NOT_CONFIGURED",
                        "message": "Cần cấu hình DATABASE_URL để tra danh mục sự cố",
                        "fields": {},
                    }
                },
            )
        try:
            category = classifier.classify(request.issue_desc)
        except CategoryNotConfigured as error:
            return JSONResponse(
                status_code=503,
                content={
                    "error": {
                        "code": "CATEGORY_NOT_CONFIGURED",
                        "message": f"Danh mục {error.args[0]} chưa được cấu hình",
                        "fields": {},
                    }
                },
            )
        return ClassifyResponse(
            category_id=category.category_id,
            category_name=category.category_name,
            priority=category.default_priority,
        )

    return app


app = create_app()