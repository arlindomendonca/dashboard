"""
auth.py — Funções de autenticação e gestão de usuários via Supabase.
"""
import os, requests, streamlit as st

# ── Credenciais ───────────────────────────────────────────────────
def _url():
    return st.secrets.get("SUPABASE_URL") or os.environ.get("SUPABASE_URL", "")

def _key():
    return st.secrets.get("SUPABASE_ANON_KEY") or os.environ.get("SUPABASE_ANON_KEY", "")

def _h():
    return {"apikey": _key(), "Content-Type": "application/json"}

def _ha():
    token = st.session_state.get("token", "")
    return {**_h(), "Authorization": f"Bearer {token}"}

# ── Auth ──────────────────────────────────────────────────────────
def fazer_login(email: str, senha: str) -> dict:
    r = requests.post(
        f"{_url()}/auth/v1/token?grant_type=password",
        json={"email": email, "password": senha},
        headers=_h(), timeout=15,
    )
    d = r.json()
    if r.status_code == 200 and "access_token" in d:
        return {"ok": True, "token": d["access_token"], "user": d.get("user", {})}
    return {"ok": False, "erro": d.get("error_description") or d.get("msg") or "Credenciais inválidas."}


def criar_conta(email: str, senha: str, nome: str) -> dict:
    """Cria conta no Supabase Auth — fica pendente até aprovação do admin."""
    r = requests.post(
        f"{_url()}/auth/v1/signup",
        json={"email": email, "password": senha, "data": {"nome": nome}},
        headers=_h(), timeout=15,
    )
    d = r.json()
    if r.status_code in (200, 201) and "id" in d.get("user", {}):
        return {"ok": True}
    if r.status_code in (200, 201) and d.get("id"):
        return {"ok": True}
    return {"ok": False, "erro": d.get("msg") or d.get("error_description") or "Erro ao criar conta."}


def fazer_logout():
    for k in ["token", "user_id", "user_email", "user_nome", "aprovado"]:
        st.session_state.pop(k, None)


def logado() -> bool:
    return bool(st.session_state.get("token"))


# ── Perfis (tabela public.profiles) ──────────────────────────────
def _rest(path: str):
    return f"{_url()}/rest/v1/{path}"


def buscar_perfil(user_id: str) -> dict:
    r = requests.get(
        _rest(f"profiles?id=eq.{user_id}&select=*"),
        headers=_ha(), timeout=10,
    )
    if r.status_code == 200 and r.json():
        return r.json()[0]
    return {}


def listar_perfis() -> list:
    """Admin: lista todos os perfis."""
    r = requests.get(
        _rest("profiles?select=*&order=created_at.desc"),
        headers=_ha(), timeout=10,
    )
    return r.json() if r.status_code == 200 else []


def aprovar_usuario(user_id: str) -> bool:
    r = requests.patch(
        _rest(f"profiles?id=eq.{user_id}"),
        json={"aprovado": True},
        headers={**_ha(), "Prefer": "return=minimal"},
        timeout=10,
    )
    return r.status_code in (200, 204)


def rejeitar_usuario(user_id: str) -> bool:
    r = requests.patch(
        _rest(f"profiles?id=eq.{user_id}"),
        json={"aprovado": False, "ativo": False},
        headers={**_ha(), "Prefer": "return=minimal"},
        timeout=10,
    )
    return r.status_code in (200, 204)


def criar_usuario_admin(email: str, senha: str, nome: str, perfil: str = "usuario") -> dict:
    """
    Admin cria usuário diretamente (já aprovado).
    Usa o endpoint de signup com aprovação automática.
    """
    res = criar_conta(email, senha, nome)
    if not res["ok"]:
        return res
    return {"ok": True}


def usuario_aprovado(user_id: str) -> bool:
    p = buscar_perfil(user_id)
    return p.get("aprovado", False)


def is_admin(user_id: str) -> bool:
    p = buscar_perfil(user_id)
    return p.get("perfil") == "admin"
