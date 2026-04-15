# Báo Cáo Cá Nhân — Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Dương Chí Thành
**Vai trò:** Cleaning
**Ngày nộp:** 15/4/2026
**Độ dài yêu cầu:** **400–650 từ**

---

> Viết **"tôi"**, đính kèm **run_id**, **tên file**, **đoạn log** hoặc **dòng CSV** thật.  
> Nếu làm phần clean/expectation: nêu **một số liệu thay đổi** (vd `quarantine_records`, `hits_forbidden`, `top1_doc_expected`) khớp bảng `metric_impact` của nhóm.  
> Lưu: `reports/individual/[ten_ban].md`

---

## 1. Tôi phụ trách phần nào? (80–120 từ)

**File / module:**

- `transform/cleaning_rules.py`
- `contracts/data_contract.yaml`

Tôi chịu trách nhiệm chính cho phần làm sạch dữ liệu và đồng bộ hợp đồng dữ liệu. Tôi đã bổ sung hai rule mới trong `clean_rows` để đảm bảo dữ liệu `cleaned` đủ chất lượng trước khi embed, và hoàn thành phần TODO trong `data_contract.yaml` để owner, SLA freshness, và alert_channel rõ ràng.

**Kết nối với thành viên khác:**

Tôi phối hợp với người phụ trách ingest để xác định các trường raw cần validate, và với người phụ trách monitoring để đưa `alert_channel` vào `data_contract.yaml`.

**Bằng chứng (commit / comment trong code):**

- Thay đổi file `transform/cleaning_rules.py` và `contracts/data_contract.yaml`.
- Rule mới ghi rõ lý do `quarantine` bằng `reason`.

---

## 2. Một quyết định kỹ thuật (100–150 từ)

Tôi quyết định không chỉ dựa vào `doc_id` và `effective_date`, mà phải validate luôn trường `exported_at` vì đó là mốc thời gian publish quan trọng cho downstream. Nếu `exported_at` bị thiếu hoặc không đúng ISO, tôi đưa hàng vào quarantine thay vì giữ lại dữ liệu không rõ nguồn gốc.

Bên cạnh đó, tôi thêm rule kiểm tra độ dài `chunk_text` tối thiểu 8 ký tự. Quyết định này giúp loại bỏ các bản ghi noise quá ngắn, giảm nguy cơ làm lệch embedding và retrieval. Hai rule này cải thiện chất lượng `cleaned_records` và làm rõ nguyên nhân `quarantine_records` bằng mã lý do cụ thể.

---

## 3. Một lỗi hoặc anomaly đã xử lý (100–150 từ)

Triệu chứng: raw export có thể chứa `exported_at` trống hoặc không phải ISO datetime, và một số `chunk_text` chỉ toàn ký tự thưa thớt. Nếu không kiểm tra, những bản ghi này sẽ vào pipeline và gây nhiễu cho downstream retrieval.

Tôi xử lý bằng cách bổ sung `_normalize_exported_at` trong `transform/cleaning_rules.py` và thêm hai lý do quarantine cụ thể: `missing_exported_at` / `invalid_exported_at_format` và `chunk_text_too_short`. Nhờ đó, `quarantine_records` sẽ tăng rõ ràng khi gặp các lỗi này, và nhóm có thể chứng minh metric impact trong `reports/group_report.md`.

---

## 4. Bằng chứng trước / sau (80–120 từ)

Tôi đã chạy pipeline thực tế với `run_id=duong_chi_thanh` và thu được kết quả:

- `raw_records=10`
- `cleaned_records=6`
- `quarantine_records=4`
- `cleaned_csv=artifacts/cleaned/cleaned_duong_chi_thanh.csv`
- `quarantine_csv=artifacts/quarantine/quarantine_duong_chi_thanh.csv`
- `run_id=duong_chi_thanh`

Bảng eval được lưu tại `artifacts/eval/before_after_eval_duong_chi_thanh.csv` và hai dòng mẫu là:

```csv
q_refund_window,Khách hàng có bao nhiêu ngày để yêu cầu hoàn tiền kể từ khi xác nhận đơn?,policy_refund_v4,Yêu cầu được gửi trong vòng 7 ngày làm việc kể từ thời điểm xác nhận đơn hàng.,yes,no,,3
q_p1_sla,SLA phản hồi đầu tiên cho ticket P1 là bao lâu?,sla_p1_2026,Ticket P1 có SLA phản hồi ban đầu 15 phút và resolution trong 4 giờ.,yes,no,,3
```

Đây là bằng chứng thực tế cho thấy rule clean mới đã chạy được với dữ liệu hiện tại và artifacts. 

---

## 5. Cải tiến tiếp theo (40–80 từ)

Nếu có thêm 2 giờ, tôi sẽ mở rộng rule bằng cách thêm kiểm tra `chunk_text` phải chứa ít nhất một keyword hợp lệ từ contract, và bổ sung expectation cho `exported_at`/`effective_date` để cảnh báo sớm thay vì chỉ quarantine.
