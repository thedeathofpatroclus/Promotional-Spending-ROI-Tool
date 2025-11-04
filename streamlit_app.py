import pandas as pd
import streamlit as st
from streamlit_extras.metric_cards import style_metric_cards

# -------------------------------
# 1. Load and Merge Data
# -------------------------------
def load_data():
    trip_df = pd.read_csv("TRIP_FILE.csv")
    patron_df = pd.read_csv("PATRON_DATABASE.csv")
    merged_df = pd.merge(trip_df, patron_df, on=['PATRON_ID', 'PROP_NUM'], how='inner')
    return merged_df

# -------------------------------
# 2. Segment Patrons
# -------------------------------
def segment_patrons(df):
    df['Value_Tier'] = pd.qcut(df['COIN_IN'], q=[0, 0.2, 0.6, 1.0], labels=['Low', 'Mid', 'High'])
    df['Freq_Tier'] = pd.cut(df['TRIPS'], bins=[0, 2, 5, 30], labels=['Rare', 'Occasional', 'Frequent'])
    return df[['PATRON_ID', 'PROP_NUM', 'TRIPS', 'COIN_IN', 'Value_Tier', 'Freq_Tier']]

# -------------------------------
# 3. Define Hardcoded Assumptions
# -------------------------------
def get_promotion_costs():
    return {
        '$50 Free Play': 50,
        '$100 Free Play': 100,
        'Hotel Comp': 120,
        'SMS Campaign': 2,
        'VIP Event Invite': 250
    }

def get_response_rates():
    return {
        ('High', 'Frequent'): {'$50 Free Play': 0.4, '$100 Free Play': 0.45, 'Hotel Comp': 0.3, 'SMS Campaign': 0.5, 'VIP Event Invite': 0.35},
        ('High', 'Occasional'): {'$50 Free Play': 0.3, '$100 Free Play': 0.35, 'Hotel Comp': 0.25, 'SMS Campaign': 0.4, 'VIP Event Invite': 0.3},
        ('High', 'Rare'): {'$50 Free Play': 0.2, '$100 Free Play': 0.25, 'Hotel Comp': 0.2, 'SMS Campaign': 0.35, 'VIP Event Invite': 0.25},
        ('Mid', 'Frequent'): {'$50 Free Play': 0.3, '$100 Free Play': 0.35, 'Hotel Comp': 0.25, 'SMS Campaign': 0.4, 'VIP Event Invite': 0.3},
        ('Mid', 'Occasional'): {'$50 Free Play': 0.25, '$100 Free Play': 0.3, 'Hotel Comp': 0.2, 'SMS Campaign': 0.35, 'VIP Event Invite': 0.2},
        ('Mid', 'Rare'): {'$50 Free Play': 0.15, '$100 Free Play': 0.2, 'Hotel Comp': 0.15, 'SMS Campaign': 0.25, 'VIP Event Invite': 0.15},
        ('Low', 'Frequent'): {'$50 Free Play': 0.2, '$100 Free Play': 0.25, 'Hotel Comp': 0.2, 'SMS Campaign': 0.3, 'VIP Event Invite': 0.2},
        ('Low', 'Occasional'): {'$50 Free Play': 0.15, '$100 Free Play': 0.2, 'Hotel Comp': 0.15, 'SMS Campaign': 0.2, 'VIP Event Invite': 0.15},
        ('Low', 'Rare'): {'$50 Free Play': 0.15, '$100 Free Play': 0.2, 'Hotel Comp': 0.1, 'SMS Campaign': 0.2, 'VIP Event Invite': 0.1}
    }

# -------------------------------
# 4. Calculate Average LTV
# -------------------------------
def calculate_average_ltv(df, value_tier, freq_tier, assumed_retention_months=12):
    segment_df = df[(df['Value_Tier'] == value_tier) & (df['Freq_Tier'] == freq_tier)]
    if segment_df.empty:
        return 0
    avg_monthly_coin_in = segment_df['COIN_IN'].mean()
    hold_percentage = 0.08
    ltv = avg_monthly_coin_in * hold_percentage * assumed_retention_months
    return ltv

# -------------------------------
# 5. Calculate Expected ROI
# -------------------------------
def calculate_roi(df, value_tier, freq_tier, promo_type, campaign_size, response_rate_override=None):
    promo_costs = get_promotion_costs()
    response_rates = get_response_rates()

    cost_per_patron = promo_costs[promo_type]
    default_response_rate = response_rates.get((value_tier, freq_tier), {}).get(promo_type, 0)

    response_rate = response_rate_override if response_rate_override is not None else default_response_rate

    if response_rate == 0:
        return None

    avg_ltv = calculate_average_ltv(df, value_tier, freq_tier)

    expected_responders = campaign_size * response_rate
    incremental_revenue = expected_responders * avg_ltv
    total_promo_cost = campaign_size * cost_per_patron

    roi = (incremental_revenue - total_promo_cost) / total_promo_cost if total_promo_cost != 0 else 0

    return {
        'Average_LTV': avg_ltv,
        'Expected_Responders': expected_responders,
        'Incremental_Revenue': incremental_revenue,
        'Total_Promo_Cost': total_promo_cost,
        'ROI': roi
    }

# -------------------------------
# 6. Streamlit App
# -------------------------------
def main():
    st.set_page_config(page_title="PromoPlay Lab 🎯", layout="wide")
    st.markdown("""
        <style>
        .purple-gold-box {
            background-color: #4B0082;
            color: gold;
            padding: 2rem;
            border-radius: 1rem;
            text-align: center;
            font-size: 1.2rem;
        }
        </style>
    """, unsafe_allow_html=True)

    st.sidebar.title("PromoPlay Lab 🎯")
    st.sidebar.markdown("A simulator for strategic casino promotions.")

    merged_df = load_data()
    segmented_df = segment_patrons(merged_df)

    st.title("🎰 Casino Promo Strategy Simulator")

    value_tier = st.sidebar.selectbox("Select Value Tier", ['High', 'Mid', 'Low'])
    freq_tier = st.sidebar.selectbox("Select Frequency Tier", ['Frequent', 'Occasional', 'Rare'])
    promo_type = st.sidebar.selectbox("Choose Promotions", list(get_promotion_costs().keys()))
    campaign_size = st.sidebar.slider("Number of patrons to target", 100, 10000, 1000, step=100)

    default_rate = int(get_response_rates().get((value_tier, freq_tier), {}).get(promo_type, 0) * 100)
    sensitivity = st.sidebar.slider("📊 Adjust Response Rate (%)", 0, 100, default_rate)

    results = calculate_roi(segmented_df, value_tier, freq_tier, promo_type, campaign_size, response_rate_override=sensitivity/100)

    st.markdown(f"### 📊 Segment: `{value_tier} Value / {freq_tier} Frequency`")

    if results:
        col1, col2, col3 = st.columns(3)
        with col1:
            st.markdown(f"""
            <div class="purple-gold-box">
                Projected Trips<br><strong>{segmented_df[(segmented_df['Value_Tier'] == value_tier) & (segmented_df['Freq_Tier'] == freq_tier)]['TRIPS'].mean():.1f}</strong>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class="purple-gold-box">
                Projected Coin-In<br><strong>${segmented_df[(segmented_df['Value_Tier'] == value_tier) & (segmented_df['Freq_Tier'] == freq_tier)]['COIN_IN'].sum():,.2f}</strong>
            </div>""", unsafe_allow_html=True)
        with col3:
            st.markdown(f"""
            <div class="purple-gold-box">
                Estimated ROI<br><strong>{results['ROI']:.2f}x</strong>
            </div>""", unsafe_allow_html=True)

        st.divider()
        st.subheader("🎯 Promotion Details")
        st.write(f"**Average LTV:** ${results['Average_LTV']:.2f}")
        st.write(f"**Expected Responders:** {results['Expected_Responders']:.0f} patrons")
        st.write(f"**Incremental Revenue:** ${results['Incremental_Revenue']:.2f}")
        st.write(f"**Total Promotion Cost:** ${results['Total_Promo_Cost']:.2f}")

    else:
        st.error("No valid ROI calculation for this segment and promotion.")

if __name__ == "__main__":
    main()
