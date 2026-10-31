# Hợp đồng API — Luồng L2 (track SE)

## 1. Danh sách endpoint

| Phương thức | Đường dẫn | Mục đích | User Story | Mã trạng thái |
|---|---|---|---|---|
| POST | /api/auth/login | Đăng nhập tài khoản demo, nhận access token | N/A (prototype) | 200, 400, 401, 503 |
| GET | /api/customers?phone={phone} | Danh sách khách hoặc tra cứu theo SĐT | US1 | 200, 400 |
| POST | /api/customers | Tạo khách hàng mới | US2 | 201, 400, 409 |
| GET | /api/customers/{id} | Xem hồ sơ khách hàng | US1 | 200, 404 |
| PATCH | /api/customers/{id} | Cập nhật hồ sơ khách hàng | BT2 CRUD | 200, 400, 404, 409 |
| DELETE | /api/customers/{id} | Xóa khách hàng chưa có thiết bị/phiếu tham chiếu | BT2 CRUD, QT-13 | 204, 404, 409 |
| GET | /api/customers/{id}/devices | Danh sách thiết bị của khách hàng | US1 | 200, 404 |
| POST | /api/customers/{id}/devices | Ghi nhận thiết bị ngoài lịch sử mua | US3 | 201, 400, 404, 409 |
| GET | /api/devices/{id} | Xem chi tiết thiết bị | BT2 CRUD | 200, 404 |
| PATCH | /api/devices/{id} | Cập nhật thiết bị | BT2 CRUD | 200, 400, 404, 409 |
| DELETE | /api/devices/{id} | Xóa thiết bị chưa có phiếu tham chiếu | BT2 CRUD, QT-13 | 204, 404, 409 |
| POST | /api/classify | Đề xuất nhóm sự cố và mức ưu tiên từ mô tả lỗi | US4 | 200, 400 |
| POST | /api/tickets | Tạo phiếu bảo hành (sinh mã, hạn cam kết, tình trạng bảo hành) | US3, US5 | 201, 400, 404, 409 |
| GET | /api/tickets?center_id=&status=&due_before=&page=&size= | Danh sách phiếu, sắp theo hạn cam kết | US6 | 200, 400 |
| PATCH | /api/tickets/{id}/status | Chuyển trạng thái phiếu | US7 | 200, 400, 404, 409 |

## 2. Quy ước chung

- JSON, UTF-8, header `Content-Type: application/json`. Tên trường `snake_case`, khớp tên cột trong `db/schema.sql`.
- Thời gian ISO 8601 kèm múi giờ, ví dụ `2026-10-12T14:30:00+07:00`.
- Phân trang: `page` (từ 1), `size` (mặc định 20, tối đa 100); response kèm `total`.
- Lỗi cùng một cấu trúc: `{ "error": { "code": "...", "message": "...", "fields": {...} } }`.
- Endpoint nghiệp vụ được bảo vệ nhận `Authorization: Bearer <access_token>`. Thiếu, sai hoặc hết hạn token trả 401 với mã `UNAUTHORIZED`.
- Prototype chỉ có một tài khoản demo cấu hình bằng `DEMO_USERNAME`, `DEMO_PASSWORD` và `JWT_SECRET_KEY`; token hiện chỉ mang `sub` và thời hạn. Chưa có đăng ký, đăng nhập thật, `employee_id`, `center_id` hay phân quyền theo vai trò.
- Các endpoint CRUD mới ở BT2 chỉ xóa khách hàng chưa có thiết bị/phiếu và thiết bị chưa có phiếu. Xóa bản ghi đang được tham chiếu trả **409**; không cung cấp thao tác xóa phiếu bảo hành (QT-13).

### Đăng nhập prototype

`POST /api/auth/login` nhận `{ "username": "demo", "password": "<DEMO_PASSWORD>" }` và trả **200** `{ "access_token": "<JWT>", "token_type": "bearer", "expires_in": 1800 }`.

- **400** `VALIDATION_FAILED` nếu thiếu hoặc sai hình dạng trường.
- **401** `INVALID_CREDENTIALS` nếu thông tin đăng nhập không đúng.
- **503** `AUTH_NOT_CONFIGURED` nếu thiếu cấu hình tài khoản hoặc khóa ký JWT.
- Token ký HS256; thời hạn cấu hình bằng `JWT_ACCESS_TOKEN_MINUTES` (mặc định 30 phút). Khóa ký phải dài tối thiểu 32 ký tự và chỉ đặt trong `.env`, không commit.

## 3. GET /api/customers?phone={phone} — US1 (luồng 3a)

- `phone` bỏ trống trả danh sách khách; có `phone` thì tra cứu chính xác. **200**:
```json
[{ "customer_id": 1024, "full_name": "Nguyễn Văn An", "phone": "090****567", "address": "12 Lê Lợi, Q.1" }]
```
- **400** — `phone` sai định dạng (QT-02). Prototype chưa có phân quyền nên API luôn che bốn chữ số giữa theo NFR2.

## 3.1. CRUD khách hàng và thiết bị — BT2

- `POST /api/customers` nhận `full_name`, `phone`, `address?` → **201**; điện thoại phải gồm 10 chữ số bắt đầu bằng 0. Điện thoại trùng trả **409** `PHONE_EXISTS`.
- `GET /api/customers/{id}` và `GET /api/customers/{id}/devices` trả hồ sơ/danh sách; danh sách thiết bị có thêm `priority` từ phiếu đang mở gần nhất (null nếu chưa có phiếu); không tìm thấy khách hàng trả **404** `CUSTOMER_NOT_FOUND`.
- `PATCH /api/customers/{id}` nhận ít nhất một trường trong `full_name`, `phone`, `address`; điện thoại trùng trả **409** `PHONE_EXISTS`.
- `DELETE /api/customers/{id}` trả **204** chỉ khi khách chưa có thiết bị và chưa được phiếu tham chiếu; nếu không trả **409** `CUSTOMER_HAS_DEVICES` hoặc `CUSTOMER_HAS_TICKETS`.
- `POST /api/customers/{id}/devices` nhận `model_name`, `serial_no`, `note` (bắt buộc), `purchase_date?`, `warranty_months?`; serial trùng trả **409** `SERIAL_EXISTS`.
- `GET /api/devices/{id}` và `PATCH /api/devices/{id}` đọc/cập nhật thiết bị. `customer_id` không thể thay đổi qua PATCH.
- `DELETE /api/devices/{id}` trả **204** khi thiết bị chưa có phiếu; nếu có phiếu trả **409** `DEVICE_HAS_TICKETS`. Không xóa dây chuyền dữ liệu; không có API xóa phiếu.
- Mọi endpoint CRUD yêu cầu bearer token. Không có API đăng ký tài khoản trong prototype.

## 4. POST /api/classify — US4

Yêu cầu `Authorization: Bearer <access_token>`. Request `{ "issue_desc": "Máy sạc không vào, cắm sạc báo lỗi phụ kiện" }` → **200** `{ "category_id": 3, "category_name": "SAC", "priority": "TRUNG_BINH" }`. **400** nếu `issue_desc` không hợp lệ; **401** nếu token thiếu/sai/hết hạn; **503** nếu database hoặc danh mục sự cố chưa được cấu hình. Chỉ là ĐỀ XUẤT; nhân viên xác nhận hoặc điều chỉnh trước khi lưu phiếu.

## 5. POST /api/tickets — US3, US5

Request:
```json
{ "customer_id": 1024, "device_id": 3311, "category_id": 3,
  "issue_desc": "Máy sạc không vào, cắm sạc báo lỗi phụ kiện", "priority": "TRUNG_BINH" }
```
`center_id` và `received_by` lấy từ token, không nhận từ body. **201 Created**:
```json
{ "ticket_id": 5102, "ticket_code": "BH-000231/2026", "status": "MOI", "warranty_status": "CON_BAO_HANH",
  "received_at": "2026-10-09T14:30:00+07:00", "due_date": "2026-10-12T14:30:00+07:00" }
```
- **400** `VALIDATION_FAILED` (xem bảng dưới) · **404** `customer_id`/`device_id` không tồn tại · **409** `DEVICE_HAS_OPEN_TICKET` — thiết bị đang có phiếu chưa đóng (luồng 7a), kèm `ticket_code` của phiếu đó.

| Trường | Bắt buộc | Kiểu / ràng buộc | Thông báo khi vi phạm |
|---|---|---|---|
| customer_id | Có | Số nguyên dương, phải tồn tại | Không tìm thấy khách hàng |
| device_id | Có | Số nguyên dương, phải thuộc customer_id (QT-03) | Thiết bị không thuộc khách hàng này |
| category_id | Không | Phải tồn tại và is_active; NULL = chưa phân loại | Nhóm sự cố không hợp lệ |
| issue_desc | Có | Chuỗi 10–2000 ký tự | Mô tả lỗi phải có từ 10 đến 2000 ký tự |
| priority | Không | CAO / TRUNG_BINH / THAP; mặc định theo nhóm sự cố | Mức ưu tiên không hợp lệ |

Hệ thống tự sinh: `ticket_code`, `status = MOI`, `received_at`, `due_date` (QT-04), `warranty_status` (QT-05: CON_BAO_HANH / HET_BAO_HANH / CHUA_XAC_MINH khi thiếu ngày mua) và một dòng `ticket_status_log`.

## 6. POST /api/customers — US2 · POST /api/customers/{id}/devices — US3

- Tạo khách: body `full_name`, `phone`, `address?`; **201**; **409** `PHONE_EXISTS` kèm hồ sơ có sẵn (QT-01); **400** sai định dạng.
- Thêm thiết bị ngoài lịch sử mua (luồng 4a): body `model_name`, `serial_no`, `note` (bắt buộc), `purchase_date?`, `warranty_months?`; **201**; **409** `SERIAL_EXISTS` (QT-03); **404** khách không tồn tại.

## 7. GET /api/tickets — US6

Tham số: `center_id` (mặc định lấy từ token), `status?`, `due_before?` (ISO 8601; "sắp quá hạn" = `due_before` là thời điểm hiện tại + khoảng cảnh báo), `page`, `size`. Sắp theo `due_date` tăng dần. **200** `{ "total": 1, "items": [ { "ticket_code": "...", "customer_name": "...", "serial_no": "...", "category_name": "...", "priority": "...", "status": "...", "due_date": "..." } ] }`. Dùng index `idx_ticket_center_status_due` (NFR1).

## 8. PATCH /api/tickets/{id}/status — US7

Request `{ "to_status": "DA_PHAN_CONG", "note": "..." }` → **200** `{ "from_status": "MOI", "to_status": "DA_PHAN_CONG", "changed_at": "..." }` và ghi một dòng `ticket_status_log`. **400** `to_status` không hợp lệ · **404** không có phiếu · **409** `INVALID_TRANSITION` — chuyển sai vòng đời hoặc quay lại trạng thái trước (QT-06).

## 9. Tự kiểm

- [x] Mỗi endpoint nối được về ít nhất một User Story; mỗi endpoint có ≥ 1 response thành công và ≥ 2 response lỗi.
- [x] Mọi trường request đều là cột của `db/schema.sql` (hoặc lấy từ token: `center_id`, `received_by`, `changed_by`).
- [x] QT-01, QT-02, QT-03, QT-04, QT-05, QT-06, QT-13, QT-15 xuất hiện ở bảng validation hoặc mã lỗi.
