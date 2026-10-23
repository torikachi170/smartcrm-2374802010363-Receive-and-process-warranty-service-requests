# Smart CRM - Mekong Mobile

Track SE, luồng L2: tiếp nhận và phân loại yêu cầu bảo hành.

## 2. Yêu cầu môi trường

- Python 3.14
- PostgreSQL 16 trở lên
- Git và PowerShell (Windows) hoặc shell tương đương

## 3. Cài đặt và chạy dự án

Chạy từng lệnh theo thứ tự tại thư mục dự án.

### 3.1 Tạo môi trường Python

```powershell
python -m venv .venv
```

### 3.2 Kích hoạt môi trường

```powershell
.\.venv\Scripts\Activate.ps1
```

### 3.3 Cài dependencies

```powershell
python -m pip install -r requirements.txt
```

### 3.4 Tạo file cấu hình cục bộ

```powershell
Copy-Item .env.example .env
```

Mở `.env`, đặt `DATABASE_URL` tới PostgreSQL cục bộ, đổi `DEMO_PASSWORD` và
đặt `JWT_SECRET_KEY` thành chuỗi ngẫu nhiên dài ít nhất 32 ký tự. Không commit
file `.env` hoặc dùng mật khẩu mẫu ở môi trường thật.

### 3.5 Chuẩn bị cơ sở dữ liệu

Mỗi lệnh dưới đây là một bước riêng; chạy từ thư mục dự án sau khi đã cài
PostgreSQL và cấu hình quyền truy cập.

#### 3.5.1 Tạo database chạy ứng dụng

```powershell
createdb smart_crm_l2
```

#### 3.5.2 Tạo schema

```powershell
psql -d smart_crm_l2 -v ON_ERROR_STOP=1 -f db/schema.sql
```

#### 3.5.3 Nạp danh mục nhóm sự cố và mức ưu tiên

```powershell
psql -d smart_crm_l2 -v ON_ERROR_STOP=1 -f db/seed.sql
```

`db/seed.sql` nạp sáu nhóm sự cố cấu hình của nghiệp vụ. Hiện chưa có bộ dữ liệu
khách hàng/phiếu bảo hành mẫu; các luồng khách hàng và phiếu chưa được triển khai.

#### 3.5.4 Tùy chọn: tạo database riêng cho test ràng buộc

```powershell
createdb smart_crm_test
```

Nếu dùng database test, đặt `TEST_DATABASE_URL` trong `.env` trỏ tới
`smart_crm_test`. Test tạo và xóa schema tạm trong database này; tuyệt đối
không trỏ biến này tới database chứa dữ liệu thật.

### 3.6 Chạy ứng dụng

#### 3.6.1 Khởi động API

```powershell
python -m uvicorn src.presentation.api:app --reload --port 8000
```

#### 3.6.2 Mở giao diện

Mở `http://127.0.0.1:8000/login`, đăng nhập bằng `DEMO_USERNAME` và
`DEMO_PASSWORD` trong `.env`. Nhập mô tả sự cố dài từ 10 đến 2000 ký tự để
nhận đề xuất nhóm sự cố và mức ưu tiên. API sử dụng danh mục đang hoạt động
trong PostgreSQL; đây chỉ là đề xuất, không tự tạo phiếu. Swagger UI tại
`http://127.0.0.1:8000/docs`.

## 4. Chạy kiểm thử

Chạy toàn bộ test và hiển thị tên từng test cùng tổng kết:

```powershell
python -m pytest -v
```

Các test PostgreSQL sẽ bị bỏ qua nếu chưa cấu hình `TEST_DATABASE_URL`. Bộ test
còn lại bao phủ đăng nhập, token, API phân loại, validation, trường hợp ngoại
lệ và giao diện tĩnh.

## 5. Phạm vi prototype

- Đã hiện thực: health check, đăng nhập demo bằng JWT, giao diện đăng nhập và
  `POST /api/classify` dùng danh mục sự cố trong PostgreSQL.
- Chưa hiện thực: tra cứu/tạo khách hàng, tạo/danh sách/cập nhật phiếu và
  phân quyền nhân viên/trung tâm.
- Đăng nhập chỉ có một tài khoản demo cấu hình qua môi trường; không dùng cấu
  hình mẫu cho môi trường thật.

## Tài liệu

- `docs/srs.md` - SRS rút gọn và bảng truy vết.
- `docs/architecture.md` - Kiến trúc bốn lớp.
- `docs/erd.drawio` và `db/schema.sql` - ERD và DDL.
- `docs/api-contract.md` - Hợp đồng API.
- `docs/ai-disclosure.md` - Khai báo sử dụng công cụ AI.
- `docs/Phu_luc_minh_chung_luong_prototype.docx` - Ảnh chụp các luồng prototype.
- `docs/screenshots/` - Ảnh PNG riêng cho từng trạng thái đã kiểm thử.

Mở file `.drawio` bằng diagrams.net.
