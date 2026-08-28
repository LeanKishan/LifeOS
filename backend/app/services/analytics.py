from __future__ import annotations

import csv
import io
from collections import defaultdict
from collections.abc import Iterable
from datetime import date, datetime, timedelta

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.finance import Category, Transaction, TransactionKind
from app.models.job_tracker import Application, ApplicationStatus
from app.models.learning import Flashcard, Lesson
from app.models.projects import Task, TaskPriority
from app.schemas.analytics import (
    AnalyticsOverview,
    DateRange,
    FinanceTrend,
    JobSearchStats,
    LearningStats,
    MonthPoint,
    NamedAmount,
    Productivity,
    WeekPoint,
)

MAX_RANGE_DAYS = 366
DEFAULT_RANGE_DAYS = 90


def resolve_range(date_from: date | None, date_to: date | None) -> tuple[date, date]:
    end = date_to or date.today()
    start = date_from or (end - timedelta(days=DEFAULT_RANGE_DAYS))
    if end < start:
        raise LookupError("`to` must not be before `from`")
    if (end - start).days > MAX_RANGE_DAYS:
        raise LookupError(f"range too large (max {MAX_RANGE_DAYS} days)")
    return start, end


def _week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def _weekly(points: Iterable[tuple[date, int]]) -> list[WeekPoint]:
    buckets: dict[date, int] = defaultdict(int)
    for day, amount in points:
        buckets[_week_start(day)] += amount
    return [WeekPoint(week=w.isoformat(), count=c) for w, c in sorted(buckets.items())]


# --------------------------------------------------------------------------- #
# Sections
# --------------------------------------------------------------------------- #
def _productivity(db: Session, user_id: int, start: date, end: date) -> Productivity:
    tasks = list(db.scalars(select(Task).where(Task.user_id == user_id)))
    total = len(tasks)
    done = [t for t in tasks if t.done]

    by_priority = {p.value: 0 for p in TaskPriority}
    for task in tasks:
        if not task.done:
            by_priority[task.priority.value] += 1

    today = date.today()
    overdue = sum(
        1 for t in tasks if not t.done and t.due_on is not None and t.due_on < today
    )

    done_in_range = [
        t
        for t in done
        if t.completed_at is not None and start <= t.completed_at.date() <= end
    ]
    cycle_days = [
        (t.completed_at - t.created_at).days
        for t in done_in_range
        if t.completed_at is not None
    ]
    avg_cycle = round(sum(cycle_days) / len(cycle_days), 2) if cycle_days else None

    return Productivity(
        tasks_total=total,
        tasks_done=len(done),
        completion_rate=round(len(done) / total, 3) if total else 0.0,
        avg_cycle_days=avg_cycle,
        overdue=overdue,
        by_priority=by_priority,
        done_by_week=_weekly(
            (t.completed_at.date(), 1) for t in done_in_range if t.completed_at
        ),
    )


def _finance(db: Session, user_id: int, start: date, end: date) -> FinanceTrend:
    rows = db.execute(
        select(Transaction.occurred_on, Transaction.kind, Transaction.amount_cents).where(
            Transaction.user_id == user_id,
            Transaction.occurred_on >= start,
            Transaction.occurred_on <= end,
        )
    ).all()

    months: dict[str, dict[str, int]] = defaultdict(lambda: {"income": 0, "expense": 0})
    for occurred_on, kind, amount in rows:
        key = occurred_on.strftime("%Y-%m")
        bucket = "income" if TransactionKind(kind) is TransactionKind.INCOME else "expense"
        months[key][bucket] += int(amount or 0)

    by_month = [
        MonthPoint(
            month=key,
            income_cents=v["income"],
            expense_cents=v["expense"],
            net_cents=v["income"] - v["expense"],
        )
        for key, v in sorted(months.items())
    ]

    category_rows = db.execute(
        select(Category.name, func.sum(Transaction.amount_cents))
        .join(Category, Category.id == Transaction.category_id)
        .where(
            Transaction.user_id == user_id,
            Transaction.kind == TransactionKind.EXPENSE,
            Transaction.occurred_on >= start,
            Transaction.occurred_on <= end,
        )
        .group_by(Category.name)
        .order_by(func.sum(Transaction.amount_cents).desc())
        .limit(6)
    ).all()
    top = [NamedAmount(name=name, spent_cents=int(total or 0)) for name, total in category_rows]

    return FinanceTrend(by_month=by_month, top_categories=top)


def _learning(db: Session, user_id: int, start: date, end: date) -> LearningStats:
    intervals = list(
        db.scalars(select(Flashcard.interval_days).where(Flashcard.user_id == user_id))
    )
    maturity = {"new": 0, "learning": 0, "young": 0, "mature": 0}
    for days in intervals:
        if days <= 0:
            maturity["new"] += 1
        elif days < 7:
            maturity["learning"] += 1
        elif days < 30:
            maturity["young"] += 1
        else:
            maturity["mature"] += 1

    week_ago = date.today() - timedelta(days=7)
    reviews_last_7d = len(
        list(
            db.scalars(
                select(Flashcard.id).where(
                    Flashcard.user_id == user_id,
                    Flashcard.last_reviewed_on.is_not(None),
                    Flashcard.last_reviewed_on >= week_ago,
                )
            )
        )
    )

    lesson_days = db.scalars(
        select(Lesson.completed_on).where(
            Lesson.user_id == user_id,
            Lesson.completed_on.is_not(None),
            Lesson.completed_on >= start,
            Lesson.completed_on <= end,
        )
    ).all()

    return LearningStats(
        cards_total=len(intervals),
        reviews_last_7d=reviews_last_7d,
        maturity=maturity,
        lessons_done_by_week=_weekly((d, 1) for d in lesson_days if d is not None),
    )


def _job_search(db: Session, user_id: int, start: date, end: date) -> JobSearchStats:
    funnel = {s.value: 0 for s in ApplicationStatus}
    status_rows = db.execute(
        select(Application.status, func.count())
        .where(Application.user_id == user_id)
        .group_by(Application.status)
    ).all()
    for status_value, count in status_rows:
        funnel[ApplicationStatus(status_value).value] = int(count or 0)

    created = db.scalars(
        select(Application.created_at).where(
            Application.user_id == user_id,
            Application.created_at >= datetime.combine(start, datetime.min.time()),
            Application.created_at
            <= datetime.combine(end, datetime.max.time()),
        )
    ).all()

    return JobSearchStats(
        funnel=funnel,
        applications_by_week=_weekly((c.date(), 1) for c in created),
    )


def overview(
    db: Session, user_id: int, date_from: date | None, date_to: date | None
) -> AnalyticsOverview:
    start, end = resolve_range(date_from, date_to)
    return AnalyticsOverview(
        range=DateRange(date_from=start, date_to=end),
        productivity=_productivity(db, user_id, start, end),
        finance=_finance(db, user_id, start, end),
        learning=_learning(db, user_id, start, end),
        job_search=_job_search(db, user_id, start, end),
    )


# --------------------------------------------------------------------------- #
# Export
# --------------------------------------------------------------------------- #
def _flat_rows(data: AnalyticsOverview) -> list[tuple[str, str, str]]:
    p, f, learn, job = data.productivity, data.finance, data.learning, data.job_search
    cycle = "" if p.avg_cycle_days is None else str(p.avg_cycle_days)
    rows: list[tuple[str, str, str]] = [
        ("productivity", "tasks_total", str(p.tasks_total)),
        ("productivity", "tasks_done", str(p.tasks_done)),
        ("productivity", "completion_rate", f"{p.completion_rate:.3f}"),
        ("productivity", "avg_cycle_days", cycle),
        ("productivity", "overdue", str(p.overdue)),
        ("learning", "cards_total", str(learn.cards_total)),
        ("learning", "reviews_last_7d", str(learn.reviews_last_7d)),
    ]
    rows += [("productivity_open_by_priority", k, str(v)) for k, v in p.by_priority.items()]
    rows += [("learning_maturity", k, str(v)) for k, v in learn.maturity.items()]
    rows += [("job_funnel", k, str(v)) for k, v in job.funnel.items()]
    rows += [(f"finance_{m.month}", "net_cents", str(m.net_cents)) for m in f.by_month]
    rows += [("finance_top_category", c.name, str(c.spent_cents)) for c in f.top_categories]
    return rows


def to_csv(data: AnalyticsOverview) -> str:
    buffer = io.StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["section", "metric", "value"])
    writer.writerows(_flat_rows(data))
    return buffer.getvalue()


def to_pdf(data: AnalyticsOverview) -> bytes:
    buffer = io.BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=LETTER)
    width, height = LETTER
    y = height - inch

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(
        inch, y, f"Analytics — {data.range.date_from} to {data.range.date_to}"
    )
    y -= 0.5 * inch

    pdf.setFont("Helvetica", 11)
    for section, metric, value in _flat_rows(data):
        pdf.drawString(inch, y, f"{section} · {metric}")
        pdf.drawRightString(width - inch, y, value)
        y -= 0.26 * inch
        if y < inch:
            pdf.showPage()
            y = height - inch
            pdf.setFont("Helvetica", 11)

    pdf.showPage()
    pdf.save()
    return buffer.getvalue()
