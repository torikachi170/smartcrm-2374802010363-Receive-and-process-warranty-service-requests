import os
from datetime import date

from dotenv import load_dotenv
from sqlalchemy import Engine, create_engine, text
from sqlalchemy.exc import IntegrityError

from src.business.customer_service import Customer, Device, DuplicateRecord


class CustomerRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def list_customers(self, phone: str | None = None) -> list[Customer]:
        where_clause = "WHERE phone = :phone " if phone is not None else ""
        statement = text(
            "SELECT customer_id, full_name, phone, address "
            f"FROM customer {where_clause}ORDER BY customer_id"
        )
        with self._engine.connect() as connection:
            parameters = {"phone": phone} if phone is not None else {}
            rows = connection.execute(statement, parameters).mappings().all()
        return [self._customer(row) for row in rows]

    def get_customer(self, customer_id: int) -> Customer | None:
        statement = text(
            "SELECT customer_id, full_name, phone, address "
            "FROM customer WHERE customer_id = :customer_id"
        )
        with self._engine.connect() as connection:
            row = (
                connection.execute(statement, {"customer_id": customer_id})
                .mappings()
                .first()
            )
        return self._customer(row) if row is not None else None

    def create_customer(
        self, full_name: str, phone: str, address: str | None
    ) -> Customer:
        statement = text(
            "INSERT INTO customer (full_name, phone, address) "
            "VALUES (:full_name, :phone, :address) "
            "RETURNING customer_id, full_name, phone, address"
        )
        try:
            with self._engine.begin() as connection:
                row = (
                    connection.execute(
                        statement,
                        {"full_name": full_name, "phone": phone, "address": address},
                    )
                    .mappings()
                    .one()
                )
        except IntegrityError as error:
            if self._sqlstate(error) == "23505":
                raise DuplicateRecord("Số điện thoại đã được đăng ký") from error
            raise
        return self._customer(row)

    def update_customer(
        self, customer_id: int, changes: dict[str, object]
    ) -> Customer | None:
        assignments = ", ".join(f"{field} = :{field}" for field in changes)
        statement = text(
            f"UPDATE customer SET {assignments} "
            "WHERE customer_id = :customer_id "
            "RETURNING customer_id, full_name, phone, address"
        )
        parameters = {**changes, "customer_id": customer_id}
        try:
            with self._engine.begin() as connection:
                row = (
                    connection.execute(statement, parameters)
                    .mappings()
                    .first()
                )
        except IntegrityError as error:
            if self._sqlstate(error) == "23505":
                raise DuplicateRecord("Số điện thoại đã được đăng ký") from error
            raise
        return self._customer(row) if row is not None else None

    def customer_has_devices(self, customer_id: int) -> bool:
        return self._exists(
            "SELECT EXISTS(SELECT 1 FROM device WHERE customer_id = :record_id)",
            customer_id,
        )

    def customer_has_tickets(self, customer_id: int) -> bool:
        return self._exists(
            "SELECT EXISTS(SELECT 1 FROM ticket WHERE customer_id = :record_id)",
            customer_id,
        )

    def delete_customer(self, customer_id: int) -> bool:
        statement = text(
            "DELETE FROM customer WHERE customer_id = :customer_id"
        )
        try:
            with self._engine.begin() as connection:
                result = connection.execute(
                    statement, {"customer_id": customer_id}
                )
        except IntegrityError as error:
            if self._sqlstate(error) == "23503":
                return False
            raise
        return result.rowcount == 1

    def list_devices(self, customer_id: int) -> list[Device]:
        statement = text(
            "SELECT device_id, customer_id, model_name, serial_no, "
            "purchase_date, warranty_months, note "
            "FROM device WHERE customer_id = :customer_id ORDER BY device_id"
        )
        with self._engine.connect() as connection:
            rows = (
                connection.execute(statement, {"customer_id": customer_id})
                .mappings()
                .all()
            )
        return [self._device(row) for row in rows]

    def get_device(self, device_id: int) -> Device | None:
        statement = text(
            "SELECT device_id, customer_id, model_name, serial_no, "
            "purchase_date, warranty_months, note "
            "FROM device WHERE device_id = :device_id"
        )
        with self._engine.connect() as connection:
            row = (
                connection.execute(statement, {"device_id": device_id})
                .mappings()
                .first()
            )
        return self._device(row) if row is not None else None

    def create_device(
        self,
        customer_id: int,
        model_name: str,
        serial_no: str,
        purchase_date: date | None,
        warranty_months: int,
        note: str,
    ) -> Device:
        statement = text(
            "INSERT INTO device "
            "(customer_id, model_name, serial_no, purchase_date, warranty_months, note) "
            "VALUES (:customer_id, :model_name, :serial_no, :purchase_date, "
            ":warranty_months, :note) "
            "RETURNING device_id, customer_id, model_name, serial_no, "
            "purchase_date, warranty_months, note"
        )
        try:
            with self._engine.begin() as connection:
                row = (
                    connection.execute(
                        statement,
                        {
                            "customer_id": customer_id,
                            "model_name": model_name,
                            "serial_no": serial_no,
                            "purchase_date": purchase_date,
                            "warranty_months": warranty_months,
                            "note": note,
                        },
                    )
                    .mappings()
                    .one()
                )
        except IntegrityError as error:
            if self._sqlstate(error) == "23505":
                raise DuplicateRecord("Serial/IMEI đã được đăng ký") from error
            raise
        return self._device(row)

    def update_device(
        self, device_id: int, changes: dict[str, object]
    ) -> Device | None:
        assignments = ", ".join(f"{field} = :{field}" for field in changes)
        statement = text(
            f"UPDATE device SET {assignments} WHERE device_id = :device_id "
            "RETURNING device_id, customer_id, model_name, serial_no, "
            "purchase_date, warranty_months, note"
        )
        parameters = {**changes, "device_id": device_id}
        try:
            with self._engine.begin() as connection:
                row = (
                    connection.execute(statement, parameters)
                    .mappings()
                    .first()
                )
        except IntegrityError as error:
            if self._sqlstate(error) == "23505":
                raise DuplicateRecord("Serial/IMEI đã được đăng ký") from error
            raise
        return self._device(row) if row is not None else None

    def device_has_tickets(self, device_id: int) -> bool:
        return self._exists(
            "SELECT EXISTS(SELECT 1 FROM ticket WHERE device_id = :record_id)",
            device_id,
        )

    def delete_device(self, device_id: int) -> bool:
        statement = text("DELETE FROM device WHERE device_id = :device_id")
        try:
            with self._engine.begin() as connection:
                result = connection.execute(statement, {"device_id": device_id})
        except IntegrityError as error:
            if self._sqlstate(error) == "23503":
                return False
            raise
        return result.rowcount == 1

    def _exists(self, statement: str, record_id: int) -> bool:
        with self._engine.connect() as connection:
            return bool(
                connection.execute(
                    text(statement), {"record_id": record_id}
                ).scalar_one()
            )

    @staticmethod
    def _customer(row) -> Customer:
        return Customer(
            customer_id=row["customer_id"],
            full_name=row["full_name"],
            phone=row["phone"],
            address=row["address"],
        )

    @staticmethod
    def _device(row) -> Device:
        return Device(
            device_id=row["device_id"],
            customer_id=row["customer_id"],
            model_name=row["model_name"],
            serial_no=row["serial_no"],
            purchase_date=row["purchase_date"],
            warranty_months=row["warranty_months"],
            note=row["note"],
        )

    @staticmethod
    def _sqlstate(error: IntegrityError) -> str | None:
        return getattr(error.orig, "sqlstate", None)


def customer_repository_from_environment() -> CustomerRepository | None:
    load_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        return None
    return CustomerRepository(create_engine(database_url, pool_pre_ping=True))
