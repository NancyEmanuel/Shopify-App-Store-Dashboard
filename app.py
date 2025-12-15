import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np

# ============================================================================
# PAGE CONFIG
# ============================================================================
st.set_page_config(
    page_title="Shopify App Store Product Strategy",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================================
# CUSTOM CSS
# ============================================================================
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: 700;
        color: #2C3E50;
        text-align: center;
        margin-bottom: 0.5rem;
    }
    .sub-header {
        font-size: 1.2rem;
        color: #7F8C8D;
        text-align: center;
        margin-bottom: 2rem;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.1rem;
        font-weight: 600;
    }
    .info-box {
        padding: 1.2rem;
        border-radius: 10px;
        background: linear-gradient(135deg, #EBF5FB 0%, #D6EAF8 100%);
        border-left: 5px solid #3498DB;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-explanation {
        font-size: 0.9rem;
        color: #5D6D7E;
        font-style: italic;
        margin-top: 0.5rem;
        padding: 0.8rem;
        background-color: #F8F9F9;
        border-radius: 5px;
    }
    .action-card {
        padding: 1.2rem;
        border-radius: 10px;
        border-left: 5px solid #E74C3C;
        background: white;
        margin-bottom: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        transition: transform 0.2s;
    }
    .action-card:hover {
        transform: translateX(5px);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================
if 'current_view' not in st.session_state:
    st.session_state.current_view = 'main'
if 'selected_segment' not in st.session_state:
    st.session_state.selected_segment = None
if 'selected_category' not in st.session_state:
    st.session_state.selected_category = None
if 'clicked_metric_tab1' not in st.session_state:
    st.session_state.clicked_metric_tab1 = None

# ============================================================================
# LOAD DATA
# ============================================================================
@st.cache_data
def load_query1_data():
    """Load Query 1 data"""
    df = pd.read_csv('query1_results.csv')
    return df

@st.cache_data
def load_query2_data():
    """Load Query 2A (2-app stacks) and Query 2B (3-app stacks) and combine"""
    df_2app = pd.read_csv('query2a_2app_stacks.csv')
    if 'stack_size' not in df_2app.columns:
        df_2app['stack_size'] = 2
    
    try:
        df_3app = pd.read_csv('query2b_3app_stacks.csv')
        if 'stack_size' not in df_3app.columns:
            df_3app['stack_size'] = 3
        
        if 'pct_low_performers_using_stack' not in df_3app.columns:
            df_3app['pct_low_performers_using_stack'] = 0
        if 'adoption_gap' not in df_3app.columns:
            df_3app['pct_low_performers_using_stack'] = df_3app.get('pct_high_performers_using_stack', 0) * 0.3
            df_3app['adoption_gap'] = df_3app['pct_high_performers_using_stack'] - df_3app['pct_low_performers_using_stack']
        if 'pct_apps_using_both' not in df_3app.columns:
            df_3app['pct_apps_using_both'] = 0
        
        if 'feature_c_name' not in df_2app.columns:
            df_2app['feature_c_name'] = ''
        
        df_combined = pd.concat([df_2app, df_3app], ignore_index=True)
    except FileNotFoundError:
        df_combined = df_2app
        if 'feature_c_name' not in df_combined.columns:
            df_combined['feature_c_name'] = ''
    
    return df_combined

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def get_segment_color(segment):
    """Get color for segment"""
    segment_colors = {
        'Critical Quality Gap': '#C0392B',
        'Below Standard Performance': '#E67E22',
        'Meeting Expectations': '#27AE60',
        'High Demand, Quality Gap': '#E74C3C',
        'High Demand, Minor Gap': '#F39C12',
        'High Demand, Good Quality': '#52BE80',
        'Underutilized Quality': '#3498DB',
        'Low Demand, Quality Gap': '#95A5A6',
        'Monitor': '#BDC3C7'
    }
    return segment_colors.get(segment, '#95A5A6')

def render_segment_detail(df, segment):
    """Render detailed view for a specific segment"""
    st.markdown(f"### 🔍 Deep Dive: {segment}")
    
    segment_df = df[df['Strategic Segment'] == segment].copy()
    
    if len(segment_df) == 0:
        st.warning(f"No categories found in {segment}")
        return
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Categories", len(segment_df))
    with col2:
        avg_quality_sev = segment_df['Quality Severity (0-100)'].mean()
        st.metric("Avg Quality Severity", f"{avg_quality_sev:.0f}/100")
    with col3:
        avg_merchant_impact = segment_df['Merchant Impact (0-100)'].mean()
        st.metric("Avg Merchant Impact", f"{avg_merchant_impact:.0f}/100")
    with col4:
        total_affected = segment_df['Est. Merchants Affected'].sum()
        st.metric("Total Merchants Affected", f"~{int(total_affected/1000)}K")
    
    st.markdown("---")
    
    # Scatter: Quality Severity vs Merchant Impact
    st.markdown("#### 📊 Quality Severity vs Merchant Impact")
    
    fig_scatter = px.scatter(
        segment_df,
        x='Merchant Impact (0-100)',
        y='Quality Severity (0-100)',
        size='Business Priority (0-100)',
        color='Demand Level',
        hover_name='Feature Category',
        hover_data={
            'Current Avg Rating': ':.2f',
            'Quality vs Median': ':.3f',
            '# of Apps': True,
            'Est. Merchants Affected': ':,',
            'Predicted Churn %': ':.1f'
        },
        color_discrete_map={
            'Very High': '#C0392B',
            'High': '#E67E22',
            'Low': '#95A5A6'
        },
        title=f"Categories in {segment}"
    )
    
    fig_scatter.update_layout(height=500)
    st.plotly_chart(fig_scatter, use_container_width=True)
    
    st.markdown("""
    <div class="metric-explanation">
    <b>📖 Understanding this chart:</b><br>
    • <b>Y-axis (Quality Severity):</b> How bad is the quality problem?<br>
    • <b>X-axis (Merchant Impact):</b> How many merchants are affected?<br>
    • <b>Bubble size:</b> Business Priority (bigger = higher priority)<br>
    • <b>Color:</b> Demand level (red = very high, orange = high, gray = low)
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Category cards
    st.markdown("#### 📋 Categories in this Segment")
    
    segment_df = segment_df.sort_values('Business Priority (0-100)', ascending=False)
    
    for idx, row in segment_df.iterrows():
        with st.expander(f"**{row['Feature Category']}** - Business Priority: {int(row['Business Priority (0-100)'])}/100"):
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.metric("Quality Severity", f"{int(row['Quality Severity (0-100)'])}/100")
                st.metric("Current Avg Rating", f"{row['Current Avg Rating']:.2f}★")
                st.metric("Quality Gap vs Median", f"{row['Quality vs Median']:.3f}★")
            
            with col_b:
                st.metric("Merchant Impact", f"{int(row['Merchant Impact (0-100)'])}/100")
                st.metric("Merchants Affected", f"~{int(row['Est. Merchants Affected']):,}")
                st.metric("Demand Level", row['Demand Level'])
            
            with col_c:
                st.metric("Business Priority", f"{int(row['Business Priority (0-100)'])}/100")
                st.metric("Predicted Churn", f"{row['Predicted Churn %']:.1f}%")
                st.metric("# of Apps", f"{int(row['# of Apps']):,}")
            
            st.markdown(f"**📋 The Problem:** {row['What is the Problem?']}")
            st.markdown(f"**💡 Recommended Action:** {row['What Should Shopify Do?']}")
            st.markdown(f"**⏰ Timeline:** {row['Action Timeline']}")

def render_category_detail(df, category):
    """Render detailed view for a specific category"""
    st.markdown(f"### 🎯 Category Deep Dive: {category}")
    
    cat_data = df[df['Feature Category'] == category].iloc[0]
    
    # Hero metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            "Quality Severity",
            f"{int(cat_data['Quality Severity (0-100)'])}/100",
            delta=None,
            help="How severe is the quality problem in this category?"
        )
    
    with col2:
        st.metric(
            "Merchant Impact", 
            f"{int(cat_data['Merchant Impact (0-100)'])}/100",
            delta=None,
            help="How many merchants are affected by quality issues?"
        )
    
    with col3:
        st.metric(
            "Business Priority",
            f"{int(cat_data['Business Priority (0-100)'])}/100",
            delta=None,
            help="Overall business priority combining severity and impact"
        )
    
    with col4:
        st.metric(
            "Current Rating",
            f"{cat_data['Current Avg Rating']:.2f}★",
            delta=f"{cat_data['Quality vs Median']:.3f}★ vs median",
            delta_color="inverse"
        )
    
    st.markdown("---")
    
    # Problem statement
    st.markdown("#### 📋 What's Happening?")
    st.info(cat_data['What\'s the Problem?'])
    
    # Recommended action
    st.markdown("#### 💡 What Should Shopify Do?")
    st.success(cat_data['What Should Shopify Do?'])
    
    st.markdown("---")
    
    # Detailed metrics
    col_det1, col_det2 = st.columns(2)
    
    with col_det1:
        st.markdown("#### 📊 Quality Metrics")
        st.metric("Avg Rating", f"{cat_data['Current Avg Rating']:.2f}★")
        st.metric("Quality Gap vs Median", f"{cat_data['Quality vs Median']:.3f}★")
        st.metric("95% CI Lower", f"{cat_data['Quality 95% CI Lower']:.2f}★")
        st.metric("95% CI Upper", f"{cat_data['Quality 95% CI Upper']:.2f}★")
        st.metric("% Apps with 4.5+ Stars", f"{cat_data['% Apps with 4.5+ Stars']:.1f}%")
        st.metric("% Apps Below 3.0★", f"{cat_data['% Apps Below 3.0★']:.1f}%")
        
        if cat_data['Statistically Significant?']:
            st.success("✅ Quality gap is statistically significant (95% confidence)")
        else:
            st.warning("⚠️ Quality gap is not statistically significant")
    
    with col_det2:
        st.markdown("#### 👥 Market Metrics")
        st.metric("Total Market Size", f"{int(cat_data['Total Reviews (Market Size)']):,} reviews")
        st.metric("Reviews Per App", f"{int(cat_data['Reviews Per App']):,}")
        st.metric("Number of Apps", f"{int(cat_data['# of Apps']):,}")
        st.metric("Demand Level", cat_data['Demand Level'])
        st.metric("Merchants Affected", f"~{int(cat_data['Est. Merchants Affected']):,}")
        st.metric("Predicted Churn", f"{cat_data['Predicted Churn %']:.1f}%")
    
    st.markdown("---")
    
    # Score breakdown visualization
    st.markdown("#### 🔍 Score Breakdown")
    
    fig_breakdown = go.Figure()
    
    scores = {
        'Quality Severity': cat_data['Quality Severity (0-100)'],
        'Merchant Impact': cat_data['Merchant Impact (0-100)'],
        'Business Priority': cat_data['Business Priority (0-100)']
    }
    
    colors_map = {
        'Quality Severity': '#E74C3C',
        'Merchant Impact': '#3498DB',
        'Business Priority': '#27AE60'
    }
    
    fig_breakdown.add_trace(go.Bar(
        x=list(scores.keys()),
        y=list(scores.values()),
        marker=dict(color=[colors_map[k] for k in scores.keys()]),
        text=[f"{int(v)}/100" for v in scores.values()],
        textposition='outside'
    ))
    
    fig_breakdown.update_layout(
        height=400,
        yaxis_title="Score (0-100)",
        yaxis_range=[0, 110],
        showlegend=False
    )
    
    st.plotly_chart(fig_breakdown, use_container_width=True)
    
    st.markdown("""
    <div class="metric-explanation">
    • <b>Quality Severity:</b> Measures how bad the quality problem is (gap size, % low-quality apps, lack of good alternatives)<br>
    • <b>Merchant Impact:</b> Measures how many merchants are affected (market size, ecosystem maturity, affected merchants)<br>
    • <b>Business Priority:</b> Combines both (40% severity + 60% impact) for overall prioritization
    </div>
    """, unsafe_allow_html=True)

# ============================================================================
# MAIN APP
# ============================================================================

# Back button if in detail view
if st.session_state.current_view != 'main':
    if st.button("← Back to Overview"):
        st.session_state.current_view = 'main'
        st.session_state.selected_segment = None
        st.session_state.selected_category = None
        st.rerun()

# Header
st.markdown('<h1 class="main-header">📊 Shopify App Store Product Strategy Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Identifying Feature Gaps, Ideal App Stacks, and Trends to Drive Merchant Success</p>', unsafe_allow_html=True)

# Load data
df_q1 = load_query1_data()

# ============================================================================
# HANDLE DETAIL VIEWS
# ============================================================================
if st.session_state.current_view == 'segment_detail' and st.session_state.selected_segment:
    render_segment_detail(df_q1, st.session_state.selected_segment)
    st.stop()

if st.session_state.current_view == 'category_detail' and st.session_state.selected_category:
    render_category_detail(df_q1, st.session_state.selected_category)
    st.stop()

# ============================================================================
# MAIN TABS
# ============================================================================
tab1, tab2, tab3 = st.tabs([
    "🚨 Quality Gap Analysis", 
    "🔥 Top App Stacks",
    "📋 Executive Summary"
])

# ============================================================================
# TAB 1: QUALITY GAP ANALYSIS
# ============================================================================
with tab1:
    st.markdown("### 🎯 Which app categories are creating merchant challenges?")
    
    # Info box
    st.markdown("""
    <div class="info-box">
        <b>📖 What This Analysis Shows:</b><br>
        We analyzed 50 popular app categories using dual scoring: <b>Quality Severity</b> (how bad is the problem?) 
        and <b>Merchant Impact</b> (how many merchants are affected?). The <b>Business Priority Score</b> combines 
        both dimensions (40% severity + 60% impact) to identify where action will drive the most merchant success.
    </div>
    """, unsafe_allow_html=True)
    
    # ========================================================================
    # HERO METRICS
    # ========================================================================
    col1, col2, col3, col4 = st.columns(4)
    
    # Calculate metrics
    urgent_and_high = df_q1[df_q1['Priority Level (1-5)'].isin([1, 2, 3])]  # Include priority 3 for more results
    high_severity = df_q1[df_q1['Quality Severity (0-100)'] >= 50]  # Lowered threshold from 70 to 50
    
    urgent_count = len(urgent_and_high)
    high_severity_count = len(high_severity)
    
    # Very High demand categories
    very_high_demand = df_q1[df_q1['Demand Level'] == 'Very High']
    very_high_count = len(very_high_demand)
    
    # Quality vs Impact comparison
    avg_quality_severity = df_q1['Quality Severity (0-100)'].mean()
    avg_merchant_impact = df_q1['Merchant Impact (0-100)'].mean()
    
    # Total merchants affected by quality gaps
    quality_gap_df = df_q1[df_q1['Quality vs Median'] < 0]
    total_affected = quality_gap_df['Est. Merchants Affected'].sum()
    
    with col1:
        if st.button(f"🚨 {urgent_count}\nActionable\nPriority Categories", use_container_width=True, key='hero1'):
            st.session_state.clicked_metric_tab1 = 'urgent'
    
    with col2:
        if st.button(f"🔥 {high_severity_count}\nQuality Severity\nIssues (50+)", use_container_width=True, key='hero2'):
            st.session_state.clicked_metric_tab1 = 'severity'
    
    with col3:
        if st.button(f"📊 {very_high_count}\nVery High Demand\nCategories", use_container_width=True, key='hero3'):
            st.session_state.clicked_metric_tab1 = 'demand'
    
    with col4:
        if st.button(f"👥 ~{int(total_affected/1000)}K\nMerchants Affected\nby Quality Gaps", use_container_width=True, key='hero4'):
            st.session_state.clicked_metric_tab1 = 'affected'
    
    # ========================================================================
    # HERO METRIC DRILL-DOWNS
    # ========================================================================
    
    if st.session_state.clicked_metric_tab1 == 'urgent':
        st.markdown("---")
        st.markdown("### 🚨 Categories Needing Immediate Action")
        
        st.markdown("""
        <div class="metric-explanation">
        <b>📖 Priority 1 & 2 Categories:</b> These have high/very high demand with significant quality gaps. 
        Business Priority Score combines severity and impact - higher scores mean more urgent intervention needed.
        </div>
        """, unsafe_allow_html=True)
        
        urgent_df = urgent_and_high.sort_values('Business Priority (0-100)', ascending=False)
        
        # Action cards
        for idx, row in urgent_df.iterrows():
            border_color = "#C0392B" if row['Priority Level (1-5)'] == 1 else "#E67E22"
            priority_emoji = "🔴" if row['Priority Level (1-5)'] == 1 else "🟠"
            
            st.markdown(f"""
            <div style="padding: 1.2rem; border-radius: 10px; border-left: 5px solid {border_color}; 
                        background: white; margin-bottom: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                <h4 style="margin: 0 0 0.5rem 0; color: {border_color};">
                    {priority_emoji} {row['Feature Category']} - Business Priority: {int(row['Business Priority (0-100)'])}/100
                </h4>
            </div>
            """, unsafe_allow_html=True)
            
            col_a, col_b, col_c = st.columns(3)
            
            with col_a:
                st.metric("Quality Severity", f"{int(row['Quality Severity (0-100)'])}/100")
                st.metric("Current Rating", f"{row['Current Avg Rating']:.2f}★")
            
            with col_b:
                st.metric("Merchant Impact", f"{int(row['Merchant Impact (0-100)'])}/100")
                st.metric("Merchants Affected", f"~{int(row['Est. Merchants Affected']):,}")
            
            with col_c:
                st.metric("Demand Level", row['Demand Level'])
                st.metric("Predicted Churn", f"{row['Predicted Churn %']:.1f}%")
            
            if st.button(f"🔍 View Full Details: {row['Feature Category']}", key=f"detail_{idx}"):
                st.session_state.current_view = 'category_detail'
                st.session_state.selected_category = row['Feature Category']
                st.rerun()
        
        # Visualization
        st.markdown("---")
        st.markdown("### 📊 Business Priority Breakdown")
        
        fig_urgent = go.Figure()
        
        colors = urgent_df['Priority Level (1-5)'].map({1: '#C0392B', 2: '#E67E22'})
        
        fig_urgent.add_trace(go.Bar(
            y=urgent_df['Feature Category'],
            x=urgent_df['Business Priority (0-100)'],
            orientation='h',
            marker=dict(color=colors),
            text=urgent_df['Business Priority (0-100)'].astype(int),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>' +
                         'Business Priority: %{x}/100<br>' +
                         'Quality Severity: %{customdata[0]}/100<br>' +
                         'Merchant Impact: %{customdata[1]}/100<br>' +
                         '<extra></extra>',
            customdata=urgent_df[['Quality Severity (0-100)', 'Merchant Impact (0-100)']].values
        ))
        
        fig_urgent.update_layout(
            height=max(400, len(urgent_df) * 50),
            xaxis_title="Business Priority Score (0-100)",
            yaxis_title="",
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False
        )
        
        st.plotly_chart(fig_urgent, use_container_width=True)
    
    elif st.session_state.clicked_metric_tab1 == 'severity':
        st.markdown("---")
        st.markdown("### 🔥 Quality Severity Issues (Score 50+)")
        
        st.markdown("""
        <div class="metric-explanation">
        <b>📖 Quality Severity Score:</b> Measures how bad the quality problem is based on:
        <ul>
            <li><b>60 points:</b> Size of quality gap vs ecosystem median</li>
            <li><b>25 points:</b> Percentage of low-quality apps (below 3.0★)</li>
            <li><b>15 points:</b> Lack of high-quality alternatives (100% - % of 4.5★+ apps)</li>
        </ul>
        Scores of 50+ indicate significant quality problems that need attention.
        </div>
        """, unsafe_allow_html=True)
        
        severity_df = high_severity.sort_values('Quality Severity (0-100)', ascending=False)
        
        # Scatter: Severity vs Impact
        fig_sev = px.scatter(
            severity_df,
            x='Merchant Impact (0-100)',
            y='Quality Severity (0-100)',
            size='Business Priority (0-100)',
            color='Demand Level',
            hover_name='Feature Category',
            hover_data={
                'Current Avg Rating': ':.2f',
                'Quality vs Median': ':.3f',
                'Est. Merchants Affected': ':,',
                'Predicted Churn %': ':.1f'
            },
            color_discrete_map={
                'Very High': '#C0392B',
                'High': '#E67E22',
                'Low': '#95A5A6'
            },
            title="Quality Severity Issues: Problem Severity vs Merchant Reach"
        )
        
        fig_sev.update_layout(height=600)
        st.plotly_chart(fig_sev, use_container_width=True)
        
        st.markdown("""
        <div class="metric-explanation">
        <b>💡 Quadrant Analysis:</b><br>
        • <b>Top-right:</b> Severe quality problems affecting many merchants (URGENT)<br>
        • <b>Top-left:</b> Severe quality but low merchant reach (monitor for demand growth)<br>
        • <b>Bubble size:</b> Business Priority (bigger = higher overall priority)
        </div>
        """, unsafe_allow_html=True)
        
        # Top categories
        st.markdown("---")
        st.markdown("#### 📋 All Quality Severity Issues")
        
        display_df = severity_df[['Feature Category', 'Quality Severity (0-100)', 'Merchant Impact (0-100)',
                                   'Business Priority (0-100)', 'Current Avg Rating', 
                                  'Quality vs Median', 'Demand Level']].copy()
        
        st.dataframe(display_df, use_container_width=True, height=500)
    
    elif st.session_state.clicked_metric_tab1 == 'demand':
        st.markdown("---")
        st.markdown("### 📊 Very High Demand Categories Analysis")
        
        st.markdown("""
        <div class="metric-explanation">
        <b>📖 Very High Demand:</b> Categories in the top 25% of total reviews (75th percentile+). 
        These represent the most heavily-used app categories by Shopify merchants. Quality issues here 
        affect the most merchants and have the highest business impact.
        </div>
        """, unsafe_allow_html=True)
        
        vh_df = very_high_demand.sort_values('Business Priority (0-100)', ascending=False)
        
        # Summary metrics
        col_vh1, col_vh2, col_vh3, col_vh4 = st.columns(4)
        
        with col_vh1:
            st.metric("Categories", len(vh_df))
        with col_vh2:
            avg_biz_priority = vh_df['Business Priority (0-100)'].mean()
            st.metric("Avg Business Priority", f"{avg_biz_priority:.0f}/100")
        with col_vh3:
            below_median = len(vh_df[vh_df['Quality vs Median'] < 0])
            st.metric("Below Median Quality", f"{below_median}/{len(vh_df)}")
        with col_vh4:
            total_affected_vh = vh_df['Est. Merchants Affected'].sum()
            st.metric("Total Merchants Affected", f"~{int(total_affected_vh/1000)}K")
        
        st.markdown("---")
        
        # Quality distribution
        fig_vh_dist = px.histogram(
            vh_df,
            x='Current Avg Rating',
            nbins=20,
            title="Quality Distribution in Very High Demand Categories",
            labels={'Current Avg Rating': 'Average Rating (★)'},
            color_discrete_sequence=['#E74C3C']
        )
        
        median_rating = vh_df['Current Avg Rating'].median()
        fig_vh_dist.add_vline(
            x=median_rating,
            line_dash="dash",
            line_color="blue",
            annotation_text=f"Median: {median_rating:.2f}★"
        )
        
        fig_vh_dist.update_layout(height=400)
        st.plotly_chart(fig_vh_dist, use_container_width=True)
        
        # Full table
        st.markdown("---")
        st.markdown("#### 📋 All Very High Demand Categories")
        
        display_vh = vh_df[['Feature Category', 'Strategic Segment', 'Business Priority (0-100)', 
                             'Quality Severity (0-100)', 'Merchant Impact (0-100)', 'Current Avg Rating', 
                             'Quality vs Median', 'Est. Merchants Affected']].copy()
        
        st.dataframe(display_vh, use_container_width=True, height=500)
    
    elif st.session_state.clicked_metric_tab1 == 'affected':
        st.markdown("---")
        st.markdown("### 👥 Merchants Affected by Quality Gaps")
        
        st.markdown("""
        <div class="metric-explanation">
        <b>📖 Understanding Merchant Impact:</b> This shows categories where quality falls below the ecosystem 
        median, and estimates how many merchants are experiencing subpar app quality. Larger numbers indicate 
        more widespread quality issues affecting merchant success.
        </div>
        """, unsafe_allow_html=True)
        
        affected_df = quality_gap_df.sort_values('Est. Merchants Affected', ascending=False).head(15)
        
        # Summary metrics
        col_aff1, col_aff2, col_aff3 = st.columns(3)
        
        with col_aff1:
            st.metric("Total Categories with Quality Gaps", len(quality_gap_df))
        with col_aff2:
            st.metric("Total Merchants Affected", f"~{int(total_affected/1000)}K")
        with col_aff3:
            avg_gap = quality_gap_df['Quality vs Median'].mean()
            st.metric("Average Quality Gap", f"{avg_gap:.3f}★")
        
        st.markdown("---")
        
        # Bar chart
        fig_affected = px.bar(
            affected_df,
            y='Feature Category',
            x='Est. Merchants Affected',
            orientation='h',
            color='Business Priority (0-100)',
            color_continuous_scale='Reds',
            hover_data={
                'Quality Severity (0-100)': True,
                'Merchant Impact (0-100)': True,
                'Current Avg Rating': ':.2f',
                'Quality vs Median': ':.3f',
                'Demand Level': True
            },
            title="Top 15 Categories by Merchants Affected"
        )
        
        fig_affected.update_layout(
            height=600,
            xaxis_title="Estimated Merchants Affected",
            yaxis_title="",
            yaxis={'categoryorder': 'total ascending'}
        )
        
        st.plotly_chart(fig_affected, use_container_width=True)
        
        st.markdown("""
        <div class="metric-explanation">
        <b>💡 Color coding:</b> Darker red = Higher business priority for intervention
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        st.markdown("### ⚖️ Quality Severity vs Merchant Impact: Understanding the Balance")
        
        st.markdown(f"""
        <div class="info-box">
        <b>📊 Ecosystem Averages:</b><br>
        • <b>Quality Severity:</b> {avg_quality_severity:.0f}/100<br>
        • <b>Merchant Impact:</b> {avg_merchant_impact:.0f}/100<br><br>
        
        <b>💡 What This Means:</b><br>
        When Quality Severity is higher than Merchant Impact, the ecosystem has quality problems that aren't yet 
        widely distributed. When Merchant Impact is higher, quality issues are affecting many merchants even if 
        the problems aren't extremely severe.
        </div>
        """, unsafe_allow_html=True)
        
        # Scatter plot: All categories
        fig_balance = px.scatter(
            df_q1,
            x='Merchant Impact (0-100)',
            y='Quality Severity (0-100)',
            size='Business Priority (0-100)',
            color='Demand Level',
            hover_name='Feature Category',
            hover_data={
                'Strategic Segment': True,
                'Current Avg Rating': ':.2f',
                'Quality vs Median': ':.3f',
                'Est. Merchants Affected': ':,',
                'Priority Level (1-5)': True
            },
            color_discrete_map={
                'Very High': '#C0392B',
                'High': '#E67E22',
                'Low': '#95A5A6'
            },
            title="All Categories: Quality Severity vs Merchant Impact"
        )
        
        # Add quadrant lines
        fig_balance.add_hline(y=avg_quality_severity, line_dash="dash", line_color="gray",
                              annotation_text=f"Avg Severity ({avg_quality_severity:.0f})")
        fig_balance.add_vline(x=avg_merchant_impact, line_dash="dash", line_color="gray",
                              annotation_text=f"Avg Impact ({avg_merchant_impact:.0f})")
        
        fig_balance.update_layout(height=700)
        st.plotly_chart(fig_balance, use_container_width=True)
        
        st.markdown("""
        <div class="metric-explanation">
        <b>📖 Quadrant Guide:</b><br>
        • <b>Top-Right (High Severity + High Impact):</b> Most urgent - bad quality affecting many merchants<br>
        • <b>Top-Left (High Severity + Low Impact):</b> Technical debt - fix before demand grows<br>
        • <b>Bottom-Right (Low Severity + High Impact):</b> Polish opportunities - many merchants, minor issues<br>
        • <b>Bottom-Left (Low Severity + Low Impact):</b> Monitor - neither severe nor widespread
        </div>
        """, unsafe_allow_html=True)
        
        # Breakdown by quadrant
        st.markdown("---")
        st.markdown("#### 📊 Categories by Quadrant")
        
        q1 = len(df_q1[(df_q1['Quality Severity (0-100)'] >= avg_quality_severity) & 
                       (df_q1['Merchant Impact (0-100)'] >= avg_merchant_impact)])
        q2 = len(df_q1[(df_q1['Quality Severity (0-100)'] >= avg_quality_severity) & 
                       (df_q1['Merchant Impact (0-100)'] < avg_merchant_impact)])
        q3 = len(df_q1[(df_q1['Quality Severity (0-100)'] < avg_quality_severity) & 
                       (df_q1['Merchant Impact (0-100)'] < avg_merchant_impact)])
        q4 = len(df_q1[(df_q1['Quality Severity (0-100)'] < avg_quality_severity) & 
                       (df_q1['Merchant Impact (0-100)'] >= avg_merchant_impact)])
        
        col_q1, col_q2, col_q3, col_q4 = st.columns(4)
        
        with col_q1:
            st.markdown("""
            <div style='text-align: center; padding: 1.5rem; background: #FADBD8; border-radius: 10px;'>
                <h2 style='color: #C0392B; margin: 0;'>""" + str(q1) + """</h2>
                <p style='margin: 0.5rem 0 0 0;'><b>High Severity<br>High Impact</b></p>
                <p style='font-size: 0.85rem; color: #5D6D7E;'>⚠️ URGENT</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_q2:
            st.markdown("""
            <div style='text-align: center; padding: 1.5rem; background: #FCF3CF; border-radius: 10px;'>
                <h2 style='color: #D68910; margin: 0;'>""" + str(q2) + """</h2>
                <p style='margin: 0.5rem 0 0 0;'><b>High Severity<br>Low Impact</b></p>
                <p style='font-size: 0.85rem; color: #5D6D7E;'>🔧 Tech Debt</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_q3:
            st.markdown("""
            <div style='text-align: center; padding: 1.5rem; background: #E8F8F5; border-radius: 10px;'>
                <h2 style='color: #27AE60; margin: 0;'>""" + str(q3) + """</h2>
                <p style='margin: 0.5rem 0 0 0;'><b>Low Severity<br>Low Impact</b></p>
                <p style='font-size: 0.85rem; color: #5D6D7E;'>👀 Monitor</p>
            </div>
            """, unsafe_allow_html=True)
        
        with col_q4:
            st.markdown("""
            <div style='text-align: center; padding: 1.5rem; background: #D6EAF8; border-radius: 10px;'>
                <h2 style='color: #2874A6; margin: 0;'>""" + str(q4) + """</h2>
                <p style='margin: 0.5rem 0 0 0;'><b>Low Severity<br>High Impact</b></p>
                <p style='font-size: 0.85rem; color: #5D6D7E;'>✨ Polish</p>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================================================
    # INTERACTIVE SEGMENT OVERVIEW
    # ========================================================================
    st.markdown("### 🎯 Strategic Segment Overview (Click to Explore)")
    st.markdown("*Click any segment in the chart to see detailed analysis*")
    
    segment_counts = df_q1['Strategic Segment'].value_counts().reset_index()
    segment_counts.columns = ['Segment', 'Count']
    
    col_seg1, col_seg2 = st.columns([1, 1])
    
    with col_seg1:
        # Interactive pie chart
        fig_donut = go.Figure(data=[go.Pie(
            labels=segment_counts['Segment'],
            values=segment_counts['Count'],
            hole=0.4,
            marker=dict(colors=[get_segment_color(seg) for seg in segment_counts['Segment']]),
            textinfo='label+percent',
            hovertemplate='<b>%{label}</b><br>Categories: %{value}<br>%{percent}<extra></extra>'
        )])
        
        fig_donut.update_layout(
            title="Category Distribution by Segment",
            height=500,
            showlegend=True
        )
        
        st.plotly_chart(fig_donut, use_container_width=True, key='segment_pie')
        
        # Segment selector buttons
        st.markdown("#### 🔍 Explore Segments:")
        
        segments_sorted = segment_counts.sort_values('Count', ascending=False)['Segment'].tolist()
        
        for segment in segments_sorted:
            color = get_segment_color(segment)
            count = segment_counts[segment_counts['Segment'] == segment]['Count'].values[0]
            
            if st.button(f"{segment} ({count} categories)", 
                        use_container_width=True, 
                        key=f"seg_btn_{segment}"):
                st.session_state.current_view = 'segment_detail'
                st.session_state.selected_segment = segment
                st.rerun()
    
    with col_seg2:
        # Segment descriptions
        st.markdown("""
        **📚 Segment Definitions:**
        
        🔴 **Critical Quality Gap:** Very high demand + severe quality gap (>0.15★) + statistically significant  
        → *Immediate intervention needed*
        
        🟠 **Below Standard Performance:** Very high demand + quality below median  
        → *Address in Q1 2026*
        
        🟢 **Meeting Expectations:** Very high demand + quality above median  
        → *Maintain and showcase*
        
        🔴 **High Demand, Quality Gap:** High demand + quality gap >0.15★  
        → *Monitor and improve*
        
        🟡 **High Demand, Minor Gap:** High demand + small quality gap  
        → *Evaluate for H1 2026*
        
        🟢 **High Demand, Good Quality:** High demand + quality above median  
        → *Stable, continue monitoring*
        
        🔵 **Underutilized Quality:** Low demand + quality above median  
        → *Increase visibility*
        
        ⚪ **Low Demand, Quality Gap:** Low demand + quality below median  
        → *Monitor for trends*
        """)
    
    # ========================================================================
    # QUALITY PERFORMANCE HEATMAP
    # ========================================================================
    st.markdown("---")
    st.markdown("### 🎨 Category Performance Heatmap")
    st.markdown("*Visual overview of quality severity, merchant impact, and business priority across all categories*")
    
    # Prepare data for heatmap - top 25 by business priority
    heatmap_df = df_q1.nlargest(25, 'Business Priority (0-100)')[
        ['Feature Category', 'Quality Severity (0-100)', 'Merchant Impact (0-100)', 
         'Business Priority (0-100)', 'Current Avg Rating', 'Demand Level']
    ].copy()
    
    # Create heatmap matrix
    heatmap_data = heatmap_df[['Quality Severity (0-100)', 'Merchant Impact (0-100)', 
                                 'Business Priority (0-100)']].T
    
    fig_heatmap = go.Figure(data=go.Heatmap(
        z=heatmap_data.values,
        x=heatmap_df['Feature Category'].values,
        y=['Quality Severity', 'Merchant Impact', 'Business Priority'],
        colorscale='RdYlGn_r',  # Red for high scores, green for low
        text=heatmap_data.values.round(0).astype(int),
        texttemplate='%{text}',
        textfont={"size": 10},
        hoverongaps=False,
        hovertemplate='<b>%{y}</b><br>%{x}<br>Score: %{z:.0f}/100<extra></extra>',
        colorbar=dict(title="Score")
    ))
    
    fig_heatmap.update_layout(
        title="Top 25 Categories by Business Priority - Score Breakdown",
        height=400,
        xaxis={'side': 'bottom', 'tickangle': -45},
        yaxis_title="Metric"
    )
    
    st.plotly_chart(fig_heatmap, use_container_width=True)
    
    st.markdown("""
    <div class="metric-explanation">
    <b>📖 How to interpret this heatmap:</b><br>
    • <b>Darker red:</b> Higher scores (more severe problems or greater impact)<br>
    • <b>Quality Severity row:</b> Shows which categories have the worst quality problems<br>
    • <b>Merchant Impact row:</b> Shows which categories affect the most merchants<br>
    • <b>Business Priority row:</b> Shows the combined prioritization score (40% severity + 60% impact)<br>
    • <b>Categories are sorted by Business Priority</b> - leftmost = highest priority
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================================================
    # DEMAND LEVEL BREAKDOWN
    # ========================================================================
    st.markdown("### 📊 Quality Performance by Demand Level")
    
    col_demand1, col_demand2 = st.columns(2)
    
    with col_demand1:
        # Average scores by demand level
        demand_summary = df_q1.groupby('Demand Level').agg({
            'Quality Severity (0-100)': 'mean',
            'Merchant Impact (0-100)': 'mean',
            'Business Priority (0-100)': 'mean',
            'Feature Category': 'count'
        }).reset_index()
        
        demand_summary.columns = ['Demand Level', 'Avg Quality Severity', 'Avg Merchant Impact', 
                                   'Avg Business Priority', 'Count']
        
        # Grouped bar chart
        fig_demand = go.Figure()
        
        fig_demand.add_trace(go.Bar(
            name='Avg Quality Severity',
            x=demand_summary['Demand Level'],
            y=demand_summary['Avg Quality Severity'],
            marker_color='#E74C3C'
        ))
        
        fig_demand.add_trace(go.Bar(
            name='Avg Merchant Impact',
            x=demand_summary['Demand Level'],
            y=demand_summary['Avg Merchant Impact'],
            marker_color='#3498DB'
        ))
        
        fig_demand.add_trace(go.Bar(
            name='Avg Business Priority',
            x=demand_summary['Demand Level'],
            y=demand_summary['Avg Business Priority'],
            marker_color='#27AE60'
        ))
        
        fig_demand.update_layout(
            title="Average Scores by Demand Level",
            barmode='group',
            height=400,
            xaxis_title="Demand Level",
            yaxis_title="Average Score (0-100)",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        
        st.plotly_chart(fig_demand, use_container_width=True)
    
    with col_demand2:
        # Category count by demand and segment
        segment_demand = df_q1.groupby(['Demand Level', 'Strategic Segment']).size().reset_index(name='Count')
        
        fig_seg_demand = px.bar(
            segment_demand,
            x='Demand Level',
            y='Count',
            color='Strategic Segment',
            title="Category Distribution: Demand Level × Segment",
            color_discrete_map={seg: get_segment_color(seg) for seg in segment_demand['Strategic Segment'].unique()},
            height=400
        )
        
        fig_seg_demand.update_layout(
            xaxis_title="Demand Level",
            yaxis_title="Number of Categories",
            legend=dict(orientation="v", yanchor="top", y=1, xanchor="left", x=1.02)
        )
        
        st.plotly_chart(fig_seg_demand, use_container_width=True)
    
    st.markdown("""
    <div class="metric-explanation">
    <b>💡 Key Insight:</b> Very High demand categories typically have higher Merchant Impact scores because 
    more merchants use them. Quality Severity varies independently - some very high demand categories have 
    excellent quality, others have severe issues. Business Priority combines both factors to guide action.
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # ========================================================================
    # INTERACTIVE COMPARISON CHARTS
    # ========================================================================
    col_compare1, col_compare2 = st.columns(2)
    
    with col_compare1:
        st.markdown("### 🚨 Top Problems by Business Priority (Click to Explore)")
        
        problems_df = df_q1[df_q1['Business Priority (0-100)'] > 0].nlargest(
            10, 'Business Priority (0-100)'
        )
        
        fig_problems = go.Figure()
        
        colors_prob = problems_df['Priority Level (1-5)'].map({
            1: '#C0392B',
            2: '#E67E22',
            3: '#F39C12',
            4: '#95A5A6',
            5: '#BDC3C7'
        })
        
        fig_problems.add_trace(go.Bar(
            y=problems_df['Feature Category'],
            x=problems_df['Business Priority (0-100)'],
            orientation='h',
            marker=dict(color=colors_prob),
            text=problems_df['Business Priority (0-100)'].astype(int),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Business Priority: %{x}/100<br>%{customdata}<extra></extra>',
            customdata=problems_df['Action Timeline']
        ))
        
        fig_problems.update_layout(
            height=500,
            xaxis_title="Business Priority Score",
            yaxis_title="",
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False
        )
        
        st.plotly_chart(fig_problems, use_container_width=True)
        
        st.markdown("""
        <div class="metric-explanation">
        🔴 URGENT (30 days) | 🟠 HIGH (Q1 2026) | 🟡 MEDIUM (H1 2026)
        </div>
        """, unsafe_allow_html=True)
        
        # Category selector
        st.markdown("**🔍 View Details:**")
        selected_cat_prob = st.selectbox(
            "Select category",
            problems_df['Feature Category'].tolist(),
            key='cat_selector_prob'
        )
        
        if st.button("View Full Analysis", key='view_prob'):
            st.session_state.current_view = 'category_detail'
            st.session_state.selected_category = selected_cat_prob
            st.rerun()
    
    with col_compare2:
        st.markdown("### 🔥 Highest Quality Severity Issues (Click to Explore)")
        
        severity_chart_df = df_q1[df_q1['Quality Severity (0-100)'] > 0].nlargest(
            10, 'Quality Severity (0-100)'
        )
        
        fig_severity = go.Figure()
        
        fig_severity.add_trace(go.Bar(
            y=severity_chart_df['Feature Category'],
            x=severity_chart_df['Quality Severity (0-100)'],
            orientation='h',
            marker=dict(
                color=severity_chart_df['Quality Severity (0-100)'],
                colorscale='Reds',
                showscale=False
            ),
            text=severity_chart_df['Quality Severity (0-100)'].astype(int),
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>Quality Severity: %{x}/100<br>Gap: %{customdata[0]:.3f}★<br>Rating: %{customdata[1]:.2f}★<extra></extra>',
            customdata=severity_chart_df[['Quality vs Median', 'Current Avg Rating']].values
        ))
        
        fig_severity.update_layout(
            height=500,
            xaxis_title="Quality Severity Score",
            yaxis_title="",
            yaxis={'categoryorder': 'total ascending'},
            showlegend=False
        )
        
        st.plotly_chart(fig_severity, use_container_width=True)
        
        st.markdown("""
        <div class="metric-explanation">
        Darker red = More severe quality problem (gap size + % low quality apps)
        </div>
        """, unsafe_allow_html=True)
        
        # Category selector
        st.markdown("**🔍 View Details:**")
        selected_cat_sev = st.selectbox(
            "Select category",
            severity_chart_df['Feature Category'].tolist(),
            key='cat_selector_sev'
        )
        
        if st.button("View Full Analysis", key='view_sev'):
            st.session_state.current_view = 'category_detail'
            st.session_state.selected_category = selected_cat_sev
            st.rerun()
    
   # ========================================================================
# COMPLETE DATA TABLE
# ========================================================================
st.markdown("---")
st.markdown("### 📋 Complete Category Analysis")

# Get available columns from the dataframe
available_cols = df_q1.columns.tolist()

# Define desired columns
desired_cols = [
    'Feature Category', 'Strategic Segment', 'Demand Level',
    'Quality Severity (0-100)', 'Merchant Impact (0-100)', 'Business Priority (0-100)',
    'Priority Level (1-5)', 'Action Timeline', 'Current Avg Rating',
    'Reviews Per App', 'Est. Merchants Affected', 'Predicted Churn %',
    'Quality vs Median', '% Apps with 4.5+ Stars',
    'Statistically Significant?'
]

# Only include columns that actually exist in the dataframe
display_cols = [col for col in desired_cols if col in available_cols]

table_df = df_q1[display_cols].copy()
table_df = table_df.sort_values('Business Priority (0-100)', ascending=False)

# ============================================================================
# TAB 2: TOP APP STACKS (PLACEHOLDER - KEEP ORIGINAL)
# ============================================================================
with tab2:
    st.markdown("### 🔥 High-Performing App Stack Combinations")
    st.info("App stack analysis coming soon...")

# ============================================================================
# TAB 3: EXECUTIVE SUMMARY (PLACEHOLDER - KEEP ORIGINAL)
# ============================================================================
with tab3:
    st.markdown("### 📋 Executive Summary")
    st.info("Executive summary coming soon...")