# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Trần Thị Kim Ngân 
**Vai trò:** Cleaning Rules Owner A
**Ngày nộp:** 15/4/2026
**Độ dài yêu cầu:** **400–650 từ** (ngắn hơn Day 09 vì rubric slide cá nhân ~10% — vẫn phải đủ bằng chứng)

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**
- `transform/cleaning_rules.py`: Chịu trách nhiệm bổ sung logic làm sạch và chuẩn hóa chuỗi chunk.

**Kết nối với thành viên khác:**
Trong đồ án Lab Day 10, tôi giữ vai trò tiếp nhận Data từ bạn làm luồng Ingestion. Tôi chịu trách nhiệm bảo vệ cửa ngõ, sàng lọc mã độc HTML, tước bỏ thông tin vô nghĩa và đẩy bản ghi không hợp lệ vào khu cách ly. Sau đó, tôi bàn giao file làm sạch `cleaned_*.csv` chất lượng cao cho bạn làm bộ phận Embed để khởi tạo không gian index trên Vector Store an toàn.

**Bằng chứng (commit / comment trong code):**
Tôi đã thiết kế "Rule 1 (Mới)" bắt đầu từ dòng 118 của file `cleaning_rules.py`. Comment chỉ rõ: `# Rule 1 (Mới): Lọc và xóa bỏ các HTML tags rác hoặc phần tử vỡ ra khỏi chunk_text`.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

> VD: chọn halt vs warn, chiến lược idempotency, cách đo freshness, format quarantine.

Một quyết định kỹ thuật quan trọng của tôi là áp dụng chiến lược "Quarantine thay vì Drop" cho dữ liệu hỏng định dạng nhẹ. Khi một dòng dữ liệu `chunk_text` tình cờ dính các thẻ như `<script>`, tôi dùng Regex `re.sub(r'<[^>]+>', '', text)` để gột rửa thay vì vứt bỏ nó ngay lập tức (Drop khỏi pipeline).

Nếu sau quá trình bóc tách HTML này, chuỗi text trở nên rỗng (ví dụ toàn bộ nội dung ban đầu chỉ là HTML rác, không có text thực sự), tôi mới gán lý do `"empty_after_html_strip"` và đẩy vào bảng Quarantine. Nhờ kỹ thuật này, data không bị hao hụt oan uổng, đồng thời vẫn cách ly triệt để dị bản để không phá hoại thuật toán Vector Search. Kèm theo đó, tại Expectation, tôi cấu hình kiểm soát Rule chặn HTML ở mức severity `halt`, bắt hệ thống đóng băng và bảo vệ data khỏi nhiễu LLM nếu để xổng rác.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

> Mô tả triệu chứng → metric/check nào phát hiện → fix.

Anomaly bất thường tôi ghi nhận là một số tài liệu Export từ bộ văn bản IT Helpdesk chứa nguyên xi cấu trúc giao diện hoặc lọt lệnh thực thi như `<script>alert('hack');</script>`. Triệu chứng gặp phải là file CSV xuất ra bị vỡ cấu trúc và các chunk ngắn có nội dung lạ. Nếu đưa trực tiếp data này vào mô hình Embed, độ chính xác của câu trả lời Retriever sẽ bị méo mó, LLM dễ mắc lỗi ảo giác khi trích xuất.

Metric tôi dùng để bắt vi phạm chính là chiều dài thực tế sau khi Strip HTML. Tại vòng lặp `clean_rows` trong module `cleaning_rules.py`, tôi cho kiểm tra nhạy dấu `<` và `>`. Tiến hành fix triệt để. Các dòng test cho thấy pipeline đã đẩy các thẻ này sang khoanh vùng cách ly một cách mượt mà và an toàn.

---

## 4. Bằng chứng trước / sau (80–120 từ)

> Dán ngắn 2 dòng từ `before_after_eval.csv` hoặc tương đương; ghi rõ `run_id`.

Tôi xác nhận sự thay đổi tích cực thông qua log nội bộ của phiên chạy `run_id=test-rule1`.

Trong quá trình đưa 12 bản ghi thô (raw) vào, kết quả sau rule thể hiện như sau:
- `raw_records=12`
- `cleaned_records=8`
- `quarantine_records=4` (Tăng từ 2 lên 4)

Điều đó đồng nghĩa với việc Rule 1 đã làm đúng chức năng khóa mục tiêu. Trong file cách ly xuất ra báo lỗi chuẩn xác theo mã của tôi:
`12,it_helpdesk_faq,"<script>alert('hack');</script>",2026-02-01,...,empty_after_html_strip`

---

## 5. Cải tiến tiếp theo (40–80 từ)

> Nếu có thêm 2 giờ — một việc cụ thể (không chung chung).

Nếu có thêm 2 giờ phát triển Data Pipeline, tôi sẽ thiết lập bộ luật NLP sử dụng gói thư viện Presidio Analyzer của Microsoft. Chức năng dự kiến là dùng module rà soát (AnalyzerEngine) phân tích `chunk_text`, định vị Masking (làm mờ / thay thế chuỗi bằng các biến ẩn danh) đối với dữ liệu PII như số thẻ, số tài khoản VPN của user lọt vào, nâng cấp Data Contract lên tiêu chuẩn bảo vệ danh tính mức cao nhất.
