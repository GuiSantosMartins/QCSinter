import pandas as pd
import streamlit as st

from styles.setup import setup_page

st.set_page_config(
    page_title="Sistema de Consultas",
    layout="wide",
)


setup_page()

from components.charts import (
    show_heatmap,
    show_machine_chart,
    show_pareto,
    show_pie_chart,
    show_top_parts_chart,
)
from components.kpis import show_kpis
from components.sidebar import build_sidebar
from services.filters import apply_filters
from services.loaders import carregar_setup, carregar_wastage
from utils.auth import require_login

def main():
    require_login("Faça Login")

    st.title ("Análise de Quebras")

    df_final = montar_base_wastage()
    if df_final.empty:
        st.warning("Nenhum dado encontrado nos arquivos XLSM.")
        return

    filtros = build_sidebar(df_final)
    df_filtrado = apply_filters(df_final, filtros)

    show_kpis(df_filtrado)

    col1, col2 = st.columns([1.2, 1])
    with col1:
        show_machine_chart(df_filtrado)
    with col2:
        show_top_parts_chart(df_filtrado)

    col3, col4 = st.columns(2)
    with col3:
        show_pie_chart(df_filtrado)
    with col4:
        show_pareto(df_filtrado)

    show_heatmap(df_filtrado)
    show_table(df_filtrado)


def montar_base_wastage():
    df_wastage = carregar_wastage()
    df_setup = carregar_setup()

    setup_cols = [
        col
        for col in ["part", "lote", "date", "setup", "status", "production"]
        if col in df_setup.columns
    ]

    if {"part", "lote"}.issubset(df_setup.columns):
        df_setup = df_setup[setup_cols].drop_duplicates(["part", "lote"])
        return df_wastage.merge(df_setup, on=["part", "lote"], how="left")

    return df_wastage


def show_table(df_filtrado):
    st.subheader("Dados Detalhados")

    columns = [
        col
        for col in [
            "date",
            "part",
            "lote",
            "customer",
            "machine",
            "type",
            "type2",
            "qtd",
            "qtd_prdz",
            "tax",
            "status",
        ]
        if col in df_filtrado.columns
    ]
    table = df_filtrado[columns].copy()
    sort_cols = [col for col in ["date", "part", "lote"] if col in columns]
    if sort_cols:
        table = table.sort_values(sort_cols, ascending=True)

    if "date" in table.columns:
        table["date"] = (
            pd.to_datetime(table["date"], errors="coerce")
            .dt.strftime("%d/%m/%Y")
            .fillna("")
        )

    formatters = {}
    if "qtd" in table.columns:
        formatters["qtd"] = "{:,.0f}"
    if "qtd_prdz" in table.columns:
        formatters["qtd_prdz"] = "{:,.0f}"
    if "tax" in table.columns:
        formatters["tax"] = "{:.2%}"

    st.dataframe(
        table.style.format(formatters, na_rep=""),
        use_container_width=True,
        hide_index=True,
    )


if __name__ == "__main__":
    main()
