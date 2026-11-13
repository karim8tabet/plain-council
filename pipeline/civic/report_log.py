from dataclasses import dataclass
from datetime import date, datetime, timedelta
from io import BytesIO
import re
import openpyxl

@dataclass
class ReportRequest:
    item_ref: str
    directive: str
    status: str
    status_label: str
    closed_by: str
    meeting_date: date | None
    report_back_timing: date | str | None
    assigned_to: str
    is_follow_up: bool

def excel_serial_to_date(n):
    # Excel's day 0 is 1899-12-30 (this accounts for Excel's fake 1900 leap day).
    return date(1899, 12, 30) + timedelta(days=int(float(n)))

def parse_report_log(xlsx_bytes, ref):
    wb = openpyxl.load_workbook(BytesIO(xlsx_bytes), data_only=True)
    ws = wb["Main Data"]
    rows = list(ws.values)
    headers = [re.sub(r"\s+", " ", str(v or "")).strip() for v in rows[0]]
    data = [dict(zip(headers, row)) for row in rows[1:]]
    glossary = {}
    if "Glossary" in wb.sheetnames:
        for row in wb["Glossary"].values:
            vals = [str(v).strip() for v in row if v is not None]
            if len(vals) >= 2:
                glossary[vals[0].lower()] = vals[1]
                code = re.search(r"\((\w+)\)", vals[0])  # "Not Carried Forward (NCF)" -> "ncf"
                if code: glossary[code.group(1).lower()] = vals[1]
    first = [row for row in data if str(row.get("Item Number", "")).strip() == ref]
    follow_refs = {str(row.get("Closed by")).strip() for row in first if row.get("Closed by")}
    selected = [(row, False) for row in first] + [(row, True) for row in data if str(row.get("Item Number", "")).strip() in follow_refs]
    def get(row, *keys): return next((row.get(k) for k in keys if k in row), None)
    result = []
    for row, follow in selected:
        status = str(get(row, "Status") or "").strip().lower()
        meeting, timing = get(row, "Meeting Date"), get(row, "Report Back Timing")
        if isinstance(meeting, datetime): meeting = meeting.date()
        if isinstance(timing, datetime): timing = timing.date()
        result.append(ReportRequest(str(get(row, "Item Number") or ""), str(get(row, "Directive") or ""), status, glossary.get(status, ""), str(get(row, "Closed by") or ""), excel_serial_to_date(meeting) if isinstance(meeting, (int, float)) else meeting if isinstance(meeting, date) else None, excel_serial_to_date(timing) if isinstance(timing, (int, float)) else timing if isinstance(timing, date) else timing, str(get(row, "Assigned to") or ""), follow))
    return result
