from dataclasses import dataclass
from datetime import date
from typing import Protocol


@dataclass(frozen=True)
class Customer:
    customer_id: int
    full_name: str
    phone: str
    address: str | None


@dataclass(frozen=True)
class Device:
    device_id: int
    customer_id: int
    model_name: str
    serial_no: str
    purchase_date: date | None
    warranty_months: int
    note: str | None
    priority: str | None = None


class CustomerStore(Protocol):
    def list_customers(self, phone: str | None = None) -> list[Customer]: ...

    def get_customer(self, customer_id: int) -> Customer | None: ...

    def create_customer(
        self, full_name: str, phone: str, address: str | None
    ) -> Customer: ...

    def update_customer(
        self, customer_id: int, changes: dict[str, object]
    ) -> Customer | None: ...

    def customer_has_devices(self, customer_id: int) -> bool: ...

    def customer_has_tickets(self, customer_id: int) -> bool: ...

    def delete_customer(self, customer_id: int) -> bool: ...

    def list_devices(self, customer_id: int) -> list[Device]: ...

    def get_device(self, device_id: int) -> Device | None: ...

    def create_device(
        self,
        customer_id: int,
        model_name: str,
        serial_no: str,
        purchase_date: date | None,
        warranty_months: int,
        note: str,
    ) -> Device: ...

    def update_device(
        self, device_id: int, changes: dict[str, object]
    ) -> Device | None: ...

    def device_has_tickets(self, device_id: int) -> bool: ...

    def delete_device(self, device_id: int) -> bool: ...


class CustomerServiceError(Exception):
    status_code = 400
    code = "VALIDATION_FAILED"

    def __init__(
        self, message: str, field: str | None = None, code: str | None = None
    ) -> None:
        super().__init__(message)
        self.field = field
        if code is not None:
            self.code = code


class CustomerNotFound(CustomerServiceError):
    status_code = 404
    code = "CUSTOMER_NOT_FOUND"


class DeviceNotFound(CustomerServiceError):
    status_code = 404
    code = "DEVICE_NOT_FOUND"


class DuplicateRecord(CustomerServiceError):
    status_code = 409
    code = "DUPLICATE_RECORD"


class ReferencedRecord(CustomerServiceError):
    status_code = 409
    code = "RECORD_IN_USE"


class CustomerService:
    def __init__(self, store: CustomerStore) -> None:
        self._store = store

    def list_customers(self, phone: str | None = None) -> list[Customer]:
        if phone is not None:
            phone = self._validate_phone(phone)
        return self._store.list_customers(phone)

    def get_customer(self, customer_id: int) -> Customer:
        customer = self._store.get_customer(customer_id)
        if customer is None:
            raise CustomerNotFound("Không tìm thấy khách hàng")
        return customer

    def create_customer(
        self, full_name: str, phone: str, address: str | None
    ) -> Customer:
        name = self._validate_text(full_name, "full_name", 120)
        normalized_phone = self._validate_phone(phone)
        normalized_address = self._validate_optional_text(address, "address", 255)
        try:
            return self._store.create_customer(
                name, normalized_phone, normalized_address
            )
        except DuplicateRecord as error:
            raise DuplicateRecord(
                "Số điện thoại đã được đăng ký", "phone", "PHONE_EXISTS"
            ) from error

    def update_customer(
        self, customer_id: int, changes: dict[str, object]
    ) -> Customer:
        self.get_customer(customer_id)
        if not changes:
            raise CustomerServiceError("Cần cung cấp ít nhất một trường để cập nhật")

        normalized: dict[str, object] = {}
        if "full_name" in changes:
            value = changes["full_name"]
            if not isinstance(value, str):
                raise CustomerServiceError("Họ tên phải là chuỗi", "full_name")
            normalized["full_name"] = self._validate_text(
                value, "full_name", 120
            )
        if "phone" in changes:
            value = changes["phone"]
            if not isinstance(value, str):
                raise CustomerServiceError("Số điện thoại phải là chuỗi", "phone")
            normalized["phone"] = self._validate_phone(value)
        if "address" in changes:
            value = changes["address"]
            if value is not None and not isinstance(value, str):
                raise CustomerServiceError("Địa chỉ phải là chuỗi", "address")
            normalized["address"] = self._validate_optional_text(
                value, "address", 255
            )
        try:
            updated = self._store.update_customer(customer_id, normalized)
        except DuplicateRecord as error:
            raise DuplicateRecord(
                "Số điện thoại đã được đăng ký", "phone", "PHONE_EXISTS"
            ) from error
        if updated is None:
            raise CustomerNotFound("Không tìm thấy khách hàng")
        return updated

    def delete_customer(self, customer_id: int) -> None:
        self.get_customer(customer_id)
        if self._store.customer_has_devices(customer_id):
            raise ReferencedRecord(
                "Không thể xóa khách hàng còn thiết bị", code="CUSTOMER_HAS_DEVICES"
            )
        if self._store.customer_has_tickets(customer_id):
            raise ReferencedRecord(
                "Không thể xóa khách hàng đã có phiếu bảo hành",
                code="CUSTOMER_HAS_TICKETS",
            )
        if not self._store.delete_customer(customer_id):
            raise ReferencedRecord(
                "Bản ghi đang được dữ liệu khác sử dụng", code="RECORD_IN_USE"
            )

    def list_devices(self, customer_id: int) -> list[Device]:
        self.get_customer(customer_id)
        return self._store.list_devices(customer_id)

    def get_device(self, device_id: int) -> Device:
        device = self._store.get_device(device_id)
        if device is None:
            raise DeviceNotFound("Không tìm thấy thiết bị")
        return device

    def create_device(
        self,
        customer_id: int,
        model_name: str,
        serial_no: str,
        purchase_date: date | None,
        warranty_months: int,
        note: str,
    ) -> Device:
        self.get_customer(customer_id)
        model = self._validate_text(model_name, "model_name", 120)
        serial = self._validate_text(serial_no, "serial_no", 50)
        normalized_note = self._validate_text(note, "note", 255)
        if warranty_months < 1 or warranty_months > 32767:
            raise CustomerServiceError(
                "Thời hạn bảo hành phải từ 1 đến 32767 tháng", "warranty_months"
            )
        try:
            return self._store.create_device(
                customer_id,
                model,
                serial,
                purchase_date,
                warranty_months,
                normalized_note,
            )
        except DuplicateRecord as error:
            raise DuplicateRecord(
                "Serial/IMEI đã được đăng ký", "serial_no", "SERIAL_EXISTS"
            ) from error

    def update_device(
        self, device_id: int, changes: dict[str, object]
    ) -> Device:
        self.get_device(device_id)
        if not changes:
            raise CustomerServiceError("Cần cung cấp ít nhất một trường để cập nhật")

        normalized: dict[str, object] = {}
        for field, maximum in (("model_name", 120), ("serial_no", 50)):
            if field in changes:
                value = changes[field]
                if not isinstance(value, str):
                    raise CustomerServiceError(f"{field} phải là chuỗi", field)
                normalized[field] = self._validate_text(value, field, maximum)
        if "purchase_date" in changes:
            value = changes["purchase_date"]
            if value is not None and not isinstance(value, date):
                raise CustomerServiceError(
                    "Ngày mua không hợp lệ", "purchase_date"
                )
            normalized["purchase_date"] = value
        if "warranty_months" in changes:
            value = changes["warranty_months"]
            if not isinstance(value, int) or value < 1 or value > 32767:
                raise CustomerServiceError(
                    "Thời hạn bảo hành phải từ 1 đến 32767 tháng",
                    "warranty_months",
                )
            normalized["warranty_months"] = value
        if "note" in changes:
            value = changes["note"]
            if value is not None and not isinstance(value, str):
                raise CustomerServiceError("Ghi chú phải là chuỗi", "note")
            normalized["note"] = self._validate_optional_text(value, "note", 255)
        try:
            updated = self._store.update_device(device_id, normalized)
        except DuplicateRecord as error:
            raise DuplicateRecord(
                "Serial/IMEI đã được đăng ký", "serial_no", "SERIAL_EXISTS"
            ) from error
        if updated is None:
            raise DeviceNotFound("Không tìm thấy thiết bị")
        return updated

    def delete_device(self, device_id: int) -> None:
        self.get_device(device_id)
        if self._store.device_has_tickets(device_id):
            raise ReferencedRecord(
                "Không thể xóa thiết bị đã có phiếu bảo hành",
                code="DEVICE_HAS_TICKETS",
            )
        if not self._store.delete_device(device_id):
            raise ReferencedRecord(
                "Bản ghi đang được dữ liệu khác sử dụng", code="RECORD_IN_USE"
            )

    @staticmethod
    def _validate_text(value: str, field: str, maximum: int) -> str:
        normalized = value.strip()
        if not normalized:
            raise CustomerServiceError("Trường này không được để trống", field)
        if len(normalized) > maximum:
            raise CustomerServiceError(
                f"Trường này không được vượt quá {maximum} ký tự", field
            )
        return normalized

    @classmethod
    def _validate_phone(cls, phone: str) -> str:
        normalized = phone.strip()
        if len(normalized) != 10 or not normalized.isascii() or not normalized.isdigit() or not normalized.startswith("0"):
            raise CustomerServiceError(
                "Số điện thoại phải gồm 10 chữ số và bắt đầu bằng 0", "phone"
            )
        return normalized

    @classmethod
    def _validate_optional_text(
        cls, value: str | None, field: str, maximum: int
    ) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if len(normalized) > maximum:
            raise CustomerServiceError(
                f"Trường này không được vượt quá {maximum} ký tự", field
            )
        return normalized or None
