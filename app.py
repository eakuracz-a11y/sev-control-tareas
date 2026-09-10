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
    mail_configuration_report,
    send_test_email,
    send_admin_event,
    send_assignment_email,
    send_closed_email,
)
from reminders import run_reminders


# ============================================================
# CONFIGURACIÓN GENERAL
# ============================================================

APP_VERSION = "V2.29"

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
    ("Alejandro Kuracz", "kuraczg7@gmail.com"),
    ("Camille Maia", "camille.maia@sevion.com.br"),
    ("Eduardo Matos", "eduardo.matos@sevion.com.br"),
    ("Bruno Maia", "bruno.maia@sevion.com.br"),
    ("Ana Nolasco", "ana.nolasco@sevion.com.br"),
    ("Flavia Guedes", "flavia.guedes@sevion.com.br"),
    ("Marcela Roque", "marcela.roque@sevion.com.br"),
]

ADMIN_NAME = "Alejandro Kuracz"
ADMIN_EMAIL = "kuraczg7@gmail.com"
LEGACY_ADMIN_EMAIL = "alejandro.kuracz@sevion.com.br"


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
    "Solos": "SOL",
    "Servicios": "SER",
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
BRAND_BG = "#F4F7F5"
BRAND_BORDER = "#D6E1DA"

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
# CSS GENERAL · V2.23
# ============================================================

st.markdown(
    f"""
<style>
:root {{
    --sev-green: {BRAND_GREEN};
    --sev-dark: {BRAND_DARK};
    --sev-bg: {BRAND_BG};
    --sev-border: {BRAND_BORDER};
}}

.stApp {{
    background:
        radial-gradient(circle at 92% 3%, rgba(25,115,74,.055), transparent 22rem),
        {BRAND_BG};
}}

.block-container {{
    padding-top: 1.15rem;
    padding-bottom: 1.55rem;
    max-width: 1500px;
    overflow: visible;
}}

[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #F3F7F4 0%, #EDF3EF 100%);
    border-right: 1px solid {BRAND_BORDER};
}}

[data-testid="stSidebar"] * {{
    color: #203B2E !important;
}}

[data-testid="stSidebar"] [role="radiogroup"] label {{
    border-radius: 10px;
    padding-top: .26rem;
    padding-bottom: .26rem;
    transition: background .15s ease, transform .15s ease;
}}

[data-testid="stSidebar"] [role="radiogroup"] label:hover {{
    background: #E2ECE5;
    transform: translateX(2px);
}}

h1, h2, h3 {{
    color: {BRAND_DARK};
    letter-spacing: -0.025em;
}}

div[data-testid="stMetric"] {{
    background: rgba(255,255,255,.96);
    border: 1px solid {BRAND_BORDER};
    border-top: 3px solid rgba(25,115,74,.86);
    border-radius: 13px;
    padding: 10px 13px 9px 13px;
    min-height: 90px;
    box-shadow: 0 5px 16px rgba(24,61,45,.045);
}}

div[data-testid="stMetricLabel"] {{
    color: #65786E;
    font-weight: 700;
    font-size: .76rem;
}}

div[data-testid="stMetricValue"] {{
    color: {BRAND_DARK};
    font-size: 1.58rem;
    line-height: 1.08;
    letter-spacing: -.02em;
}}

div[data-testid="stMetricDelta"] {{
    font-size: .70rem;
}}

[data-testid="stDataFrame"] {{
    border: 1px solid {BRAND_BORDER};
    border-radius: 11px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(24,61,45,.025);
}}

button[kind="primary"] {{
    background-color: {BRAND_GREEN} !important;
    border-color: {BRAND_GREEN} !important;
    color: white !important;
}}

.stButton > button {{
    border-radius: 10px;
}}

[data-testid="stExpander"] {{
    border: 1px solid {BRAND_BORDER};
    border-radius: 11px;
    background: rgba(255,255,255,.76);
}}

.sev-section {{
    margin: .68rem 0 .48rem 0;
    padding: .54rem .82rem .50rem .82rem;
    border-left: 4px solid {BRAND_GREEN};
    background: linear-gradient(90deg, #EAF4ED 0%, rgba(244,247,245,.20) 78%);
    border-radius: 0 10px 10px 0;
}}

.sev-section-title {{
    color: {BRAND_DARK};
    font-size: 1.13rem;
    line-height: 1.14;
    font-weight: 790;
    margin: 0;
}}

.sev-section-note {{
    color: #71847A;
    font-size: .72rem;
    margin-top: .17rem;
}}

.sev-panel-title {{
    display:flex;
    align-items:center;
    gap:.44rem;
    color:{BRAND_DARK};
    font-weight:770;
    font-size:.91rem;
    margin:.08rem 0 .38rem 0;
}}

.sev-dot {{
    width:8px;
    height:8px;
    border-radius:999px;
    background:{BRAND_GREEN};
    box-shadow: 0 0 0 3px rgba(25,115,74,.10);
    flex:0 0 8px;
}}

.sev-mini-card {{
    background:#FFFFFF;
    border:1px solid {BRAND_BORDER};
    border-radius:11px;
    padding:.57rem .66rem;
    margin-bottom:.40rem;
    box-shadow:0 2px 7px rgba(24,61,45,.035);
}}

.sev-mini-kicker {{
    color:#75877E;
    font-size:.66rem;
    font-weight:750;
    text-transform:uppercase;
    letter-spacing:.045em;
}}

.sev-mini-main {{
    color:{BRAND_DARK};
    font-size:.80rem;
    font-weight:720;
    line-height:1.21;
    margin-top:.09rem;
}}

.sev-mini-sub {{
    color:#75877E;
    font-size:.69rem;
    margin-top:.13rem;
}}

.sev-kpi-strip {{
    color:#708179;
    font-size:.70rem;
    margin-top:-.15rem;
    margin-bottom:.26rem;
}}

.sev-exec-grid {{
    display:grid;
    grid-template-columns:repeat(3, minmax(0,1fr));
    gap:.62rem;
    margin:.20rem 0 .38rem 0;
}}

.sev-exec-card {{
    background:linear-gradient(145deg,#FFFFFF 0%,#F7FAF8 100%);
    border:1px solid {BRAND_BORDER};
    border-radius:12px;
    padding:.70rem .78rem;
    min-height:82px;
    box-shadow:0 4px 14px rgba(24,61,45,.035);
}}

.sev-exec-kicker {{
    color:#75877E;
    font-size:.64rem;
    font-weight:800;
    text-transform:uppercase;
    letter-spacing:.055em;
}}

.sev-exec-value {{
    color:{BRAND_DARK};
    font-size:1.12rem;
    font-weight:800;
    line-height:1.05;
    margin-top:.12rem;
}}

.sev-exec-note {{
    color:#74847D;
    font-size:.68rem;
    margin-top:.18rem;
}}

.sev-header-wrap {{
    background:rgba(255,255,255,.73);
    border:1px solid {BRAND_BORDER};
    border-radius:14px;
    padding:.58rem .72rem;
    box-shadow:0 5px 18px rgba(24,61,45,.035);
    margin-bottom:.66rem;
}}

div[data-testid="stSelectbox"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stDateInput"] label {{
    font-size:.73rem;
    color:#5D7166;
    font-weight:680;
}}

div[data-baseweb="select"] > div,
input {{
    min-height: 36px !important;
}}

hr {{
    margin:.56rem 0 !important;
}}

.sev-action-summary {{
    display:grid;
    grid-template-columns:repeat(4,minmax(0,1fr));
    gap:.48rem;
    margin:.18rem 0 .52rem 0;
}}
.sev-action-pill {{
    background:#FFFFFF;
    border:1px solid {BRAND_BORDER};
    border-radius:10px;
    padding:.48rem .58rem;
    min-height:58px;
}}
.sev-action-pill .n {{
    color:{BRAND_DARK};
    font-size:1.08rem;
    font-weight:820;
    line-height:1;
}}
.sev-action-pill .t {{
    color:#72837A;
    font-size:.67rem;
    font-weight:720;
    margin-top:.18rem;
}}
.sev-ranking-row {{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:.55rem;
    padding:.38rem 0;
    border-bottom:1px solid #E7ECE8;
}}
.sev-ranking-name {{
    color:{BRAND_DARK};
    font-size:.76rem;
    font-weight:730;
}}
.sev-ranking-meta {{
    color:#74847D;
    font-size:.66rem;
}}
.sev-ranking-score {{
    min-width:48px;
    text-align:right;
    color:{BRAND_GREEN};
    font-size:.92rem;
    font-weight:820;
}}
.sev-progress-row {{ margin:.34rem 0 .50rem 0; }}
.sev-progress-head {{
    display:flex;
    justify-content:space-between;
    gap:.6rem;
    color:{BRAND_DARK};
    font-size:.72rem;
    font-weight:720;
    margin-bottom:.16rem;
}}
.sev-progress-track {{
    height:7px;
    background:#E7ECE8;
    border-radius:999px;
    overflow:hidden;
}}
.sev-progress-fill {{
    height:100%;
    background:{BRAND_GREEN};
    border-radius:999px;
}}

.sev-year-grid {{
    display:grid;
    grid-template-columns:repeat(4,minmax(0,1fr));
    gap:.52rem;
    margin:.20rem 0 .62rem 0;
}}
.sev-month-card {{
    background:#FFFFFF;
    border:1px solid {BRAND_BORDER};
    border-radius:11px;
    padding:.58rem .64rem;
    min-height:92px;
}}
.sev-month-name {{
    color:#6D8076;
    font-size:.64rem;
    font-weight:820;
    letter-spacing:.055em;
    text-transform:uppercase;
}}
.sev-month-status {{
    color:{BRAND_DARK};
    font-size:.80rem;
    font-weight:790;
    line-height:1.18;
    margin-top:.20rem;
}}
.sev-month-date {{
    color:#75877E;
    font-size:.68rem;
    margin-top:.16rem;
}}
.sev-month-on {{
    border-top:3px solid {COLOR_OK};
}}
.sev-month-late {{
    border-top:3px solid {COLOR_WARNING};
}}
.sev-month-bad {{
    border-top:3px solid {COLOR_DANGER};
}}
.sev-month-open {{
    border-top:3px solid {COLOR_WAIT};
}}
.sev-month-neutral {{
    border-top:3px solid {COLOR_NEUTRAL};
}}
.sev-annual-note {{
    color:#6F8077;
    font-size:.70rem;
    margin:.10rem 0 .36rem 0;
}}

.sev-action-list {{
    display:flex;
    flex-direction:column;
    gap:.44rem;
    margin-top:.18rem;
}}

.sev-action-row {{
    display:grid;
    grid-template-columns:112px minmax(0,1fr) 138px 92px 88px;
    gap:.58rem;
    align-items:center;
    background:#FFFFFF;
    border:1px solid {BRAND_BORDER};
    border-radius:11px;
    padding:.56rem .64rem;
}}

.sev-action-status {{
    display:inline-flex;
    align-items:center;
    justify-content:center;
    min-height:28px;
    padding:.20rem .48rem;
    border-radius:999px;
    font-size:.66rem;
    font-weight:800;
    white-space:nowrap;
}}

.sev-badge-late {{
    color:#8F2F29;
    background:#FCEDEA;
}}
.sev-badge-pending {{
    color:#9A5A10;
    background:#FFF4E2;
}}
.sev-badge-attention {{
    color:#8C6500;
    background:#FFF8D8;
}}
.sev-badge-close {{
    color:#345F8B;
    background:#EDF4FB;
}}

.sev-action-title {{
    min-width:0;
    color:{BRAND_DARK};
    font-size:.77rem;
    font-weight:740;
    line-height:1.20;
}}
.sev-action-owner {{
    color:#5E7167;
    font-size:.70rem;
    font-weight:680;
}}
.sev-action-meta {{
    color:#74857D;
    font-size:.68rem;
}}
.sev-action-progress {{
    color:{BRAND_DARK};
    font-size:.72rem;
    font-weight:760;
    text-align:right;
}}

.sev-action-head {{
    display:grid;
    grid-template-columns:112px minmax(0,1fr) 138px 92px 88px;
    gap:.58rem;
    padding:0 .64rem .20rem .64rem;
    color:#7B8A83;
    font-size:.62rem;
    font-weight:760;
    text-transform:uppercase;
    letter-spacing:.035em;
}}

.sev-progress-card {{
    background:#FFFFFF;
    border:1px solid {BRAND_BORDER};
    border-radius:11px;
    padding:.58rem .66rem;
    margin-bottom:.46rem;
}}
.sev-progress-top {{
    display:flex;
    justify-content:space-between;
    align-items:flex-start;
    gap:.65rem;
}}
.sev-progress-title2 {{
    min-width:0;
    color:{BRAND_DARK};
    font-size:.78rem;
    font-weight:760;
    line-height:1.20;
}}
.sev-progress-value2 {{
    flex:0 0 auto;
    color:{BRAND_GREEN};
    font-size:.88rem;
    font-weight:830;
}}
.sev-progress-sub {{
    display:flex;
    flex-wrap:wrap;
    gap:.34rem .60rem;
    margin:.22rem 0 .34rem 0;
    color:#71827A;
    font-size:.67rem;
}}
.sev-progress-sub strong {{
    color:#4D6257;
    font-weight:730;
}}
.sev-progress-track2 {{
    height:8px;
    background:#E8EEE9;
    border-radius:999px;
    overflow:hidden;
}}
.sev-progress-fill2 {{
    height:100%;
    background:{BRAND_GREEN};
    border-radius:999px;
}}

.sev-owner-card {{
    background:#FFFFFF;
    border:1px solid {BRAND_BORDER};
    border-radius:11px;
    padding:.58rem .64rem;
    margin-bottom:.42rem;
}}
.sev-owner-top {{
    display:flex;
    justify-content:space-between;
    gap:.5rem;
    align-items:center;
}}
.sev-owner-name {{
    color:{BRAND_DARK};
    font-size:.76rem;
    font-weight:760;
}}
.sev-owner-score {{
    color:{BRAND_GREEN};
    font-size:.92rem;
    font-weight:830;
}}
.sev-owner-meta {{
    color:#75867D;
    font-size:.66rem;
    margin-top:.16rem;
}}
.sev-owner-bar {{
    height:6px;
    background:#E8EEE9;
    border-radius:999px;
    overflow:hidden;
    margin-top:.34rem;
}}
.sev-owner-fill {{
    height:100%;
    background:{BRAND_GREEN};
    border-radius:999px;
}}

@media (max-width: 980px) {{
    .sev-action-head {{ display:none !important; }}
    .sev-action-row {{
        grid-template-columns:1fr 1fr !important;
        gap:.35rem .55rem !important;
    }}
    .sev-action-title {{ grid-column:1 / -1; }}
    .sev-action-progress {{ text-align:left !important; }}
}}

.sev-cal-note {{
    background:linear-gradient(135deg,#F2F8F5 0%,#EAF5EF 100%);
    border:1px solid #CFE2D7;
    border-left:4px solid {BRAND_GREEN};
    border-radius:12px;
    padding:.68rem .78rem;
    min-height:68px;
    color:{BRAND_DARK};
    font-size:.73rem;
    line-height:1.35;
}}
.sev-cal-note strong {{ color:{BRAND_GREEN}; }}
.sev-cal-legend {{
    background:#FFFFFF;
    border:1px solid {BRAND_BORDER};
    border-radius:12px;
    padding:.68rem .72rem;
    margin-bottom:.55rem;
}}
.sev-cal-side-title {{
    color:{BRAND_DARK};
    font-size:.78rem;
    font-weight:820;
    margin-bottom:.38rem;
}}
.sev-cal-legend-row {{
    display:flex;
    align-items:center;
    gap:.42rem;
    padding:.16rem 0;
    color:#64766D;
    font-size:.68rem;
}}
.sev-cal-dot {{
    width:9px;height:9px;border-radius:50%;flex:0 0 9px;
}}
.sev-cal-summary {{
    display:grid;
    grid-template-columns:repeat(2,minmax(0,1fr));
    gap:.38rem;
}}
.sev-cal-stat {{
    background:#FFFFFF;
    border:1px solid {BRAND_BORDER};
    border-radius:10px;
    padding:.48rem .52rem;
}}
.sev-cal-stat .n {{
    color:{BRAND_DARK};font-size:1rem;font-weight:840;line-height:1;
}}
.sev-cal-stat .t {{
    color:#74857D;font-size:.62rem;font-weight:690;margin-top:.14rem;
}}
.sev-cal-day {{
    background:#FFFFFF;
    border:1px solid {BRAND_BORDER};
    border-radius:11px;
    padding:.48rem .52rem;
    min-height:112px;
    margin-bottom:.42rem;
}}
.sev-cal-today {{
    background:#F1FAF5;
    border:1px solid #8BC9A6;
    box-shadow:inset 0 0 0 1px #D7EFE1;
}}
.sev-cal-daynum {{
    display:flex;justify-content:space-between;align-items:center;
    color:{BRAND_DARK};font-size:.76rem;font-weight:840;margin-bottom:.30rem;
}}
.sev-cal-today-tag {{
    color:{BRAND_GREEN};background:#E4F5EB;border-radius:999px;
    padding:.10rem .34rem;font-size:.57rem;font-weight:800;
}}
.sev-cal-event {{
    border-radius:7px;padding:.24rem .30rem;margin:.20rem 0;
    font-size:.61rem;line-height:1.20;overflow:hidden;
}}
.sev-cal-event-title {{
    font-weight:760;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;
}}
.sev-cal-event-meta {{ margin-top:.10rem;opacity:.84;font-size:.56rem; }}
.sev-cal-green {{ background:#E8F6ED;color:#176B43;border-left:3px solid #1B8A55; }}
.sev-cal-blue {{ background:#EAF3FB;color:#28618C;border-left:3px solid #438BC3; }}
.sev-cal-yellow {{ background:#FFF6DE;color:#8A650A;border-left:3px solid #E3A719; }}
.sev-cal-red {{ background:#FCEBE8;color:#9A3D35;border-left:3px solid #D45145; }}
.sev-cal-gray {{ background:#F2F5F3;color:#6C7B73;border-left:3px solid #A9B5AF; }}
.sev-cal-empty {{ color:#A0ADA6;font-size:.63rem;margin-top:.55rem; }}
.sev-cal-weekhead {{
    text-align:center;color:#53685D;font-size:.67rem;font-weight:800;
    padding:.16rem 0 .28rem 0;
}}

@media (max-width: 768px) {{
    .sev-action-summary {{ grid-template-columns:repeat(2,minmax(0,1fr)) !important; }}
    .sev-year-grid {{ grid-template-columns:repeat(2,minmax(0,1fr)) !important; }}
}}

@media (max-width: 768px) {{
    .block-container {{
        padding-top: .70rem !important;
        padding-left: .58rem !important;
        padding-right: .58rem !important;
        padding-bottom: 1.5rem !important;
        max-width: 100% !important;
    }}
    [data-testid="stSidebar"] {{
        min-width: 78vw !important;
        max-width: 88vw !important;
    }}
    div[data-testid="stHorizontalBlock"] {{
        flex-wrap: wrap !important;
        gap: .42rem !important;
    }}
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
        min-width: 46% !important;
        flex: 1 1 46% !important;
    }}
    h1 {{ font-size: 1.42rem !important; }}
    h2 {{ font-size: 1.18rem !important; }}
    h3 {{ font-size: 1.00rem !important; }}
    .sev-section {{
        margin:.50rem 0 .38rem 0 !important;
        padding:.44rem .58rem !important;
    }}
    .sev-section-title {{ font-size:.99rem !important; }}
    .sev-section-note {{ font-size:.67rem !important; }}
    div[data-testid="stMetric"] {{
        padding: 8px 9px !important;
        border-radius: 10px !important;
        min-height:74px !important;
    }}
    div[data-testid="stMetricValue"] {{ font-size: 1.20rem !important; }}
    .sev-exec-grid {{
        grid-template-columns:1fr !important;
        gap:.42rem !important;
    }}
    .sev-exec-card {{
        min-height:auto !important;
        padding:.58rem .65rem !important;
    }}
    .stButton > button, [data-testid="stFormSubmitButton"] > button {{
        min-height: 44px !important;
        width: 100% !important;
        font-size: .88rem !important;
    }}
    [data-testid="stDataFrame"] {{ font-size: .74rem !important; }}
}}

@media (max-width: 480px) {{
    div[data-testid="stHorizontalBlock"] > div[data-testid="column"] {{
        min-width: 100% !important;
        flex: 1 1 100% !important;
    }}
}}
</style>
""",
    unsafe_allow_html=True,
)


# ============================================================
# ENCABEZADO NATIVO
# ============================================================

def render_header():
    st.markdown('<div class="sev-header-wrap">', unsafe_allow_html=True)

    logo_col, title_col, version_col = st.columns(
        [1.0, 5.8, 1.0],
        vertical_alignment="center",
    )

    with logo_col:
        if LOGO.exists():
            st.image(str(LOGO), width=126)
        else:
            st.markdown("### Sevion")

    with title_col:
        st.markdown(
            """
            <div style="padding-top:0.01rem;">
                <div style="font-size:0.64rem;letter-spacing:0.15em;font-weight:800;color:#6F8378;margin-bottom:0.04rem;">
                    GESTIÓN OPERACIONAL
                </div>
                <div style="font-size:1.72rem;line-height:1.06;font-weight:810;color:#183D2D;margin:0;">
                    Control de Tareas
                </div>
                <div style="font-size:0.72rem;color:#7A8C83;margin-top:0.16rem;">
                    Prioridades · ejecución · cumplimiento · alertas
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with version_col:
        st.markdown(
            f"""
            <div style="text-align:right;padding-top:0.08rem;">
                <div style="font-size:.59rem;color:#87968F;font-weight:750;margin-bottom:.16rem;">VERSIÓN</div>
                <span style="display:inline-block;border:1px solid #CFE0D5;background:#EAF4ED;border-radius:999px;
                padding:0.30rem 0.66rem;font-size:0.74rem;font-weight:800;color:#19734A;">{APP_VERSION}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("</div>", unsafe_allow_html=True)



# ============================================================
# SECCIONES NATIVAS
# ============================================================

def section(title, note=""):
    note_html = f'<div class="sev-section-note">{note}</div>' if note else ""
    st.markdown(
        f"""
        <div class="sev-section">
            <div class="sev-section-title">{title}</div>
            {note_html}
        </div>
        """,
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
            active INTEGER DEFAULT 1,
            role TEXT DEFAULT 'Responsable'

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
            created_at TEXT,
            archived INTEGER DEFAULT 0,
            operational_cycle TEXT,
            restart_parent_id INTEGER

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

    # Migración V2.7: permite quitar tareas de las listas operativas
    # sin borrar su historial, correos ni eventos de auditoría.
    task_columns = {
        row["name"]
        for row in c.execute("PRAGMA table_info(tasks)").fetchall()
    }
    if "archived" not in task_columns:
        c.execute(
            "ALTER TABLE tasks ADD COLUMN archived INTEGER DEFAULT 0"
        )
        c.commit()

    # Migración V2.13: nueva etapa operativa sin borrar historial.
    task_columns = {
        row["name"]
        for row in c.execute("PRAGMA table_info(tasks)").fetchall()
    }
    if "operational_cycle" not in task_columns:
        c.execute("ALTER TABLE tasks ADD COLUMN operational_cycle TEXT")
    if "restart_parent_id" not in task_columns:
        c.execute("ALTER TABLE tasks ADD COLUMN restart_parent_id INTEGER")
    c.execute(
        "UPDATE tasks SET operational_cycle = COALESCE(NULLIF(operational_cycle, ''), 'Histórico')"
    )
    c.commit()

    people_columns = {
        row["name"]
        for row in c.execute("PRAGMA table_info(people)").fetchall()
    }
    if "role" not in people_columns:
        c.execute(
            "ALTER TABLE people ADD COLUMN role TEXT DEFAULT 'Responsable'"
        )
        c.commit()

    # Migración V2.12: conservar el mismo usuario administrador y sus tareas
    # al cambiar el correo desde Sevion a la cuenta Gmail personal.
    old_admin = c.execute(
        "SELECT id FROM people WHERE email = ?",
        (LEGACY_ADMIN_EMAIL,),
    ).fetchone()
    new_admin = c.execute(
        "SELECT id FROM people WHERE email = ?",
        (ADMIN_EMAIL,),
    ).fetchone()

    if old_admin and not new_admin:
        c.execute(
            "UPDATE people SET email = ?, name = ?, role = 'Administrador', active = 1 WHERE id = ?",
            (ADMIN_EMAIL, ADMIN_NAME, old_admin["id"]),
        )
    elif old_admin and new_admin and old_admin["id"] != new_admin["id"]:
        # Si ambas cuentas existieran por una publicación intermedia, unificar
        # las tareas en el usuario Gmail y retirar el registro duplicado.
        c.execute(
            "UPDATE tasks SET assignee_id = ? WHERE assignee_id = ?",
            (new_admin["id"], old_admin["id"]),
        )
        c.execute(
            "DELETE FROM people WHERE id = ?",
            (old_admin["id"],),
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

    c.execute(
        """
        UPDATE people
        SET name = ?, role = 'Administrador', active = 1
        WHERE email = ?
        """,
        (ADMIN_NAME, ADMIN_EMAIL),
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

def _safe_date(value):
    """Convierte fechas provenientes de SQLite/Pandas sin dejar pasar NaN/NaT."""

    if value is None:
        return None

    try:
        if pd.isna(value):
            return None
    except Exception:
        pass

    if isinstance(value, date) and not isinstance(value, datetime):
        return value

    parsed = pd.to_datetime(
        value,
        errors="coerce",
    )

    if pd.isna(parsed):
        return None

    return parsed.date()


def theoretical(
    row,
    reference=None,
):

    reference = (
        _safe_date(reference)
        if reference is not None
        else date.today()
    )

    if reference is None:
        reference = date.today()

    if row["status"] == "Cerrada":

        return 100.0

    start = _safe_date(
        row["start_date"]
    )

    due = _safe_date(
        row["due_date"]
    )

    if start is None or due is None:

        return None

    # Un registro histórico mal cargado no debe romper el tablero.
    if due < start:

        return None

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

    due = _safe_date(
        row["due_date"]
    )

    if (
        due is not None
        and date.today() > due
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
    """
    Genera las próximas instancias de tareas recurrentes.

    V2.18:
    - Mantiene una tarea maestra.
    - Genera todas las ocurrencias necesarias hasta 45 días hacia adelante.
    - No crea retroactivamente meses antiguos que nunca fueron registrados.
    - Evita duplicados por recurrence_parent_id + due_date.
    """

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

    today = date.today()
    horizon = today + timedelta(days=45)

    for task in masters:

        try:
            base_due = pd.to_datetime(task["due_date"]).date()
        except Exception:
            continue

        if not base_due:
            continue

        # Conserva la duración original de la tarea.
        duration = 0
        if task["start_date"]:
            try:
                base_start = pd.to_datetime(task["start_date"]).date()
                duration = max((base_due - base_start).days, 0)
            except Exception:
                duration = 0

        candidate = next_recurrence(base_due, task["recurrence"])
        safety = 0

        # Avanzar hasta la primera recurrencia vigente sin fabricar histórico.
        while candidate and candidate < today:
            candidate = next_recurrence(candidate, task["recurrence"])
            safety += 1
            if safety > 240:
                break

        # Crear las instancias futuras necesarias dentro del horizonte.
        while candidate and candidate <= horizon and safety <= 260:

            existing = c.execute(
                """
                SELECT 1
                FROM tasks
                WHERE recurrence_parent_id = ?
                AND due_date = ?
                """,
                (
                    task["id"],
                    candidate.isoformat(),
                ),
            ).fetchone()

            if not existing:
                next_start = candidate - timedelta(days=duration)

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
                        today.isoformat(),
                        next_start.isoformat(),
                        candidate.isoformat(),
                        "Asignada",
                        0,
                        task["observation"],
                        secrets.token_urlsafe(24),
                        task["recurrence"],
                        candidate.day,
                        task["id"],
                        datetime.now().isoformat(),
                    ),
                )

            candidate = next_recurrence(candidate, task["recurrence"])
            safety += 1

    c.commit()
    c.close()


def recurring_family_rows(connection, master_id):
    """Devuelve maestra + instancias de una recurrencia, incluso archivadas."""
    return pd.read_sql_query(
        """
        SELECT
            t.*,
            p.name AS assignee,
            p.email
        FROM tasks t
        JOIN people p ON p.id = t.assignee_id
        WHERE t.id = ?
           OR t.recurrence_parent_id = ?
        ORDER BY t.due_date, t.id
        """,
        connection,
        params=(int(master_id), int(master_id)),
    )


def recurring_monthly_year_control(connection, master_row, year):
    """
    Control anual mensual V2.21.

    Soporta también tareas recurrentes históricas que tienen recurrence_day
    pero no due_date. En ese caso usa requested/created_at como fecha de inicio
    administrativo y construye la fecha prevista de cada mes con recurrence_day.
    """
    master_id = int(master_row["id"])
    family = recurring_family_rows(connection, master_id)

    base_due = _safe_date(master_row.get("due_date"))

    recurrence_day = master_row.get("recurrence_day")
    try:
        recurrence_day = int(recurrence_day) if recurrence_day else None
    except Exception:
        recurrence_day = None

    # Fallback para registros existentes creados antes de que due_date fuera obligatorio.
    start_reference = base_due
    if start_reference is None:
        for field in ["requested", "created_at", "start_date"]:
            candidate = _safe_date(master_row.get(field))
            if candidate is not None:
                start_reference = candidate
                break

    if recurrence_day is None:
        if base_due is not None:
            recurrence_day = base_due.day
        elif start_reference is not None:
            recurrence_day = start_reference.day
        else:
            return pd.DataFrame()

    # Si no hay ninguna fecha histórica utilizable, al menos permite visualizar
    # el año seleccionado usando el día recurrente configurado.
    if start_reference is None:
        start_reference = date(int(year), 1, min(recurrence_day, 28))

    rows = []
    today = date.today()

    for month in range(1, 13):
        last_day = calendar.monthrange(int(year), month)[1]
        planned_day = min(recurrence_day, last_day)
        planned = date(int(year), month, planned_day)

        # No exigir cumplimiento antes del mes en que se creó/configuró la rutina.
        if planned < date(start_reference.year, start_reference.month, 1):
            rows.append({
                "Mes nº": month,
                "Prevista": planned,
                "Finalizada": None,
                "Estado anual": "— No aplica",
                "Clase": "neutral",
                "Desvío días": None,
                "Código": "",
                "Estado tarefa": "",
                "Avance %": None,
            })
            continue

        month_instances = family.copy()
        month_instances["_due"] = pd.to_datetime(
            month_instances["due_date"], errors="coerce"
        )

        # La maestra antigua puede no tener due_date. Para el mes de inicio,
        # se la considera instancia válida si coincide el año/mes administrativo.
        valid_due = month_instances[
            month_instances["_due"].notna()
            & (month_instances["_due"].dt.year == int(year))
            & (month_instances["_due"].dt.month == month)
        ].copy()

        if valid_due.empty and base_due is None:
            master_candidates = month_instances[
                month_instances["id"].astype(int) == master_id
            ].copy()
            if (
                not master_candidates.empty
                and start_reference.year == int(year)
                and start_reference.month == month
            ):
                valid_due = master_candidates.copy()
                valid_due["_due"] = pd.Timestamp(planned)

        month_instances = valid_due

        if not month_instances.empty:
            month_instances["_diff"] = (
                month_instances["_due"].dt.date.apply(
                    lambda d: abs((d - planned).days)
                )
            )
            inst = month_instances.sort_values(["_diff", "id"]).iloc[0]

            finished = pd.to_datetime(inst.get("finished_at"), errors="coerce")
            closed = pd.to_datetime(inst.get("closed_at"), errors="coerce")
            actual_ts = finished if not pd.isna(finished) else closed
            actual = None if pd.isna(actual_ts) else actual_ts.date()

            status = str(inst.get("status") or "")
            progress = float(inst.get("progress") or 0)

            if actual is not None:
                delta = (actual - planned).days
                if delta <= 0:
                    annual_status = "🟢 Cumplida"
                    css_class = "on"
                else:
                    annual_status = "🟡 Cumplida fuera de plazo"
                    css_class = "late"
            elif planned < today:
                delta = None
                annual_status = "🔴 Vencida"
                css_class = "bad"
            elif planned == today:
                delta = None
                annual_status = "🔵 Vence hoy"
                css_class = "open"
            else:
                delta = None
                annual_status = "🔵 Programada"
                css_class = "open"

            rows.append({
                "Mes nº": month,
                "Prevista": planned,
                "Finalizada": actual,
                "Estado anual": annual_status,
                "Clase": css_class,
                "Desvío días": delta,
                "Código": str(inst.get("code") or ""),
                "Estado tarefa": status,
                "Avance %": round(progress, 0),
            })

        else:
            if planned < today:
                annual_status = "⚪ Sin registro"
                css_class = "neutral"
            elif planned == today:
                annual_status = "🔵 Vence hoy"
                css_class = "open"
            else:
                annual_status = "○ Programada"
                css_class = "neutral"

            rows.append({
                "Mes nº": month,
                "Prevista": planned,
                "Finalizada": None,
                "Estado anual": annual_status,
                "Clase": css_class,
                "Desvío días": None,
                "Código": "",
                "Estado tarefa": "",
                "Avance %": None,
            })

    return pd.DataFrame(rows)


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
    """Gantt compacto y legible en PC y celular."""

    gantt = view[
        view["start_date"].notna()
        & (view["start_date"] != "")
        & view["due_date"].notna()
        & (view["due_date"] != "")
    ].copy()

    if gantt.empty:
        st.info("No hay tareas con fecha de inicio y finalización para mostrar.")
        return

    gantt["Inicio"] = pd.to_datetime(gantt["start_date"], errors="coerce")
    gantt["Final"] = pd.to_datetime(gantt["due_date"], errors="coerce")
    gantt = gantt.dropna(subset=["Inicio", "Final"]).copy()

    if gantt.empty:
        st.info("No hay fechas válidas para construir el Gantt.")
        return

    # Etiqueta corta: evita que el nombre de la tarea consuma la mitad del gráfico.
    def _short_code(code):
        raw = str(code or "")
        parts = raw.split("-")
        return parts[-1] if parts else raw

    gantt["Código corto"] = gantt["code"].apply(_short_code)
    gantt["Tarea corta"] = gantt["title"].astype(str).apply(
        lambda value: value if len(value) <= 29 else value[:27].rstrip() + "…"
    )
    gantt["Etiqueta"] = gantt["Código corto"] + " · " + gantt["Tarea corta"]
    gantt["Cumplimiento"] = gantt["Semáforo"]

    acceptance = gantt.apply(acceptance_metrics, axis=1)
    gantt["Asignada"] = acceptance.apply(lambda x: x["assigned_at"])
    gantt["Aceptada"] = acceptance.apply(lambda x: x["accepted_at"])
    gantt["Fin aceptación"] = acceptance.apply(lambda x: x["acceptance_end"])
    gantt["Demora aceptación (h)"] = acceptance.apply(lambda x: x["acceptance_hours"])
    gantt["Control aceptación"] = acceptance.apply(lambda x: x["acceptance_label"])
    gantt["Aceptación confirmada"] = acceptance.apply(lambda x: x["accepted"])

    colors = {
        "🟢 Cerrada": BRAND_GREEN,
        "🟢 En término": COLOR_OK,
        "🟡 Atención": COLOR_WARNING,
        "🔴 Atrasada": COLOR_DANGER,
        "🔴 Vencida": "#9F342C",
        "🔵 Espera cierre": COLOR_WAIT,
        "⚪ Sin cronograma": COLOR_NEUTRAL,
    }

    # Orden: primero las que terminan antes. En pantalla se muestran de arriba hacia abajo.
    gantt = gantt.sort_values(["Final", "Inicio", "priority"], ascending=[True, True, True])

    fig = px.timeline(
        gantt,
        x_start="Inicio",
        x_end="Final",
        y="Etiqueta",
        color="Cumplimiento",
        color_discrete_map=colors,
        custom_data=[
            "code",
            "title",
            "assignee",
            "priority",
            "status",
            "progress",
            "Teórico %",
            "Inicio",
            "Final",
            "Control aceptación",
        ],
    )

    # Barra más clara y ligeramente redondeada visualmente por grosor/espaciado.
    fig.update_traces(
        marker_line_width=0,
        opacity=0.90,
        hovertemplate=(
            "<b>%{customdata[0]}</b><br>"
            "%{customdata[1]}<br><br>"
            "Responsable: <b>%{customdata[2]}</b><br>"
            "Prioridad: %{customdata[3]}<br>"
            "Estado: %{customdata[4]}<br>"
            "Avance real: %{customdata[5]:.0f}%<br>"
            "Avance teórico: %{customdata[6]:.0f}%<br>"
            "Inicio: %{customdata[7]|%d/%m/%Y}<br>"
            "Final: %{customdata[8]|%d/%m/%Y}<br>"
            "%{customdata[9]}"
            "<extra></extra>"
        ),
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
            legend_name = "Aceptación"
            showlegend = not accepted_legend_added
            accepted_legend_added = True
        else:
            line_color = COLOR_WARNING
            marker_color = COLOR_DANGER
            legend_name = "Pendiente aceptación"
            showlegend = not pending_legend_added
            pending_legend_added = True

        fig.add_trace(
            go.Scatter(
                x=[assigned, end_acceptance],
                y=[row["Etiqueta"], row["Etiqueta"]],
                mode="lines+markers",
                name=legend_name,
                showlegend=showlegend,
                line=dict(color=line_color, width=5),
                marker=dict(
                    color=[line_color, marker_color],
                    size=[6, 9],
                    symbol=["circle", "diamond"],
                ),
                opacity=0.78,
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
        automargin=True,
        tickfont=dict(size=11),
        showgrid=False,
    )
    fig.update_xaxes(
        title=None,
        gridcolor="#E8ECE9",
        tickformat="%d/%m",
        dtick="D7",
        showline=True,
        linecolor="#DDE5DF",
        rangeslider=dict(visible=False),
    )

    today_ms = pd.Timestamp(date.today()).timestamp() * 1000
    fig.add_vline(
        x=today_ms,
        line_width=1.5,
        line_dash="dash",
        line_color="#6B7770",
    )
    fig.add_annotation(
        x=today_ms,
        y=1.02,
        xref="x",
        yref="paper",
        text="Hoy",
        showarrow=False,
        font=dict(size=10, color="#6B7770"),
    )

    fig.update_layout(
        height=max(350, min(760, 30 * len(gantt) + 112)),
        margin=dict(l=8, r=10, t=40, b=12),
        bargap=0.22,
        legend=dict(
            title_text="",
            orientation="h",
            yanchor="bottom",
            y=1.07,
            xanchor="left",
            x=0,
            font=dict(size=10),
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(color=BRAND_DARK, size=10),
        hoverlabel=dict(
            bgcolor="#FFFFFF",
            font_size=12,
            font_family="Arial",
        ),
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={
            "displaylogo": False,
            "responsive": True,
            "modeBarButtonsToRemove": [
                "lasso2d",
                "select2d",
                "autoScale2d",
            ],
        },
    )

    # En celular es más útil una lista corta debajo del gráfico que depender del hover.
    with st.expander("Ver cronograma en formato lista", expanded=False):
        mobile_view = gantt[[
            "code", "title", "assignee", "Inicio", "Final", "Cumplimiento", "progress"
        ]].copy()
        mobile_view["Inicio"] = mobile_view["Inicio"].dt.strftime("%d/%m/%Y")
        mobile_view["Final"] = mobile_view["Final"].dt.strftime("%d/%m/%Y")
        mobile_view["progress"] = pd.to_numeric(mobile_view["progress"], errors="coerce").fillna(0).round(0)
        mobile_view = mobile_view.rename(columns={
            "code": "Código",
            "title": "Tarea",
            "assignee": "Responsable",
            "Cumplimiento": "Estado",
            "progress": "Avance %",
        })
        st.dataframe(
            mobile_view,
            hide_index=True,
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
# CALENDARIO OPERATIVO V2.11
# ============================================================

def _month_add(original_date, months):
    month = original_date.month - 1 + months
    year = original_date.year + month // 12
    month = month % 12 + 1
    day = min(original_date.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


def _recurrence_occurrences(task_row, month_start):
    recurrence = str(task_row.get("recurrence") or "No")
    if recurrence == "No":
        return []
    month_end = date(month_start.year, month_start.month, calendar.monthrange(month_start.year, month_start.month)[1])
    base = _safe_date(task_row.get("due_date")) or _safe_date(task_row.get("start_date"))
    occurrences = []
    if recurrence == "Mensual":
        raw_day = pd.to_numeric(task_row.get("recurrence_day"), errors="coerce")
        day = int(raw_day) if not pd.isna(raw_day) else (base.day if base else 1)
        day = min(max(day, 1), calendar.monthrange(month_start.year, month_start.month)[1])
        candidate = date(month_start.year, month_start.month, day)
        if base is None or candidate >= base:
            occurrences.append(candidate)
        return occurrences
    if base is None:
        return []
    if recurrence == "Semanal":
        candidate = base
        if candidate < month_start:
            delta = (month_start - candidate).days
            candidate = candidate + timedelta(days=((delta + 6) // 7) * 7)
        while candidate <= month_end:
            if candidate >= month_start:
                occurrences.append(candidate)
            candidate += timedelta(days=7)
        return occurrences
    step_months = {"Trimestral": 3, "Semestral": 6, "Anual": 12}.get(recurrence)
    if not step_months:
        return []
    candidate = base
    guard = 0
    while candidate < month_start and guard < 500:
        candidate = _month_add(candidate, step_months)
        guard += 1
    if month_start <= candidate <= month_end:
        occurrences.append(candidate)
    return occurrences


def calendar_events_for_month(tasks_df, month_start):
    events = {}
    month_end = date(month_start.year, month_start.month, calendar.monthrange(month_start.year, month_start.month)[1])
    for _, row in tasks_df.iterrows():
        due = _safe_date(row.get("due_date"))
        if due and month_start <= due <= month_end:
            events.setdefault(due, []).append({
                "kind": "due",
                "label": f"🔔 {row.get('code', '')} · {row.get('title', '')}",
                "status": str(row.get("status") or ""),
            })
        for occurrence in _recurrence_occurrences(row, month_start):
            label = f"🔁 {row.get('code', '')} · {row.get('title', '')}"
            current = events.setdefault(occurrence, [])
            if not any(item.get("label") == label for item in current):
                current.append({"kind": "recurrence", "label": label, "status": str(row.get("status") or "")})
    return events


def _calendar_event_style(item, current_day):
    status = str(item.get("status") or "")
    kind = str(item.get("kind") or "")

    if status == "Cerrada":
        return "green", "Cumplida"
    if status == "Terminada - espera cierre":
        return "blue", "Espera cierre"
    if status == "En ejecución":
        return "blue", "En ejecución"
    if kind == "recurrence":
        return "blue", "Recurrente"
    if current_day < date.today() and status not in ["Cerrada", "Terminada - espera cierre"]:
        return "red", "Vencida"
    if current_day <= date.today() + timedelta(days=7):
        return "yellow", "Próxima"
    return "gray", status or "Programada"


def render_month_calendar(tasks_df, month_start):
    events = calendar_events_for_month(tasks_df, month_start)
    headers = ["Lun", "Mar", "Mié", "Jue", "Vie", "Sáb", "Dom"]

    header_cols = st.columns(7)
    for col, label in zip(header_cols, headers):
        col.markdown(
            f'<div class="sev-cal-weekhead">{label}</div>',
            unsafe_allow_html=True,
        )

    for week in calendar.monthcalendar(month_start.year, month_start.month):
        cols = st.columns(7)
        for col, day_number in zip(cols, week):
            with col:
                if day_number == 0:
                    st.markdown(
                        '<div style="min-height:112px;margin-bottom:.42rem;"></div>',
                        unsafe_allow_html=True,
                    )
                    continue

                current_day = date(month_start.year, month_start.month, day_number)
                day_events = events.get(current_day, [])
                today_class = " sev-cal-today" if current_day == date.today() else ""
                today_tag = (
                    '<span class="sev-cal-today-tag">HOY</span>'
                    if current_day == date.today()
                    else ""
                )

                event_html = []
                if not day_events:
                    event_html.append('<div class="sev-cal-empty">Sin tareas</div>')
                else:
                    for item in day_events[:3]:
                        style, state_label = _calendar_event_style(item, current_day)
                        raw_label = str(item.get("label") or "")
                        clean_label = raw_label.replace("🔔 ", "").replace("🔁 ", "")
                        if len(clean_label) > 42:
                            clean_label = clean_label[:40].rstrip() + "…"
                        type_label = "Recurrente" if item.get("kind") == "recurrence" else state_label
                        event_html.append(
                            '<div class="sev-cal-event sev-cal-{style}">'
                            '<div class="sev-cal-event-title">{title}</div>'
                            '<div class="sev-cal-event-meta">{meta}</div>'
                            '</div>'.format(
                                style=style,
                                title=clean_label,
                                meta=type_label,
                            )
                        )
                    if len(day_events) > 3:
                        event_html.append(
                            f'<div class="sev-cal-empty">+ {len(day_events)-3} más</div>'
                        )

                cell_html = (
                    f'<div class="sev-cal-day{today_class}">'
                    f'<div class="sev-cal-daynum"><span>{day_number}</span>{today_tag}</div>'
                    + "".join(event_html)
                    + "</div>"
                )
                st.markdown(cell_html, unsafe_allow_html=True)



def due_alerts(tasks_df, reference=None, horizon_days=7):
    reference = reference or date.today()
    rows = []
    for _, row in tasks_df.iterrows():
        if str(row.get("status") or "") == "Cerrada":
            continue
        due = _safe_date(row.get("due_date"))
        if due is None:
            continue
        days = (due - reference).days
        if days <= horizon_days:
            if days < 0:
                notice = f"🔴 Vencida hace {abs(days)} día(s)"
            elif days == 0:
                notice = "🟠 Vence hoy"
            elif days <= 2:
                notice = f"🟡 Vence en {days} día(s)"
            else:
                notice = f"🔔 Vence en {days} día(s)"
            rows.append({
                "Aviso": notice,
                "Código": row.get("code"),
                "Tarea": row.get("title"),
                "Responsable": row.get("assignee"),
                "Finalización": due.strftime("%d/%m/%Y"),
                "Estado": row.get("status"),
                "Días": days,
            })
    if not rows:
        return pd.DataFrame()
    return pd.DataFrame(rows).sort_values(["Días", "Responsable", "Código"])


# ============================================================
# PANEL ADMINISTRADOR
# ============================================================

render_header()


page = st.sidebar.radio(
    "CONTROL DE TAREAS",
    [
        "Tablero",
        "Nueva etapa",
        "Nueva tarea",
        "Tareas",
        "Calendario / Gantt",
        "Recurrentes",
        "Mantenimiento",
        "Operarios",
        "Usuarios",
        "Cierres pendientes",
        "Avisos",
    ],
)

st.sidebar.divider()
st.sidebar.caption("MODO ADMINISTRADOR")
st.sidebar.markdown(f"**{ADMIN_NAME}**")
st.sidebar.caption(ADMIN_EMAIL)


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
    WHERE COALESCE(t.archived, 0) = 0
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
        "Tablero ejecutivo",
        "Prioridades, ejecución, atención inmediata y próximos vencimientos",
    )

    f1, f2, f3, f4 = st.columns(4)
    sector_filter = f1.selectbox("Sector", ["Todos", *SECTORES.values()], key="dash_sector_v217")
    area_filter = f2.selectbox("Área", ["Todas", *AREAS.values()], key="dash_area_v217")
    operator_filter = f3.selectbox("Operario", ["Todos", *people["name"].tolist()], key="dash_operator_v217")
    status_filter = f4.selectbox(
        "Estado",
        ["Todos", "Pendiente", "Asignada", "Aceptada", "En ejecución",
         "Terminada - espera cierre", "Cerrada"],
        key="dash_status_v217",
    )

    view = tasks.copy()
    if sector_filter != "Todos":
        view = view[view["sector"] == sector_filter]
    if area_filter != "Todas":
        view = view[view["area"] == area_filter]
    if operator_filter != "Todos":
        view = view[view["assignee"] == operator_filter]
    if status_filter != "Todos":
        view = view[view["status"] == status_filter]

    view = view.copy()
    view["Teórico %"] = view.apply(theoretical, axis=1)
    view["Desvío pp"] = view.apply(schedule_delta, axis=1)
    view["Semáforo"] = view.apply(traffic_light, axis=1)

    # V2.17: los indicadores operativos usan sólo tareas abiertas.
    active_view = view[view["status"] != "Cerrada"].copy()
    open_count = len(active_view)
    execution_count = int((active_view["status"] == "En ejecución").sum())
    waiting_close = int((active_view["status"] == "Terminada - espera cierre").sum())

    pending_acceptance_mask = (
        active_view["status"].isin(["Asignada", "Pendiente"])
        & active_view["accepted_at"].isna()
    )
    pending_acceptance_count = int(pending_acceptance_mask.sum())

    overdue_mask = active_view["Semáforo"].astype(str).str.contains(
        "🔴 Atrasada|🔴 Vencida", regex=True
    )
    overdue_count = int(overdue_mask.sum())

    attention_mask = active_view["Semáforo"].astype(str).str.contains(
        "🟡 Atención", regex=False
    )
    attention_count = int(attention_mask.sum())

    on_time_mask = active_view["Semáforo"].astype(str).str.contains(
        "🟢 En término", regex=False
    )
    on_time_count = int(on_time_mask.sum())

    requested_month = int(
        (
            pd.to_datetime(view["requested"], errors="coerce").dt.to_period("M")
            == pd.Period(date.today(), freq="M")
        ).sum()
    )

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Total activas", open_count, delta=f"{requested_month} solicitadas este mes")
    k2.metric("En ejecución", execution_count)
    k3.metric("Sin aceptar", pending_acceptance_count)
    k4.metric("Atrasadas", overdue_count)
    k5.metric("En término", on_time_count)

    st.markdown(
        f'<div class="sev-kpi-strip">Esperan cierre: <b>{waiting_close}</b> · '
        f'Vista filtrada: <b>{len(view)}</b> tarea(s)</div>',
        unsafe_allow_html=True,
    )

    section(
        "Atención inmediata",
        "Acciones pendientes ordenadas por urgencia y fecha",
    )
    left_action, right_hitos = st.columns([3.30, 1.00], gap="medium")

    with left_action:
        st.markdown(
            f"""
            <div class="sev-action-summary">
                <div class="sev-action-pill">
                    <div class="n">{overdue_count}</div>
                    <div class="t">Atrasadas / vencidas</div>
                </div>
                <div class="sev-action-pill">
                    <div class="n">{attention_count}</div>
                    <div class="t">En atención</div>
                </div>
                <div class="sev-action-pill">
                    <div class="n">{pending_acceptance_count}</div>
                    <div class="t">Sin aceptar</div>
                </div>
                <div class="sev-action-pill">
                    <div class="n">{waiting_close}</div>
                    <div class="t">Esperando cierre</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        urgent = active_view.copy()
        urgent["_due"] = pd.to_datetime(urgent["due_date"], errors="coerce")
        urgent["_pending_acceptance"] = (
            urgent["status"].isin(["Asignada", "Pendiente"])
            & urgent["accepted_at"].isna()
        )
        urgent["_late"] = urgent["Semáforo"].astype(str).str.contains(
            "🔴 Atrasada|🔴 Vencida", regex=True
        )
        urgent["_attention"] = urgent["Semáforo"].astype(str).str.contains(
            "🟡 Atención", regex=False
        )
        urgent["_waiting_close"] = urgent["status"] == "Terminada - espera cierre"
        urgent["_urgent"] = (
            urgent["_late"]
            | urgent["_attention"]
            | urgent["_pending_acceptance"]
            | urgent["_waiting_close"]
        )
        urgent = urgent[urgent["_urgent"]].copy()

        def _action_label_v219(row):
            if bool(row["_late"]):
                return "Atrasada", "late"
            if bool(row["_pending_acceptance"]):
                return "Sin aceptar", "pending"
            if bool(row["_attention"]):
                return "Atención", "attention"
            if bool(row["_waiting_close"]):
                return "Espera cierre", "close"
            return "Revisar", "pending"

        if urgent.empty:
            st.success("Sin acciones críticas en la vista seleccionada.")
        else:
            priority_order = {"Crítica": 0, "Alta": 1, "Media": 2, "Baja": 3}
            urgent["_prio"] = urgent["priority"].map(priority_order).fillna(9)
            urgent = urgent.sort_values(
                ["_late", "_pending_acceptance", "_attention", "_due", "_prio"],
                ascending=[False, False, False, True, True],
                na_position="last",
            )

            st.markdown(
                """
                <div class="sev-action-head">
                    <div>Acción</div>
                    <div>Tarea</div>
                    <div>Responsable</div>
                    <div>Prioridad</div>
                    <div>Avance</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            for _, task_row in urgent.head(7).iterrows():
                action_label, action_class = _action_label_v219(task_row)
                title = str(task_row.get("title") or "—")
                owner = str(task_row.get("assignee") or "—")
                priority = str(task_row.get("priority") or "—")
                progress = float(task_row.get("progress") or 0)

                due_ts = task_row.get("_due")
                if pd.isna(due_ts):
                    due_text = "Sin fecha"
                else:
                    due_text = due_ts.strftime("%d/%m/%Y")

                st.markdown(
                    f"""
                    <div class="sev-action-row">
                        <div>
                            <span class="sev-action-status sev-badge-{action_class}">
                                {action_label}
                            </span>
                        </div>
                        <div class="sev-action-title">{title}</div>
                        <div class="sev-action-owner">{owner}</div>
                        <div class="sev-action-meta">
                            {priority}<br>
                            <span style="font-size:.62rem;">{due_text}</span>
                        </div>
                        <div class="sev-action-progress">{progress:.0f}%</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            if len(urgent) > 7:
                with st.expander(
                    f"Ver todas las {len(urgent)} acciones pendientes",
                    expanded=False,
                ):
                    full_urgent = urgent.copy()
                    full_urgent["Acción"] = full_urgent.apply(
                        lambda row: _action_label_v219(row)[0], axis=1
                    )
                    full_urgent["Vence"] = full_urgent["_due"].dt.strftime(
                        "%d/%m/%Y"
                    ).fillna("—")
                    full_urgent["Avance %"] = pd.to_numeric(
                        full_urgent["progress"], errors="coerce"
                    ).fillna(0).round(0)

                    st.dataframe(
                        full_urgent[
                            [
                                "Acción",
                                "title",
                                "assignee",
                                "priority",
                                "Vence",
                                "Avance %",
                            ]
                        ].rename(
                            columns={
                                "title": "Tarea",
                                "assignee": "Responsable",
                                "priority": "Prioridad",
                            }
                        ),
                        hide_index=True,
                        use_container_width=True,
                    )

    with right_hitos:
        st.markdown(
            '<div class="sev-panel-title"><span class="sev-dot"></span>Próximos hitos</div>',
            unsafe_allow_html=True,
        )

        hitos = active_view.copy()
        hitos["_due"] = pd.to_datetime(hitos["due_date"], errors="coerce")
        hitos = hitos[hitos["_due"].notna()].sort_values("_due").head(5)

        if hitos.empty:
            st.caption("No hay próximos vencimientos.")
        else:
            for _, hito in hitos.iterrows():
                due_hito = hito["_due"].date()
                dias = (due_hito - date.today()).days

                if dias < 0:
                    plazo = f"Vencida {abs(dias)} d"
                    state_color = COLOR_DANGER
                elif dias == 0:
                    plazo = "Hoy"
                    state_color = COLOR_WARNING
                elif dias == 1:
                    plazo = "Mañana"
                    state_color = COLOR_WARNING
                else:
                    plazo = f"En {dias} d"
                    state_color = BRAND_GREEN

                title_hito = str(hito.get("title") or "")
                if len(title_hito) > 28:
                    title_hito = title_hito[:26].rstrip() + "…"

                st.markdown(
                    f"""
                    <div class="sev-mini-card">
                        <div class="sev-mini-kicker">{str(hito.get("assignee") or "—")}</div>
                        <div class="sev-mini-main">{title_hito}</div>
                        <div class="sev-mini-sub">
                            {due_hito.strftime("%d/%m/%Y")} ·
                            <span style="color:{state_color};font-weight:750;">{plazo}</span>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    section(
        "Avance operativo",
        "Seguimiento de tareas activas y desempeño por responsable",
    )
    progress_col, ranking_col = st.columns([3.30, 1.00], gap="medium")

    with progress_col:
        progress_tasks = active_view.copy()
        progress_tasks["_due"] = pd.to_datetime(
            progress_tasks["due_date"], errors="coerce"
        )
        progress_tasks["_progress"] = pd.to_numeric(
            progress_tasks["progress"], errors="coerce"
        ).fillna(0).clip(0, 100)

        progress_tasks = progress_tasks.sort_values(
            ["_due", "_progress"],
            ascending=[True, False],
            na_position="last",
        ).head(7)

        if progress_tasks.empty:
            st.info("No hay tareas activas para mostrar.")
        else:
            for _, task_row in progress_tasks.iterrows():
                title = str(task_row.get("title") or "Tarea")
                owner = str(task_row.get("assignee") or "—")
                pct = float(task_row["_progress"])
                status_txt = str(task_row.get("Semáforo") or "—")
                due_ts = task_row.get("_due")

                if pd.isna(due_ts):
                    due_text = "Sin fecha"
                else:
                    due_text = due_ts.strftime("%d/%m/%Y")

                st.markdown(
                    f"""
                    <div class="sev-progress-card">
                        <div class="sev-progress-top">
                            <div class="sev-progress-title2">{title}</div>
                            <div class="sev-progress-value2">{pct:.0f}%</div>
                        </div>
                        <div class="sev-progress-sub">
                            <span><strong>{owner}</strong></span>
                            <span>Vence: {due_text}</span>
                            <span>{status_txt}</span>
                        </div>
                        <div class="sev-progress-track2">
                            <div class="sev-progress-fill2" style="width:{pct:.0f}%"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

        with st.expander("Comparar avance real vs. teórico", expanded=False):
            progress_chart(view)

    with ranking_col:
        st.markdown(
            '<div class="sev-panel-title"><span class="sev-dot"></span>Responsables</div>',
            unsafe_allow_html=True,
        )

        person_rows = []
        for person_name, person_tasks in view.groupby("assignee", dropna=False):
            active_person = person_tasks[
                person_tasks["status"] != "Cerrada"
            ].copy()

            total_active = len(active_person)
            if total_active == 0:
                continue

            late_n = int(
                active_person["Semáforo"].astype(str).str.contains(
                    "🔴 Atrasada|🔴 Vencida", regex=True
                ).sum()
            )
            attention_n = int(
                active_person["Semáforo"].astype(str).str.contains(
                    "🟡 Atención", regex=False
                ).sum()
            )
            green_n = int(
                active_person["Semáforo"].astype(str).str.contains(
                    "🟢 En término", regex=False
                ).sum()
            )
            evaluable_n = int(
                (
                    ~active_person["Semáforo"]
                    .astype(str)
                    .str.contains("⚪ Sin cronograma", regex=False)
                ).sum()
            )

            score = round(100 * green_n / evaluable_n) if evaluable_n > 0 else 0
            score = max(0, min(100, score))

            person_rows.append(
                {
                    "Responsable": str(person_name),
                    "Cumplimiento": score,
                    "Activas": total_active,
                    "Alertas": late_n + attention_n,
                }
            )

        person_summary = pd.DataFrame(person_rows)

        if person_summary.empty:
            st.caption("Sin responsables con tareas activas.")
        else:
            person_summary = person_summary.sort_values(
                ["Cumplimiento", "Alertas"],
                ascending=[False, True],
            )

            for _, person_row in person_summary.head(5).iterrows():
                score = float(person_row["Cumplimiento"])
                st.markdown(
                    f"""
                    <div class="sev-owner-card">
                        <div class="sev-owner-top">
                            <div class="sev-owner-name">{person_row['Responsable']}</div>
                            <div class="sev-owner-score">{score:.0f}%</div>
                        </div>
                        <div class="sev-owner-meta">
                            {int(person_row['Activas'])} activa(s) ·
                            {int(person_row['Alertas'])} alerta(s)
                        </div>
                        <div class="sev-owner-bar">
                            <div class="sev-owner-fill" style="width:{score:.0f}%"></div>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

            with st.expander("Ver ranking completo", expanded=False):
                st.dataframe(
                    person_summary,
                    hide_index=True,
                    use_container_width=True,
                    column_config={
                        "Cumplimiento": st.column_config.ProgressColumn(
                            "Cumplimiento",
                            min_value=0,
                            max_value=100,
                            format="%d%%",
                        )
                    },
                )

    section(
        "Cronograma",
        "Gantt completo disponible sin ocupar la pantalla ejecutiva inicial",
    )
    with st.expander("Abrir cronograma de cumplimiento · Gantt", expanded=False):
        gantt_chart(view)

    with st.expander("Solicitudes por mes", expanded=False):
        monthly = view.copy()
        monthly["Mes"] = (
            pd.to_datetime(monthly["requested"], errors="coerce")
            .dt.to_period("M").astype(str)
        )
        monthly = monthly.groupby("Mes").size().reset_index(name="Tareas")

        if monthly.empty:
            st.info("No hay datos para el período seleccionado.")
        else:
            fig_month = px.line(monthly, x="Mes", y="Tareas", markers=True)
            fig_month.update_traces(
                line_color=BRAND_GREEN, marker_color=BRAND_GREEN, line_width=3
            )
            fig_month.update_layout(
                height=260,
                margin=dict(l=10, r=10, t=10, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="#FFFFFF",
                font=dict(color=BRAND_DARK),
                xaxis=dict(showgrid=False),
                yaxis=dict(gridcolor="#E8ECE9", rangemode="tozero"),
            )
            st.plotly_chart(
                fig_month,
                use_container_width=True,
                config={"displaylogo": False},
            )


# ============================================================
# NUEVA ETAPA OPERATIVA · V2.13
# ============================================================

elif page == "Nueva etapa":

    section(
        "Nueva etapa operativa",
        "Reasigna tareas con nuevas fechas, conserva el historial y vuelve a enviar la aceptación.",
    )

    st.info(
        "Las tareas anteriores no se borran. Al confirmar, quedan archivadas como histórico y "
        "se crean nuevas asignaciones en 0% con estado Asignada."
    )

    restart_source = tasks.copy()
    include_closed = st.checkbox(
        "Incluir tareas cerradas",
        value=False,
        key="restart_include_closed_v213",
    )
    if not include_closed:
        restart_source = restart_source[restart_source["status"] != "Cerrada"].copy()

    if restart_source.empty:
        st.warning("No hay tareas disponibles para iniciar una nueva etapa.")
    else:
        task_ids = restart_source["id"].astype(int).tolist()
        labels = {
            int(row["id"]): f"{row['code']} · {row['title']} · {row['assignee']}"
            for _, row in restart_source.iterrows()
        }

        cycle_name = st.text_input(
            "Nombre de la nueva etapa",
            value=f"Inicio operativo {date.today().strftime('%d/%m/%Y')}",
            key="restart_cycle_name_v213",
        )

        selected_restart_ids = st.multiselect(
            "Tareas a reasignar",
            task_ids,
            default=task_ids,
            format_func=lambda task_id: labels.get(int(task_id), str(task_id)),
            key="restart_task_ids_v213",
        )

        d1, d2 = st.columns(2)
        new_start = d1.date_input(
            "Nueva fecha de inicio",
            value=date.today(),
            format="DD/MM/YYYY",
            key="restart_start_v213",
        )
        date_strategy = d2.selectbox(
            "Cómo definir la fecha final",
            ["Mantener duración original", "Usar una misma fecha final"],
            key="restart_date_strategy_v213",
        )

        common_due = None
        if date_strategy == "Usar una misma fecha final":
            common_due = st.date_input(
                "Nueva fecha de finalización para todas",
                value=date.today() + timedelta(days=30),
                format="DD/MM/YYYY",
                key="restart_common_due_v213",
            )

        send_restart_emails = st.checkbox(
            "Enviar correo de nueva asignación a cada responsable",
            value=True,
            key="restart_send_email_v213",
        )

        st.markdown("#### Vista previa")
        preview_rows = []
        for task_id in selected_restart_ids:
            row = restart_source.loc[
                restart_source["id"].astype(int) == int(task_id)
            ].iloc[0]
            old_start = _safe_date(row.get("start_date"))
            old_due = _safe_date(row.get("due_date"))
            if (
                date_strategy == "Mantener duración original"
                and old_start
                and old_due
                and old_due >= old_start
            ):
                duration = (old_due - old_start).days
                preview_due = new_start + timedelta(days=max(duration, 0))
            elif common_due is not None:
                preview_due = common_due
            else:
                preview_due = new_start + timedelta(days=30)
            preview_rows.append(
                {
                    "Tarea": row["title"],
                    "Responsable": row["assignee"],
                    "Inicio": new_start.strftime("%d/%m/%Y"),
                    "Final": preview_due.strftime("%d/%m/%Y"),
                    "Prioridad": row.get("priority") or "Media",
                }
            )

        if preview_rows:
            st.dataframe(
                pd.DataFrame(preview_rows),
                hide_index=True,
                use_container_width=True,
                height=min(420, 42 + 35 * len(preview_rows)),
            )

        confirm_restart = st.checkbox(
            "Confirmo el inicio de la nueva etapa",
            value=False,
            key="restart_confirm_v213",
        )

        if st.button(
            "Iniciar nueva etapa y reasignar",
            type="primary",
            use_container_width=True,
            disabled=(
                not selected_restart_ids
                or not confirm_restart
                or not cycle_name.strip()
            ),
            key="restart_execute_v213",
        ):
            created = 0
            sent = 0
            failed = 0
            observations = []

            for task_id in selected_restart_ids:
                old = c.execute(
                    "SELECT * FROM tasks WHERE id = ?",
                    (int(task_id),),
                ).fetchone()
                if not old:
                    continue

                old_start = _safe_date(old["start_date"])
                old_due = _safe_date(old["due_date"])
                if (
                    date_strategy == "Mantener duración original"
                    and old_start
                    and old_due
                    and old_due >= old_start
                ):
                    duration = (old_due - old_start).days
                    new_due = new_start + timedelta(days=max(duration, 0))
                elif common_due is not None:
                    new_due = common_due
                else:
                    new_due = new_start + timedelta(days=30)

                if new_due < new_start:
                    observations.append(f"{old['code']}: fecha final anterior al inicio")
                    continue

                code = next_code(old["sector"], old["area"], c)
                task_token = secrets.token_urlsafe(24)
                recurrence_value = old["recurrence"]
                recurrence_day = new_due.day if recurrence_value else None

                c.execute(
                    """
                    INSERT INTO tasks(
                        code, title, description, sector, area, maintenance_type,
                        assignee_id, priority, requested, start_date, due_date,
                        status, progress, observation, token, accepted_at,
                        finished_at, closed_at, imported, recurrence,
                        recurrence_day, recurrence_parent_id, created_at,
                        archived, operational_cycle, restart_parent_id
                    )
                    VALUES(
                        ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                        ?, ?, ?, ?, ?, ?, ?, ?
                    )
                    """,
                    (
                        code,
                        old["title"],
                        old["description"],
                        old["sector"],
                        old["area"],
                        old["maintenance_type"],
                        old["assignee_id"],
                        old["priority"],
                        date.today().isoformat(),
                        new_start.isoformat(),
                        new_due.isoformat(),
                        "Asignada",
                        0,
                        old["observation"],
                        task_token,
                        None,
                        None,
                        None,
                        old["imported"],
                        recurrence_value,
                        recurrence_day,
                        None,
                        datetime.now().isoformat(),
                        0,
                        cycle_name.strip(),
                        int(task_id),
                    ),
                )
                new_task_id = c.execute(
                    "SELECT last_insert_rowid() AS id"
                ).fetchone()["id"]
                c.execute(
                    "UPDATE tasks SET archived = 1 WHERE id = ?",
                    (int(task_id),),
                )
                c.commit()

                log_event(
                    c,
                    int(task_id),
                    "restart_archived",
                    "Administrador",
                    f"Archivada por nueva etapa {cycle_name.strip()}. Nueva tarea: {code}",
                )
                log_event(
                    c,
                    int(new_task_id),
                    "restart_created",
                    "Administrador",
                    f"Nueva etapa {cycle_name.strip()}. Origen: {old['code']}",
                )
                created += 1

                if send_restart_emails:
                    person = person_for_task(c, int(new_task_id))
                    task_mail = {
                        "id": int(new_task_id),
                        "code": code,
                        "title": old["title"],
                        "priority": old["priority"],
                        "start_date": new_start.strftime("%d/%m/%Y"),
                        "due_date": new_due.strftime("%d/%m/%Y"),
                        "token": task_token,
                        "progress": 0,
                    }
                    mail_ok, mail_detail = send_assignment_email(
                        task_mail,
                        person,
                        BASE_DIR,
                    )
                    log_email(
                        c,
                        int(new_task_id),
                        person.get("email", ""),
                        "assignment_restart",
                        f"Nueva etapa · tarea asignada · {code}",
                        mail_ok,
                        mail_detail,
                    )
                    if mail_ok:
                        sent += 1
                    else:
                        failed += 1
                        observations.append(f"{code}: {mail_detail}")

            st.success(
                f"Nueva etapa creada: {created} tarea(s). "
                f"Correos enviados: {sent}. Errores de correo: {failed}."
            )
            if observations:
                with st.expander("Ver observaciones", expanded=True):
                    for item in observations:
                        st.write("• " + item)
            st.rerun()


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

        person_id_options = people["id"].astype(int).tolist()
        admin_matches = people.loc[
            people["email"].astype(str).str.lower() == ADMIN_EMAIL.lower(),
            "id",
        ].astype(int).tolist()
        admin_default_id = admin_matches[0] if admin_matches else person_id_options[0]
        admin_default_index = (
            person_id_options.index(admin_default_id)
            if admin_default_id in person_id_options else 0
        )

        assignee_id = (
            col2.selectbox(
                "Responsable",
                person_id_options,
                index=admin_default_index,
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
        "Gestión completa: editar, cambiar estado, cerrar o quitar de la lista",
    )

    status_values = [
        "Pendiente",
        "Asignada",
        "Aceptada",
        "En ejecución",
        "Terminada - espera cierre",
        "Cerrada",
    ]

    # ========================================================
    # V2.8 · EDICIÓN COMPLETA EN PRIMER PLANO
    # ========================================================
    selected_task_id = st.session_state.get("edit_task_id_v28")

    if selected_task_id is not None:
        selected_rows = tasks.loc[tasks["id"] == int(selected_task_id)]

        if selected_rows.empty:
            st.session_state.pop("edit_task_id_v28", None)
            st.warning("La tarea seleccionada ya no está disponible.")
            st.rerun()

        selected = selected_rows.iloc[0]
        task_id = int(selected["id"])

        st.info(
            "Modo edición completo. Podés modificar todos los datos operativos de la tarea. "
            "El código, token y fechas automáticas del sistema se conservan para mantener la trazabilidad."
        )

        top1, top2 = st.columns([4.5, 1.0], vertical_alignment="center")
        with top1:
            st.markdown(f"### ✏️ {selected['title']}")
            st.caption(f"{selected['code']} · Responsable actual: {selected.get('assignee') or '—'}")
        with top2:
            if st.button("← Volver a tareas", use_container_width=True, key=f"back_edit_{task_id}"):
                st.session_state.pop("edit_task_id_v28", None)
                st.rerun()

        selected_start = pd.to_datetime(selected.get("start_date"), errors="coerce")
        selected_due = pd.to_datetime(selected.get("due_date"), errors="coerce")
        selected_requested = pd.to_datetime(selected.get("requested"), errors="coerce")

        current_assignee_id = int(selected["assignee_id"])
        person_ids = people["id"].astype(int).tolist()
        person_names = dict(zip(people["id"].astype(int), people["name"]))

        current_sector = str(selected.get("sector") or "LAB")
        current_area = str(selected.get("area") or "FER")
        current_priority = str(selected.get("priority") or "Media")
        current_status = str(selected.get("status") or "Pendiente")
        current_maintenance = str(selected.get("maintenance_type") or "")
        current_recurrence = str(selected.get("recurrence") or "No")
        if current_recurrence not in RECURRENCIAS:
            current_recurrence = "No"

        with st.form(f"edit_task_form_v28_{task_id}"):
            st.markdown("#### Datos principales")
            r1, r2 = st.columns([2.2, 1.0])
            edit_title = r1.text_input(
                "Tarea",
                value=str(selected.get("title") or ""),
            )
            edit_assignee = r2.selectbox(
                "Responsable",
                person_ids,
                index=(
                    person_ids.index(current_assignee_id)
                    if current_assignee_id in person_ids else 0
                ),
                format_func=lambda person_id: person_names.get(int(person_id), str(person_id)),
            )

            edit_description = st.text_area(
                "Descripción",
                value=str(selected.get("description") or ""),
                height=120,
                placeholder="Detalle completo de la acción o trabajo solicitado",
            )

            st.markdown("#### Clasificación y estado")
            c1, c2, c3, c4 = st.columns(4)
            sector_values = list(SECTORES.values())
            area_values = list(AREAS.values())

            edit_sector = c1.selectbox(
                "Sector",
                sector_values,
                index=(sector_values.index(current_sector) if current_sector in sector_values else 0),
            )
            edit_area = c2.selectbox(
                "Área",
                area_values,
                index=(area_values.index(current_area) if current_area in area_values else 0),
            )
            edit_priority = c3.selectbox(
                "Prioridad",
                PRIORIDADES,
                index=(PRIORIDADES.index(current_priority) if current_priority in PRIORIDADES else 2),
            )
            edit_status = c4.selectbox(
                "Estado",
                status_values,
                index=(status_values.index(current_status) if current_status in status_values else 0),
            )

            maintenance_options = ["—", *TIPOS_MANT]
            edit_maintenance = st.selectbox(
                "Tipo de mantenimiento",
                maintenance_options,
                index=(
                    maintenance_options.index(current_maintenance)
                    if current_maintenance in maintenance_options else 0
                ),
                disabled=(edit_sector != "MANT"),
            )

            st.markdown("#### Fechas y planificación")
            st.caption(
                "Todas las fechas pueden modificarse directamente. "
                "Inicio, final prevista y final real pueden quedar vacías."
            )

            selected_finished = pd.to_datetime(
                selected.get("finished_at"),
                errors="coerce",
            )

            f1, f2, f3, f4 = st.columns(4)

            edit_requested = f1.date_input(
                "Fecha de solicitud",
                value=(
                    selected_requested.date()
                    if not pd.isna(selected_requested)
                    else date.today()
                ),
                format="DD/MM/YYYY",
                key=f"edit_requested_{task_id}",
            )

            edit_start = f2.date_input(
                "Fecha de inicio",
                value=(
                    selected_start.date()
                    if not pd.isna(selected_start)
                    else None
                ),
                format="DD/MM/YYYY",
                key=f"edit_start_{task_id}",
            )

            edit_due = f3.date_input(
                "Finalización prevista",
                value=(
                    selected_due.date()
                    if not pd.isna(selected_due)
                    else None
                ),
                format="DD/MM/YYYY",
                key=f"edit_due_{task_id}",
            )

            edit_finished = f4.date_input(
                "Finalización real",
                value=(
                    selected_finished.date()
                    if not pd.isna(selected_finished)
                    else None
                ),
                format="DD/MM/YYYY",
                key=f"edit_finished_{task_id}",
                help=(
                    "Fecha real en que se completó la tarea. "
                    "Se utiliza para el control de cumplimiento y calendario anual."
                ),
            )

            st.markdown("#### Avance y recurrencia")
            p1, p2, p3 = st.columns([1.2, 1.0, 1.0])
            edit_progress = p1.slider(
                "Avance real (%)",
                0,
                100,
                int(float(selected.get("progress") or 0)),
            )
            edit_recurrence = p2.selectbox(
                "Recurrencia",
                RECURRENCIAS,
                index=RECURRENCIAS.index(current_recurrence),
            )
            recurrence_raw = pd.to_numeric(
                selected.get("recurrence_day"),
                errors="coerce",
            )
            recurrence_default = (
                1
                if pd.isna(recurrence_raw)
                else int(recurrence_raw)
            )
            recurrence_default = min(max(recurrence_default, 1), 31)
            edit_recurrence_day = p3.number_input(
                "Día de recurrencia",
                min_value=1,
                max_value=31,
                value=recurrence_default,
                step=1,
                disabled=(edit_recurrence == "No"),
            )

            edit_observation = st.text_area(
                "Observación / resultado / evidencia de cierre",
                value=str(selected.get("observation") or ""),
                height=140,
                placeholder="Agregar observaciones, resultados obtenidos o evidencia de cierre",
            )

            st.markdown("#### Datos de trazabilidad")
            t1, t2, t3 = st.columns(3)
            t1.text_input("Código", value=str(selected.get("code") or ""), disabled=True)
            t2.text_input(
                "Creada",
                value=(
                    pd.to_datetime(selected.get("created_at"), errors="coerce").strftime("%d/%m/%Y %H:%M")
                    if not pd.isna(pd.to_datetime(selected.get("created_at"), errors="coerce"))
                    else "—"
                ),
                disabled=True,
            )
            t3.text_input(
                "Aceptada",
                value=(
                    pd.to_datetime(selected.get("accepted_at"), errors="coerce").strftime("%d/%m/%Y %H:%M")
                    if not pd.isna(pd.to_datetime(selected.get("accepted_at"), errors="coerce"))
                    else "—"
                ),
                disabled=True,
            )

            b1, b2, b3 = st.columns([1.7, 1.0, 1.0])
            save_changes = b1.form_submit_button(
                "💾 Guardar todas las modificaciones",
                type="primary",
                use_container_width=True,
            )
            close_action = b2.form_submit_button(
                "✅ Guardar y cerrar",
                use_container_width=True,
            )
            cancel_edit = b3.form_submit_button(
                "Cancelar",
                use_container_width=True,
            )

        if cancel_edit:
            st.session_state.pop("edit_task_id_v28", None)
            st.rerun()

        if save_changes or close_action:
            if not edit_title.strip():
                st.error("La tarea no puede quedar sin nombre.")
            elif edit_start is not None and edit_due is not None and edit_due < edit_start:
                st.error("La fecha final prevista no puede ser anterior a la fecha de inicio.")
            elif edit_finished is not None and edit_start is not None and edit_finished < edit_start:
                st.error("La fecha real de finalización no puede ser anterior a la fecha de inicio.")
            else:
                new_status = "Cerrada" if close_action else edit_status
                new_progress = 100 if close_action or new_status == "Cerrada" else int(edit_progress)

                start_value = edit_start.isoformat() if edit_start is not None else None
                due_value = edit_due.isoformat() if edit_due is not None else None
                requested_value = edit_requested.isoformat()
                maintenance_value = (
                    None
                    if edit_sector != "MANT" or edit_maintenance == "—"
                    else edit_maintenance
                )
                recurrence_value = None if edit_recurrence == "No" else edit_recurrence
                recurrence_day_value = (
                    None if edit_recurrence == "No" else int(edit_recurrence_day)
                )

                was_closed = current_status == "Cerrada"
                will_be_closed = new_status == "Cerrada"
                closed_at = selected.get("closed_at")

                # V2.22: la fecha real de terminación es editable por el administrador.
                if edit_finished is not None:
                    previous_finished = pd.to_datetime(
                        selected.get("finished_at"),
                        errors="coerce",
                    )
                    if not pd.isna(previous_finished):
                        finish_time = previous_finished.time()
                    else:
                        finish_time = datetime.now().time().replace(microsecond=0)

                    finished_at = datetime.combine(
                        edit_finished,
                        finish_time,
                    ).isoformat()
                else:
                    finished_at = None

                if will_be_closed:
                    closed_at = closed_at or datetime.now().isoformat()
                    if finished_at is None:
                        finished_at = datetime.now().isoformat()
                elif was_closed:
                    closed_at = None

                c.execute(
                    """
                    UPDATE tasks SET
                        title = ?,
                        description = ?,
                        sector = ?,
                        area = ?,
                        maintenance_type = ?,
                        assignee_id = ?,
                        priority = ?,
                        requested = ?,
                        start_date = ?,
                        due_date = ?,
                        status = ?,
                        progress = ?,
                        observation = ?,
                        recurrence = ?,
                        recurrence_day = ?,
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
                        requested_value,
                        start_value,
                        due_value,
                        new_status,
                        float(new_progress),
                        edit_observation.strip(),
                        recurrence_value,
                        recurrence_day_value,
                        finished_at,
                        closed_at,
                        task_id,
                    ),
                )
                c.commit()

                changed_summary = (
                    f"Edición completa. Responsable: {person_names.get(int(edit_assignee), edit_assignee)}; "
                    f"estado: {new_status}; prioridad: {edit_priority}; avance: {new_progress}%; "
                    f"inicio: {start_value or 'sin fecha'}; final prevista: {due_value or 'sin fecha'}; "
                    f"final real: {finished_at or 'sin fecha'}."
                )
                log_event(
                    c,
                    task_id,
                    "closed" if will_be_closed else "edited",
                    "Administrador",
                    changed_summary,
                )

                if will_be_closed and current_status != "Cerrada":
                    person_row = people.loc[people["id"] == int(edit_assignee)]
                    if not person_row.empty:
                        person_mail = {
                            "name": str(person_row.iloc[0]["name"]),
                            "email": str(person_row.iloc[0]["email"]),
                        }
                        closed_task = dict(selected)
                        closed_task.update({
                            "title": edit_title.strip(),
                            "status": "Cerrada",
                            "progress": 100,
                            "observation": edit_observation.strip(),
                        })
                        mail_ok, mail_detail = send_closed_email(closed_task, person_mail, BASE_DIR)
                        log_email(
                            c,
                            task_id,
                            person_mail["email"],
                            "closed",
                            f"Tarea cerrada · {selected.get('code', '')}",
                            mail_ok,
                            mail_detail,
                        )

                st.session_state.pop("edit_task_id_v28", None)
                st.success("Todos los cambios fueron guardados correctamente.")
                st.rerun()

    else:
        # ====================================================
        # LISTADO COMPACTO + APERTURA INDIVIDUAL V2.11
        # ====================================================
        view = tasks.copy()
        view["Teórico %"] = view.apply(theoretical, axis=1)
        view["Semáforo"] = view.apply(traffic_light, axis=1)
        view["Inicio"] = pd.to_datetime(view["start_date"], errors="coerce").dt.strftime("%d/%m/%Y").fillna("—")
        view["Final"] = pd.to_datetime(view["due_date"], errors="coerce").dt.strftime("%d/%m/%Y").fillna("—")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Abiertas", int((view["status"] != "Cerrada").sum()))
        m2.metric("Esperan cierre", int((view["status"] == "Terminada - espera cierre").sum()))
        alerts = view["Semáforo"].astype(str).str.contains("🔴|🟡").sum()
        m3.metric("Con alerta", int(alerts))
        m4.metric("Cerradas", int((view["status"] == "Cerrada").sum()))

        f1, f2, f3 = st.columns([1.0, 1.3, 1.5])
        task_status_filter = f1.selectbox("Estado", ["Todos", *status_values], key="tasks_status_filter_v211")
        task_person_filter = f2.selectbox("Responsable", ["Todos", *people["name"].tolist()], key="tasks_person_filter_v211")
        search_task = f3.text_input("Buscar tarea", placeholder="Código, tarea, responsable u observación", key="tasks_search_v211")

        filtered = view.copy()
        if task_status_filter != "Todos": filtered = filtered[filtered["status"] == task_status_filter]
        if task_person_filter != "Todos": filtered = filtered[filtered["assignee"] == task_person_filter]
        if search_task.strip():
            needle = search_task.strip().lower()
            searchable = (filtered["code"].astype(str) + " " + filtered["title"].astype(str) + " " + filtered["assignee"].astype(str) + " " + filtered["observation"].fillna("").astype(str)).str.lower()
            filtered = filtered[searchable.str.contains(needle, regex=False)]

        st.caption(f"Mostrando {len(filtered)} de {len(view)} tareas activas.")
        if filtered.empty:
            st.info("No hay tareas que coincidan con los filtros seleccionados.")
        else:
            compact_view = st.toggle(
                "Vista compacta · recomendada para celular",
                value=True,
                key="tasks_compact_mobile_v213",
            )

            if compact_view:
                st.caption(
                    "Cada tarjeta muestra lo esencial. Tocá Abrir / modificar para ver el detalle completo."
                )
                for _, task_row in filtered.head(60).iterrows():
                    with st.container(border=True):
                        st.markdown(f"**{task_row['title']}**")
                        st.caption(f"{task_row['code']} · {task_row['Semáforo']}")
                        cc1, cc2 = st.columns(2)
                        cc1.write(f"**Responsable**  \n{task_row['assignee']}")
                        cc2.write(f"**Estado**  \n{task_row['status']}")
                        cc1.write(f"**Inicio**  \n{task_row['Inicio']}")
                        cc2.write(f"**Final**  \n{task_row['Final']}")
                        cc1.write(f"**Prioridad**  \n{task_row['priority']}")
                        cc2.write(f"**Avance**  \n{float(task_row['progress'] or 0):.0f}%")
                        if st.button(
                            "Abrir / modificar",
                            key=f"mobile_open_task_v213_{int(task_row['id'])}",
                            use_container_width=True,
                        ):
                            st.session_state["edit_task_id_v28"] = int(task_row["id"])
                            st.rerun()
                if len(filtered) > 60:
                    st.info(
                        "La vista compacta muestra las primeras 60 tareas. Usá los filtros para reducir la lista."
                    )
            else:
                display = filtered[["Semáforo", "code", "title", "assignee", "priority", "status", "Inicio", "Final", "progress", "Teórico %"]].copy()
                display["progress"] = pd.to_numeric(display["progress"], errors="coerce").fillna(0).round(0)
                display["Teórico %"] = pd.to_numeric(display["Teórico %"], errors="coerce").round(0)
                display = display.rename(columns={"code":"Código","title":"Tarea","assignee":"Responsable","priority":"Prioridad","status":"Estado","progress":"Avance %"})
                st.dataframe(display, hide_index=True, use_container_width=True, height=min(620, 74 + 35 * len(display)))

            st.markdown("#### Abrir una tarea para modificar")
            task_options = filtered["id"].astype(int).tolist()
            task_lookup = {int(row["id"]): f"{row['code']} · {row['title']} · {row['assignee']}" for _, row in filtered.iterrows()}
            selected_open_id = st.selectbox("Seleccionar tarea", task_options, format_func=lambda task_id: task_lookup.get(int(task_id), str(task_id)), key="open_task_selector_v211")
            o1, o2, o3 = st.columns([1.4, 1.0, 1.0])
            if o1.button("✏️ Abrir / modificar tarea", type="primary", use_container_width=True, key="open_task_button_v211"):
                st.session_state["edit_task_id_v28"] = int(selected_open_id)
                st.rerun()
            selected_status_row = filtered.loc[filtered["id"].astype(int) == int(selected_open_id)].iloc[0]
            if o2.button("✅ Cerrar tarea", use_container_width=True, disabled=(str(selected_status_row.get("status") or "") == "Cerrada"), key="close_selected_task_v211"):
                now = datetime.now().isoformat()
                c.execute("UPDATE tasks SET status='Cerrada', progress=100, finished_at=COALESCE(finished_at, ?), closed_at=COALESCE(closed_at, ?) WHERE id=?", (now, now, int(selected_open_id)))
                c.commit()
                log_event(c, int(selected_open_id), "closed", "Administrador", "Cierre administrativo desde listado compacto.")
                st.rerun()
            if o3.button("🗃️ Quitar de lista", use_container_width=True, key="archive_selected_task_v211"):
                st.session_state["archive_task_id_v28"] = int(selected_open_id)
            if st.session_state.get("archive_task_id_v28") == int(selected_open_id):
                st.warning("La tarea se quitará de las listas operativas, pero su historial se conservará.")
                q1, q2 = st.columns(2)
                if q1.button("Confirmar", type="primary", use_container_width=True, key="confirm_archive_v211"):
                    c.execute("UPDATE tasks SET archived=1 WHERE id=?", (int(selected_open_id),))
                    c.commit()
                    log_event(c, int(selected_open_id), "archived", "Administrador", "Tarea quitada de las listas operativas.")
                    st.session_state.pop("archive_task_id_v28", None)
                    st.rerun()
                if q2.button("Cancelar", use_container_width=True, key="cancel_archive_v211"):
                    st.session_state.pop("archive_task_id_v28", None)
                    st.rerun()

        with st.expander("Tareas quitadas de la lista · restaurar", expanded=False):
            archived = pd.read_sql_query("SELECT t.id,t.code,t.title,t.status,t.progress,t.assignee_id,p.name AS assignee FROM tasks t JOIN people p ON p.id=t.assignee_id WHERE COALESCE(t.archived,0)=1 ORDER BY t.id DESC", c)
            if archived.empty:
                st.caption("No hay tareas archivadas.")
            else:
                for _, archived_task in archived.iterrows():
                    ar1, ar2 = st.columns([4.8, 1.0], vertical_alignment="center")
                    ar1.markdown(f"**{archived_task['code']} · {archived_task['title']}**  \n{archived_task['assignee']} · {archived_task['status']} · {float(archived_task['progress'] or 0):.0f}%")
                    if ar2.button("Restaurar", key=f"restore_task_v211_{int(archived_task['id'])}", use_container_width=True):
                        c.execute("UPDATE tasks SET archived=0 WHERE id=?", (int(archived_task["id"]),))
                        c.commit()
                        log_event(c, int(archived_task["id"]), "restored", "Administrador", "Tarea restaurada a las listas operativas.")
                        st.rerun()


elif page == "Calendario / Gantt":

    section(
        "Calendario operativo",
        "Tareas rutinarias, fechas de finalización, estados y Gantt de cumplimiento",
    )

    top1, top2 = st.columns([1.05, 2.35], gap="medium")

    month_pick = top1.date_input(
        "Mes a consultar",
        value=date.today().replace(day=1),
        format="DD/MM/YYYY",
        key="calendar_month_v220",
    )
    month_start = date(month_pick.year, month_pick.month, 1)

    top2.markdown(
        '''
        <div class="sev-cal-note">
            <strong>Calendario de seguimiento</strong><br>
            Las tareas recurrentes aparecen en su fecha prevista aunque la próxima
            instancia todavía no haya sido creada. Cada actividad se identifica por
            color según su estado operativo.
        </div>
        ''',
        unsafe_allow_html=True,
    )

    month_names = [
        "enero","febrero","marzo","abril","mayo","junio",
        "julio","agosto","septiembre","octubre","noviembre","diciembre"
    ]

    month_events = calendar_events_for_month(tasks, month_start)
    flat_events = [
        (day_key, event)
        for day_key, event_list in month_events.items()
        for event in event_list
    ]

    total_month = len(flat_events)
    closed_month = sum(
        1 for _, event in flat_events
        if str(event.get("status") or "") == "Cerrada"
    )
    running_month = sum(
        1 for _, event in flat_events
        if str(event.get("status") or "") in ["En ejecución", "Terminada - espera cierre"]
    )
    overdue_month = sum(
        1 for day_key, event in flat_events
        if day_key < date.today()
        and str(event.get("status") or "") not in ["Cerrada", "Terminada - espera cierre"]
        and event.get("kind") != "recurrence"
    )
    recurrent_month = sum(
        1 for _, event in flat_events
        if event.get("kind") == "recurrence"
    )

    cal_main, cal_side = st.columns([4.15, 1.05], gap="medium")

    with cal_main:
        st.markdown(
            f"### {month_names[month_start.month - 1].capitalize()} {month_start.year}"
        )
        render_month_calendar(tasks, month_start)

    with cal_side:
        st.markdown(
            '''
            <div class="sev-cal-legend">
                <div class="sev-cal-side-title">Estado de las tareas</div>
                <div class="sev-cal-legend-row"><span class="sev-cal-dot" style="background:#1B8A55;"></span>Cerrada / cumplida</div>
                <div class="sev-cal-legend-row"><span class="sev-cal-dot" style="background:#438BC3;"></span>En ejecución / recurrente</div>
                <div class="sev-cal-legend-row"><span class="sev-cal-dot" style="background:#E3A719;"></span>Próxima a vencer</div>
                <div class="sev-cal-legend-row"><span class="sev-cal-dot" style="background:#D45145;"></span>Atrasada / vencida</div>
                <div class="sev-cal-legend-row"><span class="sev-cal-dot" style="background:#A9B5AF;"></span>Programada / sin estado</div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

        st.markdown(
            f'''
            <div class="sev-cal-legend">
                <div class="sev-cal-side-title">Resumen del mes</div>
                <div class="sev-cal-summary">
                    <div class="sev-cal-stat"><div class="n">{total_month}</div><div class="t">Eventos</div></div>
                    <div class="sev-cal-stat"><div class="n">{closed_month}</div><div class="t">Cumplidas</div></div>
                    <div class="sev-cal-stat"><div class="n">{running_month}</div><div class="t">En curso</div></div>
                    <div class="sev-cal-stat"><div class="n">{overdue_month}</div><div class="t">Vencidas</div></div>
                    <div class="sev-cal-stat"><div class="n">{recurrent_month}</div><div class="t">Recurrentes</div></div>
                </div>
            </div>
            ''',
            unsafe_allow_html=True,
        )

        st.caption("Los colores permiten identificar rápidamente qué requiere atención.")

    section(
        "Avisos de finalización",
        "Tareas vencidas, que vencen hoy o dentro de los próximos 7 días",
    )
    due_view = due_alerts(tasks, date.today(), horizon_days=7)

    if due_view.empty:
        st.success(
            "No hay tareas con vencimiento dentro de los próximos 7 días ni tareas vencidas abiertas."
        )
    else:
        overdue_n = int((due_view["Días"] < 0).sum())
        today_n = int((due_view["Días"] == 0).sum())
        soon_n = int(((due_view["Días"] > 0) & (due_view["Días"] <= 7)).sum())

        d1, d2, d3 = st.columns(3)
        d1.metric("Vencidas", overdue_n)
        d2.metric("Vencen hoy", today_n)
        d3.metric("Próximos 7 días", soon_n)

        st.dataframe(
            due_view.drop(columns=["Días"]),
            hide_index=True,
            use_container_width=True,
        )

    section(
        "Tareas rutinarias",
        "Consulta de actividades configuradas con recurrencia",
    )
    recurrent_view = tasks[
        tasks["recurrence"].notna()
        & (tasks["recurrence"].astype(str) != "No")
    ].copy()

    if recurrent_view.empty:
        st.info("No hay tareas rutinarias configuradas.")
    else:
        recurrent_view["Próxima referencia"] = (
            pd.to_datetime(recurrent_view["due_date"], errors="coerce")
            .dt.strftime("%d/%m/%Y")
            .fillna("—")
        )
        with st.expander(
            f"Ver {len(recurrent_view)} tarea(s) recurrente(s)",
            expanded=False,
        ):
            st.dataframe(
                recurrent_view[
                    ["code","title","assignee","recurrence",
                     "recurrence_day","Próxima referencia","status"]
                ].rename(
                    columns={
                        "code":"Código",
                        "title":"Tarea",
                        "assignee":"Responsable",
                        "recurrence":"Recurrencia",
                        "recurrence_day":"Día",
                        "status":"Estado",
                    }
                ),
                hide_index=True,
                use_container_width=True,
            )

    section(
        "Gantt de cumplimiento",
        "Cronograma, avance y demora entre asignación y aceptación",
    )

    gantt = tasks.copy()
    gantt["Teórico %"] = gantt.apply(theoretical, axis=1)
    gantt["Semáforo"] = gantt.apply(traffic_light, axis=1)

    acceptance_rows = gantt.apply(acceptance_metrics, axis=1)
    acceptance_hours = pd.Series(
        [item["acceptance_hours"] for item in acceptance_rows
         if item["acceptance_hours"] is not None],
        dtype=float,
    )
    accepted_hours = pd.Series(
        [item["acceptance_hours"] for item in acceptance_rows
         if item["accepted"] and item["acceptance_hours"] is not None],
        dtype=float,
    )
    pending_acceptance = int(
        sum(1 for item in acceptance_rows if not item["accepted"])
    )
    accepted_24h = int(
        sum(
            1 for item in acceptance_rows
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
        "Demora media",
        "—" if accepted_hours.empty else f"{accepted_hours.mean():.1f} h",
    )
    a3.metric(
        "Aceptadas ≤24 h",
        "—" if total_accepted == 0 else f"{accepted_24h}/{total_accepted}",
    )
    a4.metric(
        "Mayor demora",
        "—" if acceptance_hours.empty else (
            f"{acceptance_hours.max():.1f} h"
            if acceptance_hours.max() < 24
            else f"{acceptance_hours.max()/24:.1f} días"
        ),
    )

    with st.expander("Abrir vista Gantt", expanded=False):
        gantt_chart(gantt)


# ============================================================
# RECURRENTES
# ============================================================

elif page == "Recurrentes":

    section(
        "Tareas recurrentes",
        "Programación automática, fecha real de finalización y cumplimiento anual",
    )

    recurrent = tasks[
        tasks["recurrence"].notna()
        & (tasks["recurrence"].astype(str) != "No")
    ].copy()

    if recurrent.empty:
        st.info("No existen tareas recurrentes.")

    else:
        def _recurrent_expected_date(row):
            due = _safe_date(row.get("due_date"))
            if due is not None:
                return due.strftime("%d/%m/%Y")

            try:
                day = int(row.get("recurrence_day"))
            except Exception:
                return "—"

            ref = None
            for field in ["requested", "created_at", "start_date"]:
                ref = _safe_date(row.get(field))
                if ref is not None:
                    break

            if ref is None:
                ref = date.today()

            last_day = calendar.monthrange(ref.year, ref.month)[1]
            expected = date(ref.year, ref.month, min(day, last_day))
            return expected.strftime("%d/%m/%Y")

        recurrent["Final prevista"] = recurrent.apply(
            _recurrent_expected_date,
            axis=1,
        )
        recurrent["Finalizada"] = (
            pd.to_datetime(recurrent["finished_at"], errors="coerce")
            .fillna(pd.to_datetime(recurrent["closed_at"], errors="coerce"))
            .dt.strftime("%d/%m/%Y")
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
                    "Final prevista",
                    "Finalizada",
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

        # ----------------------------------------------------
        # CONTROL ANUAL DE TAREAS MENSUALES
        # ----------------------------------------------------
        section(
            "Cumplimiento anual · tareas mensuales",
            "Cada mes muestra fecha prevista, fecha real de finalización y cumplimiento",
        )

        monthly_masters = tasks[
            (tasks["recurrence"] == "Mensual")
            & tasks["recurrence_parent_id"].isna()
        ].copy()

        if monthly_masters.empty:
            st.info("No hay tareas maestras configuradas con recurrencia mensual.")
        else:
            monthly_masters = monthly_masters.sort_values(
                ["assignee", "title"]
            ).copy()

            monthly_masters["_label"] = (
                monthly_masters["title"].astype(str)
                + " · "
                + monthly_masters["assignee"].astype(str)
            )

            sel1, sel2 = st.columns([3.2, 1.0])
            selected_master_id = sel1.selectbox(
                "Tarea mensual",
                monthly_masters["id"].astype(int).tolist(),
                format_func=lambda task_id: monthly_masters.loc[
                    monthly_masters["id"].astype(int) == int(task_id),
                    "_label",
                ].iloc[0],
                key="annual_monthly_task_v218",
            )

            available_years = list(
                range(
                    min(
                        date.today().year,
                        pd.to_datetime(
                            monthly_masters["due_date"], errors="coerce"
                        ).dt.year.dropna().astype(int).min()
                        if pd.to_datetime(
                            monthly_masters["due_date"], errors="coerce"
                        ).notna().any()
                        else date.today().year,
                    ),
                    date.today().year + 2,
                )
            )
            selected_year = sel2.selectbox(
                "Año",
                available_years,
                index=available_years.index(date.today().year)
                if date.today().year in available_years
                else len(available_years) - 1,
                key="annual_monthly_year_v218",
            )

            master = monthly_masters.loc[
                monthly_masters["id"].astype(int) == int(selected_master_id)
            ].iloc[0]

            annual = recurring_monthly_year_control(
                c,
                master,
                int(selected_year),
            )

            if annual.empty:
                st.warning("No fue posible construir el calendario anual de esta tarea.")
            else:
                month_names_short = [
                    "Enero", "Febrero", "Marzo", "Abril",
                    "Mayo", "Junio", "Julio", "Agosto",
                    "Septiembre", "Octubre", "Noviembre", "Diciembre",
                ]

                due_until_today = annual[
                    annual["Prevista"].apply(
                        lambda d: isinstance(d, date) and d <= date.today()
                    )
                    & (annual["Estado anual"] != "— No aplica")
                ].copy()

                completed = int(
                    due_until_today["Estado anual"]
                    .astype(str)
                    .str.contains("Cumplida", regex=False)
                    .sum()
                )
                on_time = int(
                    due_until_today["Estado anual"]
                    .astype(str)
                    .str.contains("🟢 Cumplida", regex=False)
                    .sum()
                )
                late = int(
                    due_until_today["Estado anual"]
                    .astype(str)
                    .str.contains("fora do prazo", regex=False)
                    .sum()
                )
                overdue_or_missing = int(
                    due_until_today["Estado anual"]
                    .astype(str)
                    .str.contains("Vencida|Sem registro", regex=True)
                    .sum()
                )
                expected = len(due_until_today)
                compliance_pct = (
                    round(100 * on_time / expected)
                    if expected > 0
                    else 0
                )

                r1, r2, r3, r4, r5 = st.columns(5)
                r1.metric("Cumplimiento anual", f"{compliance_pct}%")
                r2.metric("Previstas hasta hoy", expected)
                r3.metric("En plazo", on_time)
                r4.metric("Fuera de plazo", late)
                r5.metric("Vencidas / sin registro", overdue_or_missing)

                st.markdown(
                    f'<div class="sev-annual-note"><b>{master["title"]}</b> · '
                    f'Responsável: {master["assignee"]} · '
                    f'Dia de referência: {int(master["recurrence_day"] or _safe_date(master["due_date"]).day)}</div>',
                    unsafe_allow_html=True,
                )

                cards = []
                for _, row in annual.iterrows():
                    month_idx = int(row["Mes nº"]) - 1
                    month_name = month_names_short[month_idx]
                    planned = row["Prevista"]
                    finished = row["Finalizada"]
                    planned_text = planned.strftime("%d/%m/%Y") if isinstance(planned, date) else "—"
                    finished_text = finished.strftime("%d/%m/%Y") if isinstance(finished, date) else "—"
                    status_text = str(row["Estado anual"])
                    cls = str(row["Clase"])

                    if finished_text != "—":
                        detail = f"Prevista {planned_text} · Finalizada {finished_text}"
                    else:
                        detail = f"Prevista {planned_text} · Finalizada —"

                    cards.append(
                        f"""
                        <div class="sev-month-card sev-month-{cls}">
                            <div class="sev-month-name">{month_name}</div>
                            <div class="sev-month-status">{status_text}</div>
                            <div class="sev-month-date">{detail}</div>
                        </div>
                        """
                    )

                st.markdown(
                    '<div class="sev-year-grid">'
                    + "".join(cards)
                    + "</div>",
                    unsafe_allow_html=True,
                )

                st.caption(
                    "🟢 concluída no prazo · 🟡 concluída após a data prevista · "
                    "🔴 vencida sem conclusão · 🔵 aberta/programada · ⚪ sem registro histórico."
                )

                detail = annual.copy()
                detail["Mes"] = detail["Mes nº"].apply(
                    lambda m: month_names_short[int(m) - 1]
                )
                detail["Fecha prevista"] = detail["Prevista"].apply(
                    lambda d: d.strftime("%d/%m/%Y") if isinstance(d, date) else "—"
                )
                detail["Fecha de término"] = detail["Finalizada"].apply(
                    lambda d: d.strftime("%d/%m/%Y") if isinstance(d, date) else "—"
                )
                detail["Desvío (días)"] = detail["Desvío días"].apply(
                    lambda x: "—" if pd.isna(x) else int(x)
                )

                with st.expander("Ver histórico anual detallado", expanded=False):
                    st.dataframe(
                        detail[
                            [
                                "Mes",
                                "Fecha prevista",
                                "Fecha de término",
                                "Estado anual",
                                "Desvío (días)",
                                "Código",
                                "Estado tarefa",
                                "Avance %",
                            ]
                        ].rename(
                            columns={
                                "Estado anual": "Cumplimiento",
                                "Estado tarefa": "Estado actual",
                                "Avance %": "Avance %",
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
# USUARIOS · V2.29
# ============================================================

elif page == "Usuarios":

    section(
        "Usuarios",
        "Alta, edición y categorización de usuarios del sistema",
    )

    ROLES_USUARIO = ["Administrador", "Responsable"]

    # --------------------------------------------------------
    # RESUMEN
    # --------------------------------------------------------
    all_people = pd.read_sql_query(
        """
        SELECT
            p.id,
            p.name,
            p.email,
            COALESCE(p.role, 'Responsable') AS role,
            COALESCE(p.active, 1) AS active,
            COUNT(t.id) AS tareas
        FROM people p
        LEFT JOIN tasks t ON t.assignee_id = p.id
        GROUP BY p.id, p.name, p.email, p.role, p.active
        ORDER BY p.name
        """,
        c,
    )

    total_users = len(all_people)
    active_users = int((all_people["active"] == 1).sum()) if not all_people.empty else 0
    admin_users = int(
        ((all_people["active"] == 1) & (all_people["role"] == "Administrador")).sum()
    ) if not all_people.empty else 0
    responsible_users = int(
        ((all_people["active"] == 1) & (all_people["role"] == "Responsable")).sum()
    ) if not all_people.empty else 0

    u1, u2, u3, u4 = st.columns(4)
    u1.metric("Usuarios", total_users)
    u2.metric("Activos", active_users)
    u3.metric("Administradores", admin_users)
    u4.metric("Responsables", responsible_users)

    # --------------------------------------------------------
    # ALTA DE USUARIO
    # --------------------------------------------------------
    st.markdown("#### Crear nuevo usuario")

    with st.form("new_user_v229", clear_on_submit=True):
        n1, n2 = st.columns(2)
        new_user_name = n1.text_input(
            "Nombre y apellido",
            placeholder="Ej.: Juan Pérez",
        )
        new_user_email = n2.text_input(
            "Correo electrónico",
            placeholder="usuario@sevion.com.br",
        )

        n3, n4 = st.columns(2)
        new_user_role = n3.selectbox(
            "Categoría",
            ROLES_USUARIO,
            index=1,
        )
        new_user_active = n4.checkbox(
            "Usuario activo",
            value=True,
        )

        create_user = st.form_submit_button(
            "Crear usuario",
            type="primary",
            use_container_width=True,
        )

    if create_user:
        clean_name = new_user_name.strip()
        clean_email = new_user_email.strip().lower()

        if not clean_name:
            st.error("Ingresá el nombre del usuario.")
        elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean_email):
            st.error("Ingresá un correo electrónico válido.")
        else:
            exists = c.execute(
                "SELECT id FROM people WHERE LOWER(email) = LOWER(?)",
                (clean_email,),
            ).fetchone()

            if exists:
                st.error("Ya existe un usuario con ese correo electrónico.")
            else:
                c.execute(
                    """
                    INSERT INTO people(name, email, active, role)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        clean_name,
                        clean_email,
                        1 if new_user_active else 0,
                        new_user_role,
                    ),
                )
                c.commit()

                new_id = c.execute(
                    "SELECT id FROM people WHERE LOWER(email)=LOWER(?)",
                    (clean_email,),
                ).fetchone()["id"]

                log_event(
                    c,
                    0,
                    "user_created",
                    "Administrador",
                    f"Usuario creado: {clean_name} · {clean_email} · {new_user_role} · id {new_id}",
                )

                st.success(f"Usuario {clean_name} creado correctamente.")
                st.rerun()

    # --------------------------------------------------------
    # LISTADO
    # --------------------------------------------------------
    st.markdown("#### Usuarios registrados")

    if all_people.empty:
        st.info("No hay usuarios registrados.")
    else:
        user_display = all_people.copy()
        user_display["Estado"] = user_display["active"].map(
            {1: "Activo", 0: "Inactivo"}
        ).fillna("Inactivo")
        user_display = user_display.rename(
            columns={
                "name": "Nombre",
                "email": "Correo",
                "role": "Categoría",
                "tareas": "Tareas",
            }
        )

        st.dataframe(
            user_display[
                ["Nombre", "Correo", "Categoría", "Estado", "Tareas"]
            ],
            hide_index=True,
            use_container_width=True,
        )

    # --------------------------------------------------------
    # EDICIÓN
    # --------------------------------------------------------
    if not all_people.empty:
        st.markdown("#### Editar usuario")

        user_ids = all_people["id"].astype(int).tolist()
        user_labels = {
            int(row["id"]): f"{row['name']} · {row['email']}"
            for _, row in all_people.iterrows()
        }

        selected_user_id = st.selectbox(
            "Seleccionar usuario",
            user_ids,
            format_func=lambda user_id: user_labels.get(
                int(user_id), str(user_id)
            ),
            key="user_edit_selector_v229",
        )

        current_user = all_people.loc[
            all_people["id"] == int(selected_user_id)
        ].iloc[0]

        current_role = (
            str(current_user["role"])
            if str(current_user["role"]) in ROLES_USUARIO
            else "Responsable"
        )

        with st.form(f"edit_user_v229_{int(selected_user_id)}"):
            e1, e2 = st.columns(2)
            edit_name = e1.text_input(
                "Nombre y apellido",
                value=str(current_user["name"]),
            )
            edit_email = e2.text_input(
                "Correo electrónico",
                value=str(current_user["email"]),
            )

            e3, e4 = st.columns(2)
            edit_role = e3.selectbox(
                "Categoría",
                ROLES_USUARIO,
                index=ROLES_USUARIO.index(current_role),
            )
            edit_active = e4.checkbox(
                "Usuario activo",
                value=bool(int(current_user["active"])),
            )

            save_user = st.form_submit_button(
                "Guardar cambios",
                type="primary",
                use_container_width=True,
            )

        if save_user:
            clean_name = edit_name.strip()
            clean_email = edit_email.strip().lower()

            if not clean_name:
                st.error("El nombre no puede quedar vacío.")
            elif not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", clean_email):
                st.error("Ingresá un correo electrónico válido.")
            else:
                duplicate = c.execute(
                    """
                    SELECT id
                    FROM people
                    WHERE LOWER(email) = LOWER(?)
                      AND id <> ?
                    """,
                    (clean_email, int(selected_user_id)),
                ).fetchone()

                if duplicate:
                    st.error("Ese correo ya pertenece a otro usuario.")
                else:
                    # Nunca dejar el sistema sin un administrador activo.
                    active_admins = c.execute(
                        """
                        SELECT COUNT(*) AS n
                        FROM people
                        WHERE active = 1
                          AND COALESCE(role, 'Responsable') = 'Administrador'
                        """
                    ).fetchone()["n"]

                    was_active_admin = (
                        int(current_user["active"]) == 1
                        and current_role == "Administrador"
                    )
                    will_be_active_admin = (
                        edit_active and edit_role == "Administrador"
                    )

                    if (
                        was_active_admin
                        and not will_be_active_admin
                        and int(active_admins) <= 1
                    ):
                        st.error(
                            "Debe quedar al menos un Administrador activo. "
                            "Creá o promovê otro administrador antes de cambiar este usuario."
                        )
                    else:
                        c.execute(
                            """
                            UPDATE people
                            SET name = ?, email = ?, role = ?, active = ?
                            WHERE id = ?
                            """,
                            (
                                clean_name,
                                clean_email,
                                edit_role,
                                1 if edit_active else 0,
                                int(selected_user_id),
                            ),
                        )
                        c.commit()

                        log_event(
                            c,
                            0,
                            "user_edited",
                            "Administrador",
                            (
                                f"Usuario editado: {clean_name} · {clean_email} · "
                                f"{edit_role} · "
                                f"{'Activo' if edit_active else 'Inactivo'}"
                            ),
                        )

                        st.success("Usuario actualizado correctamente.")
                        st.rerun()

        st.caption(
            "Los usuarios con historial no se eliminan: pueden quedar inactivos "
            "para conservar la trazabilidad de tareas, eventos y correos."
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

    section("Avisos y seguimiento", "Diagnóstico SMTP, prueba de correo y recordatorios automáticos")
    settings = get_mail_settings(BASE_DIR)
    report = mail_configuration_report(BASE_DIR)
    m1,m2,m3 = st.columns(3)
    m1.metric("SMTP", "Configurado" if settings.configured else "Pendiente")
    m2.metric("Correo administrador", settings.admin_email or "Pendiente")
    m3.metric("URL pública", "Configurada" if settings.app_base_url else "Pendiente")

    if report["missing"]:
        st.error("No se puede enviar correo porque faltan estas variables: " + ", ".join(report["missing"]))
        st.caption("En Streamlit Community Cloud cargalas en Manage app → Settings → Secrets. No guardes contraseñas en GitHub.")
    else:
        st.success(f"Configuración detectada: {report['host']}:{report['port']} · remitente {report['sender_email']}")

    with st.expander("Configuración esperada en Streamlit Secrets", expanded=bool(report["missing"])):
        example = (
            'SMTP_HOST = "smtp.gmail.com"\n'
            'SMTP_PORT = 587\n'
            f'SMTP_USERNAME = "{ADMIN_EMAIL}"\n'
            'SMTP_PASSWORD = "TU_CONTRASEÑA_DE_APLICACION"\n'
            f'SMTP_SENDER_EMAIL = "{ADMIN_EMAIL}"\n'
            'SMTP_SENDER_NAME = "SEV · Control de Tareas"\n'
            'SMTP_USE_TLS = true\n'
            'SMTP_USE_SSL = false\n'
            f'ADMIN_EMAIL = "{ADMIN_EMAIL}"\n'
            'APP_BASE_URL = "https://sev-control-tareas.streamlit.app"'
        )
        st.code(example, language="toml")
        st.caption("El ejemplo usa Gmail/Google Workspace. Si Sevion utiliza otro proveedor, sustituí HOST, puerto y método de seguridad.")

    t1,t2 = st.columns([1.5,1.0])
    test_recipient = t1.text_input("Enviar correo de prueba a", value=ADMIN_EMAIL, key="test_email_recipient_v211")
    if t2.button("Enviar prueba SMTP", type="primary", use_container_width=True, key="test_smtp_v211"):
        ok, detail = send_test_email(test_recipient.strip(), BASE_DIR)
        if ok: st.success("Correo de prueba enviado correctamente.")
        else: st.error(f"No se pudo enviar: {detail}")

    if st.button("Ejecutar revisión de avisos ahora", use_container_width=True, key="run_reminders_v211"):
        result = run_reminders(DB)
        st.success(f"Revisión terminada · revisadas {result['checked']} · enviadas {result['sent']} · errores {result['failed']} · omitidas {result['skipped']}")

    section("Próximos vencimientos", "Avisos visibles aunque el correo todavía no esté configurado")
    due_view = due_alerts(tasks, date.today(), horizon_days=7)
    if due_view.empty: st.success("No hay vencimientos abiertos dentro del horizonte de 7 días.")
    else: st.dataframe(due_view.drop(columns=["Días"]), hide_index=True, use_container_width=True)

    section("Historial de correos", "Registro de asignaciones, avances, recordatorios y cierres")
    email_history = pd.read_sql_query("SELECT e.sent_at AS Fecha,t.code AS Código,p.name AS Responsable,e.recipient AS Destinatario,e.email_type AS Tipo,e.status AS Estado,e.detail AS Detalle FROM email_logs e LEFT JOIN tasks t ON t.id=e.task_id LEFT JOIN people p ON p.id=t.assignee_id ORDER BY e.id DESC LIMIT 300", c)
    if email_history.empty: st.info("Todavía no hay correos registrados.")
    else: st.dataframe(email_history, hide_index=True, use_container_width=True, height=520)


# ============================================================
# FINAL
# ============================================================

c.close()

st.divider()

st.caption(
    f"SEV · Control de Tareas · {APP_VERSION}"
)
