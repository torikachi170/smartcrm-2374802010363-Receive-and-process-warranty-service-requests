from datetime import date

import pytest
from fastapi.testclient import TestClient

from src.business.auth_service import AuthService
from src.business.customer_service import Customer, Device
from src.presentation.api import create_app


class InMemoryCustomerStore:
    def __init__(self) -> None:
        self.customers: dict[int, Customer] = {}
        self.devices: dict[int, Device] = {}
        self.ticket_customer_ids: set[int] = set()
        self.ticket_device_ids: set[int] = set()
        self._next_customer_id = 1
        self._next_device_id = 1

    def list_customers(self, phone: str | None = None) -> list[Customer]:
        values = list(self.customers.values())
        return [item for item in values if phone is None or item.phone == phone]

    def get_customer(self, customer_id: int) -> Customer | None:
        return self.customers.get(customer_id)

    def create_customer(
        self, full_name: str, phone: str, address: str | None
    ) -> Customer:
        if any(item.phone == phone for item in self.customers.values()):
            from src.business.customer_service import DuplicateRecord

            raise DuplicateRecord("duplicate phone")
        customer = Customer(self._next_customer_id, full_name, phone, address)
        self.customers[customer.customer_id] = customer
        self._next_customer_id += 1
        return customer

    def update_customer(
        self, customer_id: int, changes: dict[str, object]
    ) -> Customer | None:
        customer = self.customers.get(customer_id)
        if customer is None:
            return None
        updated = Customer(**(customer.__dict__ | changes))
        self.customers[customer_id] = updated
        return updated

    def customer_has_devices(self, customer_id: int) -> bool:
        return any(item.customer_id == customer_id for item in self.devices.values())

    def customer_has_tickets(self, customer_id: int) -> bool:
        return customer_id in self.ticket_customer_ids

    def delete_customer(self, customer_id: int) -> bool:
        return self.customers.pop(customer_id, None) is not None

    def list_devices(self, customer_id: int) -> list[Device]:
        return [
            item
            for item in self.devices.values()
            if item.customer_id == customer_id
        ]

    def get_device(self, device_id: int) -> Device | None:
        return self.devices.get(device_id)

    def create_device(
        self,
        customer_id: int,
        model_name: str,
        serial_no: str,
        purchase_date: date | None,
        warranty_months: int,
        note: str,
    ) -> Device:
        from src.business.customer_service import DuplicateRecord

        if any(item.serial_no == serial_no for item in self.devices.values()):
            raise DuplicateRecord("duplicate serial")
        device = Device(
            self._next_device_id,
            customer_id,
            model_name,
            serial_no,
            purchase_date,
            warranty_months,
            note,
        )
        self.devices[device.device_id] = device
        self._next_device_id += 1
        return device

    def update_device(
        self, device_id: int, changes: dict[str, object]
    ) -> Device | None:
        device = self.devices.get(device_id)
        if device is None:
            return None
        updated = Device(**(device.__dict__ | changes))
        self.devices[device_id] = updated
        return updated

    def device_has_tickets(self, device_id: int) -> bool:
        return device_id in self.ticket_device_ids

    def delete_device(self, device_id: int) -> bool:
        return self.devices.pop(device_id, None) is not None


@pytest.fixture
def api_client() -> tuple[TestClient, InMemoryCustomerStore]:
    auth_service = AuthService(
        "demo", "demo-password", "test-secret-key-that-is-at-least-32-chars"
    )
    store = InMemoryCustomerStore()
    return TestClient(create_app(auth_service=auth_service, customer_store=store)), store


def headers(client: TestClient) -> dict[str, str]:
    response = client.post(
        "/api/auth/login",
        json={"username": "demo", "password": "demo-password"},
    )
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


def create_customer(client: TestClient, phone: str = "0900000001") -> int:
    response = client.post(
        "/api/customers",
        json={"full_name": "  Khách kiểm thử ", "phone": phone},
        headers=headers(client),
    )
    assert response.status_code == 201
    return response.json()["customer_id"]


def test_customer_crud_and_delete_unreferenced_record(
    api_client: tuple[TestClient, InMemoryCustomerStore],
) -> None:
    client, _ = api_client
    customer_id = create_customer(client)
    listing = client.get("/api/customers", headers=headers(client))
    assert listing.status_code == 200
    assert listing.json()[0]["full_name"] == "Khách kiểm thử"
    assert listing.json()[0]["phone"] == "090****001"

    updated = client.patch(
        f"/api/customers/{customer_id}",
        json={"address": "  12 Lê Lợi  "},
        headers=headers(client),
    )
    assert updated.status_code == 200
    assert updated.json()["address"] == "12 Lê Lợi"
    assert client.get(
        f"/api/customers/{customer_id}", headers=headers(client)
    ).status_code == 200

    deleted = client.delete(
        f"/api/customers/{customer_id}", headers=headers(client)
    )
    assert deleted.status_code == 204
    assert client.get(
        f"/api/customers/{customer_id}", headers=headers(client)
    ).status_code == 404


def test_customer_duplicate_phone_returns_conflict(
    api_client: tuple[TestClient, InMemoryCustomerStore],
) -> None:
    client, _ = api_client
    create_customer(client)
    response = client.post(
        "/api/customers",
        json={"full_name": "Khách khác", "phone": "0900000001"},
        headers=headers(client),
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "PHONE_EXISTS"


def test_customer_invalid_phone_returns_validation_error(
    api_client: tuple[TestClient, InMemoryCustomerStore],
) -> None:
    client, _ = api_client
    response = client.post(
        "/api/customers",
        json={"full_name": "Khách lỗi", "phone": "123"},
        headers=headers(client),
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "VALIDATION_FAILED"


def test_customer_with_device_cannot_be_deleted(
    api_client: tuple[TestClient, InMemoryCustomerStore],
) -> None:
    client, _ = api_client
    customer_id = create_customer(client)
    client.post(
        f"/api/customers/{customer_id}/devices",
        json={
            "model_name": "Điện thoại",
            "serial_no": "SERIAL-1",
            "note": "Khách mang đến",
        },
        headers=headers(client),
    )
    response = client.delete(
        f"/api/customers/{customer_id}", headers=headers(client)
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CUSTOMER_HAS_DEVICES"


def test_customer_with_ticket_cannot_be_deleted(
    api_client: tuple[TestClient, InMemoryCustomerStore],
) -> None:
    client, store = api_client
    customer_id = create_customer(client, "0900000004")
    store.ticket_customer_ids.add(customer_id)

    response = client.delete(
        f"/api/customers/{customer_id}", headers=headers(client)
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "CUSTOMER_HAS_TICKETS"


def test_device_crud_and_delete_unreferenced_record(
    api_client: tuple[TestClient, InMemoryCustomerStore],
) -> None:
    client, store = api_client
    customer_id = create_customer(client, "0900000002")
    created = client.post(
        f"/api/customers/{customer_id}/devices",
        json={
            "model_name": "Điện thoại",
            "serial_no": "SERIAL-2",
            "purchase_date": "2026-10-30",
            "warranty_months": 18,
            "note": "Khách mang đến",
        },
        headers=headers(client),
    )
    assert created.status_code == 201
    device_id = created.json()["device_id"]
    listing = client.get(
        f"/api/customers/{customer_id}/devices", headers=headers(client)
    )
    assert listing.json()[0]["priority"] is None

    store.devices[device_id] = Device(
        **(store.devices[device_id].__dict__ | {"priority": "CAO"})
    )
    listing = client.get(
        f"/api/customers/{customer_id}/devices", headers=headers(client)
    )
    assert listing.json()[0]["serial_no"] == "SERIAL-2"
    assert listing.json()[0]["priority"] == "CAO"

    updated = client.patch(
        f"/api/devices/{device_id}",
        json={"model_name": "Model mới"},
        headers=headers(client),
    )
    assert updated.status_code == 200
    assert updated.json()["model_name"] == "Model mới"
    assert client.get(
        f"/api/devices/{device_id}", headers=headers(client)
    ).status_code == 200

    deleted = client.delete(f"/api/devices/{device_id}", headers=headers(client))
    assert deleted.status_code == 204


def test_device_with_ticket_cannot_be_deleted(
    api_client: tuple[TestClient, InMemoryCustomerStore],
) -> None:
    client, store = api_client
    customer_id = create_customer(client, "0900000003")
    device = client.post(
        f"/api/customers/{customer_id}/devices",
        json={
            "model_name": "Điện thoại",
            "serial_no": "SERIAL-3",
            "note": "Khách mang đến",
        },
        headers=headers(client),
    ).json()
    store.ticket_device_ids.add(device["device_id"])

    response = client.delete(
        f"/api/devices/{device['device_id']}", headers=headers(client)
    )
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "DEVICE_HAS_TICKETS"


def test_customer_endpoints_require_login(
    api_client: tuple[TestClient, InMemoryCustomerStore],
) -> None:
    client, _ = api_client
    response = client.get("/api/customers")
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "UNAUTHORIZED"
