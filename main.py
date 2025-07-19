import streamlit as st
import pandas as pd

# === Page Configuration ===
st.set_page_config(
    page_title="COMEDK Cutoff Viewer",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === CSS Styling ===
st.markdown("""
<style>
.main .block-container {
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
    padding-left: 1rem;
    padding-right: 1rem;
    max-width: 100%;
}
div[data-testid="stDataFrame"] div[role="grid"] {
    overflow-x: auto;
}
div[data-testid="stDataFrame"] div[role="gridcell"] {
    white-space: normal !important;
    text-overflow: ellipsis;
}
</style>
""", unsafe_allow_html=True)

# === Title ===
st.title("🎓 COMEDK Branch Cutoff Viewer")

# === Instructions Expander ===
with st.expander("ℹ️ How to use this app"):
    st.write("""
    - Use filters to narrow down colleges.
    - Switch between Colleges and Rank Recommendations tabs.
    - Download results as CSV for offline analysis.
    """)

# === Load Data with Cache ===
@st.cache_data
def load_data():
    return pd.read_csv("comedk_cutoffs_normalized.csv")

with st.spinner("Loading data..."):
    df = load_data()

# === Add College Rank based on minimum closing_rank per College Code ===
college_min_rank = df.groupby("College Code")["closing_rank"].min().reset_index()
college_min_rank["College Rank"] = college_min_rank["closing_rank"].rank(method="min").astype(int)
df = df.merge(college_min_rank[["College Code", "College Rank"]], on="College Code", how="left")

# === Sidebar Filters ===
with st.sidebar.expander("🔧 Filters", expanded=True):
    college_input = st.text_input("🏫 College Name or Code", "").strip().lower()

    category_options = sorted(df['Seat Category'].dropna().unique())
    selected_category = st.selectbox("🎯 Seat Category", category_options)

    all_branches = sorted(df['branch'].unique())
    branch_keyword_input = st.text_input("🔎 Branch Filter (Type to filter branches, e.g. computer, electronics)", "").strip().lower()
    selected_branches = [b for b in all_branches if branch_keyword_input in b.lower()] if branch_keyword_input else all_branches

    st.multiselect(
        "📚 Selected Branches (Auto-selected based on keyword above)",
        options=all_branches,
        default=selected_branches,
        disabled=True
    )

    city_options = sorted(df['City'].dropna().unique())
    selected_city = st.selectbox("🏙️ Select City (Optional)", ["All"] + city_options)

    min_rank, max_rank = st.slider(
        "🔢 Closing Rank Range",
        int(df["closing_rank"].min()),
        int(df["closing_rank"].max()),
        (int(df["closing_rank"].min()), int(df["closing_rank"].max()))
    )

# === Columns to Display ===
default_columns = ["College Code", "College Name", "branch", "closing_rank", "College Rank"]

# === Filtering Function ===
def filter_dataframe(dataframe):
    filtered = dataframe.copy()

    if len(college_input) >= 3:
        filtered = filtered[
            (filtered["College Name"].str.lower().str.contains(college_input)) |
            (filtered["College Code"].str.lower() == college_input)
        ]

    filtered = filtered[filtered["Seat Category"] == selected_category]
    filtered = filtered[filtered["branch"].isin(selected_branches)]

    if selected_city != "All":
        filtered = filtered[filtered["City"] == selected_city]

    filtered = filtered[
        (filtered["closing_rank"] >= min_rank) &
        (filtered["closing_rank"] <= max_rank)
    ]

    return filtered

# === Tabs ===
tab1, tab2 = st.tabs(["Colleges", "Rank Recommendations"])

# === Tab 1: Colleges ===
with tab1:
    st.subheader("📊 Colleges")
    filtered_df = filter_dataframe(df)

    if not filtered_df.empty:
        filtered_df_display = filtered_df[default_columns].sort_values(by="closing_rank").reset_index(drop=True)
        filtered_df_display.insert(0, "S.No", filtered_df_display.index + 1)
        filtered_df_display = filtered_df_display.set_index("S.No")
        st.table(filtered_df_display)

        csv = filtered_df_display.reset_index().to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Download Results as CSV",
            data=csv,
            file_name='filtered_cutoffs.csv',
            mime='text/csv'
        )
    else:
        st.warning("⚠️ No matching records found. Please adjust your filters and try again.")

# === Tab 2: Rank Recommendations ===
with tab2:
    st.subheader("🔮 Recommended Branches Based on Your Rank")
    entered_rank = st.number_input("Enter your rank to find possible branches", min_value=0, step=1, value=100, key="entered_rank_tab")

    recommendation_df = filter_dataframe(df)
    recommendation_df = recommendation_df[
        (recommendation_df["closing_rank"] >= entered_rank) &
        (recommendation_df["closing_rank"] <= max_rank)
    ]

    if not recommendation_df.empty:
        st.success(f"✅ Showing recommendations for rank {entered_rank} in category '{selected_category}'.")
        recommendation_df_display = recommendation_df[default_columns].sort_values(by="closing_rank").reset_index(drop=True)
        recommendation_df_display.insert(0, "S.No", recommendation_df_display.index + 1)
        recommendation_df_display = recommendation_df_display.set_index("S.No")
        st.table(recommendation_df_display)
    else:
        st.warning("⚠️ No recommendations found. Please adjust filters or rank value.")

# === Footer ===
st.markdown("---")
st.caption("Developed with ❤️ using Streamlit | © 2025 YourTeamName")
