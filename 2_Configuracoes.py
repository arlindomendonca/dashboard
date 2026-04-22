"""
pages/2_Configuracoes.py — Configurações
Visualiza as tabelas do Supabase: contribuintes, atendentes, setores, atendimentos.
"""
import streamlit as st
import pandas as pd
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from supabase_client import contar_registros, listar_tabela

st.set_page_config(
    page_title="Configurações",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

import components.header as header
header.render("configuracoes")

# ─────────────────────────────────────────────
# Totalizadores
# ─────────────────────────────────────────────
st.markdown("### 📊 Dados no Supabase")

with st.spinner("Carregando contadores..."):
    totais = contar_registros()

k1, k2, k3, k4 = st.columns(4)
for col_k, tabela, emoji, cor in [
    (k1, "contribuintes",  "👤", "#6366f1"),
    (k2, "atendentes",     "🎧", "#22c55e"),
    (k3, "setores",        "🏢", "#f59e0b"),
    (k4, "atendimentos",   "📋", "#3b82f6"),
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

def _render_tabela(tabela: str, colunas_exibir: list[str] | None = None,
                   renomear: dict | None = None):
    """Renderiza tabela do Supabase com busca e export."""
    with st.spinner(f"Carregando {tabela}..."):
        dados = listar_tabela(tabela, limit=500)

    if not dados:
        st.info(f"Nenhum registro em **{tabela}** ainda. "
                f"Integre atendimentos na página Gestão de Atendimentos.")
        return

    df = pd.DataFrame(dados)

    if colunas_exibir:
        df = df[[c for c in colunas_exibir if c in df.columns]]
    if renomear:
        df = df.rename(columns=renomear)

    # Formata datas
    for col in df.columns:
        if "at" in col.lower() or "em" in col.lower():
            try:
                df[col] = pd.to_datetime(df[col], errors="coerce")\
                            .dt.strftime("%d/%m/%Y %H:%M").fillna("—")
            except Exception:
                pass

    busca = st.text_input(f"busca_{tabela}",
                           placeholder="🔍 Buscar...",
                           label_visibility="collapsed",
                           key=f"busca_{tabela}")
    df_exib = df.copy()
    if busca.strip():
        mask = pd.Series(False, index=df_exib.index)
        for c in df_exib.columns:
            mask |= df_exib[c].astype(str).str.lower().str.contains(
                busca.strip().lower(), na=False)
        df_exib = df_exib[mask]

    st.markdown(f"**{len(df_exib):,}** registro(s)")
    st.dataframe(df_exib, use_container_width=True,
                 height=min(60 + len(df_exib)*35, 500), hide_index=True)

    csv = df_exib.to_csv(index=False, sep=";", encoding="utf-8-sig")
    st.download_button(f"⬇️ Exportar {tabela}.csv", data=csv,
                        file_name=f"{tabela}.csv", mime="text/csv",
                        key=f"exp_{tabela}")

# ── Contribuintes ─────────────────────────────────────────────────
with aba_c:
    _render_tabela(
        "contribuintes",
        colunas_exibir=["uuid","name","email","created_at","synced_at"],
        renomear={"uuid":"UUID","name":"Nome","email":"E-mail",
                  "created_at":"Criado em","synced_at":"Sincronizado em"},
    )

# ── Atendentes ────────────────────────────────────────────────────
with aba_a:
    _render_tabela(
        "atendentes",
        colunas_exibir=["uuid","name","email","created_at","synced_at"],
        renomear={"uuid":"UUID","name":"Nome","email":"E-mail",
                  "created_at":"Criado em","synced_at":"Sincronizado em"},
    )

# ── Setores ───────────────────────────────────────────────────────
with aba_s:
    _render_tabela(
        "setores",
        colunas_exibir=["uuid","name","acronym","synced_at"],
        renomear={"uuid":"UUID","name":"Nome","acronym":"Sigla",
                  "synced_at":"Sincronizado em"},
    )

# ── Atendimentos ──────────────────────────────────────────────────
with aba_at:
    _render_tabela(
        "atendimentos",
        colunas_exibir=["id","protocolo","status","tipo",
                        "contribuinte_uuid","atendente_uuid","setor_uuid",
                        "aberto_em","encerrado_em","updated_at"],
        renomear={"id":"ID","protocolo":"Protocolo","status":"Status",
                  "tipo":"Tipo","contribuinte_uuid":"Contribuinte (UUID)",
                  "atendente_uuid":"Atendente (UUID)","setor_uuid":"Setor (UUID)",
                  "aberto_em":"Aberto em","encerrado_em":"Encerrado em",
                  "updated_at":"Atualizado em"},
    )

# ─────────────────────────────────────────────
# Rodapé
# ─────────────────────────────────────────────
st.markdown("---")
st.caption("⚙️ Configurações · Sistema de Atendimentos · Prefeitura de Rio Verde")
