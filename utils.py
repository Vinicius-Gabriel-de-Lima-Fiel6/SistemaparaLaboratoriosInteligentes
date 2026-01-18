# No seu arquivo central de ferramentas
def aplicar_estilo():
    import streamlit as st
    import os
    if os.path.exists("style.css"):
        with open("style.css") as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
