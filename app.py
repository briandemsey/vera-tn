"""
VERA-TN - Verification Engine for Results & Accountability
Streamlit Web Application for Tennessee Education Data

Post-ASD infrastructure for Tennessee's new three-tiered intervention system.
Early warning signals the Achievement School District never had.

Data sourced from NCES EDGE (nces.ed.gov) ArcGIS services.
"""

import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# =============================================================================
# Configuration
# =============================================================================

st.set_page_config(
    page_title="VERA-TN | Tennessee Early Warning",
    page_icon="🎸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Tennessee Colors
ORANGE = "#FF8200"
DARK_ORANGE = "#c66400"
RED = "#CC142B"
GREEN = "#00843D"
WHITE = "#FFFFFF"
CREAM = "#F8F8F5"
NAVY = "#1B2A4A"

# Custom CSS
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Public+Sans:wght@400;600;700&display=swap');

    .stApp {{
        background-color: {CREAM};
    }}

    section[data-testid="stSidebar"] {{
        background-color: {ORANGE};
    }}
    section[data-testid="stSidebar"] .stMarkdown {{
        color: white;
    }}
    section[data-testid="stSidebar"] label {{
        color: white !important;
    }}
    section[data-testid="stSidebar"] .stRadio label,
    section[data-testid="stSidebar"] .stRadio label span,
    section[data-testid="stSidebar"] .stRadio label p,
    section[data-testid="stSidebar"] .stRadio label div {{
        color: white !important;
    }}

    h1, h2, h3 {{
        font-family: 'Public Sans', sans-serif;
        color: {ORANGE};
    }}
    h1 {{
        border-bottom: 4px solid {ORANGE};
        padding-bottom: 16px;
    }}

    .stat-card {{
        background: white;
        padding: 20px;
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.06);
        border-left: 4px solid {ORANGE};
        min-width: 0;
    }}
    .stat-card .value {{
        font-size: 1.8rem;
        font-weight: 700;
        color: {ORANGE};
        white-space: nowrap;
    }}
    .stat-card .label {{
        font-size: 0.85rem;
        color: #666;
    }}

    .tier-badge {{
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
        display: inline-block;
        margin-bottom: 16px;
    }}
    .tier-1 {{ background: {GREEN}; color: white; }}
    .tier-2 {{ background: {ORANGE}; color: white; }}
    .tier-3 {{ background: {RED}; color: white; }}

    .tier-card {{
        background: white;
        padding: 24px;
        border-radius: 8px;
        margin-bottom: 16px;
    }}
    .tier-card.t1 {{ border-top: 4px solid {GREEN}; }}
    .tier-card.t2 {{ border-top: 4px solid {ORANGE}; }}
    .tier-card.t3 {{ border-top: 4px solid {RED}; }}
    .tier-card h4 {{
        color: #333;
        font-size: 1.1rem;
        margin-bottom: 12px;
    }}

    #MainMenu {{visibility: hidden;}}
    footer {{visibility: hidden;}}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# Data Functions - NCES EDGE ArcGIS API
# =============================================================================

# NCES EDGE Public Schools endpoint (2023-24 data)
NCES_ENDPOINT = "https://nces.ed.gov/opengis/rest/services/K12_School_Locations/EDGE_GEOCODE_PUBLICSCH_2324/MapServer/0/query"


@st.cache_data(ttl=3600)
def fetch_tennessee_schools():
    """Fetch all Tennessee schools from NCES EDGE endpoint."""
    all_schools = []
    offset = 0
    batch_size = 1000

    while True:
        try:
            response = requests.get(
                NCES_ENDPOINT,
                params={
                    "where": "STFIP='47'",
                    "outFields": "NCESSCH,LEAID,NAME,STREET,CITY,STATE,ZIP,NMCNTY,LOCALE,LAT,LON",
                    "f": "json",
                    "resultRecordCount": batch_size,
                    "resultOffset": offset
                },
                timeout=60
            )
            response.raise_for_status()
            data = response.json()

            features = data.get("features", [])
            if not features:
                break

            for feature in features:
                attrs = feature.get("attributes", {})
                all_schools.append(attrs)

            if len(features) < batch_size:
                break
            offset += batch_size

        except Exception as e:
            st.error(f"Error fetching school data: {e}")
            break

    return all_schools


def process_schools_data(raw_data):
    """Process raw API data into a clean DataFrame."""
    if not raw_data:
        return pd.DataFrame()

    df = pd.DataFrame(raw_data)

    # Rename columns for clarity
    df = df.rename(columns={
        "NAME": "school_name",
        "NCESSCH": "school_id",
        "LEAID": "district_id",
        "STREET": "address",
        "CITY": "city",
        "STATE": "state",
        "ZIP": "zip",
        "NMCNTY": "county",
        "LOCALE": "locale_code",
        "LAT": "latitude",
        "LON": "longitude"
    })

    # Clean county names (remove " County" suffix for cleaner display)
    if "county" in df.columns:
        df["county"] = df["county"].str.replace(" County", "", regex=False)

    # Determine locale type from locale code
    def get_locale_type(code):
        if pd.isna(code):
            return "Unknown"
        code = str(code)
        if code.startswith("1"):
            return "City"
        elif code.startswith("2"):
            return "Suburb"
        elif code.startswith("3"):
            return "Town"
        elif code.startswith("4"):
            return "Rural"
        else:
            return "Unknown"

    df["locale"] = df["locale_code"].apply(get_locale_type)

    # Filter out schools with no name
    df = df[df["school_name"].notna()]

    return df


# =============================================================================
# Sidebar
# =============================================================================

with st.sidebar:
    # Display Tennessee flag
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.image("tennessee-flag.svg", width=80)

    st.markdown(f"""
        <div style="text-align: center; padding: 10px 0 20px 0;">
            <h2 style="color: white; margin: 10px 0;">VERA-TN</h2>
            <p style="color: rgba(255,255,255,0.9); font-size: 0.9rem;">Verification Engine for Results & Accountability</p>
            <p style="color: rgba(255,255,255,0.6); font-size: 0.8rem;">Tennessee • Post-ASD</p>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    page = st.radio(
        "Navigate",
        ["📊 School Dashboard", "🎯 Tiered Intervention", "🗺️ County Explorer", "📈 Locale Analysis", "ℹ️ About VERA-TN"],
        label_visibility="collapsed"
    )

    st.markdown(f"""
        <div style="
            height: 4px;
            background: linear-gradient(90deg, #fff, rgba(255,255,255,0.5), #fff);
            margin: 30px 0 20px 0;
            border-radius: 2px;
        "></div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
        <p style="color: #fff; font-size: 1.2rem; font-weight: 700; text-align: center; margin: 12px 0 6px 0;">
            After the ASD
        </p>
        <p style="color: rgba(255,255,255,0.8); font-size: 0.8rem; text-align: center; margin: 0 0 4px 0;">
            New tiered system 2026-27
        </p>
        <p style="color: rgba(255,255,255,0.6); font-size: 0.75rem; text-align: center; margin: 0 0 12px 0;">
            Early warning • Not late intervention
        </p>
        <p style="text-align: center;">
            <a href="https://nces.ed.gov" target="_blank" style="
                color: #fff;
                font-size: 0.9rem;
                font-weight: 600;
                text-decoration: none;
                border-bottom: 2px solid #fff;
            ">NCES Data</a>
        </p>
    """, unsafe_allow_html=True)


# =============================================================================
# Load Data
# =============================================================================

with st.spinner("Loading Tennessee school data..."):
    raw_schools = fetch_tennessee_schools()
    schools_df = process_schools_data(raw_schools)


# =============================================================================
# Page: School Dashboard
# =============================================================================

if page == "📊 School Dashboard":
    st.title("Tennessee School Dashboard")
    st.caption("Live data from NCES EDGE • 2023-24 School Year")

    if schools_df.empty:
        st.error("Unable to load school data. Please try again later.")
    else:
        st.markdown("""
        **After the ASD:** Tennessee's Achievement School District was shut down after 15 years.
        The new three-tiered intervention system launches 2026-27. VERA provides the early warning
        signals the ASD never had.
        """)

        st.markdown("---")

        # Filters
        col1, col2, col3 = st.columns(3)
        with col1:
            counties = ["All"] + sorted(schools_df["county"].dropna().unique().tolist())
            selected_county = st.selectbox("County", counties)
        with col2:
            cities = ["All"] + sorted(schools_df["city"].dropna().unique().tolist())
            selected_city = st.selectbox("City", cities)
        with col3:
            locales = ["All", "City", "Suburb", "Town", "Rural"]
            selected_locale = st.selectbox("Locale", locales)

        # Filter data
        filtered = schools_df.copy()
        if selected_county != "All":
            filtered = filtered[filtered["county"] == selected_county]
        if selected_city != "All":
            filtered = filtered[filtered["city"] == selected_city]
        if selected_locale != "All":
            filtered = filtered[filtered["locale"] == selected_locale]

        # Summary stats
        st.markdown("### Overview")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="value">{len(filtered):,}</div>
                    <div class="label">Schools</div>
                </div>
            """, unsafe_allow_html=True)
        with c2:
            num_districts = filtered["district_id"].nunique()
            st.markdown(f"""
                <div class="stat-card">
                    <div class="value">{num_districts:,}</div>
                    <div class="label">Districts</div>
                </div>
            """, unsafe_allow_html=True)
        with c3:
            num_counties = filtered["county"].nunique()
            st.markdown(f"""
                <div class="stat-card">
                    <div class="value">{num_counties}</div>
                    <div class="label">Counties</div>
                </div>
            """, unsafe_allow_html=True)
        with c4:
            num_cities = filtered["city"].nunique()
            st.markdown(f"""
                <div class="stat-card">
                    <div class="value">{num_cities}</div>
                    <div class="label">Cities</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Charts
        col_left, col_right = st.columns(2)

        with col_left:
            st.markdown("### Schools by Locale Type")
            locale_counts = filtered["locale"].value_counts()

            fig = px.pie(
                values=locale_counts.values,
                names=locale_counts.index,
                color=locale_counts.index,
                color_discrete_map={
                    "City": ORANGE,
                    "Suburb": GREEN,
                    "Town": "#FFC107",
                    "Rural": NAVY,
                    "Unknown": "#888"
                },
                hole=0.4
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col_right:
            st.markdown("### Top Counties by School Count")
            county_counts = filtered["county"].value_counts().head(10)

            fig = px.bar(
                x=county_counts.values,
                y=county_counts.index,
                orientation="h",
                color=county_counts.values,
                color_continuous_scale=[GREEN, ORANGE]
            )
            fig.update_layout(height=350, yaxis=dict(autorange="reversed"), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # Schools table
        st.markdown("### Schools")
        display_df = filtered[["school_name", "city", "county", "locale", "zip"]].copy()
        display_df.columns = ["School", "City", "County", "Locale", "ZIP"]

        st.dataframe(
            display_df.sort_values("School"),
            use_container_width=True,
            hide_index=True
        )

        csv = filtered.to_csv(index=False)
        st.download_button("Download CSV", csv, "vera_tn_schools.csv", "text/csv")


# =============================================================================
# Page: Tiered Intervention
# =============================================================================

elif page == "🎯 Tiered Intervention":
    st.title("Three-Tiered Intervention System")
    st.caption("Tennessee's new accountability framework • Launching 2026-27")

    st.markdown("""
    After shutting down the Achievement School District (75-15 legislative vote in 2025),
    Tennessee is launching a new three-tiered intervention model. Schools are assigned to
    tiers based on performance, with annual review.
    """)

    st.markdown("---")

    # Tier cards
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown(f"""
        <div class="tier-card t1">
            <span class="tier-badge tier-1">TIER 1</span>
            <h4>Least Intervention</h4>
            <p style="color: #555; font-size: 0.9rem;">Schools first identified for intervention start here.</p>
            <ul style="color: #666; font-size: 0.85rem; padding-left: 20px;">
                <li>District chooses evidence-based strategy</li>
                <li>OR partners with turnaround expert</li>
                <li>Annual review for tier movement</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="tier-card t2">
            <span class="tier-badge tier-2">TIER 2</span>
            <h4>Moderate Intervention</h4>
            <p style="color: #555; font-size: 0.9rem;">Schools that don't improve at Tier 1 escalate here.</p>
            <ul style="color: #666; font-size: 0.85rem; padding-left: 20px;">
                <li>Convert to charter school</li>
                <li>Transfer to higher ed institution</li>
                <li>Replace leadership and staff</li>
                <li>Intervention committee required</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="tier-card t3">
            <span class="tier-badge tier-3">TIER 3</span>
            <h4>Most Intensive</h4>
            <p style="color: #555; font-size: 0.9rem;">Last resort for schools that continue to struggle.</p>
            <ul style="color: #666; font-size: 0.85rem; padding-left: 20px;">
                <li>School closure</li>
                <li>Complete staff replacement</li>
                <li>State-directed restructuring</li>
            </ul>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    st.markdown("### VERA's Role: Early Warning")

    st.markdown("""
    **The ASD failed because it intervened too late.** By the time schools were taken over,
    they had been struggling for years. The new system needs early warning — a way to identify
    schools heading toward Tier 2 or Tier 3 before they get there.

    **VERA provides:**
    - Pattern detection across schools showing early warning signs
    - TVAAS trend analysis to predict tier movement
    - Intervention verification to ensure resources reach students
    - Transition support for schools moving between tiers
    """)

    st.markdown("---")

    # School distribution by locale (as proxy for risk factors)
    if not schools_df.empty:
        st.markdown("### Schools by Locale (Risk Factor Analysis)")

        locale_stats = schools_df["locale"].value_counts().reset_index()
        locale_stats.columns = ["Locale", "Schools"]

        col1, col2 = st.columns(2)

        with col1:
            fig = px.bar(
                locale_stats,
                x="Locale",
                y="Schools",
                color="Locale",
                color_discrete_map={
                    "City": ORANGE,
                    "Suburb": GREEN,
                    "Town": "#FFC107",
                    "Rural": NAVY,
                    "Unknown": "#888"
                }
            )
            fig.update_layout(height=300, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("""
            **Locale as Risk Indicator:**

            - **City schools** often have higher concentrations of at-risk students
            - **Rural schools** may lack resources for intervention programs
            - **Suburban schools** typically have more stable funding

            VERA analyzes locale patterns alongside TVAAS data to identify schools
            needing early support.
            """)


# =============================================================================
# Page: County Explorer
# =============================================================================

elif page == "🗺️ County Explorer":
    st.title("County Explorer")
    st.caption("Explore Tennessee schools by county")

    if schools_df.empty:
        st.error("Unable to load school data.")
    else:
        # County summary
        county_stats = schools_df.groupby("county").agg({
            "school_name": "count",
            "district_id": "nunique",
            "city": "nunique"
        }).reset_index()
        county_stats.columns = ["County", "Schools", "Districts", "Cities"]
        county_stats = county_stats.sort_values("Schools", ascending=False)

        st.markdown("### Counties by School Count")

        fig = px.bar(
            county_stats.head(25),
            x="County",
            y="Schools",
            color="Districts",
            color_continuous_scale=[GREEN, ORANGE]
        )
        fig.update_layout(height=400, xaxis_tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("---")

        # County selector
        st.markdown("### County Details")

        selected_county = st.selectbox(
            "Select a county to explore",
            sorted(schools_df["county"].dropna().unique().tolist())
        )

        county_schools = schools_df[schools_df["county"] == selected_county]

        col1, col2, col3 = st.columns(3)

        with col1:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="value">{len(county_schools):,}</div>
                    <div class="label">Schools in {selected_county}</div>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="value">{county_schools['district_id'].nunique()}</div>
                    <div class="label">Districts</div>
                </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
                <div class="stat-card">
                    <div class="value">{county_schools['city'].nunique()}</div>
                    <div class="label">Cities</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("---")

        # Locale breakdown for selected county
        st.markdown(f"### Locale Distribution in {selected_county}")

        locale_counts = county_schools["locale"].value_counts()

        fig = px.pie(
            values=locale_counts.values,
            names=locale_counts.index,
            color=locale_counts.index,
            color_discrete_map={
                "City": ORANGE,
                "Suburb": GREEN,
                "Town": "#FFC107",
                "Rural": NAVY,
                "Unknown": "#888"
            }
        )
        fig.update_layout(height=300)
        st.plotly_chart(fig, use_container_width=True)

        # Schools in selected county
        st.markdown(f"### Schools in {selected_county}")

        display_df = county_schools[["school_name", "city", "locale", "zip"]].copy()
        display_df.columns = ["School", "City", "Locale", "ZIP"]

        st.dataframe(
            display_df.sort_values("School"),
            use_container_width=True,
            hide_index=True
        )


# =============================================================================
# Page: Locale Analysis
# =============================================================================

elif page == "📈 Locale Analysis":
    st.title("Locale Analysis")
    st.caption("Understanding Tennessee's urban-rural education landscape")

    if schools_df.empty:
        st.error("Unable to load school data.")
    else:
        st.markdown("""
        The ASD focused almost exclusively on Memphis and Nashville urban schools.
        Tennessee's new intervention system must address the full spectrum — from
        city schools to rural communities.
        """)

        st.markdown("---")

        # Locale breakdown
        st.markdown("### Statewide Locale Distribution")

        locale_stats = schools_df["locale"].value_counts().reset_index()
        locale_stats.columns = ["Locale", "Schools"]
        locale_stats["Percentage"] = (locale_stats["Schools"] / locale_stats["Schools"].sum() * 100).round(1)

        col1, col2 = st.columns(2)

        with col1:
            fig = px.pie(
                locale_stats,
                values="Schools",
                names="Locale",
                color="Locale",
                color_discrete_map={
                    "City": ORANGE,
                    "Suburb": GREEN,
                    "Town": "#FFC107",
                    "Rural": NAVY,
                    "Unknown": "#888"
                },
                hole=0.4
            )
            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            for _, row in locale_stats.iterrows():
                st.markdown(f"**{row['Locale']}:** {row['Schools']:,} schools ({row['Percentage']}%)")

        st.markdown("---")

        # Counties by dominant locale
        st.markdown("### County Locale Profiles")

        county_locale = schools_df.groupby(["county", "locale"]).size().unstack(fill_value=0)

        # Find dominant locale for each county
        county_locale["dominant"] = county_locale.idxmax(axis=1)
        county_locale["total"] = county_locale[["City", "Suburb", "Town", "Rural"]].sum(axis=1)

        dominant_counts = county_locale["dominant"].value_counts()

        fig = px.bar(
            x=dominant_counts.index,
            y=dominant_counts.values,
            color=dominant_counts.index,
            color_discrete_map={
                "City": ORANGE,
                "Suburb": GREEN,
                "Town": "#FFC107",
                "Rural": NAVY
            },
            labels={"x": "Dominant Locale Type", "y": "Number of Counties"}
        )
        fig.update_layout(height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("""
        **Key Insight:** The majority of Tennessee counties are predominantly rural or town-based.
        The ASD's urban focus left these communities without support. The new tiered system
        must address rural school challenges.
        """)


# =============================================================================
# Page: About
# =============================================================================

elif page == "ℹ️ About VERA-TN":
    st.title("About VERA-TN")

    st.markdown(f"""
    ## Verification Engine for Results & Accountability

    **VERA-TN** provides the early warning infrastructure Tennessee's new three-tiered
    intervention system needs — the infrastructure the Achievement School District never had.

    ---

    ## The ASD Lesson

    The **Achievement School District** was created to turn around Tennessee's lowest-performing
    schools through state takeover and charter conversion. After 15 years and billions spent,
    it was shut down by overwhelming legislative vote (75-15) in 2025.

    **The fundamental flaw:** The ASD intervened after schools were already in crisis. There
    was no infrastructure to detect problems before they became failures.

    ---

    ## The New System (2026-27)

    Tennessee's three-tiered intervention model:

    | Tier | Level | Actions |
    |------|-------|---------|
    | **Tier 1** | Least Intervention | District-led evidence-based strategy |
    | **Tier 2** | Moderate | Charter conversion, staff replacement |
    | **Tier 3** | Most Intensive | School closure, state restructuring |

    Schools are assigned annually based on performance, with ability to move up or down.

    ---

    ## What VERA Provides

    | Function | Description |
    |----------|-------------|
    | **Early Warning** | Identify schools heading toward crisis before they get there |
    | **TVAAS Integration** | Analyze value-added data for trend detection |
    | **Tier Prediction** | Forecast which schools will escalate tiers |
    | **Intervention Tracking** | Verify resources actually reach students |
    | **Transition Support** | Manage school transitions between tiers |

    ---

    ## Data Source

    **Live data from NCES EDGE:**

    - **Endpoint:** [nces.ed.gov/opengis/rest/services](https://nces.ed.gov/opengis/rest/services/K12_School_Locations/EDGE_GEOCODE_PUBLICSCH_2324/MapServer/0)
    - **Coverage:** All Tennessee public schools
    - **School Year:** 2023-24
    - **Fields:** School name, location, district, locale type

    ---

    <p style="color: #666; font-size: 0.9rem;">
        VERA-TN v1.0 | Post-ASD Edition | Built by <a href="https://hallucinations.cloud" style="color: {ORANGE};">Hallucinations.cloud</a> |
        An <a href="https://h-edu.solutions" style="color: {ORANGE};">H-EDU.Solutions</a> Initiative
    </p>
    """, unsafe_allow_html=True)
