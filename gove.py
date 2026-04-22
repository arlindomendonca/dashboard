"""
gove.py — Wrapper da API Gove.
Retorna dados brutos e processados para exibição e integração.
"""
import os
import requests
import streamlit as st
import pandas as pd
from datetime import datetime

def _token() -> str:
    try:    return st.secrets["GOVE_TOKEN"]
    except: return os.environ.get("GOVE_TOKEN", "")

def _base() -> str:
    try:    return st.secrets.get("GOVE_BASE_URL", "https://api.gove.digital/v2")
    except: return os.environ.get("GOVE_BASE_URL", "https://api.gove.digital/v2")

def _h() -> dict:
    return {
        "Authorization": f"Bearer {_token()}",
        "Accept":        "application/json",
        "Content-Type":  "application/json",
    }

# ─────────────────────────────────────────────
# Busca raw (sem cache) — usada na integração
# ─────────────────────────────────────────────
def _fetch_raw(params: dict) -> list[dict]:
    """Faz a requisição e retorna lista de dicts brutos da API."""
    token = _token()
    if not token:
        st.error("❌ GOVE_TOKEN não configurado nos Secrets.")
        return []

    url = f"{_base()}/chats"
    try:
        r = requests.get(url, headers=_h(), params=params, timeout=30)
    except requests.exceptions.ConnectionError:
        st.error("❌ Sem conexão com a API Gove.")
        return []
    except requests.exceptions.Timeout:
        st.error("⏱️ Timeout na API Gove.")
        return []
    except Exception as e:
        st.error(f"❌ Erro: {e}")
        return []

    if r.status_code == 401:
        st.error("❌ Token inválido (401).")
        return []
    if r.status_code != 200:
        st.error(f"❌ API retornou HTTP {r.status_code}: {r.text[:300]}")
        return []

    try:
        raw = r.json()
    except Exception:
        st.error("❌ Resposta da API não é JSON válido.")
        return []

    if isinstance(raw, list):
        return raw
    if isinstance(raw, dict):
        for k in ["data","chats","records","results","items"]:
            if k in raw:
                return raw[k]
    return []

# ─────────────────────────────────────────────
# Helpers de extração de objetos aninhados
# ─────────────────────────────────────────────
def _extract_obj(record: dict, keys: list[str]) -> dict | None:
    """Tenta extrair um sub-objeto por uma lista de possíveis chaves."""
    for k in keys:
        val = record.get(k)
        if isinstance(val, dict) and val.get("uuid"):
            return val
    return None

def _extract_uuid(record: dict, keys: list[str]) -> str | None:
    obj = _extract_obj(record, keys)
    if obj:
        return obj.get("uuid")
    # fallback: campo direto
    for k in keys:
        v = record.get(k)
        if isinstance(v, str) and len(v) > 20:
            return v
    return None

def _str(v) -> str | None:
    if v is None: return None
    s = str(v).strip()
    return s if s and s.lower() not in ("none","nan","—","-","") else None

def _dt(v) -> str | None:
    if v is None: return None
    try:
        return pd.to_datetime(v, errors="coerce").isoformat()
    except:
        return None

# ─────────────────────────────────────────────
# Estruturas extraídas de um registro
# ─────────────────────────────────────────────
def parse_contribuinte(r: dict) -> dict | None:
    obj = _extract_obj(r, ["recipient","customer","contact","contribuinte"])
    if not obj:
        return None
    return {
        "uuid":       obj.get("uuid"),
        "name":       _str(obj.get("name")),
        "email":      _str(obj.get("email")),
        "created_at": _dt(obj.get("created_at")),
    }

def parse_atendente(r: dict) -> dict | None:
    obj = _extract_obj(r, ["agent","attendant","atendente","assigned_to"])
    if not obj:
        return None
    return {
        "uuid":       obj.get("uuid"),
        "name":       _str(obj.get("name")),
        "email":      _str(obj.get("email")),
        "created_at": _dt(obj.get("created_at")),
    }

def parse_setor(r: dict) -> dict | None:
    obj = _extract_obj(r, ["sector","setor","department","queue"])
    if not obj:
        return None
    return {
        "uuid":    obj.get("uuid"),
        "name":    _str(obj.get("name")),
        "acronym": _str(obj.get("acronym")),
    }

def parse_atendimento(r: dict) -> dict:
    cont  = parse_contribuinte(r)
    atend = parse_atendente(r)
    setor = parse_setor(r)

    # Campos conhecidos que são tratados separadamente
    KNOWN = {"recipient","customer","contact","contribuinte",
             "agent","attendant","atendente","assigned_to",
             "sector","setor","department","queue"}

    # Tudo que não é objeto aninhado vai para dados_extras
    extras = {k: v for k, v in r.items()
              if k not in KNOWN and not isinstance(v, dict)}

    return {
        "id":                str(r.get("id") or r.get("uuid") or r.get("chat_id") or ""),
        "protocolo":         _str(r.get("protocol") or r.get("protocolo") or str(r.get("id",""))),
        "status":            _str(r.get("status")),
        "tipo":              _str(r.get("type") or r.get("chat_type") or r.get("protocol_type")),
        "contribuinte_uuid": cont["uuid"]  if cont  else None,
        "atendente_uuid":    atend["uuid"] if atend else None,
        "setor_uuid":        setor["uuid"] if setor else None,
        "aberto_em":         _dt(r.get("started_at") or r.get("created_at") or r.get("opened_at")),
        "encerrado_em":      _dt(r.get("finished_at") or r.get("closed_at") or r.get("ended_at")),
        "dados_extras":      extras,
        # Para exibição (não vai ao Supabase direto)
        "_contribuinte_nome": cont["name"]  if cont  else None,
        "_atendente_nome":    atend["name"] if atend else None,
        "_setor_nome":        setor["name"] if setor else None,
        "_setor_sigla":       setor["acronym"] if setor else None,
    }

# ─────────────────────────────────────────────
# Busca com cache (exibição na tabela)
# ─────────────────────────────────────────────
@st.cache_data(ttl=300, show_spinner=False)
def buscar_atendimentos(
    data_ini: str | None = None,
    data_fim: str | None = None,
    protocolo: str | None = None,
    apenas_abertos: bool = True,
    debug: bool = False,
) -> tuple[pd.DataFrame, list[dict]]:
    """
    Retorna (df_exibicao, registros_raw).
    df_exibicao: colunas amigáveis para a tabela.
    registros_raw: lista de dicts brutos para integração.
    """
    params: dict = {"order_by": "created_at", "order_direction": "desc"}
    if data_ini: params["started_at_initial"] = data_ini
    if data_fim: params["started_at_final"]   = data_fim
    if protocolo: params["id"] = protocolo.strip()

    registros = _fetch_raw(params)

    if debug and registros:
        st.info(f"🔍 Debug: {len(registros)} registros brutos. Primeiro item:")
        st.json(registros[0])

    if not registros:
        return pd.DataFrame(), []

    parsed = [parse_atendimento(r) for r in registros]

    # Filtra abertos se solicitado
    if apenas_abertos:
        parsed = [p for p in parsed if not p["encerrado_em"]]

    if not parsed:
        return pd.DataFrame(), []

    # Monta DataFrame de exibição
    rows = []
    for p in parsed:
        rows.append({
            "Protocolo":         p["protocolo"] or p["id"],
            "Status":            p["status"] or "—",
            "Tipo":              p["tipo"] or "—",
            "Contribuinte":      p["_contribuinte_nome"] or "—",
            "Atendente":         p["_atendente_nome"] or "—",
            "Setor":             p["_setor_nome"] or "—",
            "Sigla Setor":       p["_setor_sigla"] or "—",
            "Aberto em":         pd.to_datetime(p["aberto_em"]).strftime("%d/%m/%Y %H:%M")
                                 if p["aberto_em"] else "—",
            "Encerrado em":      pd.to_datetime(p["encerrado_em"]).strftime("%d/%m/%Y %H:%M")
                                 if p["encerrado_em"] else "—",
        })

    return pd.DataFrame(rows), parsed
