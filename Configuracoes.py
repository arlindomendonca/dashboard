"""
pages/Configuracoes.py — Configurações
Visualiza as tabelas do Supabase.
"""
import streamlit as st
import pandas as pd
import sys, os

# Garante que a raiz do projeto está no path (necessário para imports no Streamlit Cloud)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from shared_ui import render_header
from supabase_client import contar_registros, listar_tabela

st.set_page_config(
    page_title="Configurações",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

render_header("configuracoes")

# ─────────────────────────────────────────────
# Totalizadores
# ─────────────────────────────────────────────
st.markdown("### 📊 Dados no Supabase")

with st.spinner("Carregando contadores..."):
    totais = contar_registros()

k1, k2, k3, k4 = st.columns(4)
for col_k, tabela, emoji, cor in [
    (k1, "contribuintes", "👤", "#6366f1"),
    (k2, "atendentes",    "🎧", "#22c55e"),
    (k3, "setores",       "🏢", "#f59e0b"),
    (k4, "atendimentos",  "📋", "#3b82f6"),
]:
    with col_k:
        val = totais.get(tabela, "—")
        st.markdown(f"""<div class="kpi">
            <div class="kpi-lbl">{emoji} {tabela.capitalize()}</div>
            <div class="kpi-val" style="color:{cor}">{f"{val:,}" if isinstance(val, int) else val}</div>
            <div class="kpi-sub">registros no Supabase</div>
        </div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)
st.markdown("---")

# ─────────────────────────────────────────────
# Abas por tabela
# ─────────────────────────────────────────────
aba_c, aba_a, aba_s, aba_at = st.tabs([
    "👤 Contribuintes",
    "🎧 Atendentes",
    "🏢 Setores",
    "📋 Atendimentos",
])


def _render(tabela: str, cols: list | None = None, rename: dict | None = None):
    with st.spinner(f"Carregando {tabela}..."):
        dados = listar_tabela(tabela, limit=500)

    if not dados:
        st.info(f"Nenhum registro em **{tabela}** ainda. "
                "Integre atendimentos na página Gestão de Atendimentos.")
        return

    df = pd.DataFrame(dados)
    if cols:
        df = df[[c for c in cols if c in df.columns]]
    if rename:
        df = df.rename(columns=rename)

    # Formata datas
    for col in df.columns:
        if any(k in col.lower() for k in ["_at","_em","criado","sincron","aberto","encerrado","atualiz"]):
            try:
                df[col] = (pd.to_datetime(df[col], errors="coerce")
                           .dt.strftime("%d/%m/%Y %H:%M").fillna("—"))
            except Exception:
                pass

    busca = st.text_input("🔍 Buscar...", label_visibility="collapsed",
                           key=f"b_{tabela}", placeholder="🔍 Buscar...")
    df_e = df.copy()
    if busca.strip():
        mask = pd.Series(False, index=df_e.index)
        for c in df_e.columns:
            mask |= df_e[c].astype(str).str.lower().str.contains(
                busca.strip().lower(), na=False)
        df_e = df_e[mask]

    st.markdown(f"**{len(df_e):,}** registro(s)")
    st.dataframe(df_e, use_container_width=True,
                 height=min(60 + len(df_e) * 35, 500), hide_index=True)

    csv = df_e.to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button(f"⬇️ Exportar {tabela}.csv", data=csv,
                        file_name=f"{tabela}.csv", mime="text/csv",
                        key=f"exp_{tabela}")


with aba_c:
    _render("contribuintes",
            cols=["uuid","name","email","created_at","synced_at"],
            rename={"uuid":"UUID","name":"Nome","email":"E-mail",
                    "created_at":"Criado em","synced_at":"Sincronizado em"})

with aba_a:
    _render("atendentes",
            cols=["uuid","name","email","created_at","synced_at"],
            rename={"uuid":"UUID","name":"Nome","email":"E-mail",
                    "created_at":"Criado em","synced_at":"Sincronizado em"})

with aba_s:
    _render("setores",
            cols=["uuid","name","acronym","synced_at"],
            rename={"uuid":"UUID","name":"Nome","acronym":"Sigla",
                    "synced_at":"Sincronizado em"})

with aba_at:
    _render("atendimentos",
            cols=["id","protocolo","status","tipo",
                  "contribuinte_uuid","atendente_uuid","setor_uuid",
                  "aberto_em","encerrado_em","updated_at"],
            rename={"id":"ID","protocolo":"Protocolo","status":"Status","tipo":"Tipo",
                    "contribuinte_uuid":"Contribuinte UUID",
                    "atendente_uuid":"Atendente UUID",
                    "setor_uuid":"Setor UUID",
                    "aberto_em":"Aberto em","encerrado_em":"Encerrado em",
                    "updated_at":"Atualizado em"})

st.markdown("---")
st.caption("⚙️ Configurações · Sistema de Atendimentos · Prefeitura de Rio Verde")
