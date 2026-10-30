from datetime import date
from pathlib import Path
import time
from typing import Annotated
from uuid import uuid4

from fastapi import Depends, FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.params import Path as PathParameter
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy.exc import SQLAlchemyError

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
from src.business.customer_service import (
    Customer,
    CustomerService,
    CustomerServiceError,
    CustomerStore,
    Device,
)
from src.data_access.customer_repository import customer_repository_from_environment
from src.data_access.issue_category_repository import repository_from_environment
from src.presentation.logging_config import configure_logging


logger = configure_logging()


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


class CustomerCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str = Field(max_length=120)
    phone: str = Field(max_length=20)
    address: str | None = Field(default=None, max_length=255)


class CustomerUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    full_name: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=20)
    address: str | None = Field(default=None, max_length=255)


class CustomerResponse(BaseModel):
    customer_id: int
    full_name: str
    phone: str
    address: str | None


class DeviceCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: str = Field(max_length=120)
    serial_no: str = Field(max_length=50)
    purchase_date: date | None = None
    warranty_months: int = Field(default=12, ge=1, le=32767)
    note: str = Field(max_length=255)


class DeviceUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    model_name: str | None = Field(default=None, max_length=120)
    serial_no: str | None = Field(default=None, max_length=50)
    purchase_date: date | None = None
    warranty_months: int | None = Field(default=None, ge=1, le=32767)
    note: str | None = Field(default=None, max_length=255)


class DeviceResponse(BaseModel):
    device_id: int
    customer_id: int
    model_name: str
    serial_no: str
    purchase_date: date | None
    warranty_months: int
    note: str | None


class AuthenticationRequired(Exception):
    pass


class CustomerServiceUnavailable(Exception):
    pass


def customer_response(customer: Customer) -> CustomerResponse:
    masked_phone = f"{customer.phone[:3]}****{customer.phone[-3:]}"
    return CustomerResponse(
        customer_id=customer.customer_id,
        full_name=customer.full_name,
        phone=masked_phone,
        address=customer.address,
    )


def create_app(
    categories: CategoryLookup | None = None,
    auth_service: AuthService | None = None,
    customer_store: CustomerStore | None = None,
) -> FastAPI:
    app = FastAPI(title="Smart CRM API", version="0.1.0")
    static_directory = Path(__file__).with_name("static")
    app.mount("/static", StaticFiles(directory=static_directory), name="static")
    category_lookup = categories or repository_from_environment()
    classifier = ClassifyService(category_lookup) if category_lookup else None
    authenticator = auth_service or auth_service_from_environment()
    store = customer_store or customer_repository_from_environment()
    customer_service = CustomerService(store) if store is not None else None
    bearer_scheme = HTTPBearer(auto_error=False)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(
        _request: Request, exc: RequestValidationError
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
    async def authentication_error_handler(
        _request: Request, _exc: AuthenticationRequired
    ) -> JSONResponse:
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

    @app.exception_handler(CustomerServiceError)
    async def customer_service_error_handler(
        _request: Request, exc: CustomerServiceError
    ) -> JSONResponse:
        fields = {exc.field: [str(exc)]} if exc.field else {}
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": {
                    "code": exc.code,
                    "message": str(exc),
                    "fields": fields,
                }
            },
        )

    @app.exception_handler(CustomerServiceUnavailable)
    async def customer_service_unavailable_handler(
        _request: Request, _exc: CustomerServiceUnavailable
    ) -> JSONResponse:
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "DATABASE_NOT_CONFIGURED",
                    "message": "Cần cấu hình DATABASE_URL để quản lý khách hàng và thiết bị",
                    "fields": {},
                }
            },
        )

    @app.exception_handler(SQLAlchemyError)
    async def database_error_handler(
        request: Request, exc: SQLAlchemyError
    ) -> JSONResponse:
        logger.error(
            "Database request failed (%s)",
            type(exc).__name__,
            extra={"request_id": getattr(request.state, "request_id", None)},
        )
        return JSONResponse(
            status_code=503,
            content={
                "error": {
                    "code": "DATABASE_UNAVAILABLE",
                    "message": "Không thể truy cập cơ sở dữ liệu. Vui lòng thử lại sau.",
                    "fields": {},
                }
            },
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

    @app.middleware("http")
    async def log_request(request: Request, call_next):
        request_id = uuid4().hex
        request.state.request_id = request_id
        started = time.perf_counter()
        response = await call_next(request)
        response.headers["X-Request-Id"] = request_id
        logger.info(
            "request.completed",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round((time.perf_counter() - started) * 1000, 2),
            },
        )
        return response

    def require_customer_service() -> CustomerService:
        if customer_service is None:
            raise CustomerServiceUnavailable
        return customer_service

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get("/", include_in_schema=False)
    def home() -> RedirectResponse:
        return RedirectResponse(url="/login")

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

    @app.get(
        "/api/customers",
        response_model=list[CustomerResponse],
        dependencies=[Depends(require_authentication)],
    )
    def list_customers(
        phone: str | None = None,
        service: CustomerService = Depends(require_customer_service),
    ) -> list[CustomerResponse]:
        return [customer_response(item) for item in service.list_customers(phone)]

    @app.post(
        "/api/customers",
        response_model=CustomerResponse,
        status_code=201,
        dependencies=[Depends(require_authentication)],
    )
    def create_customer(
        request: CustomerCreateRequest,
        service: CustomerService = Depends(require_customer_service),
    ) -> CustomerResponse:
        return customer_response(
            service.create_customer(
                request.full_name, request.phone, request.address
            )
        )

    @app.get(
        "/api/customers/{customer_id}",
        response_model=CustomerResponse,
        dependencies=[Depends(require_authentication)],
    )
    def get_customer(
        customer_id: Annotated[int, PathParameter(ge=1)],
        service: CustomerService = Depends(require_customer_service),
    ) -> CustomerResponse:
        return customer_response(service.get_customer(customer_id))

    @app.patch(
        "/api/customers/{customer_id}",
        response_model=CustomerResponse,
        dependencies=[Depends(require_authentication)],
    )
    def update_customer(
        request: CustomerUpdateRequest,
        customer_id: Annotated[int, PathParameter(ge=1)],
        service: CustomerService = Depends(require_customer_service),
    ) -> CustomerResponse:
        return customer_response(
            service.update_customer(
                customer_id, request.model_dump(exclude_unset=True)
            )
        )

    @app.delete(
        "/api/customers/{customer_id}",
        status_code=204,
        dependencies=[Depends(require_authentication)],
    )
    def delete_customer(
        customer_id: Annotated[int, PathParameter(ge=1)],
        service: CustomerService = Depends(require_customer_service),
    ) -> Response:
        service.delete_customer(customer_id)
        return Response(status_code=204)

    @app.get(
        "/api/customers/{customer_id}/devices",
        response_model=list[DeviceResponse],
        dependencies=[Depends(require_authentication)],
    )
    def list_devices(
        customer_id: Annotated[int, PathParameter(ge=1)],
        service: CustomerService = Depends(require_customer_service),
    ) -> list[Device]:
        return service.list_devices(customer_id)

    @app.post(
        "/api/customers/{customer_id}/devices",
        response_model=DeviceResponse,
        status_code=201,
        dependencies=[Depends(require_authentication)],
    )
    def create_device(
        request: DeviceCreateRequest,
        customer_id: Annotated[int, PathParameter(ge=1)],
        service: CustomerService = Depends(require_customer_service),
    ) -> Device:
        return service.create_device(
            customer_id,
            request.model_name,
            request.serial_no,
            request.purchase_date,
            request.warranty_months,
            request.note,
        )

    @app.get(
        "/api/devices/{device_id}",
        response_model=DeviceResponse,
        dependencies=[Depends(require_authentication)],
    )
    def get_device(
        device_id: Annotated[int, PathParameter(ge=1)],
        service: CustomerService = Depends(require_customer_service),
    ) -> Device:
        return service.get_device(device_id)

    @app.patch(
        "/api/devices/{device_id}",
        response_model=DeviceResponse,
        dependencies=[Depends(require_authentication)],
    )
    def update_device(
        request: DeviceUpdateRequest,
        device_id: Annotated[int, PathParameter(ge=1)],
        service: CustomerService = Depends(require_customer_service),
    ) -> Device:
        return service.update_device(
            device_id, request.model_dump(exclude_unset=True)
        )

    @app.delete(
        "/api/devices/{device_id}",
        status_code=204,
        dependencies=[Depends(require_authentication)],
    )
    def delete_device(
        device_id: Annotated[int, PathParameter(ge=1)],
        service: CustomerService = Depends(require_customer_service),
    ) -> Response:
        service.delete_device(device_id)
        return Response(status_code=204)

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