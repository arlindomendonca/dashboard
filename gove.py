"""
gove.py — Wrapper da API Gove para atendimentos em aberto.
"""
import os, requests, streamlit as st
import pandas as pd

def _token():
    return st.secrets.get("GOVE_TOKEN") or os.environ.get("GOVE_TOKEN", "")

def _base():
    return st.secrets.get("GOVE_BASE_URL", "https://api.gove.digital/v2") \
           or os.environ.get("GOVE_BASE_URL", "https://api.gove.digital/v2")

def _h():
    return {
        "Authorization": f"Bearer {_token()}",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }

@st.cache_data(ttl=300, show_spinner=False)
def buscar_atendimentos_abertos(
    data_ini: str | None = None,  # dd/mm/yyyy
    data_fim: str | None = None,
) -> pd.DataFrame:
    """
    Busca atendimentos da API Gove e filtra os que estão em aberto
    (sem data de encerramento).
    Retorna DataFrame com colunas mapeadas para PT-BR.
    Cache de 5 minutos.
    """
    params = {"order_by": "created_at", "order_direction": "desc"}
    if data_ini: params["started_at_initial"] = data_ini
    if data_fim: params["started_at_final"]   = data_fim

    try:
        r = requests.get(
            f"{_base()}/chats",
            headers=_h(), params=params, timeout=30,
        )
        r.raise_for_status()
        raw = r.json()

        # Normaliza: API pode retornar lista ou dict com "data"
        if isinstance(raw, list):
            registros = raw
        elif isinstance(raw, dict):
            registros = raw.get("data") or raw.get("chats") or []
        else:
            registros = []

        if not registros:
            return pd.DataFrame()

        df = pd.DataFrame(registros)

        # ── Filtra apenas em ABERTO (sem encerramento) ────────────
        col_fim = next(
            (c for c in ["finished_at","encerrado_em","closed_at","ended_at"]
             if c in df.columns), None
        )
        if col_fim:
            df[col_fim] = pd.to_datetime(df[col_fim], errors="coerce")
            df = df[df[col_fim].isna()].copy()

        if df.empty:
            return pd.DataFrame()

        # ── Mapeia colunas conhecidas para PT-BR ──────────────────
        mapa = {
            # Protocolo
            "id":                   "Protocolo",
            "protocol":             "Protocolo",
            "protocolo":            "Protocolo",
            # Atendente
            "agent":                "Atendente",
            "agent_name":           "Atendente",
            "atendente":            "Atendente",
            "assigned_to":          "Atendente",
            # Contribuinte
            "recipient":            "Nome do Contribuinte",
            "customer_name":        "Nome do Contribuinte",
            "contact_name":         "Nome do Contribuinte",
            "nome_contribuinte":    "Nome do Contribuinte",
            # Telefone
            "phone":                "Telefone",
            "telefone":             "Telefone",
            "recipient_phone":      "Telefone",
            # Setor
            "sector":               "Setor",
            "setor":                "Setor",
            "department":           "Setor",
            "sector_name":          "Setor",
            # Tipo
            "type":                 "Tipo de Protocolo",
            "tipo":                 "Tipo de Protocolo",
            "chat_type":            "Tipo de Protocolo",
            "protocol_type":        "Tipo de Protocolo",
            # Aberto em
            "started_at":           "Aberto em",
            "created_at":           "Aberto em",
            "aberto_em":            "Aberto em",
            "opened_at":            "Aberto em",
            # Status
            "status":               "Status",
        }

        df = df.rename(columns={k: v for k, v in mapa.items() if k in df.columns})

        # Garante colunas padrão mesmo que API não retorne
        for col in ["Protocolo","Atendente","Nome do Contribuinte",
                    "Telefone","Setor","Tipo de Protocolo","Aberto em","Status"]:
            if col not in df.columns:
                df[col] = "—"

        # Formata data
        if "Aberto em" in df.columns:
            df["Aberto em"] = pd.to_datetime(df["Aberto em"], errors="coerce")\
                                .dt.strftime("%d/%m/%Y %H:%M")

        # Preenche vazios
        df = df.fillna("—").replace("", "—").replace("None", "—").replace("nan", "—")

        # Retorna apenas colunas relevantes na ordem certa
        colunas = ["Protocolo","Atendente","Nome do Contribuinte",
                   "Telefone","Setor","Tipo de Protocolo","Aberto em","Status"]
        return df[[c for c in colunas if c in df.columns]]

    except requests.exceptions.HTTPError as e:
        st.error(f"❌ Erro na API Gove ({r.status_code}): {e}")
        return pd.DataFrame()
    except requests.exceptions.ConnectionError:
        st.error("❌ Sem conexão com a API Gove.")
        return pd.DataFrame()
    except requests.exceptions.Timeout:
        st.error("⏱️ Timeout ao consultar a API Gove.")
        return pd.DataFrame()
    except Exception as e:
        st.error(f"❌ Erro inesperado: {e}")
        return pd.DataFrame()
