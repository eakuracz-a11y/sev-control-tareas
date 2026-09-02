from __future__ import annotations

import argparse
import sqlite3
from datetime import date, datetime, timedelta
from pathlib import Path

from mailer import send_responsible_reminder

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_DB = BASE_DIR / "data" / "tareas.db"


def _connection(db_path: Path) -> sqlite3.Connection:
    c = sqlite3.connect(str(db_path))
    c.row_factory = sqlite3.Row
    return c


def _ensure_email_log(c: sqlite3.Connection) -> None:
    c.execute(
        """
        CREATE TABLE IF NOT EXISTS email_logs(
            id INTEGER PRIMARY KEY,
            task_id INTEGER,
            recipient TEXT,
            email_type TEXT,
            subject TEXT,
            status TEXT,
            detail TEXT,
            reference_date TEXT,
            sent_at TEXT
        )
        """
    )
    c.commit()


def _already_sent_today(c: sqlite3.Connection, task_id: int, email_type: str, today: date) -> bool:
    row = c.execute(
        """
        SELECT 1 FROM email_logs
        WHERE task_id = ? AND email_type = ? AND reference_date = ? AND status = 'Enviado'
        LIMIT 1
        """,
        (task_id, email_type, today.isoformat()),
    ).fetchone()
    return row is not None


def _log(c: sqlite3.Connection, task_id: int, recipient: str, email_type: str, status: str, detail: str, today: date) -> None:
    c.execute(
        """
        INSERT INTO email_logs(task_id, recipient, email_type, subject, status, detail, reference_date, sent_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            task_id,
            recipient,
            email_type,
            email_type,
            status,
            detail,
            today.isoformat(),
            datetime.now().isoformat(),
        ),
    )
    c.commit()


def _theoretical(task: sqlite3.Row, today: date) -> float | None:
    if task["status"] == "Cerrada" or not task["start_date"] or not task["due_date"]:
        return 100.0 if task["status"] == "Cerrada" else None
    try:
        start = date.fromisoformat(task["start_date"])
        due = date.fromisoformat(task["due_date"])
    except ValueError:
        return None
    if today <= start:
        return 0.0
    if today >= due:
        return 100.0
    duration = max((due - start).days, 1)
    return 100.0 * (today - start).days / duration


def run_reminders(db_path: str | Path = DEFAULT_DB, today: date | None = None) -> dict[str, int]:
    current = today or date.today()
    path = Path(db_path)
    summary = {"checked": 0, "sent": 0, "failed": 0, "skipped": 0}
    if not path.exists():
        return summary

    c = _connection(path)
    _ensure_email_log(c)
    rows = c.execute(
        """
        SELECT t.*, p.name AS person_name, p.email AS person_email,
               (SELECT MAX(update_date) FROM updates u WHERE u.task_id = t.id) AS last_update_date
        FROM tasks t
        JOIN people p ON p.id = t.assignee_id
        WHERE t.status != 'Cerrada'
        """
    ).fetchall()

    for row in rows:
        summary["checked"] += 1
        task = dict(row)
        person = {"name": row["person_name"], "email": row["person_email"]}
        rules: list[tuple[str, str]] = []

        created = None
        if row["created_at"]:
            try:
                created = datetime.fromisoformat(row["created_at"]).date()
            except ValueError:
                created = None
        if not row["accepted_at"] and row["status"] in {"Asignada", "Pendiente"} and created and current >= created + timedelta(days=1):
            rules.append(("not_accepted", "La tarea todavía no registra aceptación. Ingresa al enlace y confirma la recepción."))

        due = None
        if row["due_date"]:
            try:
                due = date.fromisoformat(row["due_date"])
            except ValueError:
                due = None
        if due:
            days_left = (due - current).days
            if days_left < 0 and float(row["progress"] or 0) < 100:
                rules.append(("overdue", f"La tarea está vencida desde hace {abs(days_left)} día(s). Actualiza el avance y los bloqueos."))
            elif 0 <= days_left <= 2 and float(row["progress"] or 0) < 100:
                rules.append(("due_soon", f"La tarea vence en {days_left} día(s). Revisa el avance previsto y actualiza el estado."))

        last_activity = None
        if row["last_update_date"]:
            try:
                last_activity = date.fromisoformat(row["last_update_date"])
            except ValueError:
                pass
        if last_activity is None and row["accepted_at"]:
            try:
                last_activity = datetime.fromisoformat(row["accepted_at"]).date()
            except ValueError:
                pass
        if last_activity and current >= last_activity + timedelta(days=3) and float(row["progress"] or 0) < 100:
            rules.append(("no_update", f"No se registra una actualización de avance desde hace {(current-last_activity).days} día(s)."))

        theoretical = _theoretical(row, current)
        real = float(row["progress"] or 0)
        if theoretical is not None and real < theoretical - 15 and row["status"] not in {"Terminada - espera cierre", "Cerrada"}:
            rules.append(("behind_schedule", f"El avance informado es {real:.0f}% y el avance teórico esperado es {theoretical:.0f}%."))

        # Máximo un correo por tipo y por día.
        for email_type, message in rules:
            if _already_sent_today(c, int(row["id"]), email_type, current):
                summary["skipped"] += 1
                continue
            ok, detail = send_responsible_reminder(task, person, email_type, message, BASE_DIR)
            _log(c, int(row["id"]), str(row["person_email"]), email_type, "Enviado" if ok else "Error", detail, current)
            summary["sent" if ok else "failed"] += 1

    c.close()
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Envía recordatorios automáticos de tareas SEV.")
    parser.add_argument("--db", default=str(DEFAULT_DB), help="Ruta a tareas.db")
    args = parser.parse_args()
    summary = run_reminders(args.db)
    print(summary)


if __name__ == "__main__":
    main()
