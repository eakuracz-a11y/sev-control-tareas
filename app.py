from pathlib import Path
import sqlite3
import secrets
import calendar
from datetime import date, datetime, timedelta

import pandas as pd
import plotly.express as px
import streamlit as st


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

APP_VERSION = "V2.1"

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
TEXT_MUTED = "#66766E"

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


st.markdown(
    f"""
<style>

html, body, [class*="css"] {{
    font-family: Inter, "Segoe UI", Arial, sans-serif;
}}

.stApp {{
    background: {BRAND_BG};
    color: {BRAND_DARK};
}}

.block-container {{
    padding-top: 2.5rem;
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
    letter-spacing: -0.02em;
}}

div[data-testid="stMetric"] {{
    background: white;
    border: 1px solid {BRAND_BORDER};
    border-radius: 14px;
    padding: 13px 15px;
    box-shadow: 0 1px 2px rgba(20, 55, 40, 0.03);
}}

div[data-testid="stMetricLabel"] {{
    color: #607168;
    font-weight: 600;
}}

div[data-testid="stMetricValue"] {{
    color: {BRAND_DARK};
}}

.sev-header {{
    border-bottom: 1px solid {BRAND_BORDER};
    padding-bottom: 16px;
    margin-bottom: 18px;
}}

.sev-kicker {{
    color: {BRAND_GREEN};
    font-size: 0.75rem;
    font-weight: 700;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    margin-bottom: 4px;
}}

.sev-title {{
    color: {BRAND_DARK};
    font-size: 2.1rem;
    font-weight: 750;
    line-height: 1.10;
}}

.sev-subtitle {{
    color: {TEXT_MUTED};
    font-size: 0.92rem;
    margin-top: 6px;
}}

.sev-section {{
    margin-top: 1.3rem;
    margin-bottom: 0.65rem;
}}

.sev-section-title {{
    color: {BRAND_DARK};
    font-size: 1.15rem;
    font-weight: 700;
}}

.sev-section-note {{
    color: {TEXT_MUTED};
    font-size: 0.80rem;
    margin-top: 2px;
}}

[data-testid="stDataFrame"] {{
    border: 1px solid {BRAND_BORDER};
    border-radius: 12px;
    overflow: hidden;
}}

.stButton > button {{
    border-radius: 10px;
}}

button[kind="primary"] {{
    background-color: {BRAND_GREEN} !important;
    border-color: {BRAND_GREEN} !important;
    color: white !important;
}}

.sev-footer {{
    border-top: 1px solid {BRAND_BORDER};
    margin-top: 2rem;
    padding-top: 1rem;
    color: {TEXT_MUTED};
    font-size: 0.78rem;
}}

</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# COMPONENTES VISUALES
# ============================================================

def render_header():

    logo_col, text_col = st.columns(
        [1.0, 5.5],
        vertical_alignment="center",
    )

    with logo_col:

        if LOGO.exists():

            st.image(
                str(LOGO),
                width=175,
            )

        else:

            st.markdown("### Sevion")

    with text_col:

        header_html = (
            '<div class="sev-header">'
            '<div class="sev-kicker">Gestión operacional</div>'
            '<div class="sev-title">Control de Tareas</div>'
            f'<div class="sev-subtitle">{APP_VERSION} · planificación, ejecución y cumplimiento</div>'
            '</div>'
        )

        st.markdown(
            header_html,
            unsafe_allow_html=True,
        )


def section(title, note=""):

    section_html = (
        '<div class="sev-section">'
        f'<div class="sev-section-title">{title}</div>'
        f'<div class="sev-section-note">{note}</div>'
        '</div>'
    )

    st.markdown(
        section_html,
        unsafe_allow_html=True,
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
        ) in enumerate(SEED, 1):

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
                    secrets.token_urlsafe(24),
                    1,
                    recurrence,
                    recurrence_day,
                    datetime.now().isoformat(),
                ),
            )

        c.commit()

    c.close()


# ============================================================
# GENERACIÓN DE CÓDIGOS
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
        f"SEV-{sector}-{area}-"
        f"{year}-{next_number:04d}"
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
        (due - start).days,
        1,
    )

    elapsed_days = (
        reference - start
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

def traffic_light(row):

    if row["status"] == "Cerrada":
        return "🟢 Cerrada"

    if (
        row["status"]
        == "Terminada - espera cierre"
    ):
        return "🔵 Espera cierre"

    theoretical_progress = theoretical(
        row
    )

    if theoretical_progress is None:
        return "⚪ Sin cronograma"

    real_progress = float(
        row["progress"] or 0
    )

    if (
        row["due_date"]
        and date.today()
        > pd.to_datetime(
            row["due_date"]
        ).date()
        and real_progress < 100
    ):
        return "🔴 Vencida"

    difference = (
        real_progress
        - theoretical_progress
    )

    if difference >= -5:
        return "🟢 En término"

    if difference >= -15:
        return "🟡 Atención"

    return "🔴 Atrasada"


def schedule_delta(row):

    expected = theoretical(row)

    if expected is None:
        return None

    return round(
        float(
            row["progress"] or 0
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
                secrets.token_urlsafe(24),
                task["recurrence"],
                next_due.day,
                task["id"],
                datetime.now().isoformat(),
            ),
        )

    c.commit()
    c.close()


# ============================================================
# GRÁFICO AVANCE REAL VS TEÓRICO
# ============================================================

def progress_chart(view):

    chart = view[
        view["Teórico %"].notna()
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
            "Las tareas históricas sin fechas "
            "no tienen avance teórico calculable."
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

    chart_long["Serie"] = (
        chart_long["Serie"]
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
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(
            color=BRAND_DARK
        ),
        xaxis=dict(
            showgrid=False,
        ),
        yaxis=dict(
            gridcolor="#E8ECE9",
            range=[0, 105],
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# GANTT
# ============================================================

def gantt_chart(view):

    gantt = view[
        view["start_date"].notna()
        & (view["start_date"] != "")
        & view["due_date"].notna()
        & (view["due_date"] != "")
    ].copy()

    if gantt.empty:

        st.info(
            "No hay tareas con fecha de inicio "
            "y finalización para mostrar."
        )

        return

    gantt["Inicio"] = pd.to_datetime(
        gantt["start_date"]
    )

    gantt["Final"] = pd.to_datetime(
        gantt["due_date"]
    )

    gantt["Etiqueta"] = (
        gantt["code"]
        + " · "
        + gantt["title"]
        .astype(str)
        .str.slice(0, 45)
    )

    gantt["Cumplimiento"] = (
        gantt["Semáforo"]
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
        gantt.sort_values(
            [
                "Final",
                "priority",
            ]
        ),
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
        },
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
        x=(
            pd.Timestamp(
                date.today()
            ).timestamp()
            * 1000
        ),
        line_width=1,
        line_dash="dash",
        line_color="#6B7770",
    )

    fig.update_layout(
        height=max(
            440,
            min(
                920,
                36 * len(gantt)
                + 170,
            ),
        ),
        margin=dict(
            l=10,
            r=10,
            t=10,
            b=10,
        ),
        legend_title_text="",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(
            color=BRAND_DARK
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
    )


# ============================================================
# INICIALIZAR
# ============================================================

init_db()
generate_recurring()


# ============================================================
# PORTAL DEL RESPONSABLE
# ============================================================

token = st.query_params.get("token")


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
        task["code"],
    )

    st.write(
        f"**Responsable:** "
        f"{task['name']}"
    )

    st.write(
        f"**Tarea:** "
        f"{task['title']}"
    )

    st.write(
        f"**Prioridad:** "
        f"{task['priority']} "
        f"· **Estado:** "
        f"{task['status']}"
    )

    m1, m2, m3 = st.columns(3)

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
        traffic_light(task),
    )

    dates1, dates2 = st.columns(2)

    with dates1:

        if task["start_date"]:

            st.write(
                "**Inicio:** "
                + pd.to_datetime(
                    task["start_date"]
                ).strftime(
                    "%d/%m/%Y"
                )
            )

    with dates2:

        if task["due_date"]:

            st.write(
                "**Finalización prevista:** "
                + pd.to_datetime(
                    task["due_date"]
                ).strftime(
                    "%d/%m/%Y"
                )
            )

    if task["maintenance_type"]:

        st.write(
            "**Tipo de mantenimiento:** "
            f"{task['maintenance_type']}"
        )

    if task["observation"]:

        st.info(
            task["observation"]
        )

    if (
        not task["accepted_at"]
        and task["status"]
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
                    task["id"],
                ),
            )

            c.commit()
            st.rerun()

    if task["status"] not in (
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
                    task["progress"]
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
                    task["id"],
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
                    finished_at =
                    COALESCE(
                        ?,
                        finished_at
                    )
                WHERE id = ?
                """,
                (
                    progress,
                    new_status,
                    finished,
                    task["id"],
                ),
            )

            c.commit()
            st.rerun()

    history = pd.read_sql_query(
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
            task["id"],
        ),
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

    st.markdown(
        f'<div class="sev-footer">SEV · Control de Tareas · {APP_VERSION}</div>',
        unsafe_allow_html=True,
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

    f1, f2, f3, f4 = st.columns(4)

    sector_filter = f1.selectbox(
        "Sector",
        [
            "Todos",
            *SECTORES.values(),
        ],
    )

    area_filter = f2.selectbox(
        "Área",
        [
            "Todas",
            *AREAS.values(),
        ],
    )

    operator_filter = f3.selectbox(
        "Operario",
        [
            "Todos",
            *people["name"].tolist(),
        ],
    )

    status_filter = f4.selectbox(
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

    view = tasks.copy()

    if sector_filter != "Todos":

        view = view[
            view["sector"]
            == sector_filter
        ]

    if area_filter != "Todas":

        view = view[
            view["area"]
            == area_filter
        ]

    if operator_filter != "Todos":

        view = view[
            view["assignee"]
            == operator_filter
        ]

    if status_filter != "Todos":

        view = view[
            view["status"]
            == status_filter
        ]

    view["Teórico %"] = (
        view.apply(
            theoretical,
            axis=1,
        )
    )

    view["Desvío pp"] = (
        view.apply(
            schedule_delta,
            axis=1,
        )
    )

    view["Semáforo"] = (
        view.apply(
            traffic_light,
            axis=1,
        )
    )

    open_count = int(
        (
            view["status"]
            != "Cerrada"
        ).sum()
    )

    execution_count = int(
        (
            view["status"]
            == "En ejecución"
        ).sum()
    )

    overdue_count = int(
        view["Semáforo"]
        .astype(str)
        .str.contains(
            "Vencida|Atrasada"
        )
        .sum()
    )

    waiting_close = int(
        (
            view["status"]
            == "Terminada - espera cierre"
        ).sum()
    )

    requested_month = int(
        (
            pd.to_datetime(
                view["requested"],
                errors="coerce",
            )
            .dt.to_period("M")
            == pd.Period(
                date.today(),
                freq="M",
            )
        ).sum()
    )

    k1, k2, k3, k4, k5 = (
        st.columns(5)
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


    section(
        "Avance real vs. teórico",
        "Comparación contra el avance esperado por fecha",
    )

    progress_chart(
        view
    )


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
        view["Semáforo"]
        .astype(str)
        .str.contains(
            "🔴|🟡"
        )
    ].copy()

    if attention.empty:

        st.success(
            "No hay tareas con alertas "
            "en el filtro seleccionado."
        )

    else:

        attention["Inicio"] = (
            pd.to_datetime(
                attention["start_date"],
                errors="coerce",
            )
            .dt.strftime(
                "%d/%m/%Y"
            )
            .fillna("—")
        )

        attention["Final"] = (
            pd.to_datetime(
                attention["due_date"],
                errors="coerce",
            )
            .dt.strftime(
                "%d/%m/%Y"
            )
            .fillna("—")
        )

        attention["Real %"] = (
            attention["progress"]
            .fillna(0)
            .round(0)
        )

        attention[
            "Teórico %"
        ] = (
            attention[
                "Teórico %"
            ]
            .round(0)
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

    monthly = view.copy()

    monthly["Mes"] = (
        pd.to_datetime(
            monthly["requested"],
            errors="coerce",
        )
        .dt.to_period("M")
        .astype(str)
    )

    monthly = (
        monthly
        .groupby("Mes")
        .size()
        .reset_index(
            name="Tareas"
        )
    )

    if not monthly.empty:

        fig_month = px.line(
            monthly,
            x="Mes",
            y="Tareas",
            markers=True,
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
        list(SECTORES),
    )

    area_name = st.selectbox(
        "Área / familia",
        list(AREAS),
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

        title = st.text_input(
            "Tarea"
        )

        description = (
            st.text_area(
                "Descripción"
            )
        )

        col1, col2 = (
            st.columns(2)
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
                        people["id"]
                        == person_id,
                        "name",
                    ].iloc[0]
                ),
            )
        )

        col1, col2 = (
            st.columns(2)
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
                "Ingresa el nombre "
                "de la tarea."
            )

        elif due < start:

            st.error(
                "La fecha final no puede "
                "ser anterior a la fecha de inicio."
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

            code = next_code(
                sector_code,
                area_code,
                c,
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

            st.success(
                "Tarea creada correctamente: "
                f"{code}"
            )

            st.write(
                "**Enlace del responsable:**"
            )

            st.code(
                "?token="
                + task_token,
                language=None,
            )


# ============================================================
# LISTA DE TAREAS
# ============================================================

elif page == "Tareas":

    section(
        "Tareas",
        "Listado general de seguimiento",
    )

    view = tasks.copy()

    view["Teórico %"] = (
        view.apply(
            theoretical,
            axis=1,
        )
    )

    view["Semáforo"] = (
        view.apply(
            traffic_light,
            axis=1,
        )
    )

    view["Inicio"] = (
        pd.to_datetime(
            view["start_date"],
            errors="coerce",
        )
        .dt.strftime(
            "%d/%m/%Y"
        )
        .fillna("—")
    )

    view["Final"] = (
        pd.to_datetime(
            view["due_date"],
            errors="coerce",
        )
        .dt.strftime(
            "%d/%m/%Y"
        )
        .fillna("—")
    )

    display = view[
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
            "maintenance_type": (
                "Tipo mantenimiento"
            ),
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
        height=620,
    )


# ============================================================
# CALENDARIO / GANTT
# ============================================================

elif page == "Calendario / Gantt":

    section(
        "Calendario y Gantt",
        "Inicio, finalización y estado de cumplimiento",
    )

    gantt = tasks.copy()

    gantt["Teórico %"] = (
        gantt.apply(
            theoretical,
            axis=1,
        )
    )

    gantt["Semáforo"] = (
        gantt.apply(
            traffic_light,
            axis=1,
        )
    )

    gantt_chart(
        gantt
    )

    scheduled = gantt[
        gantt["start_date"].notna()
        & (gantt["start_date"] != "")
        & gantt["due_date"].notna()
        & (gantt["due_date"] != "")
    ].copy()

    if not scheduled.empty:

        scheduled["Inicio"] = (
            pd.to_datetime(
                scheduled[
                    "start_date"
                ]
            )
            .dt.strftime(
                "%d/%m/%Y"
            )
        )

        scheduled["Final"] = (
            pd.to_datetime(
                scheduled[
                    "due_date"
                ]
            )
            .dt.strftime(
                "%d/%m/%Y"
            )
        )

        scheduled["Real %"] = (
            scheduled[
                "progress"
            ]
            .fillna(0)
            .round(0)
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

        recurrent["Final"] = (
            pd.to_datetime(
                recurrent[
                    "due_date"
                ],
                errors="coerce",
            )
            .dt.strftime(
                "%d/%m/%Y"
            )
            .fillna("—")
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
        tasks["sector"]
        == "MANT"
    ].copy()

    if maintenance.empty:

        st.info(
            "Todavía no existen "
            "tareas de mantenimiento."
        )

    else:

        m1, m2, m3, m4 = (
            st.columns(4)
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
            font=dict(
                color=BRAND_DARK
            ),
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

        maintenance["Inicio"] = (
            pd.to_datetime(
                maintenance[
                    "start_date"
                ],
                errors="coerce",
            )
            .dt.strftime(
                "%d/%m/%Y"
            )
            .fillna("—")
        )

        maintenance["Final"] = (
            pd.to_datetime(
                maintenance[
                    "due_date"
                ],
                errors="coerce",
            )
            .dt.strftime(
                "%d/%m/%Y"
            )
            .fillna("—")
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
                    "maintenance_type": (
                        "Tipo mantenimiento"
                    ),
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
        .fillna(0)
        .round(1)
    )

    summary = (
        summary.rename(
            columns={
                "assignee": "Operario",
                "Avance_promedio":
                "Avance promedio %",
            }
        )
    )

    st.dataframe(
        summary,
        hide_index=True,
        use_container_width=True,
    )


# ============================================================
# CIERRES PENDIENTES
# ============================================================

elif page == "Cierres pendientes":

    section(
        "Cierres pendientes",
        "El responsable termina; el administrador aprueba el cierre",
    )

    pending = tasks[
        tasks["status"]
        == "Terminada - espera cierre"
    ]

    if pending.empty:

        st.success(
            "No hay tareas esperando "
            "cierre administrativo."
        )

    else:

        for _, task in (
            pending.iterrows()
        ):

            with st.container(
                border=True
            ):

                st.write(
                    f"**{task.code} · "
                    f"{task.title}**"
                )

                st.write(
                    "Responsable: "
                    f"**{task.assignee}**"
                )

                st.write(
                    "Avance informado: "
                    f"**{float(task.progress or 0):.0f}%**"
                )

                if st.button(
                    "Aprobar cierre",
                    key=(
                        f"close_"
                        f"{task.id}"
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
                    st.rerun()


# ============================================================
# FINAL
# ============================================================

c.close()


st.markdown(
    f'<div class="sev-footer">SEV · Control de Tareas · {APP_VERSION}</div>',
    unsafe_allow_html=True,
)
