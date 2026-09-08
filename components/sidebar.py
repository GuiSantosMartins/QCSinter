import pandas as pd
import streamlit as st


def build_sidebar(df_wastage):
    st.sidebar.header("Filtros")

    filtros = {
        "percent_filter": "Todos",
        "part": [],
        "lote": [],
        "machine": [],
        "customer": [],
        "site": [],
        "typewastage": [],
        "date_range": None,
    }

    if df_wastage.empty:
        st.sidebar.info("Sem dados disponíveis")
        return filtros

    filtros["percent_filter"] = st.sidebar.selectbox(
        "Percentual",
        ["Todos", "Acima de 3%", "Abaixo de 3%"],
    )

    if "date" in df_wastage.columns:
        dates = pd.to_datetime(df_wastage["date"], errors="coerce").dropna()
        if not dates.empty:
            min_date = dates.min().date()
            max_date = dates.max().date()
            filtros["date_range"] = st.sidebar.date_input(
                "Período",
                value=(min_date, max_date),
                min_value=min_date,
                max_value=max_date,
            )

    filtros["part"] = _multiselect(df_wastage, "part", "Peça")
    filtros["lote"] = _multiselect(df_wastage, "lote", "Lote")
    filtros["machine"] = _multiselect(df_wastage, "machine", "Processo")
    filtros["customer"] = _multiselect(df_wastage, "customer", "Cliente")
    filtros["site"] = _multiselect(df_wastage, "type", "Local")
    filtros["typewastage"] = _multiselect(df_wastage, "type2", "Tipo de quebra")

    return filtros


def _multiselect(df, column, label):
    if column not in df.columns:
        return []

    options = [
        value
        for value in df[column].dropna().unique()
        if str(value).strip()
    ]
    options = sorted(options, key=lambda value: str(value).casefold())
    return st.sidebar.multiselect(label, options)
