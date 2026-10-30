# Kiến trúc — Luồng L2

Sơ đồ gốc: `docs/architecture.drawio` (kiến trúc phân lớp 4 lớp, phụ thuộc một chiều).

| Lớp | Thành phần và trách nhiệm |
|---|---|
| LỚP TRÌNH BÀY | Trang đăng nhập và giao diện HTML/CSS/JavaScript tĩnh; ba màn hình Khách hàng · Thiết bị · Phân loại<br>FastAPI REST API cho đăng nhập, CRUD khách/thiết bị và phân loại<br>Trách nhiệm: nhận dữ liệu, hiển thị kết quả và thông báo lỗi; KHÔNG chứa quy tắc nghiệp vụ |
| LỚP NGHIỆP VỤ | CustomerService — kiểm tra và CRUD khách/thiết bị; chặn xóa dữ liệu đang được tham chiếu<br>ClassifyService — đề xuất nhóm sự cố và mức ưu tiên<br>Trách nhiệm: quy tắc nghiệp vụ, kiểm tra đầu vào và ánh xạ lỗi miền |
| LỚP TRUY CẬP DỮ LIỆU | CustomerRepository · IssueCategoryRepository<br>Trách nhiệm: đọc/ghi qua SQLAlchemy, tham số hóa SQL và chuyển vi phạm ràng buộc thành lỗi miền |
| LỚP LƯU TRỮ — PostgreSQL 16+ | customer · device · issue_category · ticket · ticket_status_log<br>Index (center_id, status, due_date) [NFR1]; index duy nhất một phiếu mở/thiết bị; khóa ngoại ngăn xóa dữ liệu đang được tham chiếu |

Cách các lớp trao đổi: trình duyệt gọi HTTP + JSON (docs/api-contract.md) → API FastAPI gọi Service bằng đối tượng nghiệp vụ → Repository thực hiện SQL (SQLAlchemy).

## Lập luận lựa chọn kiến trúc

Khuôn: *"Vì <mã NFR> yêu cầu <ngưỡng cụ thể>, tôi chọn <quyết định>, đánh đổi là <chi phí>."*

1. Vì NFR1 yêu cầu danh sách phiếu hiển thị dưới 2 giây với 1.000 phiếu, tôi chọn đánh index ghép (center_id, status, due_date) và phân trang 20 dòng ngay ở lớp Truy cập dữ liệu thay vì tải toàn bộ phiếu rồi lọc ở giao diện; đánh đổi là mỗi lần tạo hoặc cập nhật phiếu phải ghi thêm vào index nên chậm hơn một chút.

2. Vì NFR2 yêu cầu chỉ Quản lý trung tâm thấy số điện thoại đầy đủ nhưng prototype chưa có vai trò, API hiện che số điện thoại cho mọi tài khoản thay vì mặc định cho tài khoản demo xem dữ liệu đầy đủ; đánh đổi là chưa thể cung cấp chức năng tra cứu số đầy đủ cho đến khi có phân quyền thật.

3. Vì NFR4 yêu cầu đổi một quy tắc nghiệp vụ chỉ phải sửa trong 1 module và không sửa ở lớp khác, tôi chọn kiến trúc 4 lớp với phụ thuộc một chiều và gom toàn bộ QT-01…QT-06 vào lớp Nghiệp vụ; đánh đổi là mỗi chức năng phải viết thêm vài file trung gian (controller, service, repository) cho một thao tác đơn giản.

**NGOÀI PHẠM VI: phân công kỹ thuật viên (L4) · gửi SMS cho khách · đăng nhập/quản lý nhân sự (dùng ID ngoài) · phê duyệt bảo hành**
