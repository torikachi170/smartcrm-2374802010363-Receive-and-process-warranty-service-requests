# Smart CRM – Mekong Mobile · Luồng L2 · Tiếp nhận và phân loại yêu cầu bảo hành

Bài tập 1 (Phân tích và Thiết kế) — Chuyên đề tốt nghiệp 1, HK1 2026–2027.

- **Sinh viên:** Nguyễn Hoàng Minh Nhật — MSSV 2374802010363
- **Track:** SE · **Luồng:** L2 — Tiếp nhận và phân loại yêu cầu bảo hành
- **Phạm vi (một câu):** Quản lý tiếp nhận và phân loại yêu cầu bảo hành: nhân viên tiếp nhận ghi yêu cầu, hệ thống phân loại nhóm sự cố và mức ưu tiên, sinh hạn cam kết, và theo dõi trạng thái đến khi đóng phiếu.

## Mục lục tài liệu (thư mục `docs/`)

| File | Nội dung |
|---|---|
| `srs.md` | SRS rút gọn 6 mục, 7 User Story, tiêu chí chấp nhận, bảng truy vết |
| `usecase.drawio` · `usecase.md` | Use Case Diagram (file gốc) và đặc tả UC3 |
| `architecture.drawio` · `architecture.md` | Sơ đồ kiến trúc 4 lớp và 3 câu lập luận |
| `erd.drawio` · `../db/schema.sql` | ERD 5 bảng (chân chim) và DDL skeleton |
| `wireframe.png` | Wireframe 3 màn hình |
| `api-contract.md` | Hợp đồng API (track SE) |
| `ai-disclosure.md` | Bảng khai báo sử dụng công cụ AI |

Mở các file `.drawio` bằng https://app.diagrams.net (File → Open from → Device).

## Chạy thử CSDL

```bash
createdb smart_crm_l2
psql -d smart_crm_l2 -v ON_ERROR_STOP=1 -f db/schema.sql
```

## Công nghệ dự kiến

Python 3.14 + FastAPI + SQLAlchemy · React (Vite) · PostgreSQL 18 · pytest. Mã nguồn bắt đầu từ Bài tập 2 (`src/`, `tests/` còn rỗng ở BT1).

## Quy ước commit

`docs(srs): ...` · `docs(design): ...` · `feat(...)` · `test(...)` · `fix(...)`
