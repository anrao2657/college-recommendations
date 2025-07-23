import streamlit as st
import pandas as pd

# === Page Configuration ===
st.set_page_config(
    page_title="COMEDK Mock Round 2025 Cutoff Viewer",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# === CSS Styling ===
st.markdown("""
<style>
.main .block-container {
    padding-top: 0rem;
    margin-top: -16rem;
    padding-bottom: 0rem;
    padding-left: 0.5rem;
    padding-right: 0.5rem;
    max-width: 100%;
}
div[data-testid="stDataFrame"] div[role="grid"] {
    overflow-x: auto;
    font-size: 12px;
    border: 1px solid #444;
    border-radius: 4px;
}
div[data-testid="stDataFrame"] div[role="gridcell"] {
    white-space: normal !important;
    text-overflow: ellipsis;
}
/* Adjust tab font size */
div[data-testid="stTabs"] button {
    font-size: 12px;
}
</style>
""", unsafe_allow_html=True)

# === Title ===
st.markdown("<h3>🎓 COMEDK Mock Round 2025 Cutoff Viewer</h3>", unsafe_allow_html=True)
st.markdown("_Data source: Engineering - Cut-off Ranks Mock Round Allotment Notified on 22.07.2025")



# === Load Data with Cache ===
@st.cache_data
def load_data():
    return pd.read_csv("mock_normalized_2025.csv")

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


# === Track filter change to reset pagination ===
if 'last_college_input' not in st.session_state or st.session_state['last_college_input'] != college_input:
    st.session_state["page_number_tab1"] = 1
    st.session_state["rec_page_number"] = 1
st.session_state['last_college_input'] = college_input

if 'last_selected_category' not in st.session_state or st.session_state['last_selected_category'] != selected_category:
    st.session_state["page_number_tab1"] = 1
    st.session_state["rec_page_number"] = 1
st.session_state['last_selected_category'] = selected_category

if 'last_branch_keyword_input' not in st.session_state or st.session_state['last_branch_keyword_input'] != branch_keyword_input:
    st.session_state["page_number_tab1"] = 1
    st.session_state["rec_page_number"] = 1
st.session_state['last_branch_keyword_input'] = branch_keyword_input

if 'last_selected_city' not in st.session_state or st.session_state['last_selected_city'] != selected_city:
    st.session_state["page_number_tab1"] = 1
    st.session_state["rec_page_number"] = 1
st.session_state['last_selected_city'] = selected_city

if 'last_min_rank' not in st.session_state or st.session_state['last_min_rank'] != min_rank:
    st.session_state["page_number_tab1"] = 1
    st.session_state["rec_page_number"] = 1
st.session_state['last_min_rank'] = min_rank

if 'last_max_rank' not in st.session_state or st.session_state['last_max_rank'] != max_rank:
    st.session_state["page_number_tab1"] = 1
    st.session_state["rec_page_number"] = 1
st.session_state['last_max_rank'] = max_rank

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
    st.markdown("### Colleges")
    filtered_df = filter_dataframe(df)

    if not filtered_df.empty:
        # Order by College Rank before display
        ordered_df = filtered_df.sort_values(by=["College Rank", "closing_rank"])
        ordered_df_display = ordered_df[default_columns].reset_index(drop=True)
        ordered_df_display.insert(0, "S.No", ordered_df_display.index + 1)
        ordered_df_display = ordered_df_display.set_index("S.No")
        ordered_df_display = ordered_df_display.rename(columns={"closing_rank": "Closing Rank", "branch": "Branch"})

        record_count_msg = f"Showing {len(ordered_df_display)} records."
        if len(ordered_df_display) > 10:
            record_count_msg += " Scroll to see full results."
        st.markdown(f"<div style='background-color:#f0f2f6; color:#000000; padding:8px; border-radius:4px;'>{record_count_msg}</div>", unsafe_allow_html=True)
        st.dataframe(ordered_df_display, use_container_width=True)

        csv = filtered_df[default_columns].reset_index(drop=True).to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Download Full Results as CSV",
            data=csv,
            file_name='filtered_cutoffs.csv',
            mime='text/csv'
        )
    else:
        st.warning("⚠️ No matching records found. Please adjust your filters and try again.")

# === Tab 2: Rank Recommendations ===
with tab2:
    st.markdown("### Recommended Branches Based on Your Rank")
    entered_rank = st.number_input("Enter your rank to find possible branches", min_value=0, step=1, value=100, key="entered_rank_tab")

    recommendation_df = filter_dataframe(df)
    recommendation_df = recommendation_df[
        (recommendation_df["closing_rank"] >= entered_rank) &
        (recommendation_df["closing_rank"] <= max_rank)
    ]

    if not recommendation_df.empty:
        st.markdown(f"✅ Showing recommendations for rank **{entered_rank}** in category **'{selected_category}'**.")

        # Order by College Rank before display
        ordered_rec_df = recommendation_df.sort_values(by=["College Rank", "closing_rank"])
        rec_df_display = ordered_rec_df[default_columns].reset_index(drop=True)
        rec_df_display.insert(0, "S.No", rec_df_display.index + 1)
        rec_df_display = rec_df_display.set_index("S.No")
        rec_df_display = rec_df_display.rename(columns={"closing_rank": "Closing Rank", "branch": "Branch"})

        record_count_rec_msg = f"Showing {len(rec_df_display)} records out of {len(recommendation_df)} total."
        if len(rec_df_display) > 10:
            record_count_rec_msg += " Scroll to see full results."
        st.markdown(f"<div style='background-color:#f0f2f6; color:#000000; padding:8px; border-radius:4px;'>{record_count_rec_msg}</div>", unsafe_allow_html=True)
        st.dataframe(rec_df_display, use_container_width=True)

        # CSV download button for recommendations
        csv_rec = recommendation_df[default_columns].reset_index(drop=True).to_csv(index=False).encode('utf-8')
        st.download_button(
            label="💾 Download Recommendations as CSV",
            data=csv_rec,
            file_name='recommendations_cutoffs.csv',
            mime='text/csv'
        )

    else:
        st.warning("⚠️ No recommendations found. Please adjust filters or rank value.")

# === Footer ===
st.markdown("---")
st.markdown("""
## ⚠️ Disclaimer

This app is **not an official counselling tool**.  
It has been developed solely to assist students in analysing publicly available data efficiently.  
Always refer to **official counselling portals and authorities** for final decisions.
""")
st.caption("Developed with ❤️ using Streamlit | © 2025 YourTeamName")
