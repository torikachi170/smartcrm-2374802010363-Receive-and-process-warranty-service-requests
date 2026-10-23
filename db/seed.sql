INSERT INTO issue_category (category_name, default_priority) VALUES
    ('MAN_HINH', 'CAO'),
    ('PIN', 'TRUNG_BINH'),
    ('SAC', 'TRUNG_BINH'),
    ('PHAN_MEM', 'TRUNG_BINH'),
    ('NUOC_VAO', 'CAO'),
    ('KHAC', 'THAP')
ON CONFLICT (category_name) DO NOTHING;