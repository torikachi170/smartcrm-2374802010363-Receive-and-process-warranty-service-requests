-- =====================================================================
-- DDL skeleton — Smart CRM Mekong Mobile · Luồng L2: Tiếp nhận và phân loại yêu cầu bảo hành
-- Track SE · PostgreSQL · 5 bảng, chuẩn 3NF. Sơ đồ: docs/erd.drawio
-- Cột center_id, received_by, changed_by là MÃ do hệ thống ngoài cấp (danh mục trung tâm,
-- nhân sự) — ngoài phạm vi L2 nên không có bảng và không có khóa ngoại.
-- =====================================================================

CREATE TABLE IF NOT EXISTS customer (
    customer_id  BIGSERIAL    PRIMARY KEY,
    full_name    VARCHAR(120) NOT NULL,
    phone        VARCHAR(20)  NOT NULL UNIQUE,              -- QT-01 (duy nhất); UNIQUE đã tạo sẵn index tra cứu (US1)
    address      VARCHAR(255),
    created_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    CONSTRAINT chk_customer_phone CHECK (phone ~ '^0[0-9]{9}$')   -- QT-02: 10 chữ số, bắt đầu bằng 0
);

CREATE TABLE IF NOT EXISTS device (
    device_id        BIGSERIAL    PRIMARY KEY,
    customer_id      BIGINT       NOT NULL REFERENCES customer(customer_id),
    model_name       VARCHAR(120) NOT NULL,
    serial_no        VARCHAR(50)  NOT NULL UNIQUE,          -- QT-03: serial/IMEI duy nhất
    purchase_date    DATE,                                  -- NULL được: khách không nhớ ngày mua (QT-05)
    warranty_months  SMALLINT     NOT NULL DEFAULT 12 CHECK (warranty_months > 0),
    note             VARCHAR(255)                           -- ghi chú nguồn gốc khi nhập thiết bị ngoài lịch sử mua (luồng 4a)
);

CREATE TABLE IF NOT EXISTS issue_category (
    category_id       SERIAL      PRIMARY KEY,
    category_name     VARCHAR(60) NOT NULL UNIQUE,          -- MAN_HINH / PIN / SAC / PHAN_MEM / NUOC_VAO / KHAC
    default_priority  VARCHAR(12) NOT NULL CHECK (default_priority IN ('CAO', 'TRUNG_BINH', 'THAP')),
    is_active         BOOLEAN     NOT NULL DEFAULT TRUE     -- thêm nhóm sự cố mới = thêm dữ liệu, không sửa mã
);

CREATE TABLE IF NOT EXISTS ticket (
    ticket_id        BIGSERIAL    PRIMARY KEY,
    ticket_code      VARCHAR(20)  NOT NULL UNIQUE,          -- dạng BH-000231/2026
    customer_id      BIGINT       NOT NULL REFERENCES customer(customer_id),   -- khách tại thời điểm tiếp nhận
    device_id        BIGINT       NOT NULL REFERENCES device(device_id),
    category_id      INT          REFERENCES issue_category(category_id),      -- NULL = chưa phân loại
    center_id        BIGINT       NOT NULL,                 -- mã trung tâm (ID ngoài), phục vụ QT-14
    issue_desc       TEXT         NOT NULL CHECK (char_length(issue_desc) BETWEEN 10 AND 2000),
    priority         VARCHAR(12)  NOT NULL CHECK (priority IN ('CAO', 'TRUNG_BINH', 'THAP')),   -- nhân viên được điều chỉnh đề xuất
    status           VARCHAR(20)  NOT NULL DEFAULT 'MOI'
                     CHECK (status IN ('MOI', 'DA_PHAN_CONG', 'DANG_XU_LY',
                                       'CHO_LINH_KIEN', 'HOAN_TAT', 'DA_DONG', 'DA_HUY')),
    warranty_status  VARCHAR(20)  NOT NULL
                     CHECK (warranty_status IN ('CON_BAO_HANH', 'HET_BAO_HANH', 'CHUA_XAC_MINH')),   -- QT-05, ảnh chụp lúc tiếp nhận
    received_by      BIGINT       NOT NULL,                 -- mã nhân viên tiếp nhận (ID ngoài)
    received_at      TIMESTAMPTZ  NOT NULL DEFAULT now(),
    due_date         TIMESTAMPTZ  NOT NULL,                 -- sinh theo QT-04; lưu để cam kết không đổi và để index sắp xếp (NFR1)
    closed_at        TIMESTAMPTZ,
    CONSTRAINT chk_due_after_received    CHECK (due_date >= received_at),
    CONSTRAINT chk_closed_after_received CHECK (closed_at IS NULL OR closed_at >= received_at)
);

-- NFR1, US6: danh sách phiếu của một trung tâm, lọc theo trạng thái, sắp theo hạn cam kết
CREATE INDEX IF NOT EXISTS idx_ticket_center_status_due ON ticket (center_id, status, due_date);

-- US3 (luồng ngoại lệ 7a), QT-03: mỗi thiết bị chỉ có MỘT phiếu chưa đóng
CREATE UNIQUE INDEX IF NOT EXISTS uq_ticket_open_per_device ON ticket (device_id) WHERE status NOT IN ('DA_DONG', 'DA_HUY');

CREATE TABLE IF NOT EXISTS ticket_status_log (
    log_id       BIGSERIAL    PRIMARY KEY,
    ticket_id    BIGINT       NOT NULL REFERENCES ticket(ticket_id),
    from_status  VARCHAR(20),                               -- NULL ở dòng đầu tiên (khi tạo phiếu)
    to_status    VARCHAR(20)  NOT NULL,
    changed_at   TIMESTAMPTZ  NOT NULL DEFAULT now(),
    changed_by   BIGINT       NOT NULL,                     -- mã nhân viên thực hiện (ID ngoài)
    note         VARCHAR(255)
);

-- US7: xem lịch sử trạng thái của một phiếu theo thời gian
CREATE INDEX IF NOT EXISTS idx_log_ticket ON ticket_status_log (ticket_id, changed_at);
