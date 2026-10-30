from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
from uuid import uuid4

import psycopg
import pytest
from dotenv import load_dotenv
from sqlalchemy import create_engine

from src.business.customer_service import (
    CustomerService,
    DuplicateRecord,
    ReferencedRecord,
)
from src.data_access.customer_repository import CustomerRepository


load_dotenv()
TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")
SCHEMA_SQL = Path(__file__).parents[1].joinpath("db", "schema.sql").read_text(
    encoding="utf-8"
)
SEED_SQL = Path(__file__).parents[1].joinpath("db", "seed.sql").read_text(
    encoding="utf-8"
)


@pytest.fixture(scope="session")
def isolated_schema() -> str:
    if not TEST_DATABASE_URL:
        pytest.skip("Set TEST_DATABASE_URL to run PostgreSQL constraint tests")

    schema_name = f"track_se_test_{uuid4().hex}"
    try:
        with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
            connection.execute(f'CREATE SCHEMA "{schema_name}"')
            connection.execute(f'SET search_path TO "{schema_name}"')
            connection.execute(SCHEMA_SQL, prepare=False)

        yield schema_name
    finally:
        with psycopg.connect(TEST_DATABASE_URL, autocommit=True) as connection:
            connection.execute(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE')


@pytest.fixture
def database(isolated_schema: str):
    connection = psycopg.connect(
        TEST_DATABASE_URL, options=f"-c search_path={isolated_schema}"
    )
    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


def add_customer(connection: psycopg.Connection, phone: str = "0900000001") -> int:
    row = connection.execute(
        "INSERT INTO customer (full_name, phone) VALUES (%s, %s) RETURNING customer_id",
        ("Khách kiểm thử", phone),
    ).fetchone()
    return row[0]


def add_device(
    connection: psycopg.Connection,
    customer_id: int,
    serial_no: str = "TEST-SERIAL-1",
) -> int:
    row = connection.execute(
        "INSERT INTO device (customer_id, model_name, serial_no) "
        "VALUES (%s, %s, %s) RETURNING device_id",
        (customer_id, "Điện thoại kiểm thử", serial_no),
    ).fetchone()
    return row[0]


def add_ticket(
    connection: psycopg.Connection,
    number: int,
    *,
    issue_desc: str = "Thiết bị không khởi động được",
    status: str = "MOI",
    priority: str = "TRUNG_BINH",
    warranty_status: str = "CHUA_XAC_MINH",
    received_at: datetime | None = None,
    due_date: datetime | None = None,
    customer_id: int | None = None,
) -> None:
    owner_id = customer_id or add_customer(
        connection, phone=f"09{number:08d}"
    )
    device_id = add_device(
        connection, owner_id, serial_no=f"TEST-SERIAL-{number}"
    )
    received = received_at or datetime(2026, 10, 19, 9, tzinfo=timezone.utc)
    due = due_date or received + timedelta(hours=72)
    connection.execute(
        "INSERT INTO ticket (ticket_code, customer_id, device_id, center_id, "
        "issue_desc, priority, status, warranty_status, received_by, received_at, due_date) "
        "VALUES (%s, %s, %s, 1, %s, %s, %s, %s, 1, %s, %s)",
        (
            f"TEST-{number}",
            owner_id,
            device_id,
            issue_desc,
            priority,
            status,
            warranty_status,
            received,
            due,
        ),
    )


def test_customer_phone_must_be_unique(database: psycopg.Connection) -> None:
    add_customer(database)

    with pytest.raises(psycopg.errors.UniqueViolation):
        add_customer(database)


def test_customer_phone_must_match_format(database: psycopg.Connection) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        add_customer(database, phone="12345")


def test_device_serial_must_be_unique(database: psycopg.Connection) -> None:
    customer_id = add_customer(database)
    add_device(database, customer_id)

    with pytest.raises(psycopg.errors.UniqueViolation):
        add_device(database, customer_id, serial_no="TEST-SERIAL-1")


def test_device_customer_foreign_key_must_exist(database: psycopg.Connection) -> None:
    with pytest.raises(psycopg.errors.ForeignKeyViolation):
        add_device(database, customer_id=999999)


def test_ticket_description_minimum_length(database: psycopg.Connection) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        add_ticket(database, 1, issue_desc="Quá ngắn")


def test_ticket_description_maximum_length(database: psycopg.Connection) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        add_ticket(database, 2, issue_desc="x" * 2001)


def test_ticket_due_date_cannot_precede_receipt(database: psycopg.Connection) -> None:
    received = datetime(2026, 10, 19, 9, tzinfo=timezone.utc)
    with pytest.raises(psycopg.errors.CheckViolation):
        add_ticket(
            database,
            3,
            received_at=received,
            due_date=received - timedelta(minutes=1),
        )


def test_ticket_status_must_be_in_lifecycle(database: psycopg.Connection) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        add_ticket(database, 4, status="KHONG_HOP_LE")


def test_ticket_priority_must_be_valid(database: psycopg.Connection) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        add_ticket(database, 5, priority="KHAN_CAP")


def test_ticket_warranty_status_must_be_valid(database: psycopg.Connection) -> None:
    with pytest.raises(psycopg.errors.CheckViolation):
        add_ticket(database, 6, warranty_status="KHONG_RO")


def test_device_cannot_have_two_open_tickets(database: psycopg.Connection) -> None:
    customer_id = add_customer(database)
    device_id = add_device(database, customer_id)
    received = datetime(2026, 10, 19, 9, tzinfo=timezone.utc)
    insert_ticket = (
        "INSERT INTO ticket (ticket_code, customer_id, device_id, center_id, "
        "issue_desc, priority, status, warranty_status, received_by, received_at, due_date) "
        "VALUES (%s, %s, %s, 1, 'Thiết bị không khởi động được', 'TRUNG_BINH', "
        "'MOI', 'CHUA_XAC_MINH', 1, %s, %s)"
    )
    database.execute(
        insert_ticket,
        ("TEST-7A", customer_id, device_id, received, received + timedelta(hours=72)),
    )

    with pytest.raises(psycopg.errors.UniqueViolation):
        database.execute(
            insert_ticket,
            ("TEST-7B", customer_id, device_id, received, received + timedelta(hours=72)),
        )


def test_schema_and_seed_can_be_applied_repeatedly(
    database: psycopg.Connection,
) -> None:
    database.execute(SCHEMA_SQL, prepare=False)
    database.execute(SEED_SQL, prepare=False)
    database.execute(SCHEMA_SQL, prepare=False)
    database.execute(SEED_SQL, prepare=False)

    assert database.execute(
        "SELECT count(*) FROM issue_category"
    ).fetchone()[0] == 6


def test_repository_crud_and_referenced_delete_guards(
    database: psycopg.Connection, isolated_schema: str
) -> None:
    engine = create_engine(
        TEST_DATABASE_URL,
        connect_args={"options": f"-c search_path={isolated_schema}"},
    )
    try:
        service = CustomerService(CustomerRepository(engine))
        customer = service.create_customer(
            "Khách tích hợp", "0900000091", "12 Lê Lợi"
        )
        assert service.list_customers("0900000091") == [customer]

        updated = service.update_customer(
            customer.customer_id, {"address": "Địa chỉ mới"}
        )
        assert updated.address == "Địa chỉ mới"
        with pytest.raises(DuplicateRecord):
            service.create_customer("Khách trùng", "0900000091", None)

        device = service.create_device(
            customer.customer_id,
            "Điện thoại tích hợp",
            "INTEGRATION-91",
            None,
            12,
            "Khách mang đến",
        )
        with pytest.raises(ReferencedRecord):
            service.delete_customer(customer.customer_id)
        assert service.delete_device(device.device_id) is None

        ticket_device = service.create_device(
            customer.customer_id,
            "Điện thoại có phiếu",
            "INTEGRATION-92",
            None,
            12,
            "Khách mang đến",
        )
        received = datetime(2026, 10, 19, 9, tzinfo=timezone.utc)
        database.execute(
            "INSERT INTO ticket (ticket_code, customer_id, device_id, center_id, "
            "issue_desc, priority, status, warranty_status, received_by, received_at, due_date) "
            "VALUES (%s, %s, %s, 1, %s, %s, %s, %s, 1, %s, %s)",
            (
                "INTEGRATION-91",
                customer.customer_id,
                ticket_device.device_id,
                "Thiết bị không hoạt động",
                "TRUNG_BINH",
                "MOI",
                "CHUA_XAC_MINH",
                received,
                received + timedelta(hours=72),
            ),
        )
        database.commit()
        with pytest.raises(ReferencedRecord):
            service.delete_device(ticket_device.device_id)
    finally:
        engine.dispose()