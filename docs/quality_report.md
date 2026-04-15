# Quality report — Lab Day 10 (nhóm)

**run_id:** after-fix  
**Ngày:** 2026-04-15 (UTC+7)

---

## 1. Tóm tắt số liệu

| Chỉ số | Trước (before-fix) | Sau (after-fix) | Ghi chú |
|--------|-------|-----|---------|
| raw_records | 10 | 10 | |
| cleaned_records | 6 | 6 | |
| quarantine_records | 4 | 4 | |
| Expectation halt? | YES | NO | Lỗi 'refund_no_stale_14d_window' bẫy được ở bản Trước. |

---

## 2. Before / after retrieval (bắt buộc)

> Dẫn link tới: [before_eval.csv](../artifacts/eval/before_eval.csv) và [after_eval.csv](../artifacts/eval/after_eval.csv).

**Câu hỏi then chốt:** refund window (`q_refund_window`)  
**Trước (Corruption):**
- `contains_expected: yes`, `hits_forbidden: yes`
- Top-1 Preview: "Yêu cầu được gửi trong vòng 7 ngày làm việc kể từ thời điểm xác nhận đơn hàng." (Tuy nhiên trong top-k vẫn chứa chunk 14 ngày).

**Sau (Cleaned):**
- `contains_expected: yes`, `hits_forbidden: no`
- Top-1 Preview: "Yêu cầu được gửi trong vòng 7 ngày làm việc kể từ thời điểm xác nhận đơn hàng." (Không còn record 14 ngày trong index).

**Merit (khuyến nghị):** versioning HR — `q_leave_version` (`contains_expected`, `hits_forbidden`, cột `top1_doc_expected`)

**Trước & Sau:**
- `contains_expected: yes`, `hits_forbidden: no`, `top1_doc_expected: yes`
- Kết quả: Đạt yêu cầu ngay từ bản Before nhờ rule quarantine dựa trên `effective_date < 2026-01-01` đã hoạt động tốt.

---

## 3. Freshness & monitor (Distinction bonus: 2 boundary)

> Kết quả `freshness_check` (FAIL). Chúng tôi đã nâng cấp logic để đo đồng thời 2 mốc thời gian (boundaries):

| Tham số | Giá trị (Timestamp) | Độ trễ (Hours) | Trạng thái (SLA 24h) |
|---------|---------|----------|-----------|
| **Ingest** (Dữ liệu nguồn) | 2026-04-10T08:00:00 | ~122h | **FAIL** (Dữ liệu mẫu cũ) |
| **Publish** (Sau Pipeline) | 2026-04-15T09:45:00 | ~0.1h | **PASS** (Vừa chạy xong) |

**Giải thích SLA:** 
- Hệ thống báo **FAIL** tổng thể vì dữ liệu nguồn đã quá cũ (>24h). 
- Tuy nhiên, chỉ số **Publish** cho thấy Pipeline vẫn đang hoạt động tốt và vừa cập nhật dữ liệu mới nhất vào Vector Store thành công. Việc đo 2 mốc giúp phân biệt lỗi do "hệ thống nguồn chậm cấp data" hay lỗi do "pipeline bị treo".

---

## 4. Corruption inject (Sprint 3)

> **Mô tả:** Chúng tôi đã cố ý làm hỏng dữ liệu bằng cách sử dụng flag `--no-refund-fix` kết hợp với `--skip-validate`.
- **Duplicate:** Pipeline tự động xử lý (dedupe) và đưa vào quarantine.
- **Stale Policy:** Record chứa "14 ngày làm việc" thay vì "7 ngày" được giữ nguyên. 
- **Cách phát hiện:** Được phát hiện qua `expectation[refund_no_stale_14d_window]` với trạng thái **FAIL (halt)**. Bằng chứng evaluation cho thấy `hits_forbidden=yes`.

---

## 5. Hạn chế & việc chưa làm

- Chưa tích hợp kiểm tra dữ liệu bằng LLM.
- SLA freshness đang dựa trên timestamp cứng trong file CSV mẫu, chưa phản ánh đúng pipeline thời gian thực nếu không cập nhật file nguồn.
