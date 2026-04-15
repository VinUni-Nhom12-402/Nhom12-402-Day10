# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Bùi Cao Chinh - **MHV**: 2A202600001
**Vai trò:** Evaluation
**Ngày nộp:** 2026-04-15

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**
Tôi chịu trách nhiệm chính về module đánh giá truy xuất dữ liệu trong file `eval_retrieval.py` và tổng hợp bằng chứng chất lượng vào file báo cáo chung `docs/quality_report.md`.

**Kết nối với thành viên khác:**
Tôi làm việc chặt chẽ với người phụ trách **Cleaning** để hiểu các rule sửa lỗi và người phụ trách **Monitoring** để đồng bộ các chỉ số về Freshness. Công việc của tôi là người "kiểm chứng cuối cùng" (Gatekeeper) để đảm bảo dữ liệu sau khi qua pipeline thực sự cải thiện được độ chính xác khi AI truy xuất.

**Bằng chứng (commit / comment trong code):**
Tôi đã thực hiện các lần chạy pipeline thực tế với `run_id: before-fix` (chế độ inject lỗi) và `after-fix` (chế độ sạch) để tạo ra các tập tin bằng chứng `before_eval.csv` và `after_eval.csv` trong thư mục `artifacts/eval/`.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Một quyết định kỹ thuật quan trọng tôi đã thực hiện (phối hợp cùng nhóm monitoring) là nâng cấp cơ chế kiểm tra độ tươi của dữ liệu (Freshness Check) từ kiểm tra đơn lẻ sang **kiểm tra hai ranh giới (Dual-Boundary Freshness)**.

Thay vì chỉ kiểm tra một mốc thời gian duy nhất là khi dữ liệu được nạp vào Vector DB, tôi đã tách biệt thành: **Ingest Age** (độ trễ từ hệ thống nguồn) và **Publish Age** (độ trễ từ lần cuối pipeline chạy thành công). Quyết định này cực kỳ quan trọng cho tính quan sát dữ liệu (Data Observability): nếu hệ thống báo FAIL về Freshness, chúng tôi có thể biết ngay nguyên nhân là do "Dữ liệu nguồn chưa được export mới" hay do "Pipeline của chúng tôi bị treo không cập nhật được vào ChromaDB". Điều này giúp giảm thời gian chẩn đoán sự cố (MTTD) và đảm bảo tính minh bạch cho hệ thống RAG.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Trong quá trình thực hiện Sprint 3, tôi đã xử lý sự cố về **"Rò rỉ dữ liệu cũ" (Stale Data Leakage)** liên quan đến chính sách hoàn tiền (`q_refund_window`).

**Triệu chứng:** Khi chạy evaluation ở bản `before-fix`, mặc dù Top-1 trả về nội dung có vẻ đúng, nhưng hệ thống eval do tôi quản lý đã báo `hits_forbidden=yes`.
**Phát hiện:** Qua kiểm tra script `eval_retrieval.py`, tôi phát hiện trong Top-3 kết quả truy xuất vẫn còn tồn tại chunk chứa "14 ngày làm việc" (chính sách cũ đã hết hạn). Đây là một lỗi nghiêm trọng vì AI có thể sử dụng thông tin sai lệch này để trả lời khách hàng.
**Xử lý:** Tôi đã phối hợp cùng bộ phận Cleaning để áp dụng rule sửa lỗi 14 ngày về 7 ngày và đảm bảo cơ chế **Pruning** (xóa ID cũ) trong `cmd_embed_internal` hoạt động chính xác. Kết quả ở bản `after-fix` đã sạch hoàn toàn lỗi này, đưa `hits_forbidden` về `no`.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Dưới đây là bằng chứng trích xuất từ `artifacts/eval/` (Run ID: `before-fix` vs `after-fix`) cho câu hỏi `q_refund_window`:

| Run ID | hits_forbidden | contains_expected | Top-1 Preview |
|--------|----------------|-------------------|---------------|
| `before-fix` | **yes** | yes | "Yêu cầu được gửi trong vòng 7 ngày làm việc..." |
| `after-fix` | **no** | yes | "Yêu cầu được gửi trong vòng 7 ngày làm việc..." |

Việc loại bỏ hoàn toàn `hits_forbidden` chứng minh pipeline đã thực hiện thành công việc làm sạch và đồng bộ hóa snapshot dữ liệu trong Vector Store, không để lại dấu vết của chính sách cũ.

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ tích hợp **LLM-as-a-judge** vào script `eval_retrieval.py`. Thay vì chỉ kiểm tra keyword cứng (như "7 ngày"), tôi sẽ sử dụng một model LLM nhỏ để chấm điểm ngữ nghĩa của các chunk truy xuất được, giúp phát hiện các lỗi sai tinh vi hơn mà phương pháp keyword matching có thể bỏ sót, từ đó nâng cấp độ tin cậy cho báo cáo chất lượng lên mức cao nhất.
