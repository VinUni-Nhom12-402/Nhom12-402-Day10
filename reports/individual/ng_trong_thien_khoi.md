# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Trọng Thiên Khôi — **MHV:** 2A202600227  
**Vai trò:** Ingestion / Pipeline Owner (Người 1)  
**Ngày nộp:** 2026-04-15

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- `etl_pipeline.py` — entrypoint toàn bộ pipeline (ingest → clean → validate → embed)
- `docs/pipeline_architecture.md` — tài liệu kiến trúc

Tôi chịu trách nhiệm chính cho bước **Ingest** và **Embed**. Cụ thể, tôi vận hành luồng `cmd_run` trong `etl_pipeline.py`: đọc raw CSV, gọi cleaning, chạy expectation suite, ghi manifest và thực hiện upsert vào ChromaDB collection `day10_kb`. Tôi cũng điền toàn bộ tài liệu `pipeline_architecture.md` bao gồm sơ đồ Mermaid, bảng ranh giới trách nhiệm và phân tích idempotency.

**Kết nối với thành viên khác:**

Tôi cung cấp `cleaned_csv` và manifest cho người phụ trách Quality và Monitoring sử dụng; đồng thời phối hợp với người phụ trách Cleaning để đảm bảo schema output của `cleaning_rules.py` khớp với trường `chunk_id` mà embed cần.

**Bằng chứng:**

- File `artifacts/manifests/manifest_2026-04-15T08-49Z.json` do pipeline của tôi sinh ra.
- Log in `artifacts/logs/run_2026-04-15T08-49Z.log` ghi đủ `run_id`, `raw_records`, `cleaned_records`, `quarantine_records`.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Quyết định quan trọng nhất tôi thực hiện là chọn chiến lược **upsert + prune** để đảm bảo index ChromaDB luôn là snapshot chính xác của lần chạy hiện tại, không tích luỹ chunk lạc hậu.

Cụ thể, trong `cmd_embed_internal`, trước khi upsert tôi lấy toàn bộ `chunk_id` hiện có trong collection, so sánh với danh sách `chunk_id` của run mới và xóa các id không còn xuất hiện (`embed_prune_removed`). Sau đó mới upsert batch mới.

Lý do chọn hướng này thay vì xóa toàn bộ collection rồi insert lại: **upsert idempotent** an toàn hơn khi pipeline bị interrupt giữa chừng — nếu crash sau prune nhưng trước upsert, collection vẫn còn dữ liệu cũ chứ không bị rỗng. Rerun 2 lần liên tiếp với cùng cleaned CSV cho `embed_upsert count=6` và `embed_prune_removed=0`, xác nhận không có vector duplicate.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

**Triệu chứng:** Sau khi chạy `python etl_pipeline.py freshness --manifest artifacts/manifests/manifest_2026-04-15T08-49Z.json`, pipeline trả về `FAIL` với `age_hours=120.928`.

**Phát hiện:** Manifest ghi `latest_exported_at=2026-04-10T08:00:00` — tức dữ liệu raw được export từ ngày 10/04, cách thời điểm chạy pipeline hơn 5 ngày, vượt SLA 24 giờ. Đây không phải lỗi code mà là **anomaly dữ liệu có chủ đích** trong bộ mẫu của lab để nhóm chứng minh freshness check hoạt động đúng.

**Xử lý:** Tôi không sửa timestamp giả tạo mà ghi nhận vào `docs/runbook.md` và `docs/pipeline_architecture.md` mục "Rủi ro đã biết": SLA áp cho thời điểm export từ hệ nguồn (`latest_exported_at`), không phải thời điểm chạy pipeline (`run_timestamp`). Kết luận: freshness FAIL là hành vi **đúng và có kiểm soát** trên data mẫu này.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Run ID thực tế: `2026-04-15T08-49Z`

**Log pipeline (trích):**
```
run_id=2026-04-15T08-49Z
raw_records=10
cleaned_records=6
quarantine_records=4
embed_upsert count=6 collection=day10_kb
freshness_check=FAIL {"latest_exported_at": "2026-04-10T08:00:00", "age_hours": 120.928, "sla_hours": 24.0, "reason": "freshness_sla_exceeded"}
PIPELINE_OK
```

**Cleaned CSV** (`artifacts/cleaned/cleaned_2026-04-15T08-49Z.csv`) xác nhận chunk `policy_refund_v4_1` đã được sửa từ "14 ngày làm việc" → "7 ngày làm việc", và chunk `policy_refund_v4_2` gắn tag `[cleaned: stale_refund_window]`. Quarantine giữ lại 4 bản ghi lỗi (doc_id lạ, ngày sai, HR cũ, duplicate).

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ tách **freshness thành 2 boundary**: `ingest_age` (thời gian từ `latest_exported_at` của hệ nguồn đến lúc pipeline chạy) và `publish_age` (thời gian từ `run_timestamp` đến hiện tại). Khi FAIL, operator biết ngay nguyên nhân là dữ liệu nguồn chậm cập nhật hay pipeline bị treo — giảm thời gian chẩn đoán sự cố đáng kể.
