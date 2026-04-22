"""
pages/2_Admin.py — Painel Administrativo
Gestão de usuários: aprovar, rejeitar, criar.
Acesso restrito a administradores.
"""
import streamlit as st
from auth import (
    logado, is_admin, fazer_logout,
    listar_perfis, aprovar_usuario, rejeitar_usuario, criar_usuario_admin,
)

st.set_page_config(
    page_title="Painel Admin",
    page_icon="⚙️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Guard ─────────────────────────────────────────────────────────
if not logado():
    st.switch_page("app.py")
    st.stop()

uid = st.session_state.get("user_id", "")
if not is_admin(uid):
    st.error("🔒 Acesso restrito a administradores.")
    st.stop()

# ── CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }
.stApp { background-color: #0f1117; }
[data-testid="stSidebar"], [data-testid="collapsedControl"] { display:none !important; }

.topo {
    display:flex; justify-content:space-between; align-items:center;
    background: linear-gradient(135deg, #1e2130, #252a3d);
    border: 1px solid #2e3450; border-radius: 14px;
    padding: 16px 24px; margin-bottom: 24px;
}
.topo-titulo { font-size:20px; font-weight:800; color:#e2e8f0; }
.topo-sub    { font-size:12px; color:#64748b; margin-top:2px; }

.card-section {
    background: linear-gradient(135deg, #1e2130, #252a3d);
    border: 1px solid #2e3450; border-radius: 14px;
    padding: 24px; margin-bottom: 20px;
}
.sec-title { font-size:15px; font-weight:700; color:#e2e8f0; margin-bottom:16px; }

/* Badge status */
.badge-pend  { background:#2d2500; color:#f59e0b; border:1px solid #92400e;
               border-radius:20px; padding:2px 10px; font-size:11px; font-weight:600; }
.badge-aprov { background:#0f2a1a; color:#22c55e; border:1px solid #166534;
               border-radius:20px; padding:2px 10px; font-size:11px; font-weight:600; }
.badge-inat  { background:#1f1f1f; color:#6b7280; border:1px solid #374151;
               border-radius:20px; padding:2px 10px; font-size:11px; font-weight:600; }

div[data-testid="stTextInput"] label { font-size:13px; color:#94a3b8; font-weight:500; }
div[data-testid="stTextInput"] input {
    background: #0d1117 !important; border: 1px solid #2e3450 !important;
    color: #e2e8f0 !important; border-radius: 8px !important;
}
div[data-testid="stSelectbox"] label { font-size:13px; color:#94a3b8; font-weight:500; }
button[kind="primaryFormSubmit"] {
    background: linear-gradient(135deg,#6366f1,#4f46e5) !important;
    color:white !important; border:none !important;
    border-radius:8px !important; font-weight:700 !important;
}
hr { border-color: #2e3450; }
</style>
""", unsafe_allow_html=True)

nome_admin = st.session_state.get("user_nome", "Admin")
email_admin = st.session_state.get("user_email", "")

# ── Topo ─────────────────────────────────────────────────────────
ct1, ct2 = st.columns([5, 1])
with ct1:
    st.markdown(f"""
    <div class="topo">
        <div>
            <div class="topo-titulo">⚙️ Painel Administrativo</div>
            <div class="topo-sub">👤 {nome_admin} · {email_admin}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with ct2:
    st.markdown("<br>", unsafe_allow_html=True)
    if st.button("🔴 Em Aberto", use_container_width=True):
        st.switch_page("pages/3_Atendimentos.py")
    if st.button("🚪 Sair", use_container_width=True):
        fazer_logout()
        st.switch_page("app.py")

st.markdown("---")

# ── Abas ─────────────────────────────────────────────────────────
aba_pend, aba_todos, aba_criar = st.tabs([
    "⏳ Aguardando Aprovação",
    "👥 Todos os Usuários",
    "➕ Criar Usuário",
])

# ════════════════════════════════════════════════════
# ABA 1 — Pendentes
# ════════════════════════════════════════════════════
with aba_pend:
    with st.spinner("Carregando..."):
        perfis = listar_perfis()

    pendentes = [p for p in perfis if not p.get("aprovado") and p.get("ativo", True)]

    if not pendentes:
        st.success("✅ Nenhum usuário aguardando aprovação.")
    else:
        st.markdown(f"**{len(pendentes)} usuário(s) aguardando aprovação**")
        st.markdown("")

        for p in pendentes:
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
                with c1:
                    st.markdown(f"**{p.get('nome', '—')}**")
                    st.caption(p.get("email", "—"))
                with c2:
                    st.markdown(f"<span class='badge-pend'>⏳ Pendente</span>",
                                unsafe_allow_html=True)
                    st.caption(f"Criado: {str(p.get('created_at',''))[:10]}")
                with c3:
                    if st.button("✅ Aprovar", key=f"ap_{p['id']}", use_container_width=True):
                        if aprovar_usuario(p["id"]):
                            st.success(f"Usuário {p.get('nome','—')} aprovado!")
                            st.rerun()
                        else:
                            st.error("Erro ao aprovar.")
                with c4:
                    if st.button("❌ Rejeitar", key=f"rej_{p['id']}", use_container_width=True):
                        if rejeitar_usuario(p["id"]):
                            st.warning(f"Usuário {p.get('nome','—')} rejeitado.")
                            st.rerun()
                        else:
                            st.error("Erro ao rejeitar.")
                st.markdown("---")

# ════════════════════════════════════════════════════
# ABA 2 — Todos os usuários
# ════════════════════════════════════════════════════
with aba_todos:
    with st.spinner("Carregando..."):
        todos = listar_perfis()

    if not todos:
        st.info("Nenhum usuário cadastrado.")
    else:
        # Filtro rápido
        busca = st.text_input("🔍 Buscar por nome ou e-mail", placeholder="Digite para filtrar...")
        if busca.strip():
            todos = [p for p in todos
                     if busca.lower() in p.get("nome","").lower()
                     or busca.lower() in p.get("email","").lower()]

        st.markdown(f"**{len(todos)} usuário(s)**")
        st.markdown("")

        for p in todos:
            aprovado = p.get("aprovado", False)
            ativo    = p.get("ativo", True)
            perfil   = p.get("perfil", "usuario")

            badge = (
                "<span class='badge-aprov'>✅ Aprovado</span>" if aprovado and ativo
                else "<span class='badge-inat'>⛔ Inativo</span>" if not ativo
                else "<span class='badge-pend'>⏳ Pendente</span>"
            )

            c1, c2, c3, c4 = st.columns([3, 2, 1, 1])
            with c1:
                st.markdown(f"**{p.get('nome','—')}**")
                st.caption(f"{p.get('email','—')} · {perfil.capitalize()}")
            with c2:
                st.markdown(badge, unsafe_allow_html=True)
                st.caption(f"Criado: {str(p.get('created_at',''))[:10]}")
            with c3:
                if not aprovado and ativo:
                    if st.button("✅", key=f"tap_{p['id']}", use_container_width=True,
                                 help="Aprovar"):
                        aprovar_usuario(p["id"])
                        st.rerun()
            with c4:
                if aprovado and ativo and p["id"] != uid:
                    if st.button("🚫", key=f"trej_{p['id']}", use_container_width=True,
                                 help="Desativar"):
                        rejeitar_usuario(p["id"])
                        st.rerun()
            st.markdown("---")

# ════════════════════════════════════════════════════
# ABA 3 — Criar usuário (admin)
# ════════════════════════════════════════════════════
with aba_criar:
    st.markdown("**Criar usuário diretamente (já aprovado)**")
    st.markdown("")

    with st.form("f_criar"):
        c1, c2 = st.columns(2)
        with c1:
            nome_c  = st.text_input("Nome completo *", placeholder="João Silva")
            email_c = st.text_input("E-mail *", placeholder="joao@email.com.br")
        with c2:
            senha_c  = st.text_input("Senha temporária *", type="password",
                                     placeholder="mín. 6 caracteres")
            perfil_c = st.selectbox("Perfil", ["usuario", "admin"])

        btn_criar = st.form_submit_button("➕ Criar Usuário", use_container_width=True)

    if btn_criar:
        if not all([nome_c.strip(), email_c.strip(), senha_c]):
            st.error("Preencha todos os campos obrigatórios (*).")
        elif len(senha_c) < 6:
            st.error("Senha deve ter pelo menos 6 caracteres.")
        else:
            with st.spinner("Criando usuário..."):
                res = criar_usuario_admin(
                    email_c.strip().lower(), senha_c,
                    nome_c.strip(), perfil_c
                )
            if res["ok"]:
                st.success(f"✅ Usuário **{nome_c}** criado com sucesso! "
                           f"Ele já pode fazer login.")
            else:
                st.error(f"❌ {res.get('erro','Erro ao criar.')}")
