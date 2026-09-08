import pandas as pd
import plotly.express as px
import streamlit as st

def apply_chart_theme(fig_type):

    if st.session_state.get("theme", "light") == "dark":
        fig_type.update_layout(
            paper_bgcolor= "#8d8d8d",
            plot_bgcolor="#8d8d8d",
            font=dict(color="white"),
            legend=dict(font=dict(color="white")),
        )

        fig_type.update_xaxes(
            title_font=dict(color="white"),   # Axis title
            tickfont=dict(color="white"),     # Tick labels
            gridcolor="#3a3a3a",
            zerolinecolor="#3a3a3a",
        )

        fig_type.update_yaxes(
            title_font=dict(color="white"),
            tickfont=dict(color="white"),
            gridcolor="#3a3a3a",
            zerolinecolor="#3a3a3a",
        )

    else:
        fig_type.update_layout(
            paper_bgcolor="#ffffff",
            plot_bgcolor="#ffffff",
            font=dict(color="black"),
            legend=dict(font=dict(color="black")),
        )

        fig_type.update_xaxes(
            title_font=dict(color="black"),
            tickfont=dict(color="black"),
            gridcolor="#dddddd",
            zerolinecolor="#dddddd",
        )

        fig_type.update_yaxes(
            title_font=dict(color="black"),
            tickfont=dict(color="black"),
            gridcolor="#dddddd",
            zerolinecolor="#dddddd",
        )

    return fig_type

def show_machine_chart(df_filtrado):
    st.subheader("Quebra por Máquina")

    wastage_machine = _rate_by(df_filtrado, ["machine"])
    if wastage_machine.empty:
        _show_empty()
        return

    fig_machine = px.bar(
        wastage_machine,
        x="machine",
        y="tax",
        labels={"machine": "Máquina", "tax": "Percentual Quebra"},
    )
    fig_machine.update_yaxes(tickformat=".2%")

    fig_machine = apply_chart_theme(fig_machine)

    st.plotly_chart(fig_machine, use_container_width=True)


def show_top_parts_chart(df_filtrado):
    import pandas as pd
    import streamlit as st

    st.subheader("Peças com Maior Perda")

    top_parts = (
        _rate_by(df_filtrado, ["part"])
        .sort_values("tax", ascending=False)
        .head(10)
        .reset_index(drop=True)
    )

    if top_parts.empty:
        _show_empty()
        return

    top_parts.index = top_parts.index + 1

    top_parts = top_parts.rename(
        columns={
            "part": "Peça",
            "qtd": "Quebras",
            "qtd_prdz": "Produzido",
            "tax": "Taxa",
        }
    )

    
    display_df = top_parts.copy()

    display_df["Quebras"] = display_df["Quebras"].map("{:,.0f}".format)
    display_df["Produzido"] = display_df["Produzido"].map("{:,.0f}".format)
    display_df["Taxa"] = display_df["Taxa"].map("{:.2%}".format)

    st.table(display_df)
    


def show_pie_chart(df_filtrado):
    st.subheader("Distribuição de Quebras")

    if df_filtrado.empty or "type2" not in df_filtrado.columns:
        _show_empty()
        return

    wastage_type = (
        df_filtrado.groupby("type2", dropna=False)["qtd"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    if wastage_type["qtd"].sum() <= 0:
        _show_empty()
        return

    fig_pie = px.pie(
        wastage_type,
        names="type2",
        values="qtd",
        hole=0.4,
        labels={"type2": "Tipo de Quebra", "qtd": "Quantidade"},
    )
    fig_pie.update_traces(textposition="inside", textinfo="percent+label")

    fig_pie = apply_chart_theme(fig_pie)

    st.plotly_chart(fig_pie, use_container_width=True)


def show_pareto(df_filtrado):
    st.subheader("Pareto de Quebras")

    if df_filtrado.empty or "type2" not in df_filtrado.columns:
        _show_empty()
        return

    pareto = (
        df_filtrado.groupby("type2", dropna=False)["qtd"]
        .sum()
        .sort_values(ascending=False)
        .reset_index()
    )

    total = pareto["qtd"].sum()
    if total <= 0:
        _show_empty()
        return

    pareto["perc_acumulado"] = pareto["qtd"].cumsum() / total

    fig_pareto = px.bar(
        pareto,
        x="type2",
        y="qtd",
        labels={"type2": "Tipo de Quebra", "qtd": "Quantidade"},
    )
    fig_pareto.add_scatter(
        x=pareto["type2"],
        y=pareto["perc_acumulado"],
        mode="lines+markers",
        name="Percentual acumulado",
        yaxis="y2",
    )
    fig_pareto.update_layout(
        xaxis_tickangle=-45,
        yaxis2={
            "overlaying": "y",
            "side": "right",
            "tickformat": ".0%",
            "range": [0, 1],
        },
        legend={"orientation": "h"},
    )

    fig_pareto = apply_chart_theme(fig_pareto)

    st.plotly_chart(fig_pareto, use_container_width=True)


def show_heatmap(df_filtrado):
    st.subheader("Mapa de Quebras por Máquina")

    required = {"machine", "type2", "qtd"}
    if df_filtrado.empty or not required.issubset(df_filtrado.columns):
        _show_empty()
        return

    heatmap_data = (
        df_filtrado.groupby(["machine", "type2"], dropna=False)["qtd"]
        .sum()
        .reset_index()
    )

    heatmap_pivot = heatmap_data.pivot(
        index="machine",
        columns="type2",
        values="qtd",
    ).fillna(0)

    if heatmap_pivot.empty:
        _show_empty()
        return

    fig_heatmap = px.imshow(
        heatmap_pivot,
        aspect="auto",
        labels={"x": "Tipo de Quebra", "y": "Máquina", "color": "Qtd"},
    )

    fig_heatmap = apply_chart_theme(fig_heatmap)

    st.plotly_chart(fig_heatmap, use_container_width=True)


def _rate_by(df, group_cols):
    required = set(group_cols + ["qtd", "qtd_prdz"])
    if df.empty or not required.issubset(df.columns):
        return pd.DataFrame(columns=group_cols + ["qtd", "qtd_prdz", "tax"])

    qtd = (
        df.groupby(group_cols, dropna=False)["qtd"]
        .sum()
        .reset_index()
    )

    unique_keys = list(
        dict.fromkeys(
            group_cols
            + [col for col in ["part", "lote", "machine"] if col in df.columns]
        )
    )
    production = (
        df.drop_duplicates(unique_keys)
        .groupby(group_cols, dropna=False)["qtd_prdz"]
        .sum()
        .reset_index()
    )
        
    result = qtd.merge(production, on=group_cols, how="left")
    result["qtd"] = pd.to_numeric(result["qtd"], errors="coerce").fillna(0)
    result["qtd_prdz"] = pd.to_numeric(result["qtd_prdz"], errors="coerce").fillna(0)
    denominator = result["qtd_prdz"].where(result["qtd_prdz"] != 0)
    result["tax"] = (result["qtd"] / denominator).fillna(0)
    return result


def _show_empty():
    st.info("Sem dados para exibir.")
