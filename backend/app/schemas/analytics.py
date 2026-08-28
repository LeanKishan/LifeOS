from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class WeekPoint(BaseModel):
    week: str  # ISO date of the Monday
    count: int


class MonthPoint(BaseModel):
    month: str  # YYYY-MM
    income_cents: int
    expense_cents: int
    net_cents: int


class NamedAmount(BaseModel):
    name: str
    spent_cents: int


class DateRange(BaseModel):
    date_from: date
    date_to: date


class Productivity(BaseModel):
    tasks_total: int
    tasks_done: int
    completion_rate: float
    avg_cycle_days: float | None
    overdue: int
    by_priority: dict[str, int]
    done_by_week: list[WeekPoint] = Field(default_factory=list)


class FinanceTrend(BaseModel):
    by_month: list[MonthPoint] = Field(default_factory=list)
    top_categories: list[NamedAmount] = Field(default_factory=list)


class LearningStats(BaseModel):
    cards_total: int
    reviews_last_7d: int
    maturity: dict[str, int]
    lessons_done_by_week: list[WeekPoint] = Field(default_factory=list)


class JobSearchStats(BaseModel):
    funnel: dict[str, int]
    applications_by_week: list[WeekPoint] = Field(default_factory=list)


class AnalyticsOverview(BaseModel):
    range: DateRange
    productivity: Productivity
    finance: FinanceTrend
    learning: LearningStats
    job_search: JobSearchStats
