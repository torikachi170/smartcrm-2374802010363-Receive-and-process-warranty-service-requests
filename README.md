# Smart CRM – Mekong Mobile · Luồng L2

Prototype cá nhân cho học phần **Chuyên đề tốt nghiệp 1**, thực hiện trên case study Smart CRM – Mekong Mobile.

- **Họ tên:** Nguyễn Hoàng Minh Nhật
- **MSSV:** 2374802010363
- **Track:** SE (Software Engineering)
- **Luồng nghiệp vụ:** L2 — Tiếp nhận và phân loại yêu cầu bảo hành

## 1. Phạm vi

Quản lý tiếp nhận và phân loại yêu cầu bảo hành: nhân viên tiếp nhận ghi yêu cầu, hệ thống phân loại nhóm sự cố và mức ưu tiên, sinh hạn cam kết, và theo dõi trạng thái đến khi đóng phiếu.

Chi tiết đầy đủ: xem [`docs/srs.md`](docs/srs.md).

## 2. Công nghệ sử dụng

| Thành phần | Lựa chọn |
|---|---|
| Ngôn ngữ / runtime | Python 3.14 |
| Framework API | FastAPI |
| Truy cập dữ liệu | SQLAlchemy |
| Cơ sở dữ liệu | PostgreSQL 18 |
| Giao diện | React (Vite) |
| Kiểm thử | pytest |
| Tài liệu API | OpenAPI tự sinh bởi FastAPI |

## 3. Cách chạy dự án cục bộ

### Yêu cầu
- Python ≥ 3.11
- PostgreSQL đã cài và chạy (xem hướng dẫn chi tiết bên dưới)

### Cài đặt

```bash
# 1. Tạo và kích hoạt môi trường ảo
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# 2. Cài thư viện
pip install fastapi uvicorn sqlalchemy psycopg2-binary python-dotenv pytest

# 3. Chạy server
python -m uvicorn main:app --reload
```

Server chạy tại `http://127.0.0.1:8000`. Kiểm tra bằng:

```
http://127.0.0.1:8000/health
```

Kết quả mong đợi: `{"status":"ok"}`

### Cơ sở dữ liệu

```sql
CREATE DATABASE smart_crm_l2;
```

Mật khẩu kết nối và cấu hình khác lưu trong `.env` (xem mẫu ở `.env.example`, không commit `.env` thật).

## 4. Cấu trúc thư mục

```
docs/
  srs.md              # Bản SRS rút gọn
  usecase.md          # Đặc tả Use Case (text)
  usecase.drawio       # Sơ đồ Use Case (file gốc)
  api-contract.md      # Hợp đồng API track SE
src/                  # Mã nguồn (đang rỗng ở BT1)
tests/                # Test (đang rỗng ở BT1)
.gitignore
.env.example
README.md
```

## 5. Trạng thái hiện tại

- [x] Phân tích yêu cầu: SRS, User Story, Use Case (BT1)
- [ ] Thiết kế kiến trúc + mô hình dữ liệu (BT1, đang làm)
- [ ] Hiện thực (BT2)
- [ ] Kiểm thử (BT3)
