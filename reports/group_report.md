# Bao Cao Nhom - Lab Day 10: Data Pipeline & Data Observability

**Ten nhom:** Nhom 12 - 402  
**Thanh vien:**
| Ten | Vai tro (Day 10) | MSSV |
|-----|------------------|------|
| Nguyễn Trọng Thiên Khôi | Ingestion / Pipeline Owner (Người 1) | 2A202600227 |
| Trần Thị Kim Ngân | Cleaning Rules Owner A (Người 2) | 2A202600432 |
| Dương Chí Thành | Cleaning Rules Owner B + Data Contract YAML (Người 3) | 2A202600047 |
| Nguyễn Đức Tiến | Quality / Expectation + Runbook Owner (Người 4) | 2A202600393 |
| Bùi Cao Chinh | Retrieval Eval + Quality Report Owner (Người 5) | 2A202600001 |
| Phan Xuân Quang Linh | Monitoring / Freshness + Group Report Owner (Người 6) | 2A202600492 |

**Ngay nop:** 2026-04-15  
**Repo:** Nhom12-402-Day10  
**Do dai khuyen nghi:** 600-1000 tu

---

> **Nop tai:** `reports/group_report.md`  
> **Artifact chinh dung trong bao cao:** `artifacts/manifests/manifest_before-fix.json`, `artifacts/manifests/manifest_after-fix.json`, `artifacts/eval/before_eval.csv`, `artifacts/eval/after_eval.csv`, `docs/quality_report.md`.

---

## 1. Pipeline tong quan

Pipeline cua nhom xu ly du lieu tu file raw `data/raw/policy_export_dirty.csv`, dong vai tro nhu mot ban export ban tu he nguon truoc khi dua vao vector store phuc vu RAG. Luong chay tong the la ingest -> clean -> validate -> embed -> ghi manifest -> kiem tra freshness. O buoc ingest, he thong doc raw CSV va ghi lai cac chi so `run_id`, `raw_records`. O buoc transform, cac record loi nhu `unknown_doc_id`, thieu `effective_date`, ban HR cu, hoac chunk trung duoc dua sang quarantine CSV. Sau do expectation suite kiem tra du lieu cleaned theo muc `warn` hoac `halt`. Neu pass, pipeline embed du lieu vao ChromaDB bang co che upsert theo `chunk_id` va prune cac id cu de index luon phan anh snapshot publish moi nhat. Cuoi cung pipeline ghi manifest va goi `freshness_check` de danh gia do moi cua du lieu o hai moc ingest va publish. Trong lan chay that dung cho bao cao, nhom dung hai `run_id` la `before-fix` va `after-fix`, the hien ro truoc va sau khi sua loi policy refund.

**Lenh chay mot dong:**

```bash
python etl_pipeline.py run
```

Ngoai ra, nhom dung:

```bash
python etl_pipeline.py run --run-id before-fix --no-refund-fix --skip-validate
python etl_pipeline.py run --run-id after-fix
python etl_pipeline.py freshness --manifest artifacts/manifests/manifest_after-fix.json
```

---

## 2. Cleaning & expectation

Nhom ke thua baseline cleaning gom allowlist `doc_id`, chuan hoa ngay ISO, loai ban HR stale, sua refund window 14 -> 7 ngay, va dedupe. Tren nen do, nhom mo rong them cac diem quan sat chat luong de tranh publish du lieu "nhin co ve dung" nhung van lam retrieval sai. Ve cleaning, nhom duy tri cac rule co tac dong do duoc nhu quarantine ban ghi HR cu theo `effective_date < 2026-01-01`, loai duplicate chunk, va co lap record co schema khong hop le. Ve expectation, nhom bo sung it nhat hai expectation moi la `exported_at_parseable_iso_datetime` va `chunk_id_unique`, trong do expectation lien quan den parse timestamp duoc xep muc `halt` vi anh huong truc tiep den freshness va manifest; con `chunk_id_unique` o muc `warn` de van giu kha nang quan sat khi debug index.

### 2a. Bang metric_impact

| Rule / Expectation moi (ten ngan) | Truoc (so lieu) | Sau / khi inject (so lieu) | Chung cu (log / CSV / commit) |
|-----------------------------------|------------------|-----------------------------|-------------------------------|
| `refund_no_stale_14d_window` | `before-fix`: expectation halt = YES | `after-fix`: expectation halt = NO | `docs/quality_report.md`, `artifacts/eval/before_eval.csv`, `artifacts/eval/after_eval.csv` |
| `exported_at_parseable_iso_datetime` | invalid timestamp = 0 | invalid timestamp = 0, van giu o muc halt de chan publish neu phat sinh loi tuong lai | `reports/individual/nguyen_duc_tien.md` |
| `chunk_id_unique` | duplicate chunk ids = 0 | duplicate chunk ids = 0, dong vai tro canh bao idempotency | `reports/individual/nguyen_duc_tien.md`, logic embed upsert/prune |
| Quarantine HR stale version | policy HR cu bi phat hien va dua khoi cleaned | retrieval giu dung policy 2026 sau clean | `artifacts/eval/before_eval.csv`, `artifacts/eval/after_eval.csv` |

**Rule chinh (baseline + mo rong):**

- Allowlist `doc_id` de chan tai lieu la khong thuoc tap canonical.
- Chuan hoa va kiem tra `effective_date`, `exported_at`.
- Quarantine policy HR cu de khong tron version 2025 va 2026.
- Sua stale refund window tu 14 ngay ve 7 ngay o ban clean.
- Dedupe chunk va giu `chunk_id` on dinh cho buoc embed.

**Vi du 1 lan expectation fail va cach xu ly:**

O run `before-fix`, nhom co y chay voi `--no-refund-fix --skip-validate` de giu lai chunk stale chua "14 ngay lam viec". Ket qua expectation `refund_no_stale_14d_window` tro thanh tin hieu fail quan trong. Sau khi bat lai rule fix refund va chay `after-fix`, loi nay bien mat va retrieval khong con `hits_forbidden`.

---

## 3. Before / after anh huong retrieval hoac agent

**Kich ban inject:**

Nhom mo phong corruption o Sprint 3 bang cach chay pipeline voi `run_id=before-fix`, dong thoi bat `--no-refund-fix --skip-validate`. Muc tieu la giu nguyen stale policy refund "14 ngay lam viec" trong index de kiem tra xem retrieval co con keo phai chunk cu hay khong. Sau do nhom chay lai pipeline chuan voi `run_id=after-fix` de tao snapshot sach.

**Ket qua dinh luong (tu CSV / bang):**

Evidence ro nhat nam o cau `q_refund_window` trong hai file `artifacts/eval/before_eval.csv` va `artifacts/eval/after_eval.csv`. Truoc khi fix, top-1 preview da noi dung "7 ngay lam viec", nhung cot `hits_forbidden=yes` cho thay trong top-k van con chunk chua noi dung cu "14 ngay". Day la truong hop rat quan trong ve observability: neu chi nhin top-1 thi nhom co the tuong pipeline da on, nhung thuc te vector store van con du lieu stale. Sau khi chay lai pipeline chuan, ket qua `after-fix` cho `contains_expected=yes` va `hits_forbidden=no`, chung minh co che clean + prune index da loai bo hoan toan dau vet cua chunk loi.

O cau `q_leave_version`, ca before va after deu dat `contains_expected=yes`, `hits_forbidden=no`, `top1_doc_expected=yes`. Dieu nay cho thay rule quarantine ban HR cu da hoat dong dung ngay tu dau va giu cho retrieval luon tra ve chinh sach nghi phep 2026. Nhu vay, before/after cua nhom khong chi chung minh pipeline sua duoc loi refund ma con cho thay cac rule versioning khac van on dinh trong cung mot bo du lieu.

---

## 4. Freshness & monitoring

Nhom chon SLA freshness la 24 gio. Diem mo rong quan trong la `monitoring/freshness_check.py` khong chi do mot timestamp ma do hai boundary: `latest_exported_at` cua du lieu nguon va `run_timestamp` cua lan publish gan nhat. Voi `manifest_after-fix.json`, ingest timestamp la `2026-04-10T08:00:00`, con publish timestamp la `2026-04-15T09:44:58.801379+00:00`. Vi du lieu nguon da cu hon 24 gio nen trang thai tong the la `FAIL`, nhung boundary publish van o muc gan thoi diem chay va ve mat van hanh co the xem la pipeline vua publish xong. Cach tach hai boundary giup nhom phan biet ro loi do upstream cham export du lieu voi loi do chinh pipeline bi treo hoac khong publish duoc snapshot moi.

---

## 5. Lien he Day 09

Du lieu sau embed co the phuc vu lai bai toan multi-agent Day 09. Nhom dung cung tap tai lieu nghiep vu trong `data/docs/` nhung thay buoc embed thu cong bang pipeline co clean, validate, manifest va freshness check. Collection `day10_kb` vi vay tro thanh snapshot co kiem soat version, giup agent Day 09 truy van dung policy hien hanh nhu refund 7 ngay hoac nghi phep 2026 ma khong lan chunk stale tu cac lan ingest truoc.

---

## 6. Rui ro con lai & viec chua lam

- Repo hien chua co `data/grading_questions.json`, nen `grading_run.py` da san sang nhung file `artifacts/eval/grading_run.jsonl` chi co the tao khi giang vien hoac nhom bo sung bo cau hoi grading.
- `artifacts/logs/` hien chua luu log chay thuc te, nen bao cao dang bam vao manifest va eval CSV la chinh.
- Freshness hien van dua tren timestamp cua file CSV mau; neu chuyen sang van hanh thuc te can doc watermark hoac thoi diem export tu nguon that.
- Nhom chua tich hop LLM-as-a-judge cho quality evaluation; hien tai van chu yeu dua tren retrieval + keyword evidence.

