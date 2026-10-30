# Bản SRS rút gọn — Luồng L2: Tiếp nhận và phân loại yêu cầu bảo hành

**Dự án:** Smart CRM – Mekong Mobile · **Track:** SE · **Người thực hiện:** Nguyễn Hoàng Minh Nhật — MSSV 2374802010363

## 1. Giới thiệu và phạm vi

**Bối cảnh.** Mekong Mobile chưa có hệ thống CRM. Yêu cầu bảo hành được ghi trên phiếu giấy: tra cứu ngày mua mất 5–10 phút và khoảng 30% không tra được; phân loại nhóm sự cố và mức ưu tiên làm theo cảm tính; khoảng 15% phiếu quá hạn mà không có cảnh báo (vấn đề V2, V8 của case study).

**Phạm vi (một câu).** Quản lý tiếp nhận và phân loại yêu cầu bảo hành: nhân viên tiếp nhận ghi yêu cầu, hệ thống phân loại nhóm sự cố và mức ưu tiên, sinh hạn cam kết, và theo dõi trạng thái đến khi đóng phiếu.

**Chủ ý KHÔNG làm (WON'T).**
- Chọn và phân công kỹ thuật viên (thuộc luồng L4). Trạng thái "Đã phân công" vẫn nằm trong vòng đời nhưng việc chọn kỹ thuật viên (QT-07, QT-08) không làm ở đây.
- Phê duyệt bảo hành của quản lý (phần phê duyệt của QT-05); đăng nhập và quản lý nhân sự/trung tâm (dùng mã do hệ thống ngoài cấp).
- Gửi SMS thông báo cho khách; quản lý tồn kho linh kiện (L5); khảo sát hài lòng (L8); báo cáo doanh thu (L6).

**Hướng mở rộng (COULD).** Báo cáo số phiếu quá hạn theo từng kỹ thuật viên (COULD — không hiện thực ở phiên bản này; trước đây là US8/UC7 ở bản buổi 4).

**Bảng thuật ngữ.** Mỗi khái niệm chỉ dùng MỘT tên trong SRS, sơ đồ, wireframe và mã nguồn.

| Thuật ngữ | Định nghĩa | Tên kỹ thuật |
|---|---|---|
| Khách hàng | Người đã mua hàng hoặc dùng dịch vụ của Mekong Mobile | customer |
| Thiết bị | Máy cụ thể của khách, định danh bằng số serial/IMEI | device |
| Phiếu bảo hành | Một yêu cầu bảo hành được ghi nhận, có mã duy nhất và vòng đời trạng thái | ticket |
| Trạng thái phiếu | Vị trí trong vòng đời: Mới → Đã phân công → Đang xử lý → Chờ linh kiện → Hoàn tất → Đã đóng (hoặc Đã hủy) | status |
| Lịch sử trạng thái | Mỗi lần chuyển trạng thái được ghi kèm thời điểm và người thực hiện | ticket_status_log |
| Hạn cam kết | Thời điểm chậm nhất phải hoàn tất phiếu, tính từ lúc tiếp nhận theo mức ưu tiên | due_date |
| Nhóm sự cố | Phân loại nguyên nhân: màn hình, pin, sạc, phần mềm, nước vào, khác | issue_category |
| Mức ưu tiên | Mức khẩn của phiếu: Cao / Trung bình / Thấp; quyết định hạn cam kết | priority |
| Tình trạng bảo hành | Còn bảo hành / Hết bảo hành / Chưa xác minh, xác định lúc tiếp nhận | warranty_status |
| Trung tâm | Trung tâm bảo hành tiếp nhận phiếu (định danh bằng mã do hệ thống ngoài cấp) | center_id |

## 2. Các bên liên quan và vai trò

| Tác nhân | Làm được | Không được làm |
|---|---|---|
| Nhân viên tiếp nhận | Tra cứu khách, tạo khách mới, tạo phiếu, cập nhật trạng thái phiếu của trung tâm mình | Xem phiếu của trung tâm khác; xem số điện thoại đầy đủ (QT-15) |
| Quản lý trung tâm | Xem danh sách phiếu của trung tâm mình, xem số điện thoại đầy đủ | Tạo hoặc sửa nội dung phiếu |

## 3. Yêu cầu chức năng

| Mã | Yêu cầu chức năng (kiểm chứng được) | User Story | MoSCoW |
|---|---|---|---|
| FR1 | Tra cứu khách hàng theo số điện thoại; nếu tìm thấy thì tự điền họ tên, địa chỉ và danh sách thiết bị của khách | US1 | MUST |
| FR2 | Tạo hồ sơ khách hàng mới khi số điện thoại chưa tồn tại; từ chối nếu số điện thoại đã tồn tại (QT-01) | US2 | MUST |
| FR3 | Tạo phiếu bảo hành mới với các trường bắt buộc: khách hàng, thiết bị, mô tả lỗi; cho nhập thiết bị ngoài lịch sử mua kèm serial | US3 | MUST |
| FR4 | Đề xuất nhóm sự cố và mức ưu tiên từ mô tả lỗi; nhân viên được xác nhận hoặc điều chỉnh trước khi lưu | US4 | SHOULD |
| FR5 | Tự sinh hạn cam kết theo mức ưu tiên ngay khi lưu phiếu (QT-04) và xác định tình trạng bảo hành (QT-05) | US5 | MUST |
| FR6 | Hiển thị danh sách phiếu của trung tâm, lọc theo trạng thái và hạn cam kết, sắp theo hạn cam kết tăng dần | US6 | SHOULD |
| FR7 | Cập nhật trạng thái phiếu theo đúng vòng đời, từ chối chuyển ngược (QT-06), ghi mọi lần chuyển vào lịch sử trạng thái | US7 | MUST |

### User Story

| Mã | MoSCoW | User Story |
|---|---|---|
| US1 | MUST | Là nhân viên tiếp nhận, tôi muốn tra cứu khách hàng theo số điện thoại để không phải hỏi lại thông tin đã có sẵn. |
| US2 | MUST | Là nhân viên tiếp nhận, tôi muốn tạo hồ sơ khách hàng mới khi số điện thoại chưa tồn tại để không bỏ sót khách chưa từng mua hàng. |
| US3 | MUST | Là nhân viên tiếp nhận, tôi muốn ghi nhận thiết bị và mô tả lỗi của khách để tạo một phiếu bảo hành mới. |
| US4 | SHOULD | Là nhân viên tiếp nhận, tôi muốn hệ thống đề xuất nhóm sự cố và mức ưu tiên từ mô tả lỗi để phân loại nhất quán, không phụ thuộc cảm tính cá nhân. |
| US5 | MUST | Là nhân viên tiếp nhận, tôi muốn hệ thống tự sinh hạn cam kết ngay khi tạo phiếu để biết rõ thời hạn phải hoàn tất. |
| US6 | SHOULD | Là quản lý trung tâm, tôi muốn xem danh sách phiếu sắp quá hạn theo hạn cam kết để ưu tiên nhắc xử lý trước. |
| US7 | MUST | Là nhân viên tiếp nhận, tôi muốn cập nhật trạng thái phiếu đúng theo vòng đời quy định để theo dõi tiến độ xử lý đến khi đóng. |

### Tiêu chí chấp nhận (Given–When–Then) của các story MUST

**US1**
- AC1. GIVEN số điện thoại đã có trong hệ thống, WHEN nhân viên nhập số đó và bấm Tra cứu, THEN hệ thống tự điền họ tên, địa chỉ và danh sách thiết bị của khách.
- AC2. GIVEN số điện thoại chưa có trong hệ thống, WHEN nhân viên bấm Tra cứu, THEN hệ thống báo "Không tìm thấy khách hàng" và hiện nút Tạo khách hàng mới. *(ngoại lệ 3a)*
- AC3. GIVEN số điện thoại sai định dạng, WHEN nhân viên bấm Tra cứu, THEN hệ thống từ chối và nêu rõ định dạng hợp lệ (10 chữ số, bắt đầu bằng 0). *(ngoại lệ)*

**US2**
- AC1. GIVEN số điện thoại chưa tồn tại, WHEN nhân viên điền đủ họ tên và số điện thoại rồi lưu, THEN hệ thống tạo hồ sơ khách mới.
- AC2. GIVEN số điện thoại đã tồn tại, WHEN nhân viên cố tạo khách mới, THEN hệ thống từ chối và hiển thị hồ sơ có sẵn (QT-01). *(ngoại lệ)*
- AC3. GIVEN họ tên để trống, WHEN bấm lưu, THEN hệ thống từ chối và báo rõ trường còn thiếu.

**US3**
- AC1. GIVEN khách hàng và thiết bị đã chọn, WHEN nhân viên nhập mô tả lỗi (10–2000 ký tự) và lưu, THEN hệ thống tạo phiếu ở trạng thái Mới với mã phiếu duy nhất.
- AC2. GIVEN mô tả lỗi để trống hoặc dưới 10 ký tự, WHEN bấm lưu, THEN hệ thống từ chối, báo rõ trường thiếu và giữ nguyên dữ liệu đã nhập. *(ngoại lệ 5a)*
- AC3. GIVEN thiết bị đang có một phiếu chưa đóng, WHEN nhân viên cố tạo phiếu mới cho thiết bị đó, THEN hệ thống từ chối và hiển thị mã phiếu đang xử lý. *(ngoại lệ 7a)*

**US5**
- AC1. GIVEN phiếu có mức ưu tiên Cao, WHEN lưu thành công, THEN hạn cam kết = thời điểm tiếp nhận + 24 giờ làm việc (QT-04).
- AC2. GIVEN mức ưu tiên Trung bình hoặc Thấp, WHEN lưu thành công, THEN hạn cam kết lần lượt là 72 giờ hoặc 120 giờ làm việc.
- AC3. GIVEN thời điểm tiếp nhận rơi vào Chủ Nhật, WHEN hệ thống tính hạn cam kết, THEN Chủ Nhật không được tính vào giờ làm việc. *(ngoại lệ)*

**US7**
- AC1. GIVEN phiếu đang ở trạng thái Mới, WHEN nhân viên chuyển sang Đã phân công, THEN hệ thống ghi thời điểm và người thực hiện vào lịch sử trạng thái.
- AC2. GIVEN phiếu đang ở trạng thái Đã đóng, WHEN có người cố chuyển về trạng thái trước, THEN hệ thống từ chối (QT-06). *(ngoại lệ)*
- AC3. GIVEN phiếu đang Chờ linh kiện, WHEN linh kiện đã có, THEN nhân viên chuyển được sang Hoàn tất và lịch sử được ghi.

## 4. Yêu cầu phi chức năng

| Mã | Loại | Ngưỡng đo được |
|---|---|---|
| NFR1 | Hiệu năng | Danh sách phiếu hiển thị trong dưới 2 giây với 1.000 phiếu, phân trang 20 dòng, trên máy 8 GB RAM. |
| NFR2 | Bảo mật | Số điện thoại đầy đủ chỉ hiển thị cho vai trò Quản lý trung tâm; vai trò khác thấy dạng che (090****567); 0 endpoint trả số đầy đủ cho nhân viên tiếp nhận. |
| NFR3 | Khả dụng | Nhân viên tiếp nhận mới tạo đúng một phiếu bảo hành trong dưới 3 phút, không cần hỏi đồng nghiệp. |
| NFR4 | Bảo trì | Đổi một quy tắc nghiệp vụ (ví dụ thời hạn QT-04) chỉ phải sửa trong 1 module của lớp Nghiệp vụ; 0 file phải sửa ở lớp Trình bày và lớp Truy cập dữ liệu. |

## 5. Ràng buộc và quy tắc nghiệp vụ

(Trích Bảng 9.1 của case study, chỉ các quy tắc liên quan L2)

| Mã | Quy tắc |
|---|---|
| QT-01 | Số điện thoại khách hàng là duy nhất; nhập số đã tồn tại thì hiển thị hồ sơ có sẵn thay vì tạo mới. |
| QT-02 | Số điện thoại được chuẩn hóa về 10 chữ số bắt đầu bằng 0 trước khi lưu (+84…, 84…, dấu cách, dấu chấm đều quy về dạng chuẩn). |
| QT-03 | Thiết bị xác định duy nhất bằng serial/IMEI; một thiết bị chỉ thuộc một khách hàng tại một thời điểm. |
| QT-04 | Hạn cam kết sinh tự động từ thời điểm tiếp nhận: Cao = 24 giờ, Trung bình = 72 giờ, Thấp = 120 giờ; chỉ tính ngày làm việc (thứ Hai–thứ Bảy). |
| QT-05 | Còn bảo hành nếu (ngày tiếp nhận − ngày mua) ≤ số tháng bảo hành; không có ngày mua thì đánh dấu "Chưa xác minh". Bước phê duyệt của quản lý nằm ngoài phạm vi. |
| QT-06 | Phiếu chỉ chuyển trạng thái theo vòng đời; không quay lại trạng thái trước; mọi lần chuyển ghi vào lịch sử trạng thái. |
| QT-13 | Không xóa vật lý phiếu bảo hành. Để đáp ứng CRUD của BT2, chỉ được xóa vật lý khách hàng khi không có thiết bị hoặc phiếu tham chiếu; chỉ được xóa thiết bị khi chưa có phiếu tham chiếu. Trường hợp đang được tham chiếu phải bị từ chối với HTTP 409, không xóa dây chuyền dữ liệu. Đây là điều chỉnh có kiểm soát so với phạm vi BT1. |
| QT-15 | Số điện thoại hiển thị dạng che với mọi vai trò trừ Quản lý trung tâm. |

## 6. Bảng truy vết yêu cầu

| FR | User Story | Use Case | MoSCoW | Bảng dữ liệu | Màn hình |
|---|---|---|---|---|---|
| FR1 | US1 | UC1 | MUST | customer, device | M1 |
| FR2 | US2 | UC2 | MUST | customer | M1 |
| FR3 | US3 | UC3 | MUST | ticket, device, customer, ticket_status_log | M1 |
| FR4 | US4 | UC4 | SHOULD | ticket, issue_category | M1, M3 |
| FR5 | US5 | UC3 | MUST | ticket | M1, M2, M3 |
| FR6 | US6 | UC5 | SHOULD | ticket, customer, device, issue_category | M2 |
| FR7 | US7 | UC6 | MUST | ticket, ticket_status_log | M3 |

Không có ô trống: mọi FR nối được tới User Story, Use Case, bảng dữ liệu và màn hình; mọi bảng và mọi màn hình phục vụ ít nhất một FR.

## Ghi chú thay đổi so với bản buổi 4

- User Story: từ 8 (bản buổi 4) xuống 7 vì đề bài BT1 quy định 5–7. US8 "báo cáo phiếu quá hạn theo kỹ thuật viên" mang mức COULD nên chuyển sang hướng mở rộng (quy ước MoSCoW: COULD không hiện thực).
- Use case: bỏ UC7 (ứng với US8); bỏ tác nhân "Hệ thống nhắc hạn" vì không có yêu cầu nào bảo chứng; đánh số lại UC5 = Xem danh sách phiếu sắp quá hạn, UC6 = Cập nhật trạng thái phiếu (khớp thứ tự US6, US7).
- NFR: thêm NFR4 (bảo trì) làm căn cứ cho quyết định kiến trúc 4 lớp.
- Mô hình dữ liệu: thêm các cột address, model_name, note, center_id, warranty_status, received_by để khớp hợp đồng API, QT-05 và QT-14; mã trung tâm/nhân viên là ID ngoài nên không có bảng; sửa chiều ký hiệu chân chim của ERD (bản buổi 5 vẽ ngược).
- Hợp đồng API: thêm POST /api/classify (US4) và POST /api/customers/{id}/devices (luồng 4a); bỏ mã 422 vì phê duyệt bảo hành nằm ngoài phạm vi.
