"""
supabase_client.py — Integração com Supabase via REST API.
Operações de upsert para contribuintes, atendentes, setores e atendimentos.
"""
import os
import requests
import streamlit as st
from datetime import datetime

def _url() -> str:
    try:    return st.secrets["SUPABASE_URL"]
    except: return os.environ.get("SUPABASE_URL", "")

def _key() -> str:
    try:    return st.secrets["SUPABASE_ANON_KEY"]
    except: return os.environ.get("SUPABASE_ANON_KEY", "")

def _h() -> dict:
    return {
        "apikey":       _key(),
        "Content-Type": "application/json",
        "Prefer":       "resolution=merge-duplicates,return=representation",
    }

def _rest(table: str) -> str:
    return f"{_url()}/rest/v1/{table}"

# ─────────────────────────────────────────────
# Upsert genérico
# ─────────────────────────────────────────────
def _upsert(table: str, records: list[dict], on_conflict: str = "uuid") -> dict:
    """
    Upsert em lote. Retorna dict com ok, inserted, updated, error.
    on_conflict: coluna de chave única para merge (uuid ou id).
    """
    if not records:
        return {"ok": True, "count": 0}

    # Remove duplicatas pelo campo de chave
    seen, unique = set(), []
    for r in records:
        key = r.get(on_conflict)
        if key and key not in seen:
            seen.add(key)
            unique.append(r)

    if not unique:
        return {"ok": True, "count": 0}

    url = f"{_rest(table)}?on_conflict={on_conflict}"
    try:
        r = requests.post(url, json=unique, headers=_h(), timeout=30)
        if r.status_code in (200, 201):
            return {"ok": True, "count": len(unique)}
        return {"ok": False, "count": 0,
                "error": f"HTTP {r.status_code}: {r.text[:300]}"}
    except Exception as e:
        return {"ok": False, "count": 0, "error": str(e)}

# ─────────────────────────────────────────────
# Funções específicas por entidade
# ─────────────────────────────────────────────
def upsert_contribuintes(parsed: list[dict]) -> dict:
    """Extrai contribuintes únicos e faz upsert."""
    records = []
    for p in parsed:
        if p.get("contribuinte_uuid"):
            records.append({
                "uuid":       p["contribuinte_uuid"],
                "name":       p.get("_contribuinte_nome"),
                "email":      p.get("_contribuinte_email"),
                "created_at": p.get("_contribuinte_created_at"),
                "synced_at":  datetime.utcnow().isoformat(),
            })
    return _upsert("contribuintes", records, on_conflict="uuid")


def upsert_atendentes(parsed: list[dict]) -> dict:
    """Extrai atendentes únicos e faz upsert."""
    records = []
    for p in parsed:
        if p.get("atendente_uuid"):
            records.append({
                "uuid":       p["atendente_uuid"],
                "name":       p.get("_atendente_nome"),
                "email":      p.get("_atendente_email"),
                "created_at": p.get("_atendente_created_at"),
                "synced_at":  datetime.utcnow().isoformat(),
            })
    return _upsert("atendentes", records, on_conflict="uuid")


def upsert_setores(parsed: list[dict]) -> dict:
    """Extrai setores únicos e faz upsert."""
    records = []
    for p in parsed:
        if p.get("setor_uuid"):
            records.append({
                "uuid":      p["setor_uuid"],
                "name":      p.get("_setor_nome"),
                "acronym":   p.get("_setor_sigla"),
                "synced_at": datetime.utcnow().isoformat(),
            })
    return _upsert("setores", records, on_conflict="uuid")


def upsert_atendimentos(parsed: list[dict]) -> dict:
    """Faz upsert dos atendimentos (atualiza se já existe)."""
    import json
    records = []
    for p in parsed:
        if not p.get("id"):
            continue
        records.append({
            "id":               p["id"],
            "protocolo":        p.get("protocolo"),
            "status":           p.get("status"),
            "tipo":             p.get("tipo"),
            "contribuinte_uuid":p.get("contribuinte_uuid"),
            "atendente_uuid":   p.get("atendente_uuid"),
            "setor_uuid":       p.get("setor_uuid"),
            "aberto_em":        p.get("aberto_em"),
            "encerrado_em":     p.get("encerrado_em"),
            "dados_extras":     p.get("dados_extras") or {},
            "synced_at":        datetime.utcnow().isoformat(),
            "updated_at":       datetime.utcnow().isoformat(),
        })
    return _upsert("atendimentos", records, on_conflict="id")


def integrar_tudo(parsed: list[dict]) -> dict:
    """
    Executa toda a pipeline de integração em ordem:
    1. Contribuintes, 2. Atendentes, 3. Setores, 4. Atendimentos
    Retorna resumo de cada etapa.
    """
    now = datetime.utcnow().isoformat()
    resultados = {}

    # Enriquece parsed com campos extras dos objetos aninhados
    # (email e created_at que parse_atendimento não propaga)
    # Feito aqui para não poluir a função parse_atendimento
    resultados["contribuintes"] = upsert_contribuintes(parsed)
    resultados["atendentes"]    = upsert_atendentes(parsed)
    resultados["setores"]       = upsert_setores(parsed)
    resultados["atendimentos"]  = upsert_atendimentos(parsed)

    resultados["ok"] = all(v.get("ok", False) for v in resultados.values()
                           if isinstance(v, dict))
    return resultados


# ─────────────────────────────────────────────
# Leitura para a página de Configurações
# ─────────────────────────────────────────────
def contar_registros() -> dict:
    """Conta registros em cada tabela para exibir no painel."""
    totais = {}
    for tabela in ["contribuintes", "atendentes", "setores", "atendimentos"]:
        try:
            r = requests.get(
                _rest(tabela),
                headers={**_h(), "Prefer": "count=exact"},
                params={"select": "id" if tabela == "atendimentos" else "uuid",
                        "limit": "1"},
                timeout=10,
            )
            # Supabase retorna o count no header Content-Range
            cr = r.headers.get("content-range", "")
            total = int(cr.split("/")[-1]) if "/" in cr else len(r.json())
            totais[tabela] = total
        except Exception:
            totais[tabela] = "—"
    return totais


def listar_tabela(tabela: str, limit: int = 100) -> list[dict]:
    """Lista registros de uma tabela para visualização."""
    try:
        r = requests.get(
            _rest(tabela),
            headers=_h(),
            params={"select": "*", "order": "synced_at.desc", "limit": str(limit)},
            timeout=15,
        )
        return r.json() if r.status_code == 200 else []
    except Exception:
        return []
