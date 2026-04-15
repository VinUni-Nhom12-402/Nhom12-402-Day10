# Data contract — Lab Day 10

> Bắt đầu từ `contracts/data_contract.yaml` — mở rộng và đồng bộ file này.

---

## 1. Nguồn dữ liệu (source map)

| Nguồn | Phương thức ingest | Failure mode chính | Metric / alert |
|-------|-------------------|-------------------|----------------|
| `kb_chunk_export` (CSV) | Tải file định kỳ (Batch) từ hệ cơ sở dữ liệu IT | Mất cấu trúc cột, sai định dạng ngày (`effective_date`), lỗi mã hóa ký tự (BOM). | Cảnh báo hệ thống nếu tỷ lệ bản ghi rớt vào `quarantine` vượt quá định mức 20% hoặc quá SLA `freshness` (24 giờ). |
| Document files tĩnh (VD: `hr_leave_policy`) | Upload nội dung trực tiếp qua Git Repo | Thiếu nội dung, hoặc tải nhầm file phiên bản chính sách năm cũ. | Pipeline sẽ báo lỗi (halt) ngay lập tức nếu kỳ vọng không đạt đủ độ dài text hoặc nếu tìm ra điều khoản cũ. |

---

## 2. Schema cleaned

| Cột | Kiểu | Bắt buộc | Ghi chú |
|-----|------|----------|---------|
| chunk_id | string | Có | Khóa chính sinh từ hàm băm Hash. Dùng để cấu hình UPSERT vào ChromaDB không bị trùng. |
| doc_id | string | Có | ID tĩnh neo theo tài liệu; phải thuộc danh sách allow_list (VD: `policy_refund_v4`). |
| chunk_text | string | Có | Độ dài ký tự > 8; tuyệt đối không chứa thành phần thẻ HTML, kịch bản độc hại. |
| effective_date | date | Có | Yêu cầu phải ép kiểu đúng về định dạng chuẩn ISO `YYYY-MM-DD`. |
| exported_at | datetime | Có | Marker timestamp dùng để kiểm tra tính cập nhật (freshness). |

---

## 3. Quy tắc quarantine vs drop

> Record bị flag đi đâu? Ai approve merge lại?



---

## 4. Phiên bản & canonical

> Source of truth cho policy refund: file nào / version nào?

