from pathlib import Path
import sqlite3
import secrets
import calendar
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from mailer import (
    build_task_url,
    get_mail_settings,
    send_admin_event,
    send_assignment_email,
    send_closed_email,
)
from reminders import run_reminders


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

APP_VERSION = "V2.6"

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"

DATA_DIR.mkdir(parents=True, exist_ok=True)

DB = str(DATA_DIR / "tareas.db")
LOGO = ASSETS_DIR / "sevion_logo.png"


# ============================================================
# PERSONAS
# ============================================================

PEOPLE = [
    ("Camille Maia", "camille.maia@sevion.com.br"),
    ("Eduardo Matos", "eduardo.matos@sevion.com.br"),
    ("Bruno Maia", "bruno.maia@sevion.com.br"),
    ("Ana Nolasco", "ana.nolasco@sevion.com.br"),
    ("Flavia Guedes", "flavia.guedes@sevion.com.br"),
    ("Marcela Roque", "marcela.roque@sevion.com.br"),
]


# ============================================================
# TAREAS INICIALES DE CAMILLE
# ============================================================

SEED = [
    ("Relatório de resultados de amostras de adjuvantes (Lotes)", "Cerrada", "—"),
    ("Relatório de teste de emulsão (Projeto ADJ G)", "Cerrada", "—"),
    (
        "Produção de volume teste (Projeto ADJ G)",
        "Cerrada",
        "Novo volume será necessário caso haja continuidade dos testes ou produção em maior escala.",
    ),
    ("Agendamento da avaliação nas propriedades (Projeto ADJ G)", "Cerrada", "—"),
    (
        "Revisão do manejo dos produtores e organização da pesquisa, materiais e protocolos para teste de compatibilidade (Projeto ADJ G)",
        "Cerrada",
        "—",
    ),
    ("Relatórios dos testes – Fazenda Multiagri", "Cerrada", "—"),
    ("Formulação com D-Limoneno", "Cerrada", "—"),
    ("Treinamento de Brigadista", "Cerrada", "—"),
    ("Treinamento de Emergência Química", "Cerrada", "—"),
    ("Troca da coluna de resina do deionizador", "Cerrada", "Substituição realizada."),
    ("Treinamento de Uso Correto de EPI", "Cerrada", "Conclusão prevista para 25/07."),
    ("Avaliar embalagem tipo bag de adjuvantes", "Cerrada", "Aprovado"),
    (
        "Teste de compatibilidade de calda e relatório (ADJ G).",
        "Cerrada",
        "Refazer teste e identificar outros manejos.",
    ),
    ("Ajuste de performance do AAS", "Cerrada", "Após reunião com Tecnal."),
    ("Teste de emulsão e relatório de Formulação com D-Limoneno", "Cerrada", "—"),
    ("Teste de pulverização aérea (drone)", "Cerrada", "—"),
    (
        "Conferência de estoque e atualização da planilha",
        "En ejecución",
        "Mensalmente, dia 25",
    ),
    ("Mapa mensal da PF", "En ejecución", "Mensalmente, dia 26"),
    (
        "Revisão da curva de calibração de Cu (alta sensibilidade)",
        "En ejecución",
        "Refazer.",
    ),
    (
        "Teste de pulverização aérea (drone - Derquian)",
        "En ejecución",
        "Previsão de conclusão até 13/08.",
    ),
    (
        "Testes e relatório de Formulação com D-Limoneno",
        "En ejecución",
        "Fazer teste de compatibilidade com herbicidas e inseticidas, sem fungicidas.",
    ),
    ("Teste de compatibilidade de calda e relatório (MSO-TC).", "En ejecución", ""),
    (
        "Organização do laboratório sugeridas durante o treinamento de análises de solo",
        "Pendiente",
        "Necessário definir prioridade e cronograma.",
    ),
    ("Identificação de balanças", "Pendiente", "Verificar modelo e imprimir"),
    (
        "Fazer curva de Ca e Mg e analisar amostra de água mineral",
        "Pendiente",
        "Necessário definir prioridade e cronograma.",
    ),
    (
        "Repetição das formulações de fertilizantes para confirmação das garantias",
        "Pendiente",
        "Necessário definir prioridade e cronograma.",
    ),
    (
        "Preparo das formulações discutidas na consultoria",
        "Pendiente",
        "Necessário definir prioridade e cronograma.",
    ),
    (
        "Análises de CQ dos fertilizantes formulados",
        "Pendiente",
        "Dependente da conclusão das formulações.",
    ),
]


# ============================================================
# CLASIFICACIONES
# ============================================================

SECTORES = {
    "Laboratorio": "LAB",
    "Producción": "PRD",
    "Logística": "LOG",
    "Mantenimiento": "MANT",
}

AREAS = {
    "Fungos": "FUN",
    "Biológico": "BIO",
    "Fertilizante": "FER",
    "Adjuvante": "ADJ",
}

TIPOS_MANT = [
    "Preventivo",
    "Correctivo",
    "Proactivo",
    "Predictivo",
]

PRIORIDADES = [
    "Crítica",
    "Alta",
    "Media",
    "Baja",
]

RECURRENCIAS = [
    "No",
    "Semanal",
    "Mensual",
    "Trimestral",
    "Semestral",
    "Anual",
]


# ============================================================
# IDENTIDAD VISUAL
# ============================================================

BRAND_GREEN = "#19734A"
BRAND_DARK = "#183D2D"
BRAND_BG = "#F7F8F6"
BRAND_BORDER = "#DDE5DF"

COLOR_OK = "#4C946E"
COLOR_WARNING = "#D59B29"
COLOR_DANGER = "#C7463A"
COLOR_WAIT = "#4878A8"
COLOR_NEUTRAL = "#8A9690"


st.set_page_config(
    page_title="SEV | Control de Tareas",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ============================================================
# CSS GENERAL
# ============================================================

st.markdown(
    f"""
<style>

.stApp {{
    background: {BRAND_BG};
}}

.block-container {{
    padding-top: 2.2rem;
    padding-bottom: 2.2rem;
    max-width: 1500px;
}}

[data-testid="stSidebar"] {{
    background: #F3F5F3;
    border-right: 1px solid {BRAND_BORDER};
}}

[data-testid="stSidebar"] * {{
    color: #253A30 !important;
}}

[data-testid="stSidebar"] [role="radiogroup"] label {{
    border-radius: 9px;
    padding-top: 0.30rem;
    padding-bottom: 0.30rem;
}}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
    background: #E8EEE9;
}}

h1, h2, h3 {{
    color: {BRAND_DARK};
}}

div[data-testid="stMetric"] {{
    background: white;
    border: 1px solid {BRAND_BORDER};
    border-radius: 14px;
    padding: 13px 15px;
}}

div[data-testid="stMetricLabel"] {{
    color: #607168;
    font-weight: 600;
}}

div[data-testid="stMetricValue"] {{
    color: {BRAND_DARK};
}}

[data-testid="stDataFrame"] {{
    border: 1px solid {BRAND_BORDER};
    border-radius: 12px;
    overflow: hidden;
}}

button[kind="primary"] {{
    background-color: {BRAND_GREEN} !important;
    border-color: {BRAND_GREEN} !important;
    color: white !important;
}}

.stButton > button {{
    border-radius: 10px;
}}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# ENCABEZADO NATIVO
# ============================================================

def render_header():

    logo_col, title_col, version_col = st.columns(
        [1.25, 5.4, 1.35],
        vertical_alignment="center",
    )

    with logo_col:
        if LOGO.exists():
            st.image(
                str(LOGO),
                width=145,
            )
        else:
            st.markdown("### Sevion")

    with title_col:
        st.markdown(
            """
            <div style="padding-top:0.15rem;">
                <div style="font-size:0.72rem;letter-spacing:0.13em;font-weight:700;color:#7B8D84;margin-bottom:0.12rem;">
                    GESTIÓN OPERACIONAL
                </div>
                <div style="font-size:2.20rem;line-height:1.05;font-weight:750;color:#183D2D;margin:0;">
                    Control de Tareas
                </div>
                <div style="font-size:0.82rem;color:#7B8D84;margin-top:0.30rem;">
                    Asignación · aceptación · ejecución · cumplimiento
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with version_col:
        st.markdown(
            f"""
            <div style="text-align:right;padding-top:0.35rem;">
                <span style="display:inline-block;border:1px solid #DDE5DF;background:#FFFFFF;border-radius:999px;
                padding:0.35rem 0.70rem;font-size:0.78rem;font-weight:700;color:#19734A;">{APP_VERSION}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown(
        '<div style="height:1px;background:#DDE5DF;margin:0.85rem 0 1.15rem 0;"></div>',
        unsafe_allow_html=True,
    )


# ============================================================
# SECCIONES NATIVAS
# ============================================================

def section(
    title,
    note="",
):

    st.subheader(
        title
    )

    if note:

        st.caption(
            note
        )


# ============================================================
# BASE DE DATOS
# ============================================================

def con():

    connection = sqlite3.connect(
        DB,
        check_same_thread=False,
    )

    connection.row_factory = sqlite3.Row

    return connection


def init_db():

    c = con()

    c.executescript(
        """
        CREATE TABLE IF NOT EXISTS people(

            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            active INTEGER DEFAULT 1

        );

        CREATE TABLE IF NOT EXISTS tasks(

            id INTEGER PRIMARY KEY,
            code TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            sector TEXT,
            area TEXT,
            maintenance_type TEXT,
            assignee_id INTEGER,
            priority TEXT,
            requested TEXT,
            start_date TEXT,
            due_date TEXT,
            status TEXT,
            progress REAL DEFAULT 0,
            observation TEXT,
            token TEXT UNIQUE,
            accepted_at TEXT,
            finished_at TEXT,
            closed_at TEXT,
            imported INTEGER DEFAULT 0,
            recurrence TEXT,
            recurrence_day INTEGER,
            recurrence_parent_id INTEGER,
            created_at TEXT

        );

        CREATE TABLE IF NOT EXISTS updates(

            id INTEGER PRIMARY KEY,
            task_id INTEGER,
            update_date TEXT,
            progress REAL,
            hours REAL,
            work_done TEXT,
            blockers TEXT,
            created_at TEXT

        );

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

        );

        CREATE TABLE IF NOT EXISTS task_events(

            id INTEGER PRIMARY KEY,
            task_id INTEGER,
            event_type TEXT,
            actor TEXT,
            detail TEXT,
            created_at TEXT

        );
        """
    )

    for name, email in PEOPLE:

        c.execute(
            """
            INSERT OR IGNORE INTO people(
                name,
                email,
                active
            )
            VALUES (?, ?, 1)
            """,
            (
                name,
                email,
            ),
        )

    c.commit()

    total = c.execute(
        """
        SELECT COUNT(*) AS n
        FROM tasks
        """
    ).fetchone()["n"]

    if total == 0:

        camille = c.execute(
            """
            SELECT id
            FROM people
            WHERE email = ?
            """,
            (
                "camille.maia@sevion.com.br",
            ),
        ).fetchone()["id"]

        for i, (
            title,
            status,
            observation,
        ) in enumerate(
            SEED,
            1,
        ):

            recurrence = None
            recurrence_day = None

            if "Mensalmente" in observation:

                recurrence = "Mensual"

            if "dia 25" in observation:

                recurrence_day = 25

            elif "dia 26" in observation:

                recurrence_day = 26

            if status == "Cerrada":

                progress = 100

            elif status == "En ejecución":

                progress = 25

            else:

                progress = 0

            code = (
                f"SEV-LAB-FER-2026-{i:04d}"
            )

            c.execute(
                """
                INSERT INTO tasks(

                    code,
                    title,
                    sector,
                    area,
                    assignee_id,
                    priority,
                    requested,
                    status,
                    progress,
                    observation,
                    token,
                    imported,
                    recurrence,
                    recurrence_day,
                    created_at

                )
                VALUES(
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    code,
                    title,
                    "LAB",
                    "FER",
                    camille,
                    "Media",
                    "2026-08-13",
                    status,
                    progress,
                    observation,
                    secrets.token_urlsafe(
                        24
                    ),
                    1,
                    recurrence,
                    recurrence_day,
                    datetime.now().isoformat(),
                ),
            )

        c.commit()

    c.close()


# ============================================================
# AUDITORÍA Y CORREO
# ============================================================

def log_email(connection, task_id, recipient, email_type, subject, ok, detail):

    connection.execute(
        """
        INSERT INTO email_logs(
            task_id, recipient, email_type, subject, status, detail, reference_date, sent_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            int(task_id),
            recipient or "",
            email_type,
            subject,
            "Enviado" if ok else "Error",
            detail,
            date.today().isoformat(),
            datetime.now().isoformat(),
        ),
    )
    connection.commit()


def log_event(connection, task_id, event_type, actor, detail=""):

    connection.execute(
        """
        INSERT INTO task_events(task_id, event_type, actor, detail, created_at)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            int(task_id),
            event_type,
            actor,
            detail,
            datetime.now().isoformat(),
        ),
    )
    connection.commit()


def person_for_task(connection, task_id):

    row = connection.execute(
        """
        SELECT p.name, p.email
        FROM tasks t
        JOIN people p ON p.id = t.assignee_id
        WHERE t.id = ?
        """,
        (int(task_id),),
    ).fetchone()

    return dict(row) if row else {"name": "", "email": ""}


# ============================================================
# GENERAR CÓDIGO
# ============================================================

def next_code(
    sector,
    area,
    connection=None,
):

    year = date.today().year

    own_connection = (
        connection is None
    )

    c = (
        connection
        if connection is not None
        else con()
    )

    rows = c.execute(
        """
        SELECT code
        FROM tasks
        WHERE code LIKE ?
        """,
        (
            f"SEV-%-{year}-%",
        ),
    ).fetchall()

    if own_connection:

        c.close()

    numbers = []

    for row in rows:

        try:

            numbers.append(
                int(
                    row["code"]
                    .split("-")[-1]
                )
            )

        except Exception:

            pass

    next_number = (
        max(
            numbers,
            default=0,
        )
        + 1
    )

    return (
        f"SEV-{sector}-{area}-{year}-{next_number:04d}"
    )


# ============================================================
# AVANCE TEÓRICO
# ============================================================

def theoretical(
    row,
    reference=None,
):

    reference = (
        reference
        or date.today()
    )

    if row["status"] == "Cerrada":

        return 100.0

    if (
        not row["start_date"]
        or not row["due_date"]
    ):

        return None

    start = pd.to_datetime(
        row["start_date"]
    ).date()

    due = pd.to_datetime(
        row["due_date"]
    ).date()

    if reference <= start:

        return 0.0

    if reference >= due:

        return 100.0

    total_days = max(
        (
            due
            - start
        ).days,
        1,
    )

    elapsed_days = (
        reference
        - start
    ).days

    return round(
        100
        * elapsed_days
        / total_days,
        1,
    )


# ============================================================
# SEMÁFORO
# ============================================================

def traffic_light(
    row
):

    if row["status"] == "Cerrada":

        return "🟢 Cerrada"

    if (
        row["status"]
        == "Terminada - espera cierre"
    ):

        return "🔵 Espera cierre"

    expected = theoretical(
        row
    )

    if expected is None:

        return "⚪ Sin cronograma"

    real = float(
        row["progress"]
        or 0
    )

    if (
        row["due_date"]
        and date.today()
        > pd.to_datetime(
            row["due_date"]
        ).date()
        and real < 100
    ):

        return "🔴 Vencida"

    difference = (
        real
        - expected
    )

    if difference >= -5:

        return "🟢 En término"

    if difference >= -15:

        return "🟡 Atención"

    return "🔴 Atrasada"


def schedule_delta(
    row
):

    expected = theoretical(
        row
    )

    if expected is None:

        return None

    return round(
        float(
            row["progress"]
            or 0
        )
        - expected,
        1,
    )


# ============================================================
# RECURRENCIAS
# ============================================================

def add_months(
    original_date,
    months,
):

    month = (
        original_date.month
        - 1
        + months
    )

    year = (
        original_date.year
        + month // 12
    )

    month = (
        month % 12
        + 1
    )

    day = min(
        original_date.day,
        calendar.monthrange(
            year,
            month,
        )[1],
    )

    return date(
        year,
        month,
        day,
    )


def next_recurrence(
    original_date,
    recurrence,
):

    if recurrence == "Semanal":

        return (
            original_date
            + timedelta(days=7)
        )

    if recurrence == "Mensual":

        return add_months(
            original_date,
            1,
        )

    if recurrence == "Trimestral":

        return add_months(
            original_date,
            3,
        )

    if recurrence == "Semestral":

        return add_months(
            original_date,
            6,
        )

    if recurrence == "Anual":

        return add_months(
            original_date,
            12,
        )

    return None


def generate_recurring():

    c = con()

    masters = c.execute(
        """
        SELECT *
        FROM tasks
        WHERE recurrence IS NOT NULL
        AND recurrence != 'No'
        AND recurrence_parent_id IS NULL
        AND due_date IS NOT NULL
        AND due_date != ''
        """
    ).fetchall()

    for task in masters:

        due = pd.to_datetime(
            task["due_date"]
        ).date()

        next_due = next_recurrence(
            due,
            task["recurrence"],
        )

        if not next_due:

            continue

        if (
            next_due
            > date.today()
            + timedelta(days=45)
        ):

            continue

        existing = c.execute(
            """
            SELECT 1
            FROM tasks
            WHERE recurrence_parent_id = ?
            AND due_date = ?
            """,
            (
                task["id"],
                next_due.isoformat(),
            ),
        ).fetchone()

        if existing:

            continue

        next_start = next_due

        if task["start_date"]:

            previous_start = (
                pd.to_datetime(
                    task["start_date"]
                ).date()
            )

            duration = max(
                (
                    due
                    - previous_start
                ).days,
                0,
            )

            next_start = (
                next_due
                - timedelta(
                    days=duration
                )
            )

        code = next_code(
            task["sector"],
            task["area"],
            c,
        )

        c.execute(
            """
            INSERT INTO tasks(

                code,
                title,
                description,
                sector,
                area,
                maintenance_type,
                assignee_id,
                priority,
                requested,
                start_date,
                due_date,
                status,
                progress,
                observation,
                token,
                recurrence,
                recurrence_day,
                recurrence_parent_id,
                created_at

            )
            VALUES(
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
            )
            """,
            (
                code,
                task["title"],
                task["description"],
                task["sector"],
                task["area"],
                task["maintenance_type"],
                task["assignee_id"],
                task["priority"],
                date.today().isoformat(),
                next_start.isoformat(),
                next_due.isoformat(),
                "Asignada",
                0,
                task["observation"],
                secrets.token_urlsafe(
                    24
                ),
                task["recurrence"],
                next_due.day,
                task["id"],
                datetime.now().isoformat(),
            ),
        )

    c.commit()
    c.close()


# ============================================================
# AVANCE REAL VS TEÓRICO
# ============================================================

def progress_chart(
    view
):

    chart = view[
        view[
            "Teórico %"
        ].notna()
    ][
        [
            "code",
            "progress",
            "Teórico %",
            "assignee",
        ]
    ].copy()

    if chart.empty:

        st.info(
            "Las tareas históricas sin fechas no tienen avance teórico calculable."
        )

        return

    chart_long = chart.melt(
        id_vars=[
            "code",
            "assignee",
        ],
        value_vars=[
            "progress",
            "Teórico %",
        ],
        var_name="Serie",
        value_name="Avance",
    )

    chart_long[
        "Serie"
    ] = (
        chart_long[
            "Serie"
        ]
        .replace(
            {
                "progress": "Real",
                "Teórico %": "Teórico",
            }
        )
    )

    fig = px.bar(
        chart_long,
        x="code",
        y="Avance",
        color="Serie",
        barmode="group",
        hover_data=[
            "assignee",
        ],
        labels={
            "code": "Tarea",
            "Avance": "Avance (%)",
        },
        color_discrete_map={
            "Real": BRAND_GREEN,
            "Teórico": "#AAB8B0",
        },
    )

    fig.update_layout(
        height=400,
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
        legend_title_text="",
        paper_bgcolor=(
            "rgba(0,0,0,0)"
        ),
        plot_bgcolor="#FFFFFF",
        font=dict(
            color=BRAND_DARK
        ),
        xaxis=dict(
            showgrid=False,
        ),
        yaxis=dict(
            gridcolor="#E8ECE9",
            range=[
                0,
                105,
            ],
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# CONTROL DE ACEPTACIÓN
# ============================================================

def acceptance_metrics(row, reference=None):

    reference = reference or datetime.now()

    assigned_raw = row.get("created_at") if hasattr(row, "get") else row["created_at"]
    accepted_raw = row.get("accepted_at") if hasattr(row, "get") else row["accepted_at"]
    requested_raw = row.get("requested") if hasattr(row, "get") else row["requested"]

    assigned = pd.to_datetime(assigned_raw, errors="coerce")
    if pd.isna(assigned):
        assigned = pd.to_datetime(requested_raw, errors="coerce")

    accepted = pd.to_datetime(accepted_raw, errors="coerce")

    if pd.isna(assigned):
        return {
            "assigned_at": pd.NaT,
            "accepted_at": accepted,
            "acceptance_end": pd.NaT,
            "acceptance_hours": None,
            "acceptance_label": "Sin fecha de asignación",
            "accepted": not pd.isna(accepted),
        }

    end = accepted if not pd.isna(accepted) else pd.Timestamp(reference)
    hours = max((end - assigned).total_seconds() / 3600.0, 0.0)

    if not pd.isna(accepted):
        if hours < 24:
            label = f"Aceptada en {hours:.1f} h"
        else:
            label = f"Aceptada en {hours / 24:.1f} días"
    else:
        if hours < 24:
            label = f"Pendiente hace {hours:.1f} h"
        else:
            label = f"Pendiente hace {hours / 24:.1f} días"

    return {
        "assigned_at": assigned,
        "accepted_at": accepted,
        "acceptance_end": end,
        "acceptance_hours": round(hours, 1),
        "acceptance_label": label,
        "accepted": not pd.isna(accepted),
    }


# ============================================================
# GANTT
# ============================================================

def gantt_chart(
    view
):

    gantt = view[
        view["start_date"].notna()
        & (view["start_date"] != "")
        & view["due_date"].notna()
        & (view["due_date"] != "")
    ].copy()

    if gantt.empty:
        st.info(
            "No hay tareas con fecha de inicio y finalización para mostrar."
        )
        return

    gantt["Inicio"] = pd.to_datetime(
        gantt["start_date"],
        errors="coerce",
    )
    gantt["Final"] = pd.to_datetime(
        gantt["due_date"],
        errors="coerce",
    )

    gantt["Etiqueta"] = (
        gantt["code"]
        + " · "
        + gantt["title"].astype(str).str.slice(0, 45)
    )
    gantt["Cumplimiento"] = gantt["Semáforo"]

    acceptance = gantt.apply(acceptance_metrics, axis=1)
    gantt["Asignada"] = acceptance.apply(lambda x: x["assigned_at"])
    gantt["Aceptada"] = acceptance.apply(lambda x: x["accepted_at"])
    gantt["Fin aceptación"] = acceptance.apply(lambda x: x["acceptance_end"])
    gantt["Demora aceptación (h)"] = acceptance.apply(
        lambda x: x["acceptance_hours"]
    )
    gantt["Control aceptación"] = acceptance.apply(
        lambda x: x["acceptance_label"]
    )
    gantt["Aceptación confirmada"] = acceptance.apply(
        lambda x: x["accepted"]
    )

    colors = {
        "🟢 Cerrada": BRAND_GREEN,
        "🟢 En término": COLOR_OK,
        "🟡 Atención": COLOR_WARNING,
        "🔴 Atrasada": COLOR_DANGER,
        "🔴 Vencida": "#9F342C",
        "🔵 Espera cierre": COLOR_WAIT,
        "⚪ Sin cronograma": COLOR_NEUTRAL,
    }

    fig = px.timeline(
        gantt.sort_values(["Final", "priority"]),
        x_start="Inicio",
        x_end="Final",
        y="Etiqueta",
        color="Cumplimiento",
        color_discrete_map=colors,
        hover_data={
            "assignee": True,
            "progress": ":.0f",
            "Teórico %": ":.0f",
            "priority": True,
            "Inicio": "|%d/%m/%Y",
            "Final": "|%d/%m/%Y",
            "Control aceptación": True,
        },
    )

    accepted_legend_added = False
    pending_legend_added = False

    for _, row in gantt.iterrows():
        assigned = row["Asignada"]
        end_acceptance = row["Fin aceptación"]

        if pd.isna(assigned) or pd.isna(end_acceptance):
            continue

        accepted = bool(row["Aceptación confirmada"])
        delay_text = row["Control aceptación"]

        if accepted:
            line_color = "#7D8B84"
            marker_color = BRAND_GREEN
            legend_name = "Tiempo hasta aceptación"
            showlegend = not accepted_legend_added
            accepted_legend_added = True
        else:
            line_color = COLOR_WARNING
            marker_color = COLOR_DANGER
            legend_name = "Pendiente de aceptación"
            showlegend = not pending_legend_added
            pending_legend_added = True

        fig.add_trace(
            go.Scatter(
                x=[assigned, end_acceptance],
                y=[row["Etiqueta"], row["Etiqueta"]],
                mode="lines+markers",
                name=legend_name,
                showlegend=showlegend,
                line=dict(
                    color=line_color,
                    width=7,
                ),
                marker=dict(
                    color=[line_color, marker_color],
                    size=[7, 10],
                    symbol=["circle", "diamond"],
                ),
                opacity=0.82,
                customdata=[delay_text, delay_text],
                hovertemplate=(
                    "<b>Control de aceptación</b><br>"
                    "%{customdata}<br>"
                    "%{x|%d/%m/%Y %H:%M}"
                    "<extra></extra>"
                ),
            )
        )

    fig.update_yaxes(
        autorange="reversed",
        title=None,
    )
    fig.update_xaxes(
        title="Cronograma",
        gridcolor="#E8ECE9",
    )

    fig.add_vline(
        x=pd.Timestamp(date.today()).timestamp() * 1000,
        line_width=1,
        line_dash="dash",
        line_color="#6B7770",
    )

    fig.update_layout(
        height=max(440, min(920, 36 * len(gantt) + 170)),
        margin=dict(l=10, r=10, t=10, b=10),
        legend_title_text="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(color=BRAND_DARK),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )



# ============================================================
# INICIALIZACIÓN
# ============================================================

init_db()

generate_recurring()


# ============================================================
# PORTAL DEL RESPONSABLE
# ============================================================

token = st.query_params.get(
    "token"
)


if token:

    render_header()

    c = con()

    task = c.execute(
        """
        SELECT
            t.*,
            p.name,
            p.email
        FROM tasks t
        JOIN people p
        ON p.id = t.assignee_id
        WHERE t.token = ?
        """,
        (
            token,
        ),
    ).fetchone()

    if not task:

        st.error(
            "Enlace inválido o revocado."
        )

        c.close()

        st.stop()

    section(
        "Tarea asignada",
        task[
            "code"
        ],
    )

    st.write(
        f"**Responsable:** {task['name']}"
    )

    st.write(
        f"**Tarea:** {task['title']}"
    )

    st.write(
        f"**Prioridad:** {task['priority']} · "
        f"**Estado:** {task['status']}"
    )

    m1, m2, m3 = (
        st.columns(
            3
        )
    )

    m1.metric(
        "Avance real",
        f"{float(task['progress'] or 0):.0f}%",
    )

    expected = theoretical(
        task
    )

    m2.metric(
        "Avance teórico",
        (
            "—"
            if expected is None
            else f"{expected:.0f}%"
        ),
    )

    m3.metric(
        "Cumplimiento",
        traffic_light(
            task
        ),
    )

    dates1, dates2 = (
        st.columns(
            2
        )
    )

    with dates1:

        if task[
            "start_date"
        ]:

            st.write(
                "**Inicio:** "
                + pd.to_datetime(
                    task[
                        "start_date"
                    ]
                ).strftime(
                    "%d/%m/%Y"
                )
            )

    with dates2:

        if task[
            "due_date"
        ]:

            st.write(
                "**Finalización prevista:** "
                + pd.to_datetime(
                    task[
                        "due_date"
                    ]
                ).strftime(
                    "%d/%m/%Y"
                )
            )

    if task[
        "maintenance_type"
    ]:

        st.write(
            "**Tipo de mantenimiento:** "
            f"{task['maintenance_type']}"
        )

    if task[
        "observation"
    ]:

        st.info(
            task[
                "observation"
            ]
        )

    if (
        not task[
            "accepted_at"
        ]
        and task[
            "status"
        ]
        not in (
            "Cerrada",
            "Terminada - espera cierre",
        )
    ):

        if st.button(
            "Aceptar tarea",
            type="primary",
            use_container_width=True,
        ):

            c.execute(
                """
                UPDATE tasks
                SET
                    accepted_at = ?,
                    status = 'Aceptada'
                WHERE id = ?
                """,
                (
                    datetime.now().isoformat(),
                    task[
                        "id"
                    ],
                ),
            )

            c.commit()

            log_event(
                c,
                task["id"],
                "accepted",
                task["name"],
                "Tarea aceptada por el responsable.",
            )
            accepted_task = dict(task)
            accepted_task["status"] = "Aceptada"
            person_mail = {"name": task["name"], "email": task["email"]}
            admin_ok, admin_detail = send_admin_event(
                accepted_task,
                person_mail,
                "Tarea aceptada",
                f"{task['name']} aceptó la tarea {task['code']}.",
                BASE_DIR,
            )
            settings = get_mail_settings(BASE_DIR)
            if settings.admin_email:
                log_email(
                    c,
                    task["id"],
                    settings.admin_email,
                    "accepted_admin",
                    f"Tarea aceptada · {task['code']}",
                    admin_ok,
                    admin_detail,
                )

            st.rerun()

    if task[
        "status"
    ] not in (
        "Cerrada",
        "Terminada - espera cierre",
    ):

        section(
            "Actualización diaria"
        )

        with st.form(
            "daily_update"
        ):

            progress = st.slider(
                "Avance acumulado (%)",
                0,
                100,
                int(
                    task[
                        "progress"
                    ]
                    or 0
                ),
            )

            hours = st.number_input(
                "Horas trabajadas hoy",
                min_value=0.0,
                max_value=24.0,
                value=0.0,
                step=0.5,
            )

            work = st.text_area(
                "Trabajo realizado"
            )

            blockers = st.text_area(
                "Problemas / bloqueos"
            )

            submitted = (
                st.form_submit_button(
                    "Guardar actualización",
                    type="primary",
                    use_container_width=True,
                )
            )

        if submitted:

            c.execute(
                """
                INSERT INTO updates(
                    task_id,
                    update_date,
                    progress,
                    hours,
                    work_done,
                    blockers,
                    created_at
                )
                VALUES(
                    ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    task[
                        "id"
                    ],
                    date.today().isoformat(),
                    progress,
                    hours,
                    work,
                    blockers,
                    datetime.now().isoformat(),
                ),
            )

            if progress == 100:

                new_status = (
                    "Terminada - espera cierre"
                )

                finished = (
                    datetime.now().isoformat()
                )

            else:

                new_status = (
                    "En ejecución"
                )

                finished = None

            c.execute(
                """
                UPDATE tasks
                SET
                    progress = ?,
                    status = ?,
                    finished_at = COALESCE(
                        ?,
                        finished_at
                    )
                WHERE id = ?
                """,
                (
                    progress,
                    new_status,
                    finished,
                    task[
                        "id"
                    ],
                ),
            )

            c.commit()

            log_event(
                c,
                task["id"],
                "progress_update",
                task["name"],
                f"Avance {progress:.0f}% · Horas {hours:.1f} · Trabajo: {work or '—'} · Bloqueos: {blockers or '—'}",
            )

            updated_task = dict(task)
            updated_task["progress"] = progress
            updated_task["status"] = new_status
            person_mail = {"name": task["name"], "email": task["email"]}
            event_name = (
                "Tarea finalizada · espera cierre"
                if progress == 100
                else "Actualización de avance"
            )
            detail = (
                f"{task['name']} informó {progress:.0f}% de avance. "
                f"Horas: {hours:.1f}. Trabajo: {work or '—'}. Bloqueos: {blockers or '—'}."
            )
            admin_ok, admin_detail = send_admin_event(
                updated_task,
                person_mail,
                event_name,
                detail,
                BASE_DIR,
            )
            settings = get_mail_settings(BASE_DIR)
            if settings.admin_email:
                log_email(
                    c,
                    task["id"],
                    settings.admin_email,
                    "progress_admin",
                    f"{event_name} · {task['code']}",
                    admin_ok,
                    admin_detail,
                )

            st.rerun()

    history = (
        pd.read_sql_query(
            """
            SELECT
                update_date AS Fecha,
                progress AS "Avance %",
                hours AS Horas,
                work_done AS "Trabajo realizado",
                blockers AS Bloqueos
            FROM updates
            WHERE task_id = ?
            ORDER BY id DESC
            """,
            c,
            params=(
                task[
                    "id"
                ],
            ),
        )
    )

    if not history.empty:

        section(
            "Historial diario"
        )

        st.dataframe(
            history,
            hide_index=True,
            use_container_width=True,
        )

    c.close()

    st.divider()

    st.caption(
        f"SEV · Control de Tareas · {APP_VERSION}"
    )

    st.stop()


# ============================================================
# PANEL ADMINISTRADOR
# ============================================================

render_header()


page = st.sidebar.radio(
    "CONTROL DE TAREAS",
    [
        "Tablero",
        "Nueva tarea",
        "Tareas",
        "Calendario / Gantt",
        "Recurrentes",
        "Mantenimiento",
        "Operarios",
        "Cierres pendientes",
        "Avisos",
    ],
)


c = con()


tasks = pd.read_sql_query(
    """
    SELECT
        t.*,
        p.name AS assignee,
        p.email
    FROM tasks t
    JOIN people p
    ON p.id = t.assignee_id
    ORDER BY t.id DESC
    """,
    c,
)


people = pd.read_sql_query(
    """
    SELECT *
    FROM people
    WHERE active = 1
    ORDER BY name
    """,
    c,
)


# ============================================================
# TABLERO
# ============================================================

if page == "Tablero":

    section(
        "Tablero de cumplimiento",
        "Visión ejecutiva de avance, cronograma y desvíos",
    )

    f1, f2, f3, f4 = (
        st.columns(
            4
        )
    )

    sector_filter = (
        f1.selectbox(
            "Sector",
            [
                "Todos",
                *SECTORES.values(),
            ],
        )
    )

    area_filter = (
        f2.selectbox(
            "Área",
            [
                "Todas",
                *AREAS.values(),
            ],
        )
    )

    operator_filter = (
        f3.selectbox(
            "Operario",
            [
                "Todos",
                *people[
                    "name"
                ].tolist(),
            ],
        )
    )

    status_filter = (
        f4.selectbox(
            "Estado",
            [
                "Todos",
                "Pendiente",
                "Asignada",
                "Aceptada",
                "En ejecución",
                "Terminada - espera cierre",
                "Cerrada",
            ],
        )
    )

    view = tasks.copy()

    if (
        sector_filter
        != "Todos"
    ):

        view = view[
            view[
                "sector"
            ]
            == sector_filter
        ]

    if (
        area_filter
        != "Todas"
    ):

        view = view[
            view[
                "area"
            ]
            == area_filter
        ]

    if (
        operator_filter
        != "Todos"
    ):

        view = view[
            view[
                "assignee"
            ]
            == operator_filter
        ]

    if (
        status_filter
        != "Todos"
    ):

        view = view[
            view[
                "status"
            ]
            == status_filter
        ]

    view[
        "Teórico %"
    ] = view.apply(
        theoretical,
        axis=1,
    )

    view[
        "Desvío pp"
    ] = view.apply(
        schedule_delta,
        axis=1,
    )

    view[
        "Semáforo"
    ] = view.apply(
        traffic_light,
        axis=1,
    )

    open_count = int(
        (
            view[
                "status"
            ]
            != "Cerrada"
        ).sum()
    )

    execution_count = int(
        (
            view[
                "status"
            ]
            == "En ejecución"
        ).sum()
    )

    overdue_count = int(
        view[
            "Semáforo"
        ]
        .astype(
            str
        )
        .str.contains(
            "Vencida|Atrasada"
        )
        .sum()
    )

    waiting_close = int(
        (
            view[
                "status"
            ]
            == "Terminada - espera cierre"
        ).sum()
    )

    requested_month = int(
        (
            pd.to_datetime(
                view[
                    "requested"
                ],
                errors="coerce",
            )
            .dt.to_period(
                "M"
            )
            == pd.Period(
                date.today(),
                freq="M",
            )
        ).sum()
    )

    k1, k2, k3, k4, k5 = (
        st.columns(
            5
        )
    )

    k1.metric(
        "Abiertas",
        open_count,
    )

    k2.metric(
        "En ejecución",
        execution_count,
    )

    k3.metric(
        "Con atraso",
        overdue_count,
    )

    k4.metric(
        "Esperan cierre",
        waiting_close,
    )

    k5.metric(
        "Solicitadas este mes",
        requested_month,
    )

    # --------------------------------------------------------
    # CUMPLIMIENTO POR RESPONSABLE · V2.5
    # --------------------------------------------------------
    section(
        "Cumplimiento por responsable",
        "Lectura rápida del desempeño de cada persona en las tareas filtradas",
    )

    if view.empty:
        st.info("No hay tareas para calcular cumplimiento con los filtros seleccionados.")
    else:
        person_rows = []

        for person_name, person_tasks in view.groupby("assignee", dropna=False):
            total = len(person_tasks)
            closed = int((person_tasks["status"] == "Cerrada").sum())
            waiting = int((person_tasks["status"] == "Terminada - espera cierre").sum())
            on_time = int(
                person_tasks["Semáforo"].astype(str).str.contains(
                    "🟢 En término|🟢 Cerrada", regex=True
                ).sum()
            )
            attention_n = int(person_tasks["Semáforo"].astype(str).str.contains("🟡").sum())
            late_n = int(person_tasks["Semáforo"].astype(str).str.contains("🔴").sum())
            no_schedule = int(person_tasks["Semáforo"].astype(str).str.contains("⚪").sum())

            evaluable = max(total - no_schedule, 0)
            compliance = (100.0 * on_time / evaluable) if evaluable else 0.0
            avg_real = float(person_tasks["progress"].fillna(0).mean()) if total else 0.0
            theoretical_values = pd.to_numeric(person_tasks["Teórico %"], errors="coerce").dropna()
            avg_theoretical = float(theoretical_values.mean()) if not theoretical_values.empty else None

            if late_n > 0:
                status_label = "🔴 Requiere acción"
            elif attention_n > 0:
                status_label = "🟡 Atención"
            elif waiting > 0:
                status_label = "🔵 Espera cierre"
            elif evaluable > 0:
                status_label = "🟢 En término"
            else:
                status_label = "⚪ Sin cronograma"

            person_rows.append({
                "Responsable": str(person_name),
                "Estado": status_label,
                "Tareas": total,
                "Cerradas": closed,
                "En término": on_time,
                "Atención": attention_n,
                "Atrasadas": late_n,
                "Espera cierre": waiting,
                "Cumplimiento %": round(compliance, 1),
                "Avance real %": round(avg_real, 1),
                "Avance teórico %": (round(avg_theoretical, 1) if avg_theoretical is not None else None),
            })

        person_summary = pd.DataFrame(person_rows).sort_values(
            ["Cumplimiento %", "Atrasadas", "Atención"],
            ascending=[False, True, True],
        )

        if not person_summary.empty:
            top_cols = st.columns(min(3, len(person_summary)))
            for idx, (_, person_row) in enumerate(person_summary.head(3).iterrows()):
                with top_cols[idx]:
                    st.metric(
                        person_row["Responsable"],
                        f"{person_row['Cumplimiento %']:.0f}%",
                        delta=(
                            f"{int(person_row['Atrasadas'])} atrasada(s)"
                            if person_row["Atrasadas"] > 0
                            else person_row["Estado"]
                        ),
                    )

            chart_people = person_summary.copy()
            fig_people = px.bar(
                chart_people.sort_values("Cumplimiento %"),
                x="Cumplimiento %",
                y="Responsable",
                orientation="h",
                text="Cumplimiento %",
                hover_data={
                    "Tareas": True,
                    "En término": True,
                    "Atención": True,
                    "Atrasadas": True,
                    "Avance real %": True,
                    "Avance teórico %": True,
                },
            )
            fig_people.update_traces(
                marker_color=BRAND_GREEN,
                texttemplate="%{text:.0f}%",
                textposition="outside",
                cliponaxis=False,
            )
            fig_people.update_layout(
                height=max(280, 54 * len(chart_people) + 90),
                margin=dict(l=10, r=45, t=5, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#FFFFFF",
                showlegend=False,
                xaxis=dict(
                    title="Cumplimiento (%)",
                    range=[0, 108],
                    gridcolor="#E8ECE9",
                ),
                yaxis=dict(title=None),
                font=dict(color=BRAND_DARK),
            )
            st.plotly_chart(fig_people, use_container_width=True)

            with st.expander("Ver detalle por responsable", expanded=False):
                st.dataframe(
                    person_summary,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Cumplimiento %": st.column_config.ProgressColumn(
                            "Cumplimiento %", min_value=0, max_value=100, format="%.0f%%"
                        ),
                        "Avance real %": st.column_config.ProgressColumn(
                            "Avance real %", min_value=0, max_value=100, format="%.0f%%"
                        ),
                    },
                )

    with st.expander("Avance real vs. teórico por tarea", expanded=False):
        st.caption("Comparación individual contra el avance esperado por fecha")
        progress_chart(view)

    section(
        "Cronograma de cumplimiento · Gantt",
        "La línea vertical marca la fecha actual",
    )

    gantt_chart(
        view
    )

    section(
        "Tareas que requieren atención",
        "Prioridad para tareas amarillas y rojas",
    )

    attention = view[
        view[
            "Semáforo"
        ]
        .astype(
            str
        )
        .str.contains(
            "🔴|🟡"
        )
    ].copy()

    if attention.empty:

        st.success(
            "No hay tareas con alertas en el filtro seleccionado."
        )

    else:

        attention[
            "Inicio"
        ] = (
            pd.to_datetime(
                attention[
                    "start_date"
                ],
                errors="coerce",
            )
            .dt.strftime(
                "%d/%m/%Y"
            )
            .fillna(
                "—"
            )
        )

        attention[
            "Final"
        ] = (
            pd.to_datetime(
                attention[
                    "due_date"
                ],
                errors="coerce",
            )
            .dt.strftime(
                "%d/%m/%Y"
            )
            .fillna(
                "—"
            )
        )

        attention[
            "Real %"
        ] = (
            attention[
                "progress"
            ]
            .fillna(
                0
            )
            .round(
                0
            )
        )

        attention[
            "Teórico %"
        ] = (
            attention[
                "Teórico %"
            ]
            .round(
                0
            )
        )

        st.dataframe(
            attention[
                [
                    "Semáforo",
                    "code",
                    "title",
                    "assignee",
                    "priority",
                    "Inicio",
                    "Final",
                    "Real %",
                    "Teórico %",
                    "Desvío pp",
                ]
            ].rename(
                columns={
                    "code": "Código",
                    "title": "Tarea",
                    "assignee": "Responsable",
                    "priority": "Prioridad",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )

    section(
        "Solicitudes por mes",
        "Cantidad de tareas solicitadas",
    )

    monthly = (
        view.copy()
    )

    monthly[
        "Mes"
    ] = (
        pd.to_datetime(
            monthly[
                "requested"
            ],
            errors="coerce",
        )
        .dt.to_period(
            "M"
        )
        .astype(
            str
        )
    )

    monthly = (
        monthly
        .groupby(
            "Mes"
        )
        .size()
        .reset_index(
            name="Tareas"
        )
    )

    if not monthly.empty:

        fig_month = (
            px.line(
                monthly,
                x="Mes",
                y="Tareas",
                markers=True,
            )
        )

        fig_month.update_traces(
            line_color=BRAND_GREEN,
            marker_color=BRAND_GREEN,
            line_width=3,
        )

        fig_month.update_layout(
            height=300,
            margin=dict(
                l=10,
                r=10,
                t=10,
                b=10,
            ),
            paper_bgcolor=(
                "rgba(0,0,0,0)"
            ),
            plot_bgcolor="#FFFFFF",
            font=dict(
                color=BRAND_DARK
            ),
            xaxis=dict(
                showgrid=False
            ),
            yaxis=dict(
                gridcolor="#E8ECE9"
            ),
        )

        st.plotly_chart(
            fig_month,
            use_container_width=True,
        )


# ============================================================
# NUEVA TAREA
# ============================================================

elif page == "Nueva tarea":

    section(
        "Nueva tarea",
        "La codificación SEV se genera automáticamente",
    )

    sector_name = st.selectbox(
        "Sector",
        list(
            SECTORES
        ),
    )

    area_name = st.selectbox(
        "Área / familia",
        list(
            AREAS
        ),
    )

    maintenance_type = None

    if (
        SECTORES[
            sector_name
        ]
        == "MANT"
    ):

        maintenance_type = (
            st.selectbox(
                "Tipo de mantenimiento",
                TIPOS_MANT,
            )
        )

    with st.form(
        "new_task"
    ):

        title = (
            st.text_input(
                "Tarea"
            )
        )

        description = (
            st.text_area(
                "Descripción"
            )
        )

        col1, col2 = (
            st.columns(
                2
            )
        )

        priority = (
            col1.selectbox(
                "Prioridad",
                PRIORIDADES,
            )
        )

        assignee_id = (
            col2.selectbox(
                "Responsable",
                people[
                    "id"
                ].tolist(),
                format_func=(
                    lambda person_id:
                    people.loc[
                        people[
                            "id"
                        ]
                        == person_id,
                        "name",
                    ].iloc[
                        0
                    ]
                ),
            )
        )

        col1, col2 = (
            st.columns(
                2
            )
        )

        start = (
            col1.date_input(
                "Fecha de inicio",
                format="DD/MM/YYYY",
            )
        )

        due = (
            col2.date_input(
                "Fecha de finalización",
                format="DD/MM/YYYY",
            )
        )

        recurrence = (
            st.selectbox(
                "Recurrencia",
                RECURRENCIAS,
            )
        )

        observation = (
            st.text_area(
                "Observación"
            )
        )

        submit = (
            st.form_submit_button(
                "Crear y asignar tarea",
                type="primary",
                use_container_width=True,
            )
        )

    if submit:

        if not title.strip():

            st.error(
                "Ingresa el nombre de la tarea."
            )

        elif due < start:

            st.error(
                "La fecha final no puede ser anterior a la fecha de inicio."
            )

        else:

            sector_code = (
                SECTORES[
                    sector_name
                ]
            )

            area_code = (
                AREAS[
                    area_name
                ]
            )

            code = (
                next_code(
                    sector_code,
                    area_code,
                    c,
                )
            )

            task_token = (
                secrets.token_urlsafe(
                    24
                )
            )

            c.execute(
                """
                INSERT INTO tasks(
                    code,
                    title,
                    description,
                    sector,
                    area,
                    maintenance_type,
                    assignee_id,
                    priority,
                    requested,
                    start_date,
                    due_date,
                    status,
                    progress,
                    observation,
                    token,
                    recurrence,
                    recurrence_day,
                    created_at
                )
                VALUES(
                    ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
                )
                """,
                (
                    code,
                    title.strip(),
                    description.strip(),
                    sector_code,
                    area_code,
                    maintenance_type,
                    int(
                        assignee_id
                    ),
                    priority,
                    date.today().isoformat(),
                    start.isoformat(),
                    due.isoformat(),
                    "Asignada",
                    0,
                    observation.strip(),
                    task_token,
                    (
                        None
                        if recurrence
                        == "No"
                        else recurrence
                    ),
                    due.day,
                    datetime.now().isoformat(),
                ),
            )

            c.commit()

            new_task_id = c.execute(
                "SELECT id FROM tasks WHERE code = ?",
                (code,),
            ).fetchone()["id"]

            person_row = people.loc[
                people["id"] == int(assignee_id)
            ].iloc[0]

            task_mail = {
                "id": int(new_task_id),
                "code": code,
                "title": title.strip(),
                "priority": priority,
                "start_date": start.strftime("%d/%m/%Y"),
                "due_date": due.strftime("%d/%m/%Y"),
                "token": task_token,
                "progress": 0,
            }
            person_mail = {
                "name": str(person_row["name"]),
                "email": str(person_row["email"]),
            }

            mail_ok, mail_detail = send_assignment_email(
                task_mail,
                person_mail,
                BASE_DIR,
            )
            log_email(
                c,
                new_task_id,
                person_mail["email"],
                "assignment",
                f"Nueva tarea asignada · {code}",
                mail_ok,
                mail_detail,
            )
            log_event(
                c,
                new_task_id,
                "created",
                "Administrador",
                f"Tarea asignada a {person_mail['name']}",
            )

            st.success(
                f"Tarea creada correctamente: {code}"
            )

            if mail_ok:
                st.success(
                    f"Correo enviado a {person_mail['email']}."
                )
            else:
                st.warning(
                    "La tarea fue creada, pero el correo no pudo enviarse: "
                    + mail_detail
                )

            st.write(
                "**Enlace del responsable:**"
            )

            st.code(
                build_task_url(
                    task_token,
                    BASE_DIR,
                )
            )


# ============================================================
# TAREAS
# ============================================================

elif page == "Tareas":

    section(
        "Tareas",
        "Listado general, edición y cierre administrativo",
    )

    view = tasks.copy()

    view["Teórico %"] = view.apply(
        theoretical,
        axis=1,
    )

    view["Semáforo"] = view.apply(
        traffic_light,
        axis=1,
    )

    view["Inicio"] = (
        pd.to_datetime(
            view["start_date"],
            errors="coerce",
        )
        .dt.strftime("%d/%m/%Y")
        .fillna("—")
    )

    view["Final"] = (
        pd.to_datetime(
            view["due_date"],
            errors="coerce",
        )
        .dt.strftime("%d/%m/%Y")
        .fillna("—")
    )

    f1, f2, f3 = st.columns([1.1, 1.4, 1.2])

    task_status_filter = f1.selectbox(
        "Filtrar por estado",
        [
            "Todos",
            "Pendiente",
            "Asignada",
            "Aceptada",
            "En ejecución",
            "Terminada - espera cierre",
            "Cerrada",
        ],
        key="tasks_status_filter",
    )

    task_person_filter = f2.selectbox(
        "Filtrar por responsable",
        ["Todos", *people["name"].tolist()],
        key="tasks_person_filter",
    )

    search_task = f3.text_input(
        "Buscar",
        placeholder="Código o tarea",
        key="tasks_search",
    )

    filtered = view.copy()

    if task_status_filter != "Todos":
        filtered = filtered[filtered["status"] == task_status_filter]

    if task_person_filter != "Todos":
        filtered = filtered[filtered["assignee"] == task_person_filter]

    if search_task.strip():
        needle = search_task.strip().lower()
        mask = (
            filtered["code"].astype(str).str.lower().str.contains(needle, regex=False)
            | filtered["title"].astype(str).str.lower().str.contains(needle, regex=False)
        )
        filtered = filtered[mask]

    display = filtered[
        [
            "Semáforo",
            "code",
            "title",
            "sector",
            "area",
            "maintenance_type",
            "assignee",
            "priority",
            "status",
            "Inicio",
            "Final",
            "progress",
            "Teórico %",
            "observation",
        ]
    ].rename(
        columns={
            "code": "Código",
            "title": "Tarea",
            "sector": "Sector",
            "area": "Área",
            "maintenance_type": "Tipo mantenimiento",
            "assignee": "Responsable",
            "priority": "Prioridad",
            "status": "Estado",
            "progress": "Real %",
            "observation": "Observación",
        }
    )

    st.dataframe(
        display,
        hide_index=True,
        use_container_width=True,
        height=520,
    )

    section(
        "Editar / cerrar acción",
        "Seleccioná una tarea para corregir sus datos, actualizar el avance o realizar el cierre administrativo.",
    )

    if tasks.empty:
        st.info("No existen tareas para editar.")
    else:
        task_options = tasks["id"].astype(int).tolist()
        task_labels = {
            int(row.id): f"{row.code} · {row.title}"
            for _, row in tasks.iterrows()
        }

        selected_task_id = st.selectbox(
            "Seleccionar tarea",
            task_options,
            format_func=lambda task_id: task_labels.get(int(task_id), str(task_id)),
            key="edit_task_id",
        )

        selected = tasks.loc[tasks["id"] == int(selected_task_id)].iloc[0]

        selected_start = pd.to_datetime(
            selected.get("start_date"),
            errors="coerce",
        )
        selected_due = pd.to_datetime(
            selected.get("due_date"),
            errors="coerce",
        )

        current_assignee_id = int(selected["assignee_id"])
        person_ids = people["id"].astype(int).tolist()
        person_names = dict(zip(people["id"].astype(int), people["name"]))

        status_values = [
            "Pendiente",
            "Asignada",
            "Aceptada",
            "En ejecución",
            "Terminada - espera cierre",
            "Cerrada",
        ]

        current_sector = str(selected.get("sector") or "LAB")
        current_area = str(selected.get("area") or "FER")
        current_priority = str(selected.get("priority") or "Media")
        current_status = str(selected.get("status") or "Pendiente")
        current_maintenance = str(selected.get("maintenance_type") or "")

        with st.form("edit_task_form"):
            e1, e2 = st.columns([1.7, 1.0])

            edit_title = e1.text_input(
                "Tarea",
                value=str(selected.get("title") or ""),
            )

            edit_assignee = e2.selectbox(
                "Responsable",
                person_ids,
                index=(
                    person_ids.index(current_assignee_id)
                    if current_assignee_id in person_ids
                    else 0
                ),
                format_func=lambda person_id: person_names.get(int(person_id), str(person_id)),
            )

            edit_description = st.text_area(
                "Descripción",
                value=str(selected.get("description") or ""),
                height=90,
            )

            c1, c2, c3, c4 = st.columns(4)

            sector_values = list(SECTORES.values())
            area_values = list(AREAS.values())

            edit_sector = c1.selectbox(
                "Sector",
                sector_values,
                index=sector_values.index(current_sector) if current_sector in sector_values else 0,
            )

            edit_area = c2.selectbox(
                "Área",
                area_values,
                index=area_values.index(current_area) if current_area in area_values else 0,
            )

            edit_priority = c3.selectbox(
                "Prioridad",
                PRIORIDADES,
                index=PRIORIDADES.index(current_priority) if current_priority in PRIORIDADES else 2,
            )

            edit_status = c4.selectbox(
                "Estado",
                status_values,
                index=status_values.index(current_status) if current_status in status_values else 0,
            )

            d1, d2, d3 = st.columns([1.0, 1.0, 1.1])

            use_start = d1.checkbox(
                "Definir fecha de inicio",
                value=not pd.isna(selected_start),
            )
            edit_start = d1.date_input(
                "Inicio",
                value=(selected_start.date() if not pd.isna(selected_start) else date.today()),
                format="DD/MM/YYYY",
                disabled=not use_start,
            )

            use_due = d2.checkbox(
                "Definir fecha final",
                value=not pd.isna(selected_due),
            )
            edit_due = d2.date_input(
                "Final",
                value=(selected_due.date() if not pd.isna(selected_due) else date.today()),
                format="DD/MM/YYYY",
                disabled=not use_due,
            )

            edit_progress = d3.slider(
                "Avance real (%)",
                0,
                100,
                int(float(selected.get("progress") or 0)),
            )

            maintenance_options = ["—", *TIPOS_MANT]
            edit_maintenance = st.selectbox(
                "Tipo de mantenimiento",
                maintenance_options,
                index=(
                    maintenance_options.index(current_maintenance)
                    if current_maintenance in maintenance_options
                    else 0
                ),
                disabled=(edit_sector != "MANT"),
            )

            edit_observation = st.text_area(
                "Observación / evidencia de cierre",
                value=str(selected.get("observation") or ""),
                height=110,
                help="Al cerrar una acción, conviene dejar aquí el resultado, evidencia o comentario final.",
            )

            st.caption(
                f"Estado actual: {current_status} · Responsable actual: {selected.get('assignee', '—')} · "
                f"Avance actual: {float(selected.get('progress') or 0):.0f}%"
            )

            b1, b2 = st.columns(2)
            save_changes = b1.form_submit_button(
                "Guardar cambios",
                type="primary",
                use_container_width=True,
            )
            close_action = b2.form_submit_button(
                "Cerrar acción ahora",
                use_container_width=True,
            )

        if save_changes or close_action:
            if not edit_title.strip():
                st.error("La tarea no puede quedar sin nombre.")
            elif use_start and use_due and edit_due < edit_start:
                st.error("La fecha final no puede ser anterior a la fecha de inicio.")
            else:
                new_status = "Cerrada" if close_action else edit_status
                new_progress = 100 if close_action or new_status == "Cerrada" else int(edit_progress)
                start_value = edit_start.isoformat() if use_start else None
                due_value = edit_due.isoformat() if use_due else None
                maintenance_value = (
                    None
                    if edit_sector != "MANT" or edit_maintenance == "—"
                    else edit_maintenance
                )

                was_closed = current_status == "Cerrada"
                will_be_closed = new_status == "Cerrada"
                closed_at = selected.get("closed_at")
                finished_at = selected.get("finished_at")

                if will_be_closed:
                    closed_at = closed_at or datetime.now().isoformat()
                    finished_at = finished_at or datetime.now().isoformat()
                elif was_closed and not will_be_closed:
                    closed_at = None

                c.execute(
                    """
                    UPDATE tasks
                    SET
                        title = ?,
                        description = ?,
                        sector = ?,
                        area = ?,
                        maintenance_type = ?,
                        assignee_id = ?,
                        priority = ?,
                        start_date = ?,
                        due_date = ?,
                        status = ?,
                        progress = ?,
                        observation = ?,
                        finished_at = ?,
                        closed_at = ?
                    WHERE id = ?
                    """,
                    (
                        edit_title.strip(),
                        edit_description.strip(),
                        edit_sector,
                        edit_area,
                        maintenance_value,
                        int(edit_assignee),
                        edit_priority,
                        start_value,
                        due_value,
                        new_status,
                        float(new_progress),
                        edit_observation.strip(),
                        finished_at,
                        closed_at,
                        int(selected_task_id),
                    ),
                )
                c.commit()

                if will_be_closed and not was_closed:
                    log_event(
                        c,
                        int(selected_task_id),
                        "closed",
                        "Administrador",
                        "Cierre realizado desde edición de tareas. "
                        + (edit_observation.strip() or "Sin observación final."),
                    )

                    person_row = people.loc[people["id"] == int(edit_assignee)]
                    if not person_row.empty:
                        person_mail = {
                            "name": str(person_row.iloc[0]["name"]),
                            "email": str(person_row.iloc[0]["email"]),
                        }
                        closed_task = dict(selected)
                        closed_task.update(
                            {
                                "title": edit_title.strip(),
                                "status": "Cerrada",
                                "progress": 100,
                                "observation": edit_observation.strip(),
                                "due_date": due_value,
                            }
                        )
                        mail_ok, mail_detail = send_closed_email(
                            closed_task,
                            person_mail,
                            BASE_DIR,
                        )
                        log_email(
                            c,
                            int(selected_task_id),
                            person_mail["email"],
                            "closed",
                            f"Tarea cerrada · {selected.get('code', '')}",
                            mail_ok,
                            mail_detail,
                        )

                elif was_closed and not will_be_closed:
                    log_event(
                        c,
                        int(selected_task_id),
                        "reopened",
                        "Administrador",
                        "Tarea reabierta desde edición de tareas.",
                    )
                else:
                    log_event(
                        c,
                        int(selected_task_id),
                        "edited",
                        "Administrador",
                        f"Datos actualizados. Estado: {new_status}. Avance: {new_progress}%.",
                    )

                st.success(
                    "Acción cerrada correctamente."
                    if will_be_closed
                    else "Cambios guardados correctamente."
                )
                st.rerun()


# ============================================================
# CALENDARIO / GANTT
# ============================================================

elif page == "Calendario / Gantt":

    section(
        "Calendario y Gantt",
        "Inicio, finalización y estado de cumplimiento",
    )

    gantt = (
        tasks.copy()
    )

    gantt[
        "Teórico %"
    ] = (
        gantt.apply(
            theoretical,
            axis=1,
        )
    )

    gantt[
        "Semáforo"
    ] = (
        gantt.apply(
            traffic_light,
            axis=1,
        )
    )

    acceptance_rows = gantt.apply(acceptance_metrics, axis=1)
    acceptance_hours = pd.Series(
        [
            item["acceptance_hours"]
            for item in acceptance_rows
            if item["acceptance_hours"] is not None
        ],
        dtype=float,
    )
    accepted_hours = pd.Series(
        [
            item["acceptance_hours"]
            for item in acceptance_rows
            if item["accepted"]
            and item["acceptance_hours"] is not None
        ],
        dtype=float,
    )
    pending_acceptance = int(
        sum(1 for item in acceptance_rows if not item["accepted"])
    )
    accepted_24h = int(
        sum(
            1
            for item in acceptance_rows
            if item["accepted"]
            and item["acceptance_hours"] is not None
            and item["acceptance_hours"] <= 24
        )
    )
    total_accepted = int(
        sum(1 for item in acceptance_rows if item["accepted"])
    )

    a1, a2, a3, a4 = st.columns(4)
    a1.metric("Pendientes de aceptación", pending_acceptance)
    a2.metric(
        "Demora media de aceptación",
        "—"
        if accepted_hours.empty
        else f"{accepted_hours.mean():.1f} h",
    )
    a3.metric(
        "Aceptadas dentro de 24 h",
        "—"
        if total_accepted == 0
        else f"{accepted_24h}/{total_accepted}",
    )
    a4.metric(
        "Mayor demora registrada",
        "—"
        if acceptance_hours.empty
        else (
            f"{acceptance_hours.max():.1f} h"
            if acceptance_hours.max() < 24
            else f"{acceptance_hours.max() / 24:.1f} días"
        ),
    )

    st.caption(
        "En el Gantt, la línea adicional muestra el tiempo entre la asignación "
        "y la aceptación. Si todavía no fue aceptada, se extiende hasta el momento actual."
    )

    gantt_chart(
        gantt
    )

    scheduled = gantt[
        gantt[
            "start_date"
        ].notna()
        & (
            gantt[
                "start_date"
            ]
            != ""
        )
        & gantt[
            "due_date"
        ].notna()
        & (
            gantt[
                "due_date"
            ]
            != ""
        )
    ].copy()

    if not scheduled.empty:

        scheduled[
            "Inicio"
        ] = (
            pd.to_datetime(
                scheduled[
                    "start_date"
                ]
            )
            .dt.strftime(
                "%d/%m/%Y"
            )
        )

        scheduled[
            "Final"
        ] = (
            pd.to_datetime(
                scheduled[
                    "due_date"
                ]
            )
            .dt.strftime(
                "%d/%m/%Y"
            )
        )

        scheduled[
            "Real %"
        ] = (
            scheduled[
                "progress"
            ]
            .fillna(
                0
            )
            .round(
                0
            )
        )

        scheduled["Asignada"] = pd.to_datetime(
            scheduled["created_at"],
            errors="coerce",
        ).dt.strftime("%d/%m/%Y %H:%M").fillna("—")

        scheduled["Aceptada"] = pd.to_datetime(
            scheduled["accepted_at"],
            errors="coerce",
        ).dt.strftime("%d/%m/%Y %H:%M").fillna("Pendiente")

        scheduled["Demora aceptación"] = scheduled.apply(
            lambda row: acceptance_metrics(row)["acceptance_label"],
            axis=1,
        )

        section(
            "Cronograma detallado"
        )

        st.dataframe(
            scheduled[
                [
                    "Semáforo",
                    "code",
                    "title",
                    "assignee",
                    "Asignada",
                    "Aceptada",
                    "Demora aceptación",
                    "Inicio",
                    "Final",
                    "priority",
                    "Real %",
                    "Teórico %",
                ]
            ].rename(
                columns={
                    "code": "Código",
                    "title": "Tarea",
                    "assignee": "Responsable",
                    "priority": "Prioridad",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )


# ============================================================
# RECURRENTES
# ============================================================

elif page == "Recurrentes":

    section(
        "Tareas recurrentes",
        "Programación automática de actividades repetitivas",
    )

    recurrent = tasks[
        tasks[
            "recurrence"
        ].notna()
        & (
            tasks[
                "recurrence"
            ]
            != "No"
        )
    ].copy()

    if recurrent.empty:

        st.info(
            "No existen tareas recurrentes."
        )

    else:

        recurrent[
            "Final"
        ] = (
            pd.to_datetime(
                recurrent[
                    "due_date"
                ],
                errors="coerce",
            )
            .dt.strftime(
                "%d/%m/%Y"
            )
            .fillna(
                "—"
            )
        )

        st.dataframe(
            recurrent[
                [
                    "code",
                    "title",
                    "sector",
                    "area",
                    "assignee",
                    "recurrence",
                    "recurrence_day",
                    "Final",
                    "status",
                ]
            ].rename(
                columns={
                    "code": "Código",
                    "title": "Tarea",
                    "sector": "Sector",
                    "area": "Área",
                    "assignee": "Responsable",
                    "recurrence": "Recurrencia",
                    "recurrence_day": "Día",
                    "status": "Estado",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )


# ============================================================
# MANTENIMIENTO
# ============================================================

elif page == "Mantenimiento":

    section(
        "Mantenimiento",
        "Indicadores por tipo de mantenimiento",
    )

    maintenance = tasks[
        tasks[
            "sector"
        ]
        == "MANT"
    ].copy()

    if maintenance.empty:

        st.info(
            "Todavía no existen tareas de mantenimiento."
        )

    else:

        m1, m2, m3, m4 = (
            st.columns(
                4
            )
        )

        m1.metric(
            "Preventivo",
            int(
                (
                    maintenance[
                        "maintenance_type"
                    ]
                    == "Preventivo"
                ).sum()
            ),
        )

        m2.metric(
            "Correctivo",
            int(
                (
                    maintenance[
                        "maintenance_type"
                    ]
                    == "Correctivo"
                ).sum()
            ),
        )

        m3.metric(
            "Proactivo",
            int(
                (
                    maintenance[
                        "maintenance_type"
                    ]
                    == "Proactivo"
                ).sum()
            ),
        )

        m4.metric(
            "Predictivo",
            int(
                (
                    maintenance[
                        "maintenance_type"
                    ]
                    == "Predictivo"
                ).sum()
            ),
        )

        grouped = (
            maintenance
            .groupby(
                [
                    "maintenance_type",
                    "status",
                ]
            )
            .size()
            .reset_index(
                name="Tareas"
            )
        )

        fig = px.bar(
            grouped,
            x="maintenance_type",
            y="Tareas",
            color="status",
            barmode="group",
        )

        fig.update_layout(
            paper_bgcolor=(
                "rgba(0,0,0,0)"
            ),
            plot_bgcolor="#FFFFFF",
            margin=dict(
                l=10,
                r=10,
                t=10,
                b=10,
            ),
        )

        st.plotly_chart(
            fig,
            use_container_width=True,
        )

        maintenance[
            "Inicio"
        ] = (
            pd.to_datetime(
                maintenance[
                    "start_date"
                ],
                errors="coerce",
            )
            .dt.strftime(
                "%d/%m/%Y"
            )
            .fillna(
                "—"
            )
        )

        maintenance[
            "Final"
        ] = (
            pd.to_datetime(
                maintenance[
                    "due_date"
                ],
                errors="coerce",
            )
            .dt.strftime(
                "%d/%m/%Y"
            )
            .fillna(
                "—"
            )
        )

        st.dataframe(
            maintenance[
                [
                    "code",
                    "title",
                    "area",
                    "maintenance_type",
                    "assignee",
                    "priority",
                    "status",
                    "progress",
                    "Inicio",
                    "Final",
                ]
            ].rename(
                columns={
                    "code": "Código",
                    "title": "Tarea",
                    "area": "Área",
                    "maintenance_type": "Tipo mantenimiento",
                    "assignee": "Responsable",
                    "priority": "Prioridad",
                    "status": "Estado",
                    "progress": "Avance %",
                }
            ),
            hide_index=True,
            use_container_width=True,
        )


# ============================================================
# OPERARIOS
# ============================================================

elif page == "Operarios":

    section(
        "Operarios",
        "Carga de trabajo y avance promedio",
    )

    summary = (
        tasks
        .groupby(
            "assignee"
        )
        .agg(
            Tareas=(
                "id",
                "count",
            ),
            Abiertas=(
                "status",
                lambda status:
                (
                    status
                    != "Cerrada"
                ).sum(),
            ),
            Cerradas=(
                "status",
                lambda status:
                (
                    status
                    == "Cerrada"
                ).sum(),
            ),
            Avance_promedio=(
                "progress",
                "mean",
            ),
        )
        .reset_index()
    )

    summary[
        "Avance_promedio"
    ] = (
        summary[
            "Avance_promedio"
        ]
        .fillna(
            0
        )
        .round(
            1
        )
    )

    summary = (
        summary.rename(
            columns={
                "assignee": "Operario",
                "Avance_promedio": "Avance promedio %",
            }
        )
    )

    st.dataframe(
        summary,
        hide_index=True,
        use_container_width=True,
    )


# ============================================================
# CIERRES
# ============================================================

elif page == "Cierres pendientes":

    section(
        "Cierres pendientes",
        "El responsable termina; el administrador aprueba el cierre",
    )

    pending = tasks[
        tasks[
            "status"
        ]
        == "Terminada - espera cierre"
    ]

    if pending.empty:

        st.success(
            "No hay tareas esperando cierre administrativo."
        )

    else:

        for _, task in (
            pending.iterrows()
        ):

            with st.container(
                border=True
            ):

                st.write(
                    f"**{task.code} · {task.title}**"
                )

                st.write(
                    f"Responsable: **{task.assignee}**"
                )

                st.write(
                    f"Avance informado: **{float(task.progress or 0):.0f}%**"
                )

                if st.button(
                    "Aprobar cierre",
                    key=(
                        f"close_{task.id}"
                    ),
                    type="primary",
                ):

                    c.execute(
                        """
                        UPDATE tasks
                        SET
                            status = 'Cerrada',
                            closed_at = ?
                        WHERE id = ?
                        """,
                        (
                            datetime.now().isoformat(),
                            int(
                                task.id
                            ),
                        ),
                    )

                    c.commit()

                    closed_task = task.to_dict()
                    person_mail = {
                        "name": str(task.assignee),
                        "email": str(task.email),
                    }
                    mail_ok, mail_detail = send_closed_email(
                        closed_task,
                        person_mail,
                        BASE_DIR,
                    )
                    log_email(
                        c,
                        int(task.id),
                        person_mail["email"],
                        "closed",
                        f"Tarea cerrada · {task.code}",
                        mail_ok,
                        mail_detail,
                    )
                    log_event(
                        c,
                        int(task.id),
                        "closed",
                        "Administrador",
                        "Cierre administrativo aprobado.",
                    )

                    st.rerun()


# ============================================================
# AVISOS Y SEGUIMIENTO
# ============================================================

elif page == "Avisos":

    section(
        "Avisos y seguimiento",
        "Control de correos automáticos y recordatorios de avance",
    )

    settings = get_mail_settings(BASE_DIR)

    m1, m2, m3 = st.columns(3)
    m1.metric(
        "SMTP",
        "Configurado" if settings.configured else "Pendiente",
    )
    m2.metric(
        "Correo administrador",
        settings.admin_email or "Pendiente",
    )
    m3.metric(
        "URL pública",
        "Configurada" if settings.app_base_url else "Pendiente",
    )

    if not settings.configured or not settings.app_base_url:
        st.warning(
            "Para enviar enlaces por correo configura SMTP y APP_BASE_URL en .streamlit/secrets.toml."
        )

    if st.button(
        "Ejecutar revisión de avisos ahora",
        type="primary",
        use_container_width=True,
    ):
        result = run_reminders(DB)
        st.success(
            f"Revisión terminada · revisadas {result['checked']} · "
            f"enviadas {result['sent']} · errores {result['failed']} · "
            f"omitidas {result['skipped']}"
        )

    section(
        "Historial de correos",
        "Registro de asignaciones, avances, recordatorios y cierres",
    )

    email_history = pd.read_sql_query(
        """
        SELECT
            e.sent_at AS Fecha,
            t.code AS Código,
            p.name AS Responsable,
            e.recipient AS Destinatario,
            e.email_type AS Tipo,
            e.status AS Estado,
            e.detail AS Detalle
        FROM email_logs e
        LEFT JOIN tasks t ON t.id = e.task_id
        LEFT JOIN people p ON p.id = t.assignee_id
        ORDER BY e.id DESC
        LIMIT 300
        """,
        c,
    )

    if email_history.empty:
        st.info("Todavía no hay correos registrados.")
    else:
        st.dataframe(
            email_history,
            hide_index=True,
            use_container_width=True,
            height=520,
        )


# ============================================================
# FINAL
# ============================================================

c.close()

st.divider()

st.caption(
    f"SEV · Control de Tareas · {APP_VERSION}"
)
