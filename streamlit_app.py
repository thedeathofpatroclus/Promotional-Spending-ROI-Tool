import pandas as pd
import streamlit as st
from pathlib import Path

st.set_page_config(page_title="PromoPlay Lab 🎯", layout="wide")

# --- Safe DATA_DIR handling ---
try:
    DATA_DIR = Path(__file__).parent
except NameError:
    DATA_DIR = Path.cwd()  # fallback when __file__ not defined (e.g., Streamlit Cloud)

@st.cache_data(show_spinner=False)
def load_data():
    trip_path = DATA_DIR / "TRIP_FILE.csv"
    patron_path = DATA_DIR / "PATRON_DATABASE.csv"

    if trip_path.exists() and patron_path.exists():
        trip_df = pd.read_csv(trip_path)
        patron_df = pd.read_csv(patron_path)
    else:
        st.warning("Couldn't find local CSVs. Please upload them below ⬇️")
        trip_file = st.file_uploader("Upload TRIP_FILE.csv", type="csv", key="trip")
        patron_file = st.file_uploader("Upload PATRON_DATABASE.csv", type="csv", key="patron")
        if not trip_file or not patron_file:
            st.stop()
        trip_df = pd.read_csv(trip_file)
        patron_df = pd.read_csv(patron_file)

    # Check required columns
    required_trip_cols = {"PATRON_ID", "PROP_NUM", "TRIPS", "COIN_IN"}
    required_patron_cols = {"PATRON_ID", "PROP_NUM"}
    if not required_trip_cols.issubset(trip_df.columns) or not required_patron_cols.issubset(patron_df.columns):
        st.error("Missing required columns in one or both CSVs.")
        st.stop()

    # Convert numeric columns
    trip_df["TRIPS"] = pd.to_numeric(trip_df["TRIPS"], errors="coerce")
    trip_df["COIN_IN"] = pd.to_numeric(trip_df["COIN_IN"], errors="coerce")

    merged_df = pd.merge(trip_df, patron_df, on=["PATRON_ID", "PROP_NUM"], how="inner")
    return merged_df


def segment_patrons(df):
    # Value tiers
    try:
        df["Value_Tier"] = pd.qcut(
            df["COIN_IN"].fillna(0),
            q=[0, 0.2, 0.6, 1.0],
            labels=["Low", "Mid", "High"],
            duplicates="drop"
        )
    except Exception:
        df["Value_Tier"] = pd.cut(
            df["COIN_IN"].fillna(0),
            bins=[-float("inf"), df["COIN_IN"].median(), df["COIN_IN"].quantile(0.8), float("inf")],
            labels=["Low", "Mid", "High"],
            include_lowest=True
        )

    # Frequency tiers
    df["Freq_Tier"] = pd.cut(
        df["TRIPS"].fillna(0),
        bins=[-0.001, 2, 5, float("inf")],
        labels=["Rare", "Occasional", "Frequent"],
        include_lowest=True,
        right=True
    )

    return df


# --- MAIN APP ---
st.title("🎰 PromoPlay Lab – Chickasaw Nation")

df = load_data()
segmented_df = segment_patrons(df)

st.success("✅ Data loaded and segmented successfully!")
st.dataframe(segmented_df.head(10))

# Example aggregation
st.subheader("📊 Segment Summary")
summary = (
    segmented_df.groupby(["Value_Tier", "Freq_Tier"])
    .agg({"PATRON_ID": "count", "TRIPS": "mean", "COIN_IN": "mean"})
    .rename(columns={"PATRON_ID": "Patron Count"})
)
st.dataframe(summary)
