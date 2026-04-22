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

.topo {
    background: linear-gradient(135deg, #1e2130, #252a3d);
    border: 1px solid #2e3450; border-radius: 16px;
    padding: 18px 28px; margin-bottom: 22px;
    display: flex; align-items: center; justify-content: space-between;
}
.topo-titulo { font-size: 22px; font-weight: 800; color: #e2e8f0; }
.topo-sub    { font-size: 12px; color: #64748b; margin-top: 3px; }

.filtro-box {
    background: #1e2130; border: 1px solid #2e3450;
    border-radius: 12px; padding: 20px 24px; margin-bottom: 22px;
}
.filtro-label {
    font-size: 11px; font-weight: 600; color: #94a3b8;
    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 14px;
}

.kpi {
    background: linear-gradient(135deg, #1e2130, #252a3d);
    border: 1px solid #2e3450; border-radius: 12px;
    padding: 16px 18px; text-align: center;
    box-shadow: 0 4px 14px rgba(0,0,0,0.3);
}
.kpi-lbl { font-size: 11px; color: #8b92a5; text-transform: uppercase;
           letter-spacing: 1px; margin-bottom: 5px; }
.kpi-val { font-size: 28px; font-weight: 800; line-height: 1.1; }
.kpi-sub { font-size: 11px; color: #5c6880; margin-top: 3px; }

div[data-testid="stDateInput"] label { font-size: 12px; color: #94a3b8; font-weight: 600; }
div[data-testid="stDateInput"] input {
    background: #0d1117 !important; border: 1px solid #2e3450 !important;
    color: #e2e8f0 !important; border-radius: 8px !important; font-size: 13px !important;
}
div[data-testid="stTextInput"] input {
    background: #0d1117 !important; border: 1px solid #2e3450 !important;
    color: #e2e8f0 !important; border-radius: 8px !important; font-size: 13px !important;
}

div[data-testid="stButton"] button {
    border-radius: 8px !important; font-weight: 600 !important;
    font-size: 13px !important; height: 42px !important;
    transition: all 0.2s !important;
}

div[data-testid="stDataFrame"] {
    border: 1px solid #2e3450 !important; border-radius: 12px !important; overflow: hidden !important;
}
div[data-testid="stDataFrame"] thead th {
    background-color: #13162280 !important; color: #94a3b8 !important;
    font-size: 11px !important; font-weight: 700 !important;
    text-transform: uppercase !important; letter-spacing: 0.5px !important;
}
div[data-testid="stDataFrame"] tbody td {
    color: #cbd5e1 !important; font-size: 13px !important;
    border-bottom: 1px solid #1e2130 !important;
}

.live-pill {
    display: inline-flex; align-items: center; gap: 6px;
    background: #0d1f0d; border: 1px solid #166534;
    border-radius: 20px; padding: 3px 12px;
    font-size: 11px; font-weight: 600; color: #4ade80;
}
.dot { width: 7px; height: 7px; border-radius: 50%; background: #22c55e; animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.3;transform:scale(1.5)} }

.empty-state { text-align: center; padding: 60px 20px; color: #64748b; font-size: 15px; }
.empty-icon  { font-size: 48px; margin-bottom: 12px; }

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
    <div style="text-align:right;color:#64748b;font-size:12px;line-height:1.8">
        <div>{agora.strftime('%d/%m/%Y')}</div>
        <div style="font-size:16px;font-weight:700;color:#94a3b8">{agora.strftime('%H:%M:%S')}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────────────────────────
# Estado das datas (session_state como fonte de verdade)
# ─────────────────────────────────────────────────────────────────
if "ini" not in st.session_state:
    st.session_state["ini"] = date.today() - timedelta(days=30)
if "fim" not in st.session_state:
    st.session_state["fim"] = date.today()

# ── Filtro ────────────────────────────────────────────────────────
st.markdown('<div class="filtro-box">', unsafe_allow_html=True)
st.markdown('<div class="filtro-label">📅 Filtrar por Período de Abertura</div>',
            unsafe_allow_html=True)

cf1, cf2, cf3, cf4, cf5 = st.columns([2, 2, 1, 1, 1])

with cf1:
    nova_ini = st.date_input(
        "De",
        value=st.session_state["ini"],
        format="DD/MM/YYYY",
        key="input_ini",
    )
with cf2:
    nova_fim = st.date_input(
        "Até",
        value=st.session_state["fim"],
        format="DD/MM/YYYY",
        key="input_fim",
    )
with cf3:
    st.markdown("<br>", unsafe_allow_html=True)
    btn_filtrar = st.button("🔍 Filtrar", use_container_width=True, type="primary")
with cf4:
    st.markdown("<br>", unsafe_allow_html=True)
    btn_hoje = st.button("📅 Hoje", use_container_width=True)
with cf5:
    st.markdown("<br>", unsafe_allow_html=True)
    btn_semana = st.button("📆 Esta semana", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Lógica dos botões ─────────────────────────────────────────────
if btn_hoje:
    st.session_state["ini"] = date.today()
    st.session_state["fim"] = date.today()
    st.session_state.pop("df_cache", None)   # força nova busca
    st.rerun()

if btn_semana:
    seg = date.today() - timedelta(days=date.today().weekday())
    st.session_state["ini"] = seg
    st.session_state["fim"] = date.today()
    st.session_state.pop("df_cache", None)
    st.rerun()

if btn_filtrar:
    st.session_state["ini"] = nova_ini
    st.session_state["fim"] = nova_fim
    st.session_state.pop("df_cache", None)   # invalida cache local
    st.rerun()

# Datas confirmadas
ini_usada = st.session_state["ini"]
fim_usada = st.session_state["fim"]

# ── Busca na API ──────────────────────────────────────────────────
cache_key = f"{ini_usada}_{fim_usada}"
if st.session_state.get("df_cache_key") != cache_key or "df_cache" not in st.session_state:
    with st.spinner("🔄 Consultando API Gove..."):
        df = buscar_atendimentos_abertos(
            data_ini=ini_usada.strftime("%d/%m/%Y"),
            data_fim=fim_usada.strftime("%d/%m/%Y"),
        )
    st.session_state["df_cache"]     = df
    st.session_state["df_cache_key"] = cache_key
else:
    df = st.session_state["df_cache"]

total = len(df)

# ── KPIs (seguro para df vazio ou sem colunas) ────────────────────
def safe_nunique(df, col):
    if df.empty or col not in df.columns: return 0
    return int(df[col].nunique())

def safe_count_vazio(df, col):
    if df.empty or col not in df.columns: return 0
    return int(df[col].isin(["—", "-", "", "None", "nan"]).sum())

total_setores = safe_nunique(df, "Setor")
sem_atendente = safe_count_vazio(df, "Atendente")
com_atendente = total - sem_atendente
pct_com       = f"{com_atendente/total*100:.0f}%" if total > 0 else "—"

k1, k2, k3, k4 = st.columns(4)
for col_k, lbl, val, cor, sub in [
    (k1, "Em Aberto",     f"{total:,}",        "#f59e0b",
          f"{ini_usada.strftime('%d/%m')} → {fim_usada.strftime('%d/%m/%Y')}"),
    (k2, "Setores",       f"{total_setores:,}", "#6366f1", "com pendências"),
    (k3, "Sem Atendente", f"{sem_atendente:,}", "#ef4444", "aguardando atribuição"),
    (k4, "Com Atendente", pct_com,              "#22c55e", "dos atendimentos"),
]:
    with col_k:
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
            Selecione outro período e clique em Filtrar.
        </div>
    </div>
    """, unsafe_allow_html=True)
else:
    busca = st.text_input(
        "busca",
        placeholder="🔍  Protocolo, contribuinte, setor, atendente...",
        label_visibility="collapsed",
    )

    df_exib = df.copy()
    if busca.strip():
        mask = pd.Series(False, index=df_exib.index)
        for c in df_exib.columns:
            mask |= df_exib[c].astype(str).str.lower().str.contains(
                busca.strip().lower(), na=False)
        df_exib = df_exib[mask]

    n = len(df_exib)
    txt = f' · **{n:,}** resultado(s) para *"{busca}"*' if busca.strip() else ""
    st.markdown(f"**{total:,}** atendimento(s) em aberto{txt}")
    st.markdown("")

    st.dataframe(
        df_exib,
        use_container_width=True,
        height=min(60 + n * 36, 620),
        hide_index=True,
        column_config={
            "Protocolo":             st.column_config.TextColumn("Protocolo",    width="small"),
            "Atendente":             st.column_config.TextColumn("Atendente",    width="medium"),
            "Nome do Contribuinte":  st.column_config.TextColumn("Contribuinte", width="medium"),
            "Telefone":              st.column_config.TextColumn("Telefone",     width="small"),
            "Setor":                 st.column_config.TextColumn("Setor",        width="large"),
            "Tipo de Protocolo":     st.column_config.TextColumn("Tipo",         width="medium"),
            "Aberto em":             st.column_config.TextColumn("Aberto em",    width="small"),
            "Status":                st.column_config.TextColumn("Status",       width="small"),
        },
    )

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
    "· Cache de 5 minutos · API Gove Digital · Prefeitura Municipal de Rio Verde"
)
