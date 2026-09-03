from __future__ import annotations

import html
import os
import smtplib
import ssl
from dataclasses import dataclass
from email.message import EmailMessage
from pathlib import Path
from typing import Any
from urllib.parse import urlencode

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


@dataclass(frozen=True)
class MailSettings:
    host: str
    port: int
    username: str
    password: str
    sender_email: str
    sender_name: str
    admin_email: str
    app_base_url: str
    use_ssl: bool
    use_tls: bool

    @property
    def configured(self) -> bool:
        return bool(self.host and self.sender_email and (self.username or self.password or self.host))


def _as_bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "si", "sí", "on"}


def _read_streamlit_secrets(base_dir: Path | None = None) -> dict[str, Any]:
    if tomllib is None:
        return {}
    root = base_dir or Path(__file__).resolve().parent
    path = root / ".streamlit" / "secrets.toml"
    if not path.exists():
        return {}
    try:
        with path.open("rb") as fh:
            data = tomllib.load(fh)
        mail = data.get("mail", {}) if isinstance(data, dict) else {}
        root_values = data if isinstance(data, dict) else {}
        merged = dict(root_values)
        if isinstance(mail, dict):
            merged.update(mail)
        return merged
    except Exception:
        return {}


def _read_runtime_streamlit_secrets() -> dict[str, Any]:
    """Lee Secrets configurados desde Streamlit Community Cloud.

    Streamlit puede no materializar físicamente .streamlit/secrets.toml en el
    repositorio desplegado. Por eso esta función consulta st.secrets además
    del archivo local y de las variables de entorno.
    """
    try:
        import streamlit as st
        data = dict(st.secrets)
        merged = dict(data)
        mail = data.get("mail", {}) if isinstance(data, dict) else {}
        if isinstance(mail, dict):
            merged.update(dict(mail))
        return merged
    except Exception:
        return {}


def get_mail_settings(base_dir: Path | None = None) -> MailSettings:
    file_secrets = _read_streamlit_secrets(base_dir)
    runtime_secrets = _read_runtime_streamlit_secrets()

    # Orden de prioridad: variable de entorno > Streamlit Cloud > archivo local.
    secrets_data = dict(file_secrets)
    secrets_data.update(runtime_secrets)

    def value(env_key: str, secret_key: str, default: Any = "") -> Any:
        env = os.getenv(env_key)
        if env not in (None, ""):
            return env
        # Permite claves tanto minúsculas como mayúsculas en Secrets.
        if secret_key in secrets_data:
            return secrets_data.get(secret_key, default)
        if env_key in secrets_data:
            return secrets_data.get(env_key, default)
        return default

    port_raw = value("SMTP_PORT", "smtp_port", 587)
    try:
        port = int(port_raw)
    except (TypeError, ValueError):
        port = 587

    return MailSettings(
        host=str(value("SMTP_HOST", "smtp_host", "")).strip(),
        port=port,
        username=str(value("SMTP_USERNAME", "smtp_username", "")).strip(),
        password=str(value("SMTP_PASSWORD", "smtp_password", "")),
        sender_email=str(value("SMTP_SENDER_EMAIL", "sender_email", "")).strip(),
        sender_name=str(value("SMTP_SENDER_NAME", "sender_name", "SEV · Control de Tareas")).strip(),
        admin_email=str(value("ADMIN_EMAIL", "admin_email", "")).strip(),
        app_base_url=str(value("APP_BASE_URL", "app_base_url", "")).strip().rstrip("/"),
        use_ssl=_as_bool(value("SMTP_USE_SSL", "smtp_use_ssl", False), False),
        use_tls=_as_bool(value("SMTP_USE_TLS", "smtp_use_tls", True), True),
    )


def build_task_url(token: str, base_dir: Path | None = None) -> str:
    settings = get_mail_settings(base_dir)
    query = urlencode({"token": token})
    if settings.app_base_url:
        return f"{settings.app_base_url}?{query}"
    return f"?{query}"


def _button(url: str, label: str) -> str:
    safe_url = html.escape(url, quote=True)
    safe_label = html.escape(label)
    return (
        f'<a href="{safe_url}" style="display:inline-block;padding:12px 20px;'
        'background:#19734A;color:#ffffff;text-decoration:none;border-radius:8px;'
        f'font-weight:700;">{safe_label}</a>'
    )


def _layout(title: str, body_html: str) -> str:
    return f"""
    <html>
      <body style="font-family:Arial,Helvetica,sans-serif;color:#253A30;background:#F7F8F6;padding:24px;">
        <div style="max-width:680px;margin:auto;background:#ffffff;border:1px solid #DDE5DF;border-radius:12px;padding:28px;">
          <div style="font-size:12px;letter-spacing:.08em;color:#607168;font-weight:700;">SEV · GESTIÓN OPERACIONAL</div>
          <h2 style="color:#183D2D;margin:8px 0 20px;">{html.escape(title)}</h2>
          {body_html}
          <hr style="border:none;border-top:1px solid #DDE5DF;margin:26px 0 14px;">
          <div style="font-size:12px;color:#7A8780;">Mensaje automático del sistema SEV · Control de Tareas.</div>
        </div>
      </body>
    </html>
    """


def send_email(to_email: str, subject: str, html_body: str, text_body: str = "", base_dir: Path | None = None) -> tuple[bool, str]:
    settings = get_mail_settings(base_dir)
    if not settings.configured:
        return False, "Correo no configurado: faltan SMTP_HOST y/o SMTP_SENDER_EMAIL."
    if not to_email:
        return False, "Destinatario vacío."

    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{settings.sender_name} <{settings.sender_email}>"
    msg["To"] = to_email
    msg.set_content(text_body or "Este mensaje requiere un cliente compatible con HTML.")
    msg.add_alternative(html_body, subtype="html")

    try:
        if settings.use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(settings.host, settings.port, context=context, timeout=30) as smtp:
                if settings.username:
                    smtp.login(settings.username, settings.password)
                smtp.send_message(msg)
        else:
            with smtplib.SMTP(settings.host, settings.port, timeout=30) as smtp:
                smtp.ehlo()
                if settings.use_tls:
                    context = ssl.create_default_context()
                    smtp.starttls(context=context)
                    smtp.ehlo()
                if settings.username:
                    smtp.login(settings.username, settings.password)
                smtp.send_message(msg)
        return True, "Enviado"
    except Exception as exc:
        return False, f"{type(exc).__name__}: {exc}"


def mail_configuration_report(base_dir: Path | None = None) -> dict[str, Any]:
    settings = get_mail_settings(base_dir)
    missing = []
    if not settings.host:
        missing.append("SMTP_HOST")
    if not settings.sender_email:
        missing.append("SMTP_SENDER_EMAIL")
    if settings.username and not settings.password:
        missing.append("SMTP_PASSWORD")
    if not settings.admin_email:
        missing.append("ADMIN_EMAIL")
    if not settings.app_base_url:
        missing.append("APP_BASE_URL")
    return {
        "configured": settings.configured,
        "missing": missing,
        "host": settings.host,
        "port": settings.port,
        "sender_email": settings.sender_email,
        "admin_email": settings.admin_email,
        "app_base_url": settings.app_base_url,
        "use_ssl": settings.use_ssl,
        "use_tls": settings.use_tls,
    }


def send_test_email(to_email: str, base_dir: Path | None = None) -> tuple[bool, str]:
    body = """
      <p>Este es un correo de prueba de <strong>SEV · Control de Tareas</strong>.</p>
      <p>Si recibiste este mensaje, la configuración SMTP está funcionando correctamente.</p>
    """
    return send_email(
        to_email,
        "Prueba de correo · SEV Control de Tareas",
        _layout("Prueba de configuración SMTP", body),
        "Prueba de configuración SMTP del sistema SEV.",
        base_dir,
    )


def send_assignment_email(task: dict[str, Any], person: dict[str, Any], base_dir: Path | None = None) -> tuple[bool, str]:
    url = build_task_url(str(task.get("token", "")), base_dir)
    body = f"""
      <p>Hola <strong>{html.escape(str(person.get('name', '')))}</strong>,</p>
      <p>Se te ha asignado una nueva tarea. Por favor revisa la información y confirma la recepción.</p>
      <table style="border-collapse:collapse;width:100%;margin:18px 0;">
        <tr><td style="padding:7px 0;color:#607168;">Código</td><td><strong>{html.escape(str(task.get('code','')))}</strong></td></tr>
        <tr><td style="padding:7px 0;color:#607168;">Tarea</td><td>{html.escape(str(task.get('title','')))}</td></tr>
        <tr><td style="padding:7px 0;color:#607168;">Prioridad</td><td>{html.escape(str(task.get('priority','')))}</td></tr>
        <tr><td style="padding:7px 0;color:#607168;">Inicio</td><td>{html.escape(str(task.get('start_date','')))}</td></tr>
        <tr><td style="padding:7px 0;color:#607168;">Finalización prevista</td><td>{html.escape(str(task.get('due_date','')))}</td></tr>
      </table>
      <p>{_button(url, 'ACEPTAR / VER TAREA')}</p>
      <p style="font-size:13px;color:#607168;">Desde este mismo enlace podrás informar el avance, las horas trabajadas, el trabajo realizado y los bloqueos.</p>
    """
    text = f"Nueva tarea {task.get('code')}: {task.get('title')}\nAbrir: {url}"
    return send_email(str(person.get("email", "")), f"Nueva tarea asignada · {task.get('code','')}", _layout("Nueva tarea asignada", body), text, base_dir)


def send_responsible_reminder(task: dict[str, Any], person: dict[str, Any], reminder_type: str, message: str, base_dir: Path | None = None) -> tuple[bool, str]:
    url = build_task_url(str(task.get("token", "")), base_dir)
    body = f"""
      <p>Hola <strong>{html.escape(str(person.get('name','')))}</strong>,</p>
      <p>{html.escape(message)}</p>
      <p><strong>{html.escape(str(task.get('code','')))} · {html.escape(str(task.get('title','')))}</strong></p>
      <p>Avance actual: <strong>{float(task.get('progress') or 0):.0f}%</strong> · Finalización prevista: <strong>{html.escape(str(task.get('due_date') or '—'))}</strong></p>
      <p>{_button(url, 'ACTUALIZAR AVANCE')}</p>
    """
    subject_map = {
        "not_accepted": "Tarea pendiente de aceptación",
        "no_update": "Actualización de avance pendiente",
        "due_soon": "Tarea próxima a vencer",
        "overdue": "Tarea vencida",
        "behind_schedule": "Avance por debajo de lo previsto",
    }
    subject = subject_map.get(reminder_type, "Seguimiento de tarea")
    return send_email(str(person.get("email", "")), f"{subject} · {task.get('code','')}", _layout(subject, body), f"{message}\n{url}", base_dir)


def send_admin_event(task: dict[str, Any], person: dict[str, Any], event: str, detail: str, base_dir: Path | None = None) -> tuple[bool, str]:
    settings = get_mail_settings(base_dir)
    if not settings.admin_email:
        return False, "ADMIN_EMAIL no configurado."
    body = f"""
      <p><strong>{html.escape(str(person.get('name','')))}</strong> registró un cambio en la tarea:</p>
      <p><strong>{html.escape(str(task.get('code','')))} · {html.escape(str(task.get('title','')))}</strong></p>
      <p>{html.escape(detail)}</p>
    """
    return send_email(settings.admin_email, f"{event} · {task.get('code','')}", _layout(event, body), detail, base_dir)


def send_closed_email(task: dict[str, Any], person: dict[str, Any], base_dir: Path | None = None) -> tuple[bool, str]:
    body = f"""
      <p>Hola <strong>{html.escape(str(person.get('name','')))}</strong>,</p>
      <p>La tarea <strong>{html.escape(str(task.get('code','')))} · {html.escape(str(task.get('title','')))}</strong> fue revisada y cerrada por administración.</p>
      <p>Estado final: <strong>Cerrada</strong>.</p>
    """
    return send_email(str(person.get("email", "")), f"Tarea cerrada · {task.get('code','')}", _layout("Tarea cerrada", body), "La tarea fue cerrada por administración.", base_dir)
