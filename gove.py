"""
gove.py — Wrapper da API Gove para atendimentos.
Versão robusta com tratamento de erros e debug opcional.
"""
import os
import requests
import streamlit as st
import pandas as pd

# ─────────────────────────────────────────────
# Configuração
# ─────────────────────────────────────────────
def _token() -> str:
    try:
        return st.secrets["GOVE_TOKEN"]
    except Exception:
        return os.environ.get("GOVE_TOKEN", "")

def _base() -> str:
    try:
        return st.secrets.get("GOVE_BASE_URL", "https://api.gove.digital/v2")
    except Exception:
        return os.environ.get("GOVE_BASE_URL", "https://api.gove.digital/v2")

def _headers() -> dict:
    return {
        "Authorization": f"Bearer {_token()}",
        "Accept":        "application/json",
        "Content-Type":  "application/json",
    }

# ─────────────────────────────────────────────
# Mapeamento de colunas da API → PT-BR
# ─────────────────────────────────────────────
MAPA_COLUNAS = {
    # Protocolo
    "id":                   "Protocolo",
    "protocol":             "Protocolo",
    "protocolo":            "Protocolo",
    "chat_id":              "Protocolo",
    # Atendente
    "agent":                "Atendente",
    "agent_name":           "Atendente",
    "atendente":            "Atendente",
    "assigned_to":          "Atendente",
    "attendant":            "Atendente",
    # Contribuinte
    "recipient":            "Nome do Contribuinte",
    "customer_name":        "Nome do Contribuinte",
    "contact_name":         "Nome do Contribuinte",
    "nome_contribuinte":    "Nome do Contribuinte",
    "name":                 "Nome do Contribuinte",
    "customer":             "Nome do Contribuinte",
    # Telefone
    "phone":                "Telefone",
    "telefone":             "Telefone",
    "recipient_phone":      "Telefone",
    "phone_number":         "Telefone",
    "contact_phone":        "Telefone",
    # Setor
    "sector":               "Setor",
    "setor":                "Setor",
    "department":           "Setor",
    "sector_name":          "Setor",
    "queue":                "Setor",
    "queue_name":           "Setor",
    # Tipo
    "type":                 "Tipo de Protocolo",
    "tipo":                 "Tipo de Protocolo",
    "chat_type":            "Tipo de Protocolo",
    "protocol_type":        "Tipo de Protocolo",
    "category":             "Tipo de Protocolo",
    # Aberto em
    "started_at":           "Aberto em",
    "created_at":           "Aberto em",
    "aberto_em":            "Aberto em",
    "opened_at":            "Aberto em",
    "open_date":            "Aberto em",
    # Encerrado em
    "finished_at":          "Encerrado em",
    "closed_at":            "Encerrado em",
    "ended_at":             "Encerrado em",
    "encerrado_em":         "Encerrado em",
    # Status
    "status":               "Status",
}

COLUNAS_SAIDA = [
    "Protocolo",
    "Atendente",
    "Nome do Contribuinte",
    "Telefone",
    "Setor",
    "Tipo de Protocolo",
    "Aberto em",
    "Status",
]

# Colunas que indicam encerramento
COLS_FIM = ["finished_at", "closed_at", "ended_at", "encerrado_em",
            "Encerrado em", "close_date"]


@st.cache_data(ttl=300, show_spinner=False)
def buscar_atendimentos_abertos(
    data_ini: str | None = None,
    data_fim: str | None = None,
    debug: bool = False,
) -> pd.DataFrame:
    """
    Busca atendimentos via API Gove e filtra os em aberto.
    data_ini / data_fim: formato dd/mm/yyyy
    debug=True: exibe retorno bruto no Streamlit (para diagnóstico)
    """
    token = _token()
    if not token:
        st.error("❌ Token da API Gove não configurado. Verifique os Secrets.")
        return pd.DataFrame()

    params: dict = {"order_by": "created_at", "order_direction": "desc"}
    if data_ini:
        params["started_at_initial"] = data_ini
    if data_fim:
        params["started_at_final"] = data_fim

    url = f"{_base()}/chats"

    try:
        r = requests.get(url, headers=_headers(), params=params, timeout=30)
    except requests.exceptions.ConnectionError:
        st.error("❌ Sem conexão com a API Gove.")
        return pd.DataFrame()
    except requests.exceptions.Timeout:
        st.error("⏱️ Timeout ao consultar a API Gove. Tente novamente.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro na requisição: {e}")
        return pd.DataFrame()

    # ── Trata resposta HTTP ───────────────────────────────────────
    if r.status_code == 401:
        st.error("❌ Token inválido ou expirado (401). Verifique o GOVE_TOKEN.")
        return pd.DataFrame()
    if r.status_code == 403:
        st.error("❌ Sem permissão de acesso à API (403).")
        return pd.DataFrame()
    if r.status_code == 404:
        st.error(f"❌ Endpoint não encontrado (404): {url}")
        return pd.DataFrame()
    if r.status_code != 200:
        st.error(f"❌ Erro na API Gove: HTTP {r.status_code} — {r.text[:300]}")
        return pd.DataFrame()

    # ── Parse do JSON ─────────────────────────────────────────────
    try:
        raw = r.json()
    except Exception:
        st.error("❌ Resposta da API não é um JSON válido.")
        return pd.DataFrame()

    if debug:
        st.info("🔍 **Debug — resposta bruta da API:**")
        if isinstance(raw, list):
            st.write(f"Lista com {len(raw)} itens. Primeiro item:")
            if raw:
                st.json(raw[0])
        else:
            st.write(f"Tipo: {type(raw).__name__}")
            st.json(raw if not isinstance(raw, dict) or len(str(raw)) < 2000 else dict(list(raw.items())[:5]))

    # ── Extrai lista de registros ─────────────────────────────────
    if isinstance(raw, list):
        registros = raw
    elif isinstance(raw, dict):
        registros = (
            raw.get("data") or
            raw.get("chats") or
            raw.get("records") or
            raw.get("results") or
            raw.get("items") or
            []
        )
    else:
        st.warning("⚠️ Formato de resposta desconhecido.")
        return pd.DataFrame()

    if not registros:
        return pd.DataFrame()

    # ── Monta DataFrame ───────────────────────────────────────────
    try:
        df = pd.DataFrame(registros)
    except Exception as e:
        st.error(f"❌ Erro ao montar DataFrame: {e}")
        return pd.DataFrame()

    if debug:
        st.write(f"📋 Colunas recebidas: `{df.columns.tolist()}`")
        st.write(f"📊 Total de registros: {len(df)}")

    # ── Filtra em aberto ──────────────────────────────────────────
    col_fim = next((c for c in COLS_FIM if c in df.columns), None)
    if col_fim:
        df[col_fim] = pd.to_datetime(df[col_fim], errors="coerce")
        df = df[df[col_fim].isna()].copy()

    if df.empty:
        return pd.DataFrame()

    # ── Renomeia colunas ──────────────────────────────────────────
    df = df.rename(columns={k: v for k, v in MAPA_COLUNAS.items() if k in df.columns})

    # ── Garante colunas de saída ──────────────────────────────────
    for col in COLUNAS_SAIDA:
        if col not in df.columns:
            df[col] = "—"

    # ── Formata datas ─────────────────────────────────────────────
    if "Aberto em" in df.columns:
        df["Aberto em"] = (
            pd.to_datetime(df["Aberto em"], errors="coerce")
            .dt.strftime("%d/%m/%Y %H:%M")
            .fillna("—")
        )

    # ── Converte tudo para string e limpa nulos ───────────────────
    for col in COLUNAS_SAIDA:
        df[col] = (
            df[col]
            .astype(str)
            .str.strip()
            .replace({"nan": "—", "None": "—", "none": "—", "<NA>": "—", "": "—"})
        )

    return df[COLUNAS_SAIDA]
