"""
app.py — Entry point. Redireciona para Gestão de Atendimentos.
"""
import streamlit as st

st.set_page_config(
    page_title="Sistema de Atendimentos",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)
st.switch_page("pages/1_Atendimentos.py")
