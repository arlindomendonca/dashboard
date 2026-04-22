"""
app.py — Gestão de Atendimentos (página principal)
Entry point do sistema. Contém a página de atendimentos diretamente.
"""
import streamlit as st
import pandas as pd
from datetime import date, timedelta, datetime
from gove import buscar_atendimentos
from supabase_client import integrar_tudo

st.set_page_config(
    page_title="Gestão de Atendimentos",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

import components.header as header
header.render("atendimentos")

agora = datetime.now()

# ─────────────────────────────────────────────
# Estado inicial
# ─────────────────────────────────────────────
if "ini" not in st.session_state:
    st.session_state["ini"] = date.today() - timedelta(days=30)
if "fim" not in st.session_state:
    st.session_state["fim"] = date.today()
if "protocolo_busca" not in st.session_state:
    st.session_state["protocolo_busca"] = ""
if "apenas_abertos" not in st.session_state:
    st.session_state["apenas_abertos"] = True

# ─────────────────────────────────────────────
# Filtros
# ─────────────────────────────────────────────
st.markdown('<div class="filtro-box">', unsafe_allow_html=True)
st.markdown('<div class="sec-label">🔍 Filtros</div>', unsafe_allow_html=True)

fc1, fc2, fc3, fc4 = st.columns([2, 2, 3, 1])
with fc1:
    nova_ini = st.date_input("De", value=st.session_state["ini"],
                              format="DD/MM/YYYY", key="w_ini")
with fc2:
    nova_fim = st.date_input("Até", value=st.session_state["fim"],
                              format="DD/MM/YYYY", key="w_fim")
with fc3:
    protocolo_input = st.text_input(
        "Protocolo",
        value=st.session_state["protocolo_busca"],
        placeholder="Ex: 8274553  —  deixe vazio para listar todos",
        key="w_protocolo",
    )
with fc4:
    st.markdown("<br>", unsafe_allow_html=True)
    apenas_abertos = st.checkbox("Só abertos",
                                  value=st.session_state["apenas_abertos"],
                                  key="w_abertos")

fb1, fb2, fb3, _ = st.columns([1, 1, 1, 4])
with fb1:
    btn_filtrar = st.button("🔍 Filtrar", use_container_width=True, type="primary")
with fb2:
    btn_hoje    = st.button("📅 Hoje", use_container_width=True)
with fb3:
    btn_semana  = st.button("📆 Esta semana", use_container_width=True)

st.markdown('</div>', unsafe_allow_html=True)

# ── Atalhos ───────────────────────────────────────────────────────
if btn_hoje:
    st.session_state.update({"ini": date.today(), "fim": date.today()})
    st.session_state.pop("df_cache", None)
    st.rerun()

if btn_semana:
    seg = date.today() - timedelta(days=date.today().weekday())
    st.session_state.update({"ini": seg, "fim": date.today()})
    st.session_state.pop("df_cache", None)
    st.rerun()

if btn_filtrar:
    st.session_state.update({
        "ini":              nova_ini,
        "fim":              nova_fim,
        "protocolo_busca":  protocolo_input.strip(),
        "apenas_abertos":   apenas_abertos,
    })
    st.session_state.pop("df_cache", None)
    st.rerun()

ini_usada    = st.session_state["ini"]
fim_usada    = st.session_state["fim"]
prot_usada   = st.session_state["protocolo_busca"]
abertos_flag = st.session_state["apenas_abertos"]

# ── Debug (colapsado) ─────────────────────────────────────────────
with st.expander("🔧 Diagnóstico da API", expanded=False):
    debug_mode = st.checkbox("Ativar debug (mostra JSON bruto)", value=False,
                              key="debug_mode")
    if st.session_state.get("debug_mode"):
        st.session_state.pop("df_cache", None)
debug_mode = st.session_state.get("debug_mode", False)

# ─────────────────────────────────────────────
# Busca (cache por chave)
# ─────────────────────────────────────────────
cache_key = f"{ini_usada}_{fim_usada}_{prot_usada}_{abertos_flag}"
if st.session_state.get("_cache_key") != cache_key or "df_cache" not in st.session_state:
    with st.spinner("🔄 Consultando API Gove..."):
        df, parsed = buscar_atendimentos(
            data_ini=None if prot_usada else ini_usada.strftime("%d/%m/%Y"),
            data_fim=None if prot_usada else fim_usada.strftime("%d/%m/%Y"),
            protocolo=prot_usada or None,
            apenas_abertos=abertos_flag,
            debug=debug_mode,
        )
    st.session_state["df_cache"]   = df
    st.session_state["raw_cache"]  = parsed
    st.session_state["_cache_key"] = cache_key
else:
    df     = st.session_state["df_cache"]
    parsed = st.session_state["raw_cache"]

total = len(df)

# ─────────────────────────────────────────────
# KPIs
# ─────────────────────────────────────────────
def _safe_nunique(df, col):
    if df.empty or col not in df.columns: return 0
    return int(df[col].astype(str).replace({"—": "", "": "<null>"}).nunique())

def _safe_count(df, col, vazio={"—", "-", "", "None", "nan"}):
    if df.empty or col not in df.columns: return 0
    return int(df[col].astype(str).isin(vazio).sum())

total_setores = _safe_nunique(df, "Setor")
sem_atendente = _safe_count(df, "Atendente")
com_atendente = total - sem_atendente
pct_com       = f"{com_atendente/total*100:.0f}%" if total > 0 else "—"

k1, k2, k3, k4 = st.columns(4)
for col_k, lbl, val, cor, sub in [
    (k1, "Atendimentos",  f"{total:,}",         "#f59e0b",
          f"{'abertos · ' if abertos_flag else ''}{ini_usada.strftime('%d/%m')}→{fim_usada.strftime('%d/%m/%Y')}"),
    (k2, "Setores",       f"{total_setores:,}",  "#6366f1", "com pendências"),
    (k3, "Sem Atendente", f"{sem_atendente:,}",  "#ef4444", "aguardando atribuição"),
    (k4, "Com Atendente", pct_com,               "#22c55e", "dos atendimentos"),
]:
    with col_k:
        st.markdown(f"""<div class="kpi">
            <div class="kpi-lbl">{lbl}</div>
            <div class="kpi-val" style="color:{cor}">{val}</div>
            <div class="kpi-sub">{sub}</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# Barra de ação: info + botão integrar
# ─────────────────────────────────────────────
col_info, col_btn = st.columns([5, 1])
with col_info:
    st.markdown(
        f"**{total:,}** atendimento(s) &nbsp;·&nbsp;"
        f"<span class='live-pill'><span class='dot'></span>AO VIVO</span>&nbsp;"
        f"<span style='font-size:12px;color:#64748b'>{agora.strftime('%d/%m/%Y %H:%M:%S')}</span>",
        unsafe_allow_html=True,
    )
with col_btn:
    btn_integrar = st.button(
        "⬆️ Integrar ao Supabase",
        use_container_width=True,
        type="primary",
        disabled=(total == 0),
        help="Salva/atualiza os atendimentos filtrados no Supabase",
    )

# ── Pipeline de integração ────────────────────────────────────────
if btn_integrar and parsed:
    with st.spinner("Integrando dados ao Supabase..."):
        resultado = integrar_tudo(parsed)

    if resultado.get("ok"):
        c  = resultado["contribuintes"]["count"]
        a  = resultado["atendentes"]["count"]
        s  = resultado["setores"]["count"]
        at = resultado["atendimentos"]["count"]
        st.success(
            f"✅ Integração concluída! &nbsp;"
            f"Contribuintes: **{c}** · Atendentes: **{a}** · "
            f"Setores: **{s}** · Atendimentos: **{at}**"
        )
    else:
        for entidade, res in resultado.items():
            if isinstance(res, dict) and not res.get("ok"):
                st.error(f"❌ Erro em **{entidade}**: {res.get('error', '—')}")

st.markdown("")

# ─────────────────────────────────────────────
# Tabela
# ─────────────────────────────────────────────
if df.empty:
    st.markdown("""
    <div style="text-align:center;padding:50px;color:#64748b">
        <div style="font-size:42px;margin-bottom:10px">📭</div>
        <div>Nenhum atendimento encontrado.</div>
        <div style="font-size:13px;margin-top:6px">Ajuste os filtros e clique em Filtrar.</div>
    </div>
    """, unsafe_allow_html=True)
else:
    busca = st.text_input("busca_tabela",
                           placeholder="🔍 Buscar na tabela...",
                           label_visibility="collapsed")
    df_exib = df.copy()
    if busca.strip():
        mask = pd.Series(False, index=df_exib.index)
        for c in df_exib.columns:
            mask |= df_exib[c].astype(str).str.lower().str.contains(
                busca.strip().lower(), na=False)
        df_exib = df_exib[mask]

    st.dataframe(
        df_exib,
        use_container_width=True,
        height=min(60 + len(df_exib) * 36, 620),
        hide_index=True,
        column_config={
            "Protocolo":    st.column_config.TextColumn("Protocolo",    width="small"),
            "Status":       st.column_config.TextColumn("Status",       width="small"),
            "Tipo":         st.column_config.TextColumn("Tipo",         width="medium"),
            "Contribuinte": st.column_config.TextColumn("Contribuinte", width="medium"),
            "Atendente":    st.column_config.TextColumn("Atendente",    width="medium"),
            "Setor":        st.column_config.TextColumn("Setor",        width="large"),
            "Sigla Setor":  st.column_config.TextColumn("Sigla",        width="small"),
            "Aberto em":    st.column_config.TextColumn("Aberto em",    width="small"),
            "Encerrado em": st.column_config.TextColumn("Encerrado em", width="small"),
        },
    )

    st.markdown("")
    csv = df_exib.to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button(
        "⬇️ Exportar CSV", data=csv,
        file_name=f"atendimentos_{date.today().strftime('%d%m%Y')}.csv",
        mime="text/csv",
    )

# ─────────────────────────────────────────────
# Rodapé
# ─────────────────────────────────────────────
st.markdown("---")
st.caption(
    f"🕒 {agora.strftime('%d/%m/%Y %H:%M:%S')} · "
    "Cache 5 min · API Gove Digital · Prefeitura de Rio Verde"
)
