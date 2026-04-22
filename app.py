"""
app.py — Atendimentos em Aberto
Sem autenticação. Acesso direto via API Gove.
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
from gove import buscar_atendimentos_abertos

st.set_page_config(
    page_title="Atendimentos em Aberto",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }

.stApp { background-color: #0f1117; }
[data-testid="stSidebar"],
[data-testid="collapsedControl"] { display: none !important; }

/* Topo */
.topo {
    background: linear-gradient(135deg, #1e2130, #252a3d);
    border: 1px solid #2e3450;
    border-radius: 16px;
    padding: 18px 28px;
    margin-bottom: 22px;
    display: flex;
    align-items: center;
    justify-content: space-between;
}
.topo-titulo { font-size: 22px; font-weight: 800; color: #e2e8f0; }
.topo-sub    { font-size: 12px; color: #64748b; margin-top: 3px; }

/* Filtro */
.filtro-box {
    background: #1e2130;
    border: 1px solid #2e3450;
    border-radius: 12px;
    padding: 20px 24px;
    margin-bottom: 22px;
}
.filtro-label {
    font-size: 11px; font-weight: 600; color: #94a3b8;
    text-transform: uppercase; letter-spacing: 1px;
    margin-bottom: 14px;
}

/* KPI cards */
.kpi {
    background: linear-gradient(135deg, #1e2130, #252a3d);
    border: 1px solid #2e3450;
    border-radius: 12px;
    padding: 16px 18px;
    text-align: center;
    box-shadow: 0 4px 14px rgba(0,0,0,0.3);
}
.kpi-lbl { font-size: 11px; color: #8b92a5; text-transform: uppercase;
           letter-spacing: 1px; margin-bottom: 5px; }
.kpi-val { font-size: 28px; font-weight: 800; line-height: 1.1; }
.kpi-sub { font-size: 11px; color: #5c6880; margin-top: 3px; }

/* Inputs */
div[data-testid="stDateInput"] label {
    font-size: 12px; color: #94a3b8; font-weight: 600;
}
div[data-testid="stDateInput"] input {
    background: #0d1117 !important;
    border: 1px solid #2e3450 !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
}
div[data-testid="stTextInput"] label {
    font-size: 12px; color: #94a3b8; font-weight: 600;
}
div[data-testid="stTextInput"] input {
    background: #0d1117 !important;
    border: 1px solid #2e3450 !important;
    color: #e2e8f0 !important;
    border-radius: 8px !important;
    font-size: 13px !important;
}

/* Botões */
div[data-testid="stButton"] button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    height: 42px !important;
    border: 1px solid #2e3450 !important;
    background: #1e2130 !important;
    color: #e2e8f0 !important;
    transition: all 0.2s !important;
}
div[data-testid="stButton"] button:hover {
    border-color: #6366f1 !important;
    color: #a5b4fc !important;
}
.btn-filtrar button {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: white !important;
    border: none !important;
}

/* Tabela */
div[data-testid="stDataFrame"] {
    border: 1px solid #2e3450 !important;
    border-radius: 12px !important;
    overflow: hidden !important;
}
div[data-testid="stDataFrame"] thead th {
    background-color: #13162280 !important;
    color: #94a3b8 !important;
    font-size: 11px !important;
    font-weight: 700 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
    border-bottom: 1px solid #2e3450 !important;
}
div[data-testid="stDataFrame"] tbody td {
    color: #cbd5e1 !important;
    font-size: 13px !important;
    border-bottom: 1px solid #1e2130 !important;
}

/* Live pill */
.live-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: #0d1f0d; border: 1px solid #166534;
    border-radius: 20px; padding: 3px 12px;
    font-size: 11px; font-weight: 600; color: #4ade80;
}
.dot {
    width: 7px; height: 7px; border-radius: 50%;
    background: #22c55e; animation: pulse 2s infinite;
}
@keyframes pulse {
    0%,100%{ opacity:1; transform:scale(1); }
    50%{ opacity:.3; transform:scale(1.5); }
}

/* Sem resultados */
.empty-state {
    text-align: center; padding: 60px 20px;
    color: #64748b; font-size: 15px;
}
.empty-icon { font-size: 48px; margin-bottom: 12px; }

hr { border-color: #2e3450; }
</style>
""", unsafe_allow_html=True)

agora = datetime.now()

# ── Topo ──────────────────────────────────────────────────────────
st.markdown(f"""
<div class="topo">
    <div>
        <div class="topo-titulo">🔴 Atendimentos em Aberto</div>
        <div class="topo-sub">
            Prefeitura de Rio Verde &nbsp;·&nbsp;
            Dados em tempo real via API Gove &nbsp;·&nbsp;
            <span class="live-pill"><span class="dot"></span>AO VIVO</span>
        </div>
    </div>
    <div style="text-align:right; color:#64748b; font-size:12px; line-height:1.8">
        <div>{agora.strftime('%d/%m/%Y')}</div>
        <div style="font-size:16px;font-weight:700;color:#94a3b8">
            {agora.strftime('%H:%M:%S')}
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ── Filtro ────────────────────────────────────────────────────────
st.markdown('<div class="filtro-box">', unsafe_allow_html=True)
st.markdown('<div class="filtro-label">📅 Filtrar por Período de Abertura</div>',
            unsafe_allow_html=True)

cf1, cf2, cf3, cf4, cf5 = st.columns([2, 2, 1, 1, 1])
with cf1:
    data_ini = st.date_input("De", value=date.today() - timedelta(days=30),
                              format="DD/MM/YYYY", label_visibility="visible")
with cf2:
    data_fim = st.date_input("Até", value=date.today(),
                              format="DD/MM/YYYY", label_visibility="visible")
with cf3:
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="btn-filtrar">', unsafe_allow_html=True)
    btn_filtrar = st.button("🔍 Filtrar", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
with cf4:
    st.markdown("<br>", unsafe_allow_html=True)
    btn_hoje = st.button("📅 Hoje", use_container_width=True)
with cf5:
    st.markdown("<br>", unsafe_allow_html=True)
    btn_semana = st.button("📆 Esta semana", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# Atalhos de data
if btn_hoje:
    st.session_state["_ini"] = date.today()
    st.session_state["_fim"] = date.today()
    st.rerun()
if btn_semana:
    seg = date.today() - timedelta(days=date.today().weekday())
    st.session_state["_ini"] = seg
    st.session_state["_fim"] = date.today()
    st.rerun()

_ini = st.session_state.pop("_ini", data_ini)
_fim = st.session_state.pop("_fim", data_fim)

# ── Busca na API ──────────────────────────────────────────────────
if btn_filtrar or btn_hoje or btn_semana or "df_abertos" not in st.session_state:
    with st.spinner("🔄 Consultando API Gove..."):
        df = buscar_atendimentos_abertos(
            data_ini=_ini.strftime("%d/%m/%Y"),
            data_fim=_fim.strftime("%d/%m/%Y"),
        )
    st.session_state["df_abertos"] = df
    st.session_state["_ini_usado"] = _ini
    st.session_state["_fim_usado"] = _fim
else:
    df   = st.session_state["df_abertos"]
    _ini = st.session_state.get("_ini_usado", _ini)
    _fim = st.session_state.get("_fim_usado", _fim)

total = len(df)

# ── KPIs ──────────────────────────────────────────────────────────
col_setor = "Setor"      if "Setor"      in df.columns else None
col_at    = "Atendente"  if "Atendente"  in df.columns else None

total_setores  = df[col_setor].nunique()                              if total and col_setor else 0
sem_atendente  = len(df[df[col_at].isin(["—","-","","None"])])       if total and col_at    else 0
com_atendente  = total - sem_atendente                                if total else 0
pct_com        = f"{com_atendente/total*100:.0f}%"                   if total else "—"

k1, k2, k3, k4 = st.columns(4)
kpis = [
    (k1, "Em Aberto",       f"{total:,}",        "#f59e0b", f"{_ini.strftime('%d/%m')} → {_fim.strftime('%d/%m/%Y')}"),
    (k2, "Setores",         f"{total_setores:,}", "#6366f1", "com atendimentos pendentes"),
    (k3, "Sem Atendente",   f"{sem_atendente:,}", "#ef4444", "aguardando atribuição"),
    (k4, "Com Atendente",   pct_com,              "#22c55e", "dos atendimentos"),
]
for col, lbl, val, cor, sub in kpis:
    with col:
        st.markdown(f"""<div class="kpi">
            <div class="kpi-lbl">{lbl}</div>
            <div class="kpi-val" style="color:{cor}">{val}</div>
            <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabela ────────────────────────────────────────────────────────
if df.empty:
    st.markdown("""
    <div class="empty-state">
        <div class="empty-icon">✅</div>
        <div>Nenhum atendimento em aberto no período selecionado.</div>
        <div style="font-size:13px;margin-top:6px;color:#475569">
            Tente ampliar o período ou clique em Filtrar.
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    # Busca textual
    busca = st.text_input(
        "Buscar",
        placeholder="🔍  Protocolo, contribuinte, setor, atendente...",
        label_visibility="collapsed",
    )

    df_exib = df.copy()
    if busca.strip():
        mask = pd.Series(False, index=df_exib.index)
        for c in df_exib.columns:
            mask |= df_exib[c].astype(str).str.lower()\
                              .str.contains(busca.strip().lower(), na=False)
        df_exib = df_exib[mask]

    # Contador
    txt_filtro = f' · **{len(df_exib):,}** resultado(s) para "{busca}"' if busca.strip() else ""
    st.markdown(f"**{total:,}** atendimento(s) em aberto{txt_filtro}")
    st.markdown("")

    # Tabela
    st.dataframe(
        df_exib,
        use_container_width=True,
        height=min(60 + len(df_exib) * 36, 620),
        hide_index=True,
        column_config={
            "Protocolo":            st.column_config.TextColumn("Protocolo",      width="small"),
            "Atendente":            st.column_config.TextColumn("Atendente",      width="medium"),
            "Nome do Contribuinte": st.column_config.TextColumn("Contribuinte",   width="medium"),
            "Telefone":             st.column_config.TextColumn("Telefone",       width="small"),
            "Setor":                st.column_config.TextColumn("Setor",          width="large"),
            "Tipo de Protocolo":    st.column_config.TextColumn("Tipo",           width="medium"),
            "Aberto em":            st.column_config.TextColumn("Aberto em",      width="small"),
            "Status":               st.column_config.TextColumn("Status",         width="small"),
        },
    )

    # Exportar
    st.markdown("")
    csv = df_exib.to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button(
        "⬇️  Exportar CSV",
        data=csv,
        file_name=f"abertos_{date.today().strftime('%d%m%Y')}.csv",
        mime="text/csv",
    )

# ── Rodapé ────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    f"🕒 Última consulta: {agora.strftime('%d/%m/%Y %H:%M:%S')} "
    "· Cache de 5 minutos · API Gove Digital · "
    "Prefeitura Municipal de Rio Verde"
)
