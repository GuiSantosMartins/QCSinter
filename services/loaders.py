from pathlib import Path

import pandas as pd
import streamlit as st


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
CACHE_TTL_SECONDS = 60


def _read_excel(filename):
    return pd.read_excel(DATA_DIR / filename, engine="openpyxl")


def _clean_text(df):
    df = df.copy()
    for col in df.select_dtypes(include=["object", "string"]).columns:
        df[col] = df[col].map(_clean_text_value, na_action="ignore")
    return df


def _clean_text_value(value):
    if not isinstance(value, str):
        return value
    return value.replace("\xa0", " ").strip()


def _key_value(value):
    if pd.isna(value):
        return pd.NA

    if isinstance(value, float) and value.is_integer():
        return str(int(value))

    text = str(value).replace("\xa0", " ").strip()
    if text.endswith(".0"):
        candidate = text[:-2]
        if candidate.isdigit():
            return candidate
    return text


def _normalize_keys(df, columns=("part", "lote", "of")):
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = df[col].map(_key_value, na_action="ignore")
    return df


def _numeric_columns(df, columns):
    df = df.copy()
    for col in columns:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df


def _excel_dates(series):
    if pd.api.types.is_datetime64_any_dtype(series):
        return pd.to_datetime(series, errors="coerce")

    numeric = pd.to_numeric(series, errors="coerce")
    text_values = series.mask(numeric.notna())
    text_dates = pd.to_datetime(text_values, errors="coerce", dayfirst=True)
    serial_dates = pd.to_datetime(
        numeric,
        errors="coerce",
        origin="1899-12-30",
        unit="D",
    )
    return text_dates.fillna(serial_dates)


def _safe_rate(numerator, denominator):
    denominator = denominator.where(denominator != 0)
    return (numerator / denominator).fillna(0)


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def carregar_wastage():
    df = _read_excel("dbwastagetype.xlsm")
    df = _clean_text(df)
    df = _normalize_keys(df)

    if "tax%" in df.columns:
        df = df.drop(columns=["tax%"])

    df = _numeric_columns(df, ["qtd", "qtd_prdz"])
    df["tax"] = _safe_rate(df["qtd"], df["qtd_prdz"])

    return df


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def carregar_quebras():
    df = _read_excel("dbquebras.xlsm")
    df = _clean_text(df)
    df = _normalize_keys(df)
    df = _numeric_columns(df, ["produzido", "taxaquebra", "processado1", "sum"])
    return df


@st.cache_data(ttl=CACHE_TTL_SECONDS)
def carregar_setup():
    df = _read_excel("dbsetup.xlsm")
    df = _clean_text(df)
    df = _normalize_keys(df)
    df = _numeric_columns(df, ["n", "qty", "production"])

    if "date" in df.columns:
        df["date"] = _excel_dates(df["date"])

    return df


def carregar_metricas():
    return carregar_quebras()


def carregar_production():
    return carregar_quebras()
