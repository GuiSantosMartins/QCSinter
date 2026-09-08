import pandas as pd


def apply_filters(df, filtros):
    df_filtrado = df.copy()

    df_filtrado = _apply_multi_filter(df_filtrado, filtros, "part", "part")
    df_filtrado = _apply_multi_filter(df_filtrado, filtros, "lote", "lote")
    df_filtrado = _apply_multi_filter(df_filtrado, filtros, "machine", "machine")
    df_filtrado = _apply_multi_filter(df_filtrado, filtros, "customer", "customer")
    df_filtrado = _apply_multi_filter(df_filtrado, filtros, "site", "type")
    df_filtrado = _apply_multi_filter(df_filtrado, filtros, "typewastage", "type2")

    date_range = filtros.get("date_range")
    if (
        isinstance(date_range, (list, tuple))
        and len(date_range) == 2
        and "date" in df_filtrado.columns
    ):
        dates = pd.to_datetime(df_filtrado["date"], errors="coerce")
        start_date, end_date = date_range
        start_date = pd.to_datetime(start_date).date()
        end_date = pd.to_datetime(end_date).date()
        df_filtrado = df_filtrado[
            (dates.dt.date >= start_date)
            & (dates.dt.date <= end_date)
        ]

    percent_filter = filtros.get("percent_filter", "Todos")
    if "tax" in df_filtrado.columns:
        if percent_filter == "Acima de 3%":
            df_filtrado = df_filtrado[df_filtrado["tax"] > 0.03]
        elif percent_filter == "Abaixo de 3%":
            df_filtrado = df_filtrado[df_filtrado["tax"] <= 0.03]

    return df_filtrado


def _apply_multi_filter(df, filtros, filter_key, column):
    selected = filtros.get(filter_key)
    if selected and column in df.columns:
        return df[df[column].isin(selected)]
    return df
