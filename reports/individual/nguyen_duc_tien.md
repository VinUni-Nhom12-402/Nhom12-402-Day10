# Báo Cáo Cá Nhân - Lab Day 10: Data Pipeline & Observability

**Họ và tên:** Nguyễn Đức Tiến 
**Mã HV:** 0982872004
**Vai trò:** Quality / Expectation + Runbook Owner  
**Ngày nộp:** 15/04/2026  

---

## 1. Tôi phụ trách phần nào?

Tôi phụ trách phần expectation suite và runbook vận hành tối thiểu cho pipeline Day 10. Hai file tôi làm chính là `quality/expectations.py` và `docs/runbook.md`. Ở `quality/expectations.py`, tôi bổ sung thêm các expectation để kiểm tra chất lượng dữ liệu sau bước clean, đặc biệt là các lỗi có thể làm ảnh hưởng trực tiếp đến freshness hoặc bước embed. Ở `docs/runbook.md`, tôi viết quy trình phát hiện, chẩn đoán và xử lý incident khi pipeline trả về dữ liệu stale hoặc sai version.

Tôi phối hợp với thành viên làm phần cleaning để hiểu dữ liệu nào đã bị đưa vào quarantine và với thành viên chạy pipeline để lấy `run_id=expect-check` cùng log thực tế. Bằng chứng làm việc của tôi nằm ngay trong code: trong `quality/expectations.py` có hai expectation mới là `exported_at_parseable_iso_datetime` và `chunk_id_unique`, còn `docs/runbook.md` được điền đầy đủ 5 phần Symptom, Detection, Diagnosis, Mitigation, Prevention.

---

## 2. Một quyết định kỹ thuật

Quyết định kỹ thuật quan trọng nhất của tôi là phân biệt rõ expectation nào nên là `halt`, expectation nào chỉ nên là `warn`. Tôi đặt `exported_at_parseable_iso_datetime` ở mức `halt` vì freshness check và manifest phụ thuộc trực tiếp vào timestamp này. Nếu `exported_at` sai format mà vẫn cho publish tiếp, nhóm có thể kết luận sai rằng dữ liệu đang fresh hoặc stale. Đây là lỗi có thể làm sai quyết định vận hành nên cần chặn pipeline.

Ngược lại, tôi đặt `chunk_id_unique` ở mức `warn`. Lý do là `chunk_id` được dùng làm khóa upsert cho Chroma nên trùng ID là rủi ro thật, nhưng trong bối cảnh lab này tôi muốn hệ thống vẫn log được cảnh báo để nhóm còn nhìn thấy các chỉ số khác trước khi quyết định dừng toàn bộ pipeline. Cách chia `halt` và `warn` này giúp pipeline vừa có tính kiểm soát, vừa dễ quan sát hơn khi debug.

---

## 3. Một lỗi hoặc anomaly đã xử lý

Anomaly tôi tập trung xử lý là nguy cơ dữ liệu “nhìn có vẻ sạch” nhưng vẫn gây lỗi ở bước monitor hoặc retrieval. Từ dữ liệu mẫu và file quarantine của `run_id=expect-check`, tôi thấy hệ thống đã loại 4 bản ghi lỗi, trong đó có một dòng HR cũ: `hr_leave_policy ... 10 ngay phep nam ... stale_hr_policy_effective_date`, một dòng duplicate refund, một dòng thiếu `effective_date`, và một `doc_id` lạ là `legacy_catalog_xyz_zzz`. Điều này cho thấy pipeline đã có nền tảng clean đúng, nhưng expectation vẫn cần chặn thêm các rủi ro ở lớp quality.

Tôi xử lý bằng cách thêm expectation kiểm tra `exported_at` có parse được và `chunk_id` có duy nhất không. Sau khi chạy `run_id=expect-check`, log ghi nhận:
- `expectation[exported_at_parseable_iso_datetime] OK (halt) :: invalid_exported_at_rows=0`
- `expectation[chunk_id_unique] OK (warn) :: duplicate_chunk_ids=0`

Như vậy, phần quality không chỉ kiểm tra nội dung policy stale mà còn kiểm tra được khả năng monitoring và tính an toàn của bước embed.

---

## 4. Bằng chứng trước / sau

Tôi dùng `run_id=expect-check` làm bằng chứng chính. Vì môi trường hiện tại bị lỗi Chroma disk I/O ở bước embed, tôi dùng log và quarantine CSV như bằng chứng tương đương thay cho eval CSV.

Trước clean/quarantine, file `artifacts/quarantine/quarantine_expect-check.csv` có dòng:
`7,hr_leave_policy,...,2025-01-01,...,stale_hr_policy_effective_date`
Điều này cho thấy dữ liệu raw thực sự có version HR cũ.

Sau khi thêm expectation và chạy lại pipeline, file `artifacts/logs/run_expect-check.log` có các dòng:
`expectation[hr_leave_no_stale_10d_annual] OK (halt) :: violations=0`
`expectation[exported_at_parseable_iso_datetime] OK (halt) :: invalid_exported_at_rows=0`
`expectation[chunk_id_unique] OK (warn) :: duplicate_chunk_ids=0`

Các dòng này cho thấy dữ liệu cleaned đã vượt qua các kiểm tra mà tôi phụ trách.

---

## 5. Cải tiến tiếp theo

Nếu có thêm 2 giờ, tôi sẽ thêm một expectation kiểm tra phân bố số lượng bản ghi theo `doc_id` để phát hiện trường hợp một tài liệu quan trọng bị mất toàn bộ chunk sau bước clean. Đây là lỗi chưa chắc làm pipeline fail ngay nhưng có thể làm retrieval trả lời thiếu thông tin.
