# Đặc tả Use Case — Luồng L2

## Use Case Diagram — mô tả bằng lời trước khi vẽ

**Hệ thống:** Tiếp nhận và phân loại yêu cầu bảo hành (luồng L2)

**Actor (3):**
- Nhân viên tiếp nhận (người)
- Quản lý trung tâm (người)
- Hệ thống nhắc hạn — actor thời gian (không phải người)

**Use case (7):**

| Mã | Tên use case | Actor |
|---|---|---|
| UC1 | Tra cứu khách hàng theo số điện thoại | Nhân viên tiếp nhận |
| UC2 | Tạo khách hàng mới khi chưa tồn tại | Nhân viên tiếp nhận |
| UC3 | Tạo phiếu bảo hành mới | Nhân viên tiếp nhận |
| UC4 | Phân loại nhóm sự cố và mức ưu tiên | Nhân viên tiếp nhận |
| UC5 | Theo dõi và cập nhật trạng thái phiếu | Nhân viên tiếp nhận |
| UC6 | Xem danh sách phiếu sắp quá hạn | Quản lý trung tâm, Hệ thống nhắc hạn |
| UC7 | Xem báo cáo phiếu quá hạn theo kỹ thuật viên | Quản lý trung tâm |

**Quan hệ include/extend và lý do:**
- `UC3 <<include>> UC1` — tra cứu khách là bước bắt buộc, luôn chạy mỗi lần tạo phiếu.
- `UC3 <<include>> UC4` — phân loại nhóm sự cố/mức ưu tiên luôn chạy khi tạo phiếu.
- `UC2 <<extend>> UC3` — tạo khách mới chỉ xảy ra ở nhánh điều kiện "khách chưa tồn tại", không phải bước bắt buộc.

File sơ đồ gốc: `docs/usecase.drawio` (mở bằng app.diagrams.net).

---

## Đặc tả chi tiết — UC3: Tạo phiếu bảo hành mới

**Actor chính:** Nhân viên tiếp nhận
**Mục tiêu:** Ghi nhận một yêu cầu bảo hành vào hệ thống để theo dõi đến khi đóng.
**Điều kiện trước:** Nhân viên đã đăng nhập và có quyền tiếp nhận tại trung tâm của mình.
**Điều kiện sau:** Một phiếu bảo hành ở trạng thái MỚI đã được lưu, có mã phiếu duy nhất và hạn cam kết.
**Liên quan:** US3, US5 | **Mức ưu tiên:** MUST

### Luồng chính
1. Nhân viên chọn chức năng "Tạo phiếu bảo hành mới".
2. Nhân viên nhập số điện thoại khách hàng.
3. Hệ thống tra cứu và hiển thị thông tin khách + danh sách thiết bị đã mua. *[include UC1]*
4. Nhân viên chọn thiết bị từ danh sách.
5. Nhân viên nhập mô tả lỗi (bắt buộc ≥10 ký tự).
6. Hệ thống đề xuất nhóm sự cố và mức ưu tiên. *[include UC4]*
7. Nhân viên xác nhận hoặc điều chỉnh, rồi bấm Lưu.
8. Hệ thống sinh mã phiếu, tính hạn cam kết theo mức ưu tiên (QT-04), lưu phiếu ở trạng thái MỚI, hiển thị mã phiếu.

### Luồng ngoại lệ
- **3a. Khách hàng chưa tồn tại trong hệ thống**
  → Hệ thống mở form tạo khách mới với số điện thoại đã điền sẵn. *[extend UC2]*
  → Sau khi lưu khách mới, quay lại bước 4.
- **4a. Thiết bị không nằm trong lịch sử mua hàng của khách**
  → Cho phép nhập thiết bị ngoài, bắt buộc nhập số serial và ghi chú nguồn gốc.
- **5a. Mô tả lỗi để trống**
  → Từ chối lưu, hiển thị thông báo nêu rõ trường còn thiếu. Không mất dữ liệu đã nhập.
- **7a. Thiết bị đã có một phiếu chưa đóng**
  → Hệ thống từ chối tạo phiếu mới, báo phiếu đang xử lý (tránh trùng lặp).
- **8a. Mất kết nối khi đang lưu**
  → Giữ lại dữ liệu đã nhập trên giao diện, cho phép thử lưu lại. Không tạo phiếu trùng.
