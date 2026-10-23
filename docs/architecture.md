# Kiến trúc — Luồng L2

Sơ đồ gốc: `docs/architecture.drawio` (kiến trúc phân lớp 4 lớp, phụ thuộc một chiều).

| Lớp | Thành phần và trách nhiệm |
|---|---|
| LỚP TRÌNH BÀY | Màn hình M1 Tạo phiếu · M2 Danh sách phiếu · M3 Chi tiết phiếu (React)<br>CustomerController, TicketController (REST API, FastAPI router)<br>Trách nhiệm: nhận dữ liệu nhập, hiển thị kết quả và thông báo lỗi; KHÔNG chứa quy tắc nghiệp vụ |
| LỚP NGHIỆP VỤ | CustomerService — tra cứu/tạo khách (QT-01, QT-02); che số điện thoại [NFR2]<br>TicketService — tạo phiếu, sinh hạn cam kết, tình trạng bảo hành, vòng đời (QT-03…QT-06)<br>ClassifyService — đề xuất nhóm sự cố và mức ưu tiên<br>Trách nhiệm: TOÀN BỘ quy tắc nghiệp vụ nằm ở lớp này [NFR4] |
| LỚP TRUY CẬP DỮ LIỆU | CustomerRepository · DeviceRepository · TicketRepository · IssueCategoryRepository<br>Trách nhiệm: đọc/ghi qua giao diện Repository, che giấu SQL; phân trang ở CSDL [NFR1] |
| LỚP LƯU TRỮ — PostgreSQL 18 | customer · device · issue_category · ticket · ticket_status_log<br>Index (center_id, status, due_date) [NFR1]; index duy nhất một phiếu mở/thiết bị |

Cách các lớp trao đổi: HTTP + JSON (docs/api-contract.md) → gọi hàm (đối tượng dữ liệu nghiệp vụ) → SQL (SQLAlchemy).

## Lập luận lựa chọn kiến trúc

Khuôn: *"Vì <mã NFR> yêu cầu <ngưỡng cụ thể>, tôi chọn <quyết định>, đánh đổi là <chi phí>."*

1. Vì NFR1 yêu cầu danh sách phiếu hiển thị dưới 2 giây với 1.000 phiếu, tôi chọn đánh index ghép (center_id, status, due_date) và phân trang 20 dòng ngay ở lớp Truy cập dữ liệu thay vì tải toàn bộ phiếu rồi lọc ở giao diện; đánh đổi là mỗi lần tạo hoặc cập nhật phiếu phải ghi thêm vào index nên chậm hơn một chút.

2. Vì NFR2 yêu cầu chỉ Quản lý trung tâm thấy số điện thoại đầy đủ, tôi chọn kiểm tra vai trò và che số điện thoại trong CustomerService trước khi trả dữ liệu ra lớp Trình bày thay vì chỉ ẩn trên giao diện; đánh đổi là mọi service phải nhận thêm thông tin vai trò của người gọi và mỗi phản hồi phải qua thêm một bước chuyển đổi dữ liệu.

3. Vì NFR4 yêu cầu đổi một quy tắc nghiệp vụ chỉ phải sửa trong 1 module và không sửa ở lớp khác, tôi chọn kiến trúc 4 lớp với phụ thuộc một chiều và gom toàn bộ QT-01…QT-06 vào lớp Nghiệp vụ; đánh đổi là mỗi chức năng phải viết thêm vài file trung gian (controller, service, repository) cho một thao tác đơn giản.

**NGOÀI PHẠM VI: phân công kỹ thuật viên (L4) · gửi SMS cho khách · đăng nhập/quản lý nhân sự (dùng ID ngoài) · phê duyệt bảo hành**
