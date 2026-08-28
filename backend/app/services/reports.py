from __future__ import annotations

import base64
from io import BytesIO

import redis
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas

from app.schemas.finance import FinanceSummary


def _cents(value: int) -> str:
    return f"${value / 100:,.2f}"


def render_finance_report_pdf(summary: FinanceSummary) -> bytes:
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER
    y = height - inch

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(inch, y, f"Finance report — {summary.month}")
    y -= 0.5 * inch

    pdf.setFont("Helvetica", 12)
    for label, value in (
        ("Income", _cents(summary.income_cents)),
        ("Expenses", _cents(summary.expense_cents)),
        ("Net", _cents(summary.net_cents)),
        ("Savings rate", f"{summary.savings_rate * 100:.0f}%"),
        ("Uncategorized spend", _cents(summary.uncategorized_cents)),
        ("Committed bills", _cents(summary.upcoming_bills_cents)),
    ):
        pdf.drawString(inch, y, f"{label}:")
        pdf.drawRightString(width - inch, y, value)
        y -= 0.3 * inch

    y -= 0.2 * inch
    pdf.setFont("Helvetica-Bold", 13)
    pdf.drawString(inch, y, "Spending by category")
    y -= 0.32 * inch
    pdf.setFont("Helvetica", 11)
    for row in summary.by_category:
        marker = "  (over budget)" if row.over else ""
        budget = f" / {_cents(row.budget_cents)}" if row.budget_cents is not None else ""
        pdf.drawString(inch, y, f"{row.name}{marker}")
        pdf.drawRightString(width - inch, y, f"{_cents(row.spent_cents)}{budget}")
        y -= 0.28 * inch
        if y < inch:
            pdf.showPage()
            y = height - inch
            pdf.setFont("Helvetica", 11)

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()


def _report_key(user_id: int, month: str) -> str:
    return f"report:finance:{user_id}:{month}"


def store_report(client: redis.Redis, user_id: int, month: str, pdf: bytes) -> None:
    client.set(_report_key(user_id, month), base64.b64encode(pdf).decode(), ex=7 * 86400)


def load_report(client: redis.Redis, user_id: int, month: str) -> bytes | None:
    raw = client.get(_report_key(user_id, month))
    return base64.b64decode(raw) if raw is not None else None
