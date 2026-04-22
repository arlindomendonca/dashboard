"""
pages/3_Atendimentos.py — Atendimentos em Aberto
Filtra por período e exibe dados em tempo real da API Gove.
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta
from auth import logado, fazer_logout, is_admin
from gove import buscar_atendimentos_abertos

st.set_page_config(
    page_title="Atendimentos em Aberto",
    page_icon="🔴",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Guard ─────────────────────────────────────────────────────────
if not logado():
    st.switch_page("app.py")
    st.stop()

uid = st.session_state.get("user_id", "")
from auth import usuario_aprovado
if not usuario_aprovado(uid) and not is_admin(uid):
    st.warning("⏳ Conta aguardando aprovação do administrador.")
    if st.button("Sair"):
        fazer_logout()
        st.switch_page("app.py")
    st.stop()

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
    display: flex; justify-content: space-between; align-items: center;
    background: linear-gradient(135deg, #1e2130, #252a3d);
    border: 1px solid #2e3450; border-radius: 14px;
    padding: 16px 24px; margin-bottom: 20px;
}
.topo-titulo { font-size: 20px; font-weight: 800; color: #e2e8f0; }
.topo-sub    { font-size: 12px; color: #64748b; margin-top: 2px; }

/* Filtro */
.filtro-box {
    background: #1e2130; border: 1px solid #2e3450;
    border-radius: 12px; padding: 20px 24px; margin-bottom: 20px;
}
.filtro-titulo { font-size: 13px; font-weight: 600; color: #94a3b8;
                  text-transform: uppercase; letter-spacing: 0.8px;
                  margin-bottom: 14px; }

/* KPI cards */
.kpi {
    background: linear-gradient(135deg, #1e2130, #252a3d);
    border: 1px solid #2e3450; border-radius: 12px;
    padding: 16px 18px; text-align: center;
    box-shadow: 0 4px 14px rgba(0,0,0,0.3);
}
.kpi-lbl { font-size: 11px; color: #8b92a5; text-transform: uppercase;
           letter-spacing: 1px; margin-bottom: 5px; }
.kpi-val { font-size: 26px; font-weight: 800; }
.kpi-sub { font-size: 11px; color: #5c6880; margin-top: 2px; }

/* Inputs */
div[data-testid="stDateInput"] label { font-size: 12px; color: #94a3b8; font-weight: 500; }
div[data-testid="stDateInput"] input {
    background: #0d1117 !important; border: 1px solid #2e3450 !important;
    color: #e2e8f0 !important; border-radius: 8px !important;
    font-size: 13px !important;
}

/* Botão Filtrar */
div[data-testid="stButton"] button[kind="secondary"] {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: white !important; border: none !important;
    border-radius: 8px !important; font-weight: 700 !important;
    font-size: 14px !important; height: 42px !important;
}

/* Tabela */
div[data-testid="stDataFrame"] {
    border: 1px solid #2e3450; border-radius: 12px; overflow: hidden;
}
div[data-testid="stDataFrame"] th {
    background: #1a1d27 !important;
    color: #94a3b8 !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.5px !important;
}
div[data-testid="stDataFrame"] td {
    color: #e2e8f0 !important;
    font-size: 13px !important;
}
div[data-testid="stDataFrame"] tr:hover td {
    background: #1e2130 !important;
}

/* Live pill */
.live-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: #0d1f0d; border: 1px solid #166534;
    border-radius: 20px; padding: 4px 12px;
    font-size: 11px; font-weight: 600; color: #4ade80;
}
.dot { width: 7px; height: 7px; border-radius: 50%; background: #22c55e;
       animation: pulse 2s infinite; }
@keyframes pulse {
    0%,100%{ opacity:1; transform:scale(1); }
    50%{ opacity:.3; transform:scale(1.5); }
}

hr { border-color: #2e3450; }
</style>
""", unsafe_allow_html=True)

# ── Dados da sessão ───────────────────────────────────────────────
nome  = st.session_state.get("user_nome", "Usuário")
email = st.session_state.get("user_email", "")

# ── Topo ─────────────────────────────────────────────────────────
from datetime import datetime
agora = datetime.now()

ct1, ct2 = st.columns([5, 1])
with ct1:
    st.markdown(f"""
    <div class="topo">
        <div>
            <div class="topo-titulo">🔴 Atendimentos em Aberto</div>
            <div class="topo-sub">
                👤 {nome} &nbsp;·&nbsp; {email} &nbsp;·&nbsp;
                <span class="live-pill">
                    <span class="dot"></span> AO VIVO
                </span>
                &nbsp; Atualizado: {agora.strftime('%d/%m/%Y %H:%M:%S')}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with ct2:
    st.markdown("<br>", unsafe_allow_html=True)
    if is_admin(uid):
        if st.button("⚙️ Admin", use_container_width=True):
            st.switch_page("pages/2_Admin.py")
    if st.button("🚪 Sair", use_container_width=True):
        fazer_logout()
        st.switch_page("app.py")

# ── Filtro por data ───────────────────────────────────────────────
st.markdown('<div class="filtro-box">', unsafe_allow_html=True)
st.markdown('<div class="filtro-titulo">📅 Filtrar por Período de Abertura</div>',
            unsafe_allow_html=True)

cf1, cf2, cf3, cf4 = st.columns([2, 2, 1, 1])
with cf1:
    data_ini = st.date_input(
        "De",
        value=date.today() - timedelta(days=30),
        format="DD/MM/YYYY",
    )
with cf2:
    data_fim = st.date_input(
        "Até",
        value=date.today(),
        format="DD/MM/YYYY",
    )
with cf3:
    st.markdown("<br>", unsafe_allow_html=True)
    btn_filtrar = st.button("🔍 Filtrar", use_container_width=True)
with cf4:
    st.markdown("<br>", unsafe_allow_html=True)
    btn_hoje = st.button("📅 Hoje", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# Atalho "Hoje"
if btn_hoje:
    st.session_state["_ini"] = date.today()
    st.session_state["_fim"] = date.today()
    st.rerun()

# Usa datas da sessão se existirem (para o atalho)
_ini = st.session_state.pop("_ini", data_ini)
_fim = st.session_state.pop("_fim", data_fim)

# ── Busca na API ──────────────────────────────────────────────────
executar = btn_filtrar or ("df_abertos" not in st.session_state)

if btn_filtrar or btn_hoje or executar:
    with st.spinner("🔄 Consultando API Gove..."):
        df = buscar_atendimentos_abertos(
            data_ini=_ini.strftime("%d/%m/%Y"),
            data_fim=_fim.strftime("%d/%m/%Y"),
        )
    st.session_state["df_abertos"]  = df
    st.session_state["filtro_ini"]  = _ini
    st.session_state["filtro_fim"]  = _fim
else:
    df   = st.session_state.get("df_abertos", pd.DataFrame())
    _ini = st.session_state.get("filtro_ini", _ini)
    _fim = st.session_state.get("filtro_fim", _fim)

# ── KPIs ──────────────────────────────────────────────────────────
total = len(df)

if total > 0:
    # Conta por setor
    col_setor = "Setor" if "Setor" in df.columns else None
    total_setores = df[col_setor].nunique() if col_setor else 0

    # Conta por atendente
    col_at = "Atendente" if "Atendente" in df.columns else None
    sem_atendente = len(df[df[col_at].isin(["—", "", "-", "None"])]) if col_at else 0

k1, k2, k3, k4 = st.columns(4)
with k1:
    st.markdown(f"""<div class="kpi">
        <div class="kpi-lbl">Em Aberto</div>
        <div class="kpi-val" style="color:#f59e0b">{total:,}</div>
        <div class="kpi-sub">{_ini.strftime('%d/%m')} a {_fim.strftime('%d/%m/%Y')}</div>
    </div>""", unsafe_allow_html=True)
with k2:
    val2 = total_setores if total > 0 else "—"
    st.markdown(f"""<div class="kpi">
        <div class="kpi-lbl">Setores</div>
        <div class="kpi-val" style="color:#6366f1">{val2}</div>
        <div class="kpi-sub">setores com pendências</div>
    </div>""", unsafe_allow_html=True)
with k3:
    val3 = sem_atendente if total > 0 else "—"
    st.markdown(f"""<div class="kpi">
        <div class="kpi-lbl">Sem Atendente</div>
        <div class="kpi-val" style="color:#ef4444">{val3}</div>
        <div class="kpi-sub">aguardando atribuição</div>
    </div>""", unsafe_allow_html=True)
with k4:
    pct = f"{(total-sem_atendente)/total*100:.0f}%" if total > 0 else "—"
    st.markdown(f"""<div class="kpi">
        <div class="kpi-lbl">Com Atendente</div>
        <div class="kpi-val" style="color:#22c55e">{pct}</div>
        <div class="kpi-sub">dos atendimentos</div>
    </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ── Tabela ────────────────────────────────────────────────────────
if df.empty:
    st.info("ℹ️ Nenhum atendimento em aberto encontrado no período selecionado.")
else:
    # Busca textual rápida
    busca = st.text_input(
        "🔍 Buscar na tabela",
        placeholder="Protocolo, nome, setor, atendente...",
        label_visibility="collapsed",
    )

    df_exib = df.copy()
    if busca.strip():
        mask = pd.Series(False, index=df_exib.index)
        for col in df_exib.columns:
            mask |= df_exib[col].astype(str).str.lower().str.contains(
                busca.strip().lower(), na=False)
        df_exib = df_exib[mask]

    st.markdown(f"**{len(df_exib):,} atendimento(s)** "
                f"{'· filtrado' if busca.strip() else ''}")

    st.dataframe(
        df_exib,
        use_container_width=True,
        height=min(60 + len(df_exib) * 36, 600),
        hide_index=True,
        column_config={
            "Protocolo":           st.column_config.TextColumn("Protocolo", width="small"),
            "Atendente":           st.column_config.TextColumn("Atendente", width="medium"),
            "Nome do Contribuinte":st.column_config.TextColumn("Contribuinte", width="medium"),
            "Telefone":            st.column_config.TextColumn("Telefone", width="small"),
            "Setor":               st.column_config.TextColumn("Setor", width="large"),
            "Tipo de Protocolo":   st.column_config.TextColumn("Tipo", width="medium"),
            "Aberto em":           st.column_config.TextColumn("Aberto em", width="small"),
            "Status":              st.column_config.TextColumn("Status", width="small"),
        },
    )

    # Exportar CSV
    st.markdown("")
    csv = df_exib.to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button(
        label="⬇️ Exportar CSV",
        data=csv,
        file_name=f"atendimentos_abertos_{date.today().strftime('%d%m%Y')}.csv",
        mime="text/csv",
    )

# ── Rodapé ────────────────────────────────────────────────────────
st.markdown("---")
st.caption(
    f"🕒 Dados carregados em: {agora.strftime('%d/%m/%Y %H:%M:%S')} · "
    "Cache de 5 minutos · API Gove Digital"
)
