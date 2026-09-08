import streamlit as st

def load_css(file_name):
    with open(file_name) as f:
        st.markdown(
            f"<style>{f.read()}</style>",
            unsafe_allow_html=True
        )

def theme_switcher():

    if "theme" not in st.session_state:
        st.session_state.theme = "light"

    if st.button(
        "🌙 Escuro"
        if st.session_state.theme == "light"
        else "☀️ Claro"
    ):
        st.session_state.theme = (
            "dark"
            if st.session_state.theme == "light"
            else "light"
        )
        st.rerun()

    # Shared styles
    load_css("styles/components.css")

    # Theme colors
    if st.session_state.theme == "dark":
        load_css("styles/dark.css")
    else:
        load_css("styles/light.css")

       

    