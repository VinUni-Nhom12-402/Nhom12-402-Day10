"""
Kiểm tra freshness từ manifest pipeline (SLA đơn giản theo giờ).

Sinh viên mở rộng: đọc watermark DB, so sánh với clock batch, v.v.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Tuple


def parse_iso(ts: str) -> datetime | None:
    if not ts:
        return None
    try:
        # Cho phép "2026-04-10T08:00:00" không có timezone
        if ts.endswith("Z"):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except ValueError:
        return None


def check_manifest_freshness(
    manifest_path: Path,
    *,
    sla_hours: float = 24.0,
    now: datetime | None = None,
) -> Tuple[str, Dict[str, Any]]:
    """
    Trả về ("PASS" | "WARN" | "FAIL", detail dict).

    Đo 2 ranh giới (Distinction requirement):
    1) Ingest: Khoảng cách từ lúc dữ liệu được export từ nguồn (latest_exported_at).
    2) Publish: Khoảng cách từ lúc pipeline hoàn thành (run_timestamp).
    """
    now = now or datetime.now(timezone.utc)
    if not manifest_path.is_file():
        return "FAIL", {"reason": "manifest_missing", "path": str(manifest_path)}

    data: Dict[str, Any] = json.loads(manifest_path.read_text(encoding="utf-8"))
    
    # Boundary 1: Ingest (Dữ liệu nguồn)
    ts_ingest = data.get("latest_exported_at")
    dt_ingest = parse_iso(str(ts_ingest)) if ts_ingest else None
    age_ingest = (now - dt_ingest).total_seconds() / 3600.0 if dt_ingest else None

    # Boundary 2: Publish (Hệ thống sau pipeline)
    ts_publish = data.get("run_timestamp")
    dt_publish = parse_iso(str(ts_publish)) if ts_publish else None
    age_publish = (now - dt_publish).total_seconds() / 3600.0 if dt_publish else None

    detail = {
        "ingest": {
            "timestamp": ts_ingest,
            "age_hours": round(age_ingest, 3) if age_ingest is not None else None,
        },
        "publish": {
            "timestamp": ts_publish,
            "age_hours": round(age_publish, 3) if age_publish is not None else None,
        },
        "sla_hours": sla_hours,
    }

    # FAIL nếu bất kỳ cái nào vượt SLA (ưu tiên cái cũ hơn để báo FAIL)
    status = "PASS"
    if age_publish is not None and age_publish > sla_hours:
        status = "FAIL"
        detail["reason"] = "publish_sla_exceeded"
    if age_ingest is not None and age_ingest > sla_hours:
        status = "FAIL"
        detail["reason"] = "ingest_sla_exceeded"
    
    if dt_ingest is None and dt_publish is None:
        return "WARN", {"reason": "no_timestamps_in_manifest", "manifest": data}

    return status, detail
