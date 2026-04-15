# Bao Cao Ca Nhan - Lab Day 10: Data Pipeline & Observability

**Ho va ten:** Phan Xuan Quang Linh - MSSV: 2A202600492  
**Vai tro:** Monitoring / Freshness + Group Report  
**Ngay nop:** 2026-04-15

---

## 1. Toi phu trach phan nao? (80-120 tu)

**File / module:**

Toi phu trach ba dau viec chinh la `monitoring/freshness_check.py`, `grading_run.py`, va `reports/group_report.md`. Trong `freshness_check.py`, toi mo rong logic freshness de khong chi kiem tra mot moc thoi gian ma kiem tra dong thoi do tre cua du lieu nguon va do tre cua lan publish pipeline. Trong `grading_run.py`, toi chuan bi script de doc `data/grading_questions.json`, truy van collection Chroma, va xuat JSONL cho giang vien. Ngoai ra, toi tong hop evidence tu manifest, eval CSV, quality report va cac bao cao ca nhan de hoan thien `reports/group_report.md`.

**Ket noi voi thanh vien khac:**

Toi phoi hop voi ban lam expectation va runbook de thong nhat cach dien giai PASS/WARN/FAIL, va voi ban lam eval de lay so lieu before/after cho cac cau `q_refund_window` va `q_leave_version`. Nhiem vu cua toi la bien cac chi so ky thuat nay thanh phan monitoring de nhom giai thich duoc vi sao du lieu stale va pipeline publish la hai van de khac nhau.

**Bang chung (commit / comment trong code):**

Bang chung ro nhat nam trong `monitoring/freshness_check.py` voi hai boundary `latest_exported_at` va `run_timestamp`, trong `grading_run.py` voi output du kien `artifacts/eval/grading_run.jsonl`, va trong `reports/group_report.md` o phan Freshness & monitoring.

---

## 2. Mot quyet dinh ky thuat (100-150 tu)

Quyet dinh ky thuat quan trong nhat cua toi la chon cach do freshness theo hai boundary thay vi mot boundary. Neu chi do `run_timestamp`, he thong se bao PASS ngay sau moi lan pipeline chay xong, nhung cach do do co the che mat su that la du lieu nguon da cu. Neu chi do `latest_exported_at`, he thong se bao FAIL nhung nhom lai khong biet pipeline co bi treo hay van publish deu. Vi vay, toi tach freshness thanh hai phan: `ingest` do khoang cach tu luc he nguon export du lieu, con `publish` do khoang cach tu luc pipeline hoan thanh. Quy tac nay duoc viet trong `check_manifest_freshness()` va tra ve detail dict gom `ingest.age_hours`, `publish.age_hours`, `sla_hours`, kem `reason`. Nho do, khi nhom doc manifest `after-fix`, chung toi biet du lieu nguon stale hon 24 gio nhung pipeline van vua publish thanh cong.

---

## 3. Mot loi hoac anomaly da xu ly (100-150 tu)

Anomaly toi xu ly la truong hop monitoring de bao dong "FAIL" nhung neu giai thich khong ro thi de bi hieu nham thanh pipeline loi. O `manifest_after-fix.json`, toi thay `latest_exported_at` la `2026-04-10T08:00:00`, trong khi `run_timestamp` la `2026-04-15T09:44:58.801379+00:00`. Neu he thong chi in mot dong `freshness_check=FAIL`, nguoi doc se kho biet nguyen nhan la du lieu nguon cu hay pipeline publish tre. Toi xu ly bang cach sua `freshness_check.py` de xuat chi tiet tung boundary va uu tien gan `reason` ro rang nhu `ingest_sla_exceeded` hoac `publish_sla_exceeded`. Sau do, toi dua cach giai thich nay vao `group_report.md` va `docs/quality_report.md`: ingest FAIL vi file raw mau cu, nhung publish PASS vi pipeline vua chay xong. Cach xu ly nay giup monitoring tro nen giai thich duoc, khong chi bao loi.

---

## 4. Bang chung truoc / sau (80-120 tu)

Toi dung hai run `before-fix` va `after-fix` lam bang chung cho phan monitoring va tong hop bao cao.

- `artifacts/manifests/manifest_before-fix.json`: `run_id=before-fix`, `no_refund_fix=true`, `skipped_validate=true`, `latest_exported_at=2026-04-10T08:00:00`
- `artifacts/manifests/manifest_after-fix.json`: `run_id=after-fix`, `no_refund_fix=false`, `skipped_validate=false`, `run_timestamp=2026-04-15T09:44:58.801379+00:00`

Toi doi chieu them voi eval CSV:

- `before_eval.csv`: `q_refund_window ... contains_expected=yes, hits_forbidden=yes`
- `after_eval.csv`: `q_refund_window ... contains_expected=yes, hits_forbidden=no`

Hai cap bang chung nay cho thay sau khi nhom publish lai snapshot sach, monitoring co the noi ro ca tinh trang freshness va tac dong cua clean len retrieval.

---

## 5. Cai tien tiep theo (40-80 tu)

Neu co them 2 gio, toi se nang cap `grading_run.py` de ghi them metadata lien quan den run dang duoc cham, vi du `run_id`, `manifest_path`, va boundary freshness tuong ung. Khi do file `grading_run.jsonl` se khong chi dung cho cham retrieval ma con noi duoc ket qua grading voi dung snapshot du lieu ma nhom da publish.
