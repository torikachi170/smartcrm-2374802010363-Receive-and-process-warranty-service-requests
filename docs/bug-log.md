# Bug Log

## BUG-001 · Major — Tra cứu khách hàng lỗi khi truy vấn PostgreSQL

| Dòng | Nội dung |
|---|---|
| 1. Mã và mức độ | BUG-001 · Major — endpoint danh sách/tra cứu khách không hoạt động với PostgreSQL |
| 2. Phát hiện bởi | `test_repository_crud_and_referenced_delete_guards` |
| 3. Triệu chứng | PostgreSQL báo `AmbiguousParameter` khi tìm khách bằng số điện thoại |
| 4. Cách tái lập | Cấu hình `TEST_DATABASE_URL`, chạy test repository với `phone` có giá trị |
| 5. Nguyên nhân | SQL dùng `:phone IS NULL OR phone = :phone`; PostgreSQL không suy ra kiểu của tham số trong nhánh `IS NULL` |
| 6. Cách sửa | Chỉ thêm điều kiện `WHERE phone = :phone` khi có phone; nếu không thì truy vấn toàn bộ danh sách |
| 7. Commit và xác nhận | Không có commit link vì workspace hiện chưa phải Git repository; test hồi quy PASS sau khi sửa |
