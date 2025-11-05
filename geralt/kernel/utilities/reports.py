"""Helpers for storing and managing user-submitted reports."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Sequence, Tuple, Literal

import asyncpg

ReportType = Literal["bug", "feedback"]
ReportStatus = Literal["new", "triaged", "in_progress", "resolved", "closed"]
ReportSeverity = Literal["untriaged", "low", "medium", "high", "critical"]

DEFAULT_STATUS: ReportStatus = "new"
DEFAULT_SEVERITY: ReportSeverity = "untriaged"
UNRESOLVED_STATUSES: Tuple[ReportStatus, ...] = ("new", "triaged", "in_progress")

_VALID_TYPES: Tuple[ReportType, ...] = ("bug", "feedback")
_VALID_STATUSES: Tuple[ReportStatus, ...] = (
    "new",
    "triaged",
    "in_progress",
    "resolved",
    "closed",
)
_VALID_SEVERITIES: Tuple[ReportSeverity, ...] = (
    "untriaged",
    "low",
    "medium",
    "high",
    "critical",
)

_SEVERITY_ORDER = {
    "untriaged": 0,
    "low": 1,
    "medium": 2,
    "high": 3,
    "critical": 4,
}

REPORT_STATUS_CHOICES: Tuple[ReportStatus, ...] = _VALID_STATUSES
REPORT_SEVERITY_CHOICES: Tuple[ReportSeverity, ...] = _VALID_SEVERITIES

_MISSING = object()


@dataclass(slots=True)
class ReportRecord:
    """Structured representation of a stored report."""

    id: int
    report_type: ReportType
    guild_id: Optional[int]
    channel_id: Optional[int]
    message_id: Optional[int]
    message_jump_url: Optional[str]
    reporter_id: int
    subject: str
    body: str
    status: ReportStatus
    severity: ReportSeverity
    assignee_id: Optional[int]
    github_repository: Optional[str]
    github_issue_url: Optional[str]
    github_issue_number: Optional[int]
    created_at: datetime
    updated_at: datetime

    def preview(self, *, limit: int = 250) -> str:
        """Return a human-friendly preview of the report body."""

        if len(self.body) <= limit:
            return self.body
        return self.body[: limit - 1] + "\u2026"


async def ensure_report_tables(pool: asyncpg.Pool) -> None:
    """Ensure the database contains the tables used for report tracking."""

    type_choices = ", ".join(f"'{value}'" for value in _VALID_TYPES)
    status_choices = ", ".join(f"'{value}'" for value in _VALID_STATUSES)
    severity_choices = ", ".join(f"'{value}'" for value in _VALID_SEVERITIES)

    await pool.execute(
        f"""
        CREATE TABLE IF NOT EXISTS report_tickets (
            id BIGSERIAL PRIMARY KEY,
            report_type TEXT NOT NULL CHECK (report_type = ANY(ARRAY[{type_choices}])),
            guild_id BIGINT,
            channel_id BIGINT,
            message_id BIGINT,
            message_jump_url TEXT,
            reporter_id BIGINT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT '{DEFAULT_STATUS}'
                CHECK (status = ANY(ARRAY[{status_choices}])),
            severity TEXT NOT NULL DEFAULT '{DEFAULT_SEVERITY}'
                CHECK (severity = ANY(ARRAY[{severity_choices}])),
            assignee_id BIGINT,
            github_repository TEXT,
            github_issue_url TEXT,
            github_issue_number INTEGER,
            created_at TIMESTAMPTZ NOT NULL DEFAULT (NOW()),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT (NOW())
        )
        """
    )


def _convert_record(record: Optional[asyncpg.Record]) -> Optional[ReportRecord]:
    if record is None:
        return None
    return ReportRecord(
        id=record["id"],
        report_type=record["report_type"],
        guild_id=record["guild_id"],
        channel_id=record["channel_id"],
        message_id=record["message_id"],
        message_jump_url=record["message_jump_url"],
        reporter_id=record["reporter_id"],
        subject=record["subject"],
        body=record["body"],
        status=record["status"],
        severity=record["severity"],
        assignee_id=record["assignee_id"],
        github_repository=record["github_repository"],
        github_issue_url=record["github_issue_url"],
        github_issue_number=record["github_issue_number"],
        created_at=record["created_at"],
        updated_at=record["updated_at"],
    )


def _validate_choice(name: str, value: str, valid: Sequence[str]) -> str:
    value = value.lower()
    if value not in valid:
        raise ValueError(f"{name} must be one of: {', '.join(valid)}")
    return value


async def insert_report(
    pool: asyncpg.Pool,
    *,
    report_type: ReportType,
    guild_id: Optional[int],
    channel_id: Optional[int],
    message_id: Optional[int],
    message_jump_url: Optional[str],
    reporter_id: int,
    subject: str,
    body: str,
) -> ReportRecord:
    """Persist a newly submitted report and return the stored record."""

    if report_type not in _VALID_TYPES:
        raise ValueError(f"report_type must be one of: {', '.join(_VALID_TYPES)}")

    record = await pool.fetchrow(
        """
        INSERT INTO report_tickets (
            report_type,
            guild_id,
            channel_id,
            message_id,
            message_jump_url,
            reporter_id,
            subject,
            body
        )
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
        RETURNING *
        """,
        report_type,
        guild_id,
        channel_id,
        message_id,
        message_jump_url,
        reporter_id,
        subject,
        body,
    )
    converted = _convert_record(record)
    if converted is None:
        raise RuntimeError("Failed to persist report submission.")
    return converted


async def fetch_report(pool: asyncpg.Pool, report_id: int) -> Optional[ReportRecord]:
    """Fetch a single stored report by its identifier."""

    record = await pool.fetchrow(
        "SELECT * FROM report_tickets WHERE id = $1",
        report_id,
    )
    return _convert_record(record)


async def fetch_unresolved_reports(pool: asyncpg.Pool) -> List[ReportRecord]:
    """Return reports that still require attention."""

    records = await pool.fetch(
        """
        SELECT * FROM report_tickets
        WHERE status = ANY($1::text[])
        ORDER BY created_at ASC
        """,
        list(UNRESOLVED_STATUSES),
    )
    reports = [report for record in records if (report := _convert_record(record))]
    return sorted(
        reports,
        key=lambda report: (
            -_SEVERITY_ORDER.get(report.severity, 0),
            report.created_at,
        ),
    )


async def update_report(
    pool: asyncpg.Pool,
    report_id: int,
    *,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    assignee_id: object = _MISSING,
    github_repository: Optional[str] = None,
    github_issue_url: Optional[str] = None,
    github_issue_number: Optional[int] = None,
) -> Optional[ReportRecord]:
    """Update a report with the supplied fields."""

    updates = []
    values: List[object] = []

    if status is not None:
        updates.append(f"status = ${len(values) + 1}")
        values.append(_validate_choice("status", status, _VALID_STATUSES))

    if severity is not None:
        updates.append(f"severity = ${len(values) + 1}")
        values.append(_validate_choice("severity", severity, _VALID_SEVERITIES))

    if assignee_id is not _MISSING:
        updates.append(f"assignee_id = ${len(values) + 1}")
        values.append(assignee_id)

    if github_repository is not None:
        updates.append(f"github_repository = ${len(values) + 1}")
        values.append(github_repository)

    if github_issue_url is not None:
        updates.append(f"github_issue_url = ${len(values) + 1}")
        values.append(github_issue_url)

    if github_issue_number is not None:
        updates.append(f"github_issue_number = ${len(values) + 1}")
        values.append(github_issue_number)

    if not updates:
        return await fetch_report(pool, report_id)

    updates.append("updated_at = NOW()")
    values.append(report_id)

    record = await pool.fetchrow(
        f"""
        UPDATE report_tickets
        SET {', '.join(updates)}
        WHERE id = ${{len(values)}}
        RETURNING *
        """,
        *values,
    )
    return _convert_record(record)


__all__ = [
    "DEFAULT_SEVERITY",
    "DEFAULT_STATUS",
    "ReportRecord",
    "ReportSeverity",
    "ReportStatus",
    "ReportType",
    "REPORT_SEVERITY_CHOICES",
    "REPORT_STATUS_CHOICES",
    "UNRESOLVED_STATUSES",
    "fetch_report",
    "fetch_unresolved_reports",
    "ensure_report_tables",
    "insert_report",
    "update_report",
]
