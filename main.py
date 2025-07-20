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
</style>
""", unsafe_allow_html=True)

# === Title ===
st.markdown("<h3>🎓 COMEDK Branch Cutoff Viewer</h3>", unsafe_allow_html=True)
st.markdown("_Data source: 2024 Engineering cut-off after all rounds. Notified on 17.07.2025._")



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
    st.markdown("#### Colleges")
    filtered_df = filter_dataframe(df)

    if not filtered_df.empty:
        # Pagination setup
        items_per_page = 20
        total_pages = (len(filtered_df) - 1) // items_per_page + 1
        page_number = st.session_state.get("page_number_tab1", 1)

        start_idx = (page_number - 1) * items_per_page
        end_idx = start_idx + items_per_page
        paginated_df = filtered_df.iloc[start_idx:end_idx]

        paginated_df_display = paginated_df[default_columns].sort_values(by="closing_rank").reset_index(drop=True)
        paginated_df_display.insert(0, "S.No", paginated_df_display.index + 1 + start_idx)
        paginated_df_display = paginated_df_display.set_index("S.No")

        # Rename columns for display clarity
        paginated_df_display = paginated_df_display.rename(columns={
            "closing_rank": "Closing Rank",
            "branch": "Branch"
        })

        st.write(f"Showing {len(paginated_df_display)} records out of {len(filtered_df)} total.")

        st.dataframe(
            paginated_df_display,
            use_container_width=True
        )

        # Compact Next/Prev buttons
        col1, col2, col3 = st.columns([2,1,2])
        with col1:
            prev_clicked_bottom = st.button("⬅️ Prev", key="prev_tab1")
        with col3:
            next_clicked_bottom = st.button("Next ➡️", key="next_tab1")

        if prev_clicked_bottom and page_number > 1:
            page_number -= 1
        if next_clicked_bottom and page_number < total_pages:
            page_number += 1

        st.session_state["page_number_tab1"] = page_number

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
    st.markdown("#### Recommended Branches Based on Your Rank")
    entered_rank = st.number_input("Enter your rank to find possible branches", min_value=0, step=1, value=100, key="entered_rank_tab")

    recommendation_df = filter_dataframe(df)
    recommendation_df = recommendation_df[
        (recommendation_df["closing_rank"] >= entered_rank) &
        (recommendation_df["closing_rank"] <= max_rank)
    ]

    if not recommendation_df.empty:
        # Pagination setup
        items_per_page_rec = 20
        total_pages_rec = (len(recommendation_df) - 1) // items_per_page_rec + 1
        page_number_rec = st.session_state.get("rec_page_number", 1)

        start_idx_rec = (page_number_rec - 1) * items_per_page_rec
        end_idx_rec = start_idx_rec + items_per_page_rec
        paginated_rec_df = recommendation_df.iloc[start_idx_rec:end_idx_rec]

        st.success(f"✅ Showing recommendations for rank {entered_rank} in category '{selected_category}'.")
        recommendation_df_display = paginated_rec_df[default_columns].sort_values(by="closing_rank").reset_index(drop=True)
        recommendation_df_display.insert(0, "S.No", recommendation_df_display.index + 1 + start_idx_rec)
        recommendation_df_display = recommendation_df_display.set_index("S.No")

        # Rename columns for display clarity
        recommendation_df_display = recommendation_df_display.rename(columns={
            "closing_rank": "Closing Rank",
            "branch": "Branch"
        })

        st.write(f"Showing {len(recommendation_df_display)} records out of {len(recommendation_df)} total.")

        st.dataframe(
            recommendation_df_display,
            use_container_width=True
        )

        # Compact Next/Prev buttons
        col1_rec, col2_rec, col3_rec = st.columns([2,1,2])
        with col1_rec:
            prev_clicked_bottom_rec = st.button("⬅️ Prev", key="prev_tab2")
        with col3_rec:
            next_clicked_bottom_rec = st.button("Next ➡️", key="next_tab2")

        if prev_clicked_bottom_rec and page_number_rec > 1:
            page_number_rec -= 1
        if next_clicked_bottom_rec and page_number_rec < total_pages_rec:
            page_number_rec += 1

        st.session_state["rec_page_number"] = page_number_rec

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
