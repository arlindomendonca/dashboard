"""
components/header.py — Header compartilhado com navegação entre páginas.
"""
import streamlit as st

# CSS do header (injetado uma vez)
HEADER_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
* { font-family: 'Inter', sans-serif; }

.stApp { background-color: #0f1117; }
[data-testid="stSidebar"],
[data-testid="collapsedControl"] { display: none !important; }

.header-bar {
    background: linear-gradient(135deg, #1a1d2e, #1e2340);
    border-bottom: 1px solid #2e3450;
    padding: 12px 28px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 24px;
    border-radius: 0 0 14px 14px;
}
.header-brand {
    display: flex; align-items: center; gap: 10px;
}
.header-logo  { font-size: 26px; }
.header-title { font-size: 16px; font-weight: 800; color: #e2e8f0; line-height: 1.2; }
.header-sub   { font-size: 11px; color: #64748b; }

.nav-btn button {
    background: transparent !important;
    border: 1px solid #2e3450 !important;
    color: #94a3b8 !important;
    border-radius: 8px !important;
    padding: 6px 16px !important;
    font-size: 13px !important;
    font-weight: 600 !important;
    height: 36px !important;
    transition: all 0.2s !important;
}
.nav-btn button:hover {
    border-color: #6366f1 !important;
    color: #a5b4fc !important;
    background: rgba(99,102,241,0.08) !important;
}
.nav-btn-active button {
    background: rgba(99,102,241,0.15) !important;
    border: 1px solid #6366f1 !important;
    color: #a5b4fc !important;
    border-radius: 8px !important;
    padding: 6px 16px !important;
    font-size: 13px !important;
    font-weight: 700 !important;
    height: 36px !important;
}

/* KPIs */
.kpi {
    background: linear-gradient(135deg, #1e2130, #252a3d);
    border: 1px solid #2e3450; border-radius: 12px;
    padding: 14px 16px; text-align: center;
    box-shadow: 0 4px 14px rgba(0,0,0,0.3);
}
.kpi-lbl { font-size: 10px; color: #8b92a5; text-transform: uppercase;
           letter-spacing: 1px; margin-bottom: 4px; }
.kpi-val { font-size: 24px; font-weight: 800; line-height: 1.1; }
.kpi-sub { font-size: 10px; color: #5c6880; margin-top: 2px; }

/* Filtro box */
.filtro-box {
    background: #1e2130; border: 1px solid #2e3450;
    border-radius: 12px; padding: 18px 22px; margin-bottom: 20px;
}
.sec-label {
    font-size: 11px; font-weight: 700; color: #94a3b8;
    text-transform: uppercase; letter-spacing: 1px; margin-bottom: 12px;
}

/* Inputs */
div[data-testid="stDateInput"] label,
div[data-testid="stTextInput"] label,
div[data-testid="stSelectbox"] label {
    font-size: 12px; color: #94a3b8; font-weight: 600;
}
div[data-testid="stDateInput"] input,
div[data-testid="stTextInput"] input {
    background: #0d1117 !important; border: 1px solid #2e3450 !important;
    color: #e2e8f0 !important; border-radius: 8px !important; font-size: 13px !important;
}
div[data-testid="stDataFrame"] {
    border: 1px solid #2e3450 !important; border-radius: 12px !important;
    overflow: hidden !important;
}
div[data-testid="stDataFrame"] thead th {
    background-color: #13162280 !important; color: #94a3b8 !important;
    font-size: 11px !important; font-weight: 700 !important;
    text-transform: uppercase !important;
}
div[data-testid="stDataFrame"] tbody td {
    color: #cbd5e1 !important; font-size: 13px !important;
    border-bottom: 1px solid #1a1d27 !important;
}

.live-pill {
    display: inline-flex; align-items: center; gap: 5px;
    background: #0d1f0d; border: 1px solid #166534;
    border-radius: 20px; padding: 3px 10px;
    font-size: 11px; font-weight: 600; color: #4ade80;
}
.dot { width: 6px; height: 6px; border-radius: 50%; background: #22c55e;
       animation: pulse 2s infinite; }
@keyframes pulse { 0%,100%{opacity:1;transform:scale(1)} 50%{opacity:.3;transform:scale(1.5)} }
hr { border-color: #2e3450; }
</style>
"""

def render(pagina_atual: str):
    """
    Renderiza o header com navegação.
    pagina_atual: 'atendimentos' | 'configuracoes'
    """
    st.markdown(HEADER_CSS, unsafe_allow_html=True)

    col_brand, col_nav = st.columns([4, 2])

    with col_brand:
        st.markdown("""
        <div class="header-brand" style="padding-top:4px">
            <span class="header-logo">🏛️</span>
            <div>
                <div class="header-title">Sistema de Atendimentos</div>
                <div class="header-sub">Prefeitura de Rio Verde · API Gove</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_nav:
        n1, n2 = st.columns(2)
        with n1:
            css_class = "nav-btn-active" if pagina_atual == "atendimentos" else "nav-btn"
            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
            if st.button("📋 Atendimentos", use_container_width=True, key="nav_atend"):
                st.switch_page("app.py")
            st.markdown('</div>', unsafe_allow_html=True)
        with n2:
            css_class = "nav-btn-active" if pagina_atual == "configuracoes" else "nav-btn"
            st.markdown(f'<div class="{css_class}">', unsafe_allow_html=True)
            if st.button("⚙️ Configurações", use_container_width=True, key="nav_config"):
                st.switch_page("pages/Configuracoes.py")
            st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<hr style='margin: 0 0 20px 0'>", unsafe_allow_html=True)
