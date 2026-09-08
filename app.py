import streamlit as st

from styles.setup import setup_page
from utils.auth import require_login


st.set_page_config(
    page_title="Sistema de Consultas",
    layout="wide",
)


setup_page()

st.set_page_config(
    page_title="Sistema de Consultas",
    layout="wide",
)

def main():

    require_login("Faça Login")

if __name__ == "__main__":
    main()