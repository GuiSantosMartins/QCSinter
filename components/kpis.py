import pandas as pd
import streamlit as st


def show_kpis(df_wastage):
    st.subheader("Quadro Geral")

    total_wastage = _sum_column(df_wastage, "qtd")
    total_producao = _total_production(df_wastage)
    taxa_media = total_wastage / total_producao if total_producao > 0 else 0
    total_lotes = _count_unique_lotes(df_wastage)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Perda Total", f"{total_wastage:,.0f}")
    col2.metric("Total Produzido", f"{total_producao:,.0f}")
    col3.metric("Percentual de Quebra", f"{taxa_media:.2%}")
    col4.metric("Lotes", f"{total_lotes:,.0f}")


def _sum_column(df, column):
    if column not in df.columns:
        return 0
    return pd.to_numeric(df[column], errors="coerce").fillna(0).sum()


def _total_production(df):
    production_col = "qtd_prdz" if "qtd_prdz" in df.columns else "production"
    if production_col not in df.columns:
        return 0

    unique_keys = [
        col
        for col in ["part", "lote", "machine"]
        if col in df.columns
    ]
    base = df.drop_duplicates(unique_keys) if unique_keys else df
    return pd.to_numeric(base[production_col], errors="coerce").fillna(0).sum()


def _count_unique_lotes(df):
    keys = [col for col in ["part", "lote"] if col in df.columns]
    if not keys:
        return len(df)
    return len(df.drop_duplicates(keys))
