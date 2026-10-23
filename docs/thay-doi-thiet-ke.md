# Nhật ký thay đổi thiết kế

## Sau phản hồi Bài tập 1 (19/10/2026)

### TD-01 Xác nhận cam kết trong phụ lục AI

- Phản hồi: Phụ lục AI thiếu câu xác nhận đã đọc, hiểu và chịu trách nhiệm, kèm họ tên, MSSV và ngày.
- Quyết định: GIỮ nội dung hiện có; kiểm tra lại bản Word trước khi nộp.
- Lý do: Bản Word trong workspace và `docs/ai-disclosure.md` hiện đều có câu cam kết, họ tên Nguyễn Hoàng Minh Nhật, MSSV 2374802010363 và ngày 09/10/2026.
- Ảnh hưởng: Không đổi nội dung cam kết. Cần xem lại PDF xuất cuối vì môi trường hiện tại chưa có công cụ render DOCX để xác nhận phân trang trực quan.

### TD-02 Chuẩn hóa tên file và thư mục

- Phản hồi: `gitignore`, `env.example`, `srs.md.md` sai tên; thư mục tài liệu nên là `docs/` chữ thường.
- Quyết định: SỬA.
- Lý do: Dùng tên chuẩn giúp Git nhận cấu hình ignore và đường dẫn thống nhất trên các hệ điều hành.
- Ảnh hưởng: Đổi thành `.gitignore`, `.env.example`, `docs/srs.md` và `docs/`; gộp quy tắc ignore vào `.gitignore`.

### TD-03 Gộp dòng dẫn API ở trang 9

- Phản hồi: Trang 9 gần như trống, chỉ có dòng dẫn tới `api-contract.md`; có thể gộp vào trang trước.
- Quyết định: SỬA.
- Lý do: Dòng dẫn ngắn không cần một trang riêng.
- Ảnh hưởng: Dòng dẫn được chuyển vào mục 4.4 cạnh tham chiếu DDL; kiểm tra nội dung DOCX sau sửa. Cần xuất PDF và kiểm tra trang cuối bằng Word trước khi nộp.

### TD-04 Tự động hóa 11 phép thử ràng buộc

- Phản hồi: Chuyển 11 phép thử đã chạy trên PostgreSQL thành test tự động.
- Quyết định: SỬA.
- Lý do: Test tự động giúp phát hiện hồi quy trên các ràng buộc của DDL.
- Ảnh hưởng: Thêm 11 test trong `test/test_postgres_constraints.py`, chạy trên schema tạm riêng. Chưa xác minh được bằng PostgreSQL trong môi trường hiện tại; cần đặt `TEST_DATABASE_URL` và chạy pytest.

### TD-05 Hiện thực `POST /api/classify`

- Phản hồi: Cài đặt endpoint theo hợp đồng API cho BT2.
- Quyết định: SỬA.
- Lý do: `POST /api/classify` được ánh xạ tới US4 và cần trả nhóm sự cố cùng mức ưu tiên đề xuất.
- Ảnh hưởng: Thêm route, `ClassifyService`, repository danh mục và seed dữ liệu. Bộ từ khóa chỉ đưa ra đề xuất; chưa huấn luyện mô hình và không tự tạo phiếu. Test HTTP hiện chạy đạt.

### TD-06 Đăng nhập tối thiểu cho prototype

- Phản hồi: Workshop buổi 10 yêu cầu đăng nhập và xử lý phản hồi 401; SRS BT1 ghi đăng nhập/quản lý nhân sự ngoài phạm vi.
- Quyết định: SỬA CÓ GIỚI HẠN. Thêm một tài khoản demo cấu hình qua biến môi trường và JWT access token; không làm đăng ký, quản lý nhân viên hoặc phân quyền.
- Lý do: Đáp ứng luồng xác thực tối thiểu của workshop mà không giả lập hệ thống nhân sự hay mở rộng thành module quản trị.
- Ảnh hưởng: Thêm `POST /api/auth/login`; yêu cầu Bearer token ở `POST /api/classify`; token chỉ có `sub` và thời hạn, chưa đại diện `employee_id`, `center_id` hoặc vai trò. Bí mật chỉ đặt trong `.env`; cập nhật `.env.example`, README và hợp đồng API.