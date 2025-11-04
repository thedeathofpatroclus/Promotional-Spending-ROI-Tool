import pandas as pd
import streamlit as st
from pathlib import Path

# Call this as the first Streamlit call in the script (top-level is safest)
st.set_page_config(page_title="PromoPlay Lab 🎯", layout="wide")

DATA_DIR = Path(__file__).parent  # folder that contains streamlit_app.py

@st.cache_data(show_spinner=False)
def load_data():
    # 1) Try script-relative files
    trip_path = DATA_DIR / "TRIP_FILE.csv"
    patron_path = DATA_DIR / "PATRON_DATABASE.csv"

    try:
        trip_df = pd.read_csv(trip_path)
        patron_df = pd.read_csv(patron_path)
    except FileNotFoundError:
        # 2) Fall back to user upload
        st.warning("Couldn’t find local CSVs. Please upload them.")
        t = st.file_uploader("Upload TRIP_FILE.csv", type="csv", key="trip")
        p = st.file_uploader("Upload PATRON_DATABASE.csv", type="csv", key="patron")
        if t is None or p is None:
            st.stop()
        trip_df = pd.read_csv(t)
        patron_df = pd.read_csv(p)

    # Standardize and coerce types
    required_trip_cols = {"PATRON_ID", "PROP_NUM", "TRIPS", "COIN_IN"}
    required_patron_cols = {"PATRON_ID", "PROP_NUM"}
    missing_trip = required_trip_cols - set(trip_df.columns)
    missing_patron = required_patron_cols - set(patron_df.columns)
    if missing_trip or missing_patron:
        st.error(f"Missing columns. Trip missing: {missing_trip}; Patron missing: {missing_patron}")
        st.stop()

    # Coerce numerics
    for c in ["TRIPS", "COIN_IN"]:
        trip_df[c] = pd.to_numeric(trip_df[c], errors="coerce")

    merged_df = pd.merge(trip_df, patron_df, on=["PATRON_ID", "PROP_NUM"], how="inner")
    return merged_df


def segment_patrons(df):
    # Value tiers by quantile with a safe fallback
    try:
        df["Value_Tier"] = pd.qcut(
            df["COIN_IN"].fillna(0),
            q=[0, 0.2, 0.6, 1.0],
            labels=["Low", "Mid", "High"],
            duplicates="drop"
        )
    except Exception:
        # Fallback: fixed cuts
        df["Value_Tier"] = pd.cut(
            df["COIN_IN"].fillna(0),
            bins=[-float("inf"), df["COIN_IN"].median(), df["COIN_IN"].quantile(0.8), float("inf")],
            labels=["Low", "Mid", "High"],
            include_lowest=True
        )

    # Frequency tiers (include zeros and lowest boundary)
    df["Freq_Tier"] = pd.cut(
        df["TRIPS"].fillna(0),
        bins=[-0.001, 2, 5, float("inf")],
        labels=["Rare", "Occasional", "Frequent"],
        include_lowest=True,
        right=True
    )
    return df[["PATRON_ID", "PROP_NUM", "TRIPS", "COIN_IN", "Value_Tier", "Freq_Tier"]]
