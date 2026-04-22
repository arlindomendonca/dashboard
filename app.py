"""
app.py — Tela de Login e Criação de Conta
Entry point do sistema.
"""
import streamlit as st
from auth import fazer_login, criar_conta, logado, buscar_perfil, usuario_aprovado

st.set_page_config(
    page_title="Sistema de Atendimentos",
    page_icon="🏛️",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# ── CSS ───────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

* { font-family: 'Inter', sans-serif; }

.stApp {
    background: linear-gradient(135deg, #0f1117 0%, #1a1d2e 100%);
    min-height: 100vh;
}
[data-testid="stSidebar"],
[data-testid="collapsedControl"] { display: none !important; }

/* Card central */
.card {
    background: linear-gradient(145deg, #1e2130 0%, #252a3d 100%);
    border: 1px solid #2e3450;
    border-radius: 20px;
    padding: 40px 36px 32px;
    box-shadow: 0 24px 64px rgba(0,0,0,0.5);
}
.logo { text-align:center; font-size:56px; margin-bottom:8px; }
.titulo { text-align:center; font-size:22px; font-weight:800; color:#e2e8f0; }
.subtitulo { text-align:center; font-size:12px; color:#64748b;
             margin-bottom:28px; margin-top:4px; }

/* Tabs customizadas */
[data-testid="stTabs"] [data-baseweb="tab-list"] {
    background: #13162280;
    border-radius: 10px;
    padding: 4px;
    border: 1px solid #2e3450;
    gap: 4px;
    margin-bottom: 20px;
}
[data-testid="stTabs"] [data-baseweb="tab"] {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 13px !important;
    color: #64748b !important;
    padding: 8px 20px !important;
}
[data-testid="stTabs"] [aria-selected="true"] {
    background: #6366f1 !important;
    color: white !important;
}

/* Inputs */
div[data-testid="stTextInput"] label { font-size:13px; color:#94a3b8; font-weight:500; }
div[data-testid="stTextInput"] input {
    background: #0d1117 !important;
    border: 1px solid #2e3450 !important;
    color: #e2e8f0 !important;
    border-radius: 10px !important;
    padding: 11px 14px !important;
    font-size: 14px !important;
    transition: border-color 0.2s;
}
div[data-testid="stTextInput"] input:focus {
    border-color: #6366f1 !important;
    box-shadow: 0 0 0 3px rgba(99,102,241,0.2) !important;
}

/* Botão submit */
button[kind="primaryFormSubmit"] {
    background: linear-gradient(135deg, #6366f1, #4f46e5) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    height: 46px !important;
    font-size: 15px !important;
    font-weight: 700 !important;
    width: 100% !important;
    cursor: pointer !important;
    transition: opacity 0.2s !important;
}
button[kind="primaryFormSubmit"]:hover { opacity: 0.88 !important; }

.rodape { text-align:center; font-size:11px; color:#374151; margin-top:20px; }
</style>
""", unsafe_allow_html=True)

# ── Redireciona se já logado ──────────────────────────────────────
if logado():
    uid = st.session_state.get("user_id", "")
    if uid:
        from auth import is_admin, usuario_aprovado
        if is_admin(uid):
            st.switch_page("pages/2_Admin.py")
        elif usuario_aprovado(uid):
            st.switch_page("pages/3_Atendimentos.py")
        else:
            st.warning("⏳ Sua conta ainda está aguardando aprovação do administrador.")
            if st.button("Sair"):
                from auth import fazer_logout
                fazer_logout()
                st.rerun()
    st.stop()

# ── Layout centralizado ───────────────────────────────────────────
_, col, _ = st.columns([1, 2.2, 1])
with col:
    st.markdown("""
    <div class="logo">🏛️</div>
    <div class="titulo">Sistema de Atendimentos</div>
    <div class="subtitulo">Prefeitura de Rio Verde · Acesso Restrito</div>
    """, unsafe_allow_html=True)

    aba_login, aba_conta = st.tabs(["Entrar", "Criar Conta"])

    # ── ABA LOGIN ─────────────────────────────────────────────────
    with aba_login:
        with st.form("f_login"):
            email = st.text_input("E-mail", placeholder="seu@email.com.br")
            senha = st.text_input("Senha", type="password", placeholder="••••••••")
            btn   = st.form_submit_button("Entrar →", use_container_width=True)

        if btn:
            if not email.strip() or not senha:
                st.error("Preencha e-mail e senha.")
            else:
                with st.spinner("Autenticando..."):
                    res = fazer_login(email.strip().lower(), senha)

                if res["ok"]:
                    uid  = res["user"].get("id", "")
                    nome = res["user"].get("user_metadata", {}).get("nome", email.split("@")[0].title())

                    st.session_state["token"]      = res["token"]
                    st.session_state["user_id"]    = uid
                    st.session_state["user_email"] = res["user"].get("email", email)
                    st.session_state["user_nome"]  = nome

                    # Verifica perfil e aprovação
                    from auth import is_admin, usuario_aprovado
                    if is_admin(uid):
                        st.success(f"✅ Bem-vindo, {nome}!")
                        st.switch_page("pages/2_Admin.py")
                    elif usuario_aprovado(uid):
                        st.success(f"✅ Bem-vindo, {nome}!")
                        st.switch_page("pages/3_Atendimentos.py")
                    else:
                        st.warning("⏳ Conta aguardando aprovação do administrador.")
                else:
                    st.error(f"❌ {res['erro']}")

    # ── ABA CRIAR CONTA ───────────────────────────────────────────
    with aba_conta:
        with st.form("f_conta"):
            nome_novo  = st.text_input("Nome completo", placeholder="João Silva")
            email_novo = st.text_input("E-mail", placeholder="seu@email.com.br")
            senha_nova = st.text_input("Senha", type="password", placeholder="mín. 6 caracteres")
            senha_conf = st.text_input("Confirmar senha", type="password", placeholder="repita a senha")
            btn2       = st.form_submit_button("Solicitar Acesso →", use_container_width=True)

        if btn2:
            if not all([nome_novo.strip(), email_novo.strip(), senha_nova, senha_conf]):
                st.error("Preencha todos os campos.")
            elif len(senha_nova) < 6:
                st.error("A senha deve ter pelo menos 6 caracteres.")
            elif senha_nova != senha_conf:
                st.error("As senhas não conferem.")
            else:
                with st.spinner("Criando conta..."):
                    res2 = criar_conta(email_novo.strip().lower(), senha_nova, nome_novo.strip())
                if res2["ok"]:
                    st.success("✅ Conta criada! Aguarde a aprovação do administrador para acessar o sistema.")
                else:
                    st.error(f"❌ {res2.get('erro', 'Erro desconhecido.')}")

    st.markdown('<div class="rodape">Problemas de acesso? Contate o administrador.</div>',
                unsafe_allow_html=True)
