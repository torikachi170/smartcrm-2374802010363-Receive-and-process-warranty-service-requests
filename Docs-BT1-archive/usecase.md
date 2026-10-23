# Use Case — Luồng L2

Sơ đồ gốc: `docs/usecase.drawio`. Tác nhân đặt NGOÀI ranh giới hệ thống; tên use case = động từ + đối tượng.

| Mã | Use case | Tác nhân | User Story |
|---|---|---|---|
| UC1 | Tra cứu khách hàng theo số điện thoại | Nhân viên tiếp nhận | US1 |
| UC2 | Tạo khách hàng mới | Nhân viên tiếp nhận | US2 |
| UC3 | Tạo phiếu bảo hành mới | Nhân viên tiếp nhận | US3, US5 |
| UC4 | Phân loại nhóm sự cố và mức ưu tiên | Nhân viên tiếp nhận | US4 |
| UC5 | Xem danh sách phiếu sắp quá hạn | Quản lý trung tâm | US6 |
| UC6 | Cập nhật trạng thái phiếu | Nhân viên tiếp nhận | US7 |

- `UC3 <<include>> UC1`: tra cứu khách là bước bắt buộc, luôn chạy mỗi lần tạo phiếu.
- `UC3 <<include>> UC4`: đề xuất nhóm sự cố và mức ưu tiên luôn chạy khi tạo phiếu.
- `UC2 <<extend>> UC3`: tạo khách mới chỉ xảy ra ở nhánh điều kiện "khách chưa tồn tại".
- Không có tác nhân không phải người trong phạm vi L2 (gửi SMS cho khách thuộc mức WON'T).

## UC3 — Tạo phiếu bảo hành mới

- **Tác nhân chính:** Nhân viên tiếp nhận
- **Mục tiêu:** Ghi nhận một yêu cầu bảo hành vào hệ thống để theo dõi đến khi đóng phiếu.
- **Điều kiện trước:** Nhân viên đã đăng nhập (vai trò Nhân viên tiếp nhận, thuộc một trung tâm).
- **Điều kiện sau:** Một phiếu bảo hành trạng thái Mới đã được lưu, có mã phiếu duy nhất, hạn cam kết, tình trạng bảo hành và một dòng lịch sử trạng thái.
- **User Story liên quan:** US3, US4, US5 · **Mức ưu tiên:** MUST

### Luồng chính
1. Nhân viên chọn chức năng "Tạo phiếu bảo hành" (màn hình M1).
2. Nhân viên nhập số điện thoại khách và bấm Tra cứu.
3. Hệ thống tra cứu và hiển thị họ tên, địa chỉ, danh sách thiết bị của khách. [include UC1]
4. Nhân viên chọn thiết bị từ danh sách; hệ thống hiển thị tình trạng bảo hành.
5. Nhân viên nhập mô tả lỗi (10–2000 ký tự).
6. Hệ thống đề xuất nhóm sự cố và mức ưu tiên. [include UC4]
7. Nhân viên xác nhận hoặc điều chỉnh rồi bấm Lưu phiếu.
8. Hệ thống sinh mã phiếu, tính hạn cam kết (QT-04), xác định tình trạng bảo hành (QT-05), lưu phiếu ở trạng thái Mới, ghi lịch sử trạng thái và hiển thị mã phiếu cùng hạn cam kết.

### Luồng ngoại lệ (đánh số theo bước của luồng chính)
- **3a. Khách hàng chưa tồn tại** → Hệ thống báo "Không tìm thấy khách hàng" kèm nút Tạo khách hàng mới; sau khi lưu khách mới (UC2) quay lại bước 4. [extend UC2]
- **4a. Thiết bị không có trong lịch sử mua của khách** → Cho nhập thiết bị ngoài: bắt buộc nhập serial và ghi chú nguồn gốc; thiết bị được lưu với khách này (QT-03).
- **4b. Thiết bị hết bảo hành hoặc không có ngày mua** → Hệ thống gắn tình trạng Hết bảo hành / Chưa xác minh và hiển thị cảnh báo; vẫn cho lưu phiếu (phê duyệt nằm ngoài phạm vi).
- **5a. Mô tả lỗi để trống hoặc quá ngắn** → Từ chối lưu, nêu rõ trường còn thiếu; giữ nguyên dữ liệu đã nhập.
- **7a. Thiết bị đang có một phiếu chưa đóng** → Từ chối tạo phiếu mới, hiển thị mã phiếu đang xử lý của thiết bị.
- **8a. Mất kết nối khi đang lưu** → Giữ dữ liệu trên màn hình, cho phép thử lưu lại; không tạo phiếu trùng.
