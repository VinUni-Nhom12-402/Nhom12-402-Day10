# Runbook — Lab Day 10 (incident tối giản)

---

## Symptom

> User / agent thấy gì? (VD: trả lời “14 ngày” thay vì 7 ngày)
>User hoặc agent trả lời sai nội dung do ingest nhầm chunk stale hoặc sai version. Triệu chứng điển hình:

- Câu hỏi refund trả về 14 ngày làm việc thay vì 7 ngày làm việc.
- Câu hỏi HR 2026 có thể dính chunk cũ 10 ngày phép năm thay vì 12 ngày phép năm.
- Pipeline dừng ở bước validate vì expectation halt fail.
- Lệnh freshness trả về FAIL vì latest_exported_at vượt SLA.

---

## Detection

> Metric nào báo? (freshness, expectation fail, eval `hits_forbidden`)
> Tín hiệu phát hiện chính:

- File `artifacts/logs/run_<run_id>.log` có dòng `expectation[...] FAIL`.
- `eval_retrieval.py` cho `hits_forbidden=yes`, dac biet o `q_refund_window` neu top-k van con chunk `14 ngay`.
- `contains_expected=no` hoac `top1_doc_expected=no` o cau `q_leave_version`.
- `python etl_pipeline.py freshness --manifest ...` tra ve `FAIL`.
- `quarantine_records` tang bat thuong hoac `cleaned_records` giam manh so voi run truoc.

---

## Diagnosis

| Bước | Việc làm                              | Kết quả mong đợi                                                                                                               |
| ---- | ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ |
| 1    | Kiểm tra `artifacts/manifests/*.json` | Xac dinh run dang phuc vu index va dau hieu stale/freshness                                                                    |
| 2    | Mở `artifacts/quarantine/*.csv`       | Thay record bi loai do `unknown_doc_id`, `missing_effective_date`, `stale_hr_policy_effective_date`, `duplicate_chunk_text`... |
| 3    | Chạy `python eval_retrieval.py`       | Xac nhan retrieval co dinh forbidden chunk hay khong                                                                           |

---

## Mitigation

> Rerun pipeline, rollback embed, tạm banner “data stale”, …
> Huong xu ly:

- Neu fail do expectation `halt`, sua rule clean hoac source data roi chay lai `python etl_pipeline.py run --run-id <new-run>`.
- Neu retrieval tra ve `14 ngay`, khong dung `--no-refund-fix`; rerun pipeline chuan de publish lai cleaned snapshot.
- Neu HR version bi lan, kiem tra record `hr_leave_policy` co `effective_date < 2026-01-01` va xac nhan chunk cu da vao quarantine.
- Neu freshness `FAIL`, xac nhan lai SLA hoac timestamp export. Trong demo co the giai thich day la data snapshot cu; trong van hanh that can ingest lai nguon moi.
- Neu embed/index sai, xoa collection test hoac doi `CHROMA_COLLECTION`, sau do rerun pipeline clean de tao publish boundary moi.

---

## Prevention

> Thêm expectation, alert, owner — nối sang Day 11 nếu có guardrail.
> Bien phap phong ngua:

- Giu expectation `refund_no_stale_14d_window` o muc `halt` de chan publish khi chunk stale quay lai.
- Giu expectation `hr_leave_no_stale_10d_annual` o muc `halt` de bao ve policy phien ban 2026.
- Dung `exported_at_parseable_iso_datetime` de freshness khong bi sai do timestamp ban.
- Dung `chunk_id_unique` de giam sat tinh idempotent cua buoc embed/upsert.
- Ghi `run_id`, `cleaned_records`, `quarantine_records`, `manifest_written` trong moi run de truy vet.
- Gan owner va alert channel trong `contracts/data_contract.yaml` de khi fail co nguoi nhan va xu ly.
