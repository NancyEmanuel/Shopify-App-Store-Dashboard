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
    /* Make metrics bigger */
    .stMetric {
        font-size: 1.2rem !important;
    }
    .stMetric > div {
        font-size: 2rem !important;
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

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================
def get_segment_color(segment):
    """Get color for segment with improved color scheme"""
    segment_colors = {
        'Below Standard Performance': '#C0392B',  # Deep red - most negative
        'Low Demand, Quality Gap': '#E74C3C',     # Red - negative
        'High Demand, Minor Gap': '#F39C12',       # Orange - neutral/caution
        'Underutilized Quality': '#3498DB',        # Blue - neutral/opportunity
        'High Demand, Good Quality': '#27AE60',    # Dark green - positive (combined)
        'Meeting Expectations': '#27AE60'          # Dark green - positive (will be combined)
    }
    return segment_colors.get(segment, '#95A5A6')

def render_segment_detail(df, segment):
    """Render detailed view for a specific segment"""
    # Back button at the top
    if st.button("← Back to Overview", key='back_from_segment_top'):
        st.session_state.current_view = 'main'
        st.session_state.selected_segment = None
        st.rerun()
    
    st.markdown(f"### 🔍 Deep Dive: {segment}")
    
    segment_df = df[df['Strategic Segment'] == segment].copy()
    
    if len(segment_df) == 0:
        st.warning(f"No categories found in {segment}")
        return
    
    # Define column names
    problem_col = "What's the Problem?"
    action_col = "What Should Shopify Do?"
    
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
    
    # Use segment color for scatter plot
    segment_color = get_segment_color(segment)
    
    # Check if this segment has quality issues (non-zero quality severity)
    has_quality_issues = (segment_df['Quality Severity (0-100)'] > 0).any()
    
    if has_quality_issues:
        fig_scatter = px.scatter(
            segment_df,
            x='Merchant Impact (0-100)',
            y='Quality Severity (0-100)',
            size='Business Priority (0-100)',
            hover_name='Feature Category',
            text='Feature Category',
            hover_data={
                'Current Avg Rating': ':.2f',
                'Quality vs Median': ':.3f',
                '# of Apps': True,
                'Est. Merchants Affected': ':,',
                'Predicted Churn %': ':.1f',
                'Feature Category': False
            },
            title=f"Categories in {segment}"
        )
        
        # Apply segment color to all bubbles
        fig_scatter.update_traces(
            marker=dict(color=segment_color),
            textposition='top center',
            textfont_size=9
        )
        
        fig_scatter.update_layout(height=500)
        st.plotly_chart(fig_scatter, use_container_width=True)
        
        st.markdown("""
        <div class="metric-explanation">
        <b>📖 Understanding this chart:</b><br>
        • <b>X-axis:</b> Merchant Impact (how many merchants affected)<br>
        • <b>Y-axis:</b> Quality Severity (how bad the quality problem is)<br>
        • <b>Bubble size:</b> Business Priority (combined urgency score)<br>
        • <b>Top-right quadrant = highest priority</b> (high impact + severe quality issues)
        </div>
        """, unsafe_allow_html=True)
    else:
        # For segments with no quality issues, show a performance table instead
        st.markdown(f"#### 📊 Performance Metrics for {segment}")
        st.markdown("""
        <div class="info-box">
        <b>✅ High-Performing Categories:</b> These categories are meeting or exceeding quality expectations 
        with strong merchant satisfaction. No significant quality issues detected.
        </div>
        """, unsafe_allow_html=True)
        
        performance_df = segment_df[[
            'Feature Category', 
            'Current Avg Rating',
            '# of Apps',
            'Est. Merchants Affected',
            '% Apps with 4.5+ Stars'
        ]].sort_values('Est. Merchants Affected', ascending=False)
        
        st.dataframe(performance_df, use_container_width=True, height=300)
    
    st.markdown("---")
    
    # Category list with actions
    st.markdown("#### 📝 Strategic Actions by Category")
    
    for idx, row in segment_df.iterrows():
        with st.expander(f"**{row['Feature Category']}** - Priority {row['Priority Level (1-5)']} ({row['Action Timeline']})"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.markdown(f"**📊 Key Metrics:**")
                st.markdown(f"- Current Rating: {row['Current Avg Rating']:.2f}★")
                st.markdown(f"- Quality Gap: {row['Quality vs Median']:.3f}★")
                st.markdown(f"- Merchants Affected: ~{int(row['Est. Merchants Affected']/1000)}K")
                st.markdown(f"- Predicted Churn: {row['Predicted Churn %']:.1f}%")
            
            with col2:
                st.markdown(f"**🎯 Scores:**")
                st.markdown(f"- Quality Severity: {row['Quality Severity (0-100)']:.0f}/100")
                st.markdown(f"- Merchant Impact: {row['Merchant Impact (0-100)']:.0f}/100")
                st.markdown(f"- Business Priority: {row['Business Priority (0-100)']:.0f}/100")
            
            if problem_col in row and pd.notna(row[problem_col]):
                st.markdown(f"**❓ What's the Problem?**")
                st.markdown(row[problem_col])
            
            if action_col in row and pd.notna(row[action_col]):
                st.markdown(f"**💡 Recommended Action:**")
                st.markdown(row[action_col])
    
    # Back button
    if st.button("← Back to Overview", key='back_from_segment'):
        st.session_state.current_view = 'main'
        st.rerun()

def render_category_detail(df, category):
    """Render detailed view for a specific category"""
    # Back button at the top
    if st.button("← Back to Overview", key='back_from_category_top'):
        st.session_state.current_view = 'main'
        st.session_state.selected_category = None
        st.rerun()
    
    st.markdown(f"### 🔍 Deep Dive: {category}")
    
    cat_data = df[df['Feature Category'] == category].iloc[0]
    
    # Overview metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Current Rating", f"{cat_data['Current Avg Rating']:.2f}★")
    with col2:
        st.metric("Quality Gap", f"{cat_data['Quality vs Median']:.3f}★")
    with col3:
        st.metric("Merchants Affected", f"~{int(cat_data['Est. Merchants Affected']/1000)}K")
    with col4:
        st.metric("Predicted Churn", f"{cat_data['Predicted Churn %']:.1f}%")
    
    st.markdown("---")
    
    # Strategic context
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("#### 📊 Classification")
        st.markdown(f"**Strategic Segment:** {cat_data['Strategic Segment']}")
        st.markdown(f"**Demand Level:** {cat_data['Demand Level']}")
        st.markdown(f"**Priority Level:** {cat_data['Priority Level (1-5)']} of 5")
        st.markdown(f"**Action Timeline:** {cat_data['Action Timeline']}")
    
    with col2:
        st.markdown("#### 🎯 Severity Scores")
        st.markdown(f"**Quality Severity:** {cat_data['Quality Severity (0-100)']:.0f}/100")
        st.markdown(f"**Merchant Impact:** {cat_data['Merchant Impact (0-100)']:.0f}/100")
        st.markdown(f"**Business Priority:** {cat_data['Business Priority (0-100)']:.0f}/100")
    
    st.markdown("---")
    
    # Problem and solution
    problem_col = "What's the Problem?"
    action_col = "What Should Shopify Do?"
    
    if problem_col in cat_data and pd.notna(cat_data[problem_col]):
        st.markdown("### ❓ What's Happening?")
        # Remove question marks from the text
        problem_text = str(cat_data[problem_col]).replace('?', '')
        st.markdown(f"<div class='info-box'>{problem_text}</div>", unsafe_allow_html=True)
    
    if action_col in cat_data and pd.notna(cat_data[action_col]):
        st.markdown("### 💡 Recommended Action")
        st.markdown(f"<div class='action-card'>{cat_data[action_col]}</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Additional details
    st.markdown("### 📈 Additional Details")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**Market Context:**")
        st.markdown(f"- Total Apps: {cat_data['# of Apps']}")
        # Fix: Check for correct column name
        if 'Total Reviews (Market Size)' in cat_data:
            st.markdown(f"- Total Reviews: {cat_data['Total Reviews (Market Size)']:,.0f}")
        elif 'Total Reviews' in cat_data:
            st.markdown(f"- Total Reviews: {cat_data['Total Reviews']:,.0f}")
        st.markdown(f"- Reviews per App: {cat_data['Reviews Per App']:.0f}")
    
    with col2:
        st.markdown("**Quality Distribution:**")
        st.markdown(f"- Apps with 4.5+ Stars: {cat_data['% Apps with 4.5+ Stars']:.1f}%")
        if 'Statistically Significant?' in cat_data:
            st.markdown(f"- Statistical Significance: {cat_data['Statistically Significant?']}")
    
    # Back button
    if st.button("← Back to Overview", key='back_from_category'):
        st.session_state.current_view = 'main'
        st.rerun()

# ============================================================================
# MAIN APP
# ============================================================================

# Header
st.markdown('<h1 class="main-header">🎯 Shopify App Store Product Strategy Dashboard</h1>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">Uncovering Quality Gaps and Merchant Pain Points to Prioritize Platform Improvements</p>', unsafe_allow_html=True)

# Load data
df_q1 = load_query1_data()

# ============================================================================
# HANDLE DIFFERENT VIEWS
# ============================================================================

if st.session_state.current_view == 'segment_detail':
    render_segment_detail(df_q1, st.session_state.selected_segment)

elif st.session_state.current_view == 'category_detail':
    render_category_detail(df_q1, st.session_state.selected_category)

else:
    # Main dashboard view
    tabs = st.tabs(["📊 Strategic Overview", "🎯 Priority Analysis", "📈 Performance Insights"])
    
    # ========================================================================
    # TAB 1: STRATEGIC OVERVIEW
    # ========================================================================
    with tabs[0]:
        st.markdown("### 🎯 Key Insights at a Glance")
        
        # Hero metrics
        col1, col2, col3, col4 = st.columns(4)
        
        # Calculate metrics
        # Get top categories by Business Priority (not just priority level 1-3)
        urgent_and_high = df_q1.nlargest(10, 'Business Priority (0-100)')
        high_severity = df_q1[df_q1['Quality Severity (0-100)'] >= 25]
        
        urgent_count = len(urgent_and_high)
        high_severity_count = len(high_severity)
        
        very_high_demand = df_q1[df_q1['Demand Level'] == 'Very High']
        very_high_count = len(very_high_demand)
        
        quality_gap_df = df_q1[df_q1['Quality vs Median'] < 0]
        total_affected = quality_gap_df['Est. Merchants Affected'].sum()
        
        with col1:
            st.markdown(f"""
            <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #E74C3C 0%, #C0392B 100%); 
                        border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h1 style='color: white; margin: 0; font-size: 3rem;'>{urgent_count}</h1>
                <p style='margin: 0.5rem 0 0 0; font-size: 1.1rem; font-weight: 600;'>Actionable<br>Priority Categories</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("View Details", use_container_width=True, key='hero1'):
                st.session_state.clicked_metric_tab1 = 'urgent'
        
        with col2:
            st.markdown(f"""
            <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #E67E22 0%, #D35400 100%); 
                        border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h1 style='color: white; margin: 0; font-size: 3rem;'>{high_severity_count}</h1>
                <p style='margin: 0.5rem 0 0 0; font-size: 1.1rem; font-weight: 600;'>Quality Severity<br>Issues</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("View Details", use_container_width=True, key='hero2'):
                st.session_state.clicked_metric_tab1 = 'severity'
        
        with col3:
            st.markdown(f"""
            <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #3498DB 0%, #2980B9 100%); 
                        border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h1 style='color: white; margin: 0; font-size: 3rem;'>{very_high_count}</h1>
                <p style='margin: 0.5rem 0 0 0; font-size: 1.1rem; font-weight: 600;'>Very High Demand<br>Categories</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("View Details", use_container_width=True, key='hero3'):
                st.session_state.clicked_metric_tab1 = 'demand'
        
        with col4:
            st.markdown(f"""
            <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #9B59B6 0%, #8E44AD 100%); 
                        border-radius: 10px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h1 style='color: white; margin: 0; font-size: 3rem;'>~{int(total_affected/1000)}K</h1>
                <p style='margin: 0.5rem 0 0 0; font-size: 1.1rem; font-weight: 600;'>Merchants Affected<br>by Quality Gaps</p>
            </div>
            """, unsafe_allow_html=True)
            if st.button("View Details", use_container_width=True, key='hero4'):
                st.session_state.clicked_metric_tab1 = 'affected'
        
        # ========================================================================
        # HERO METRIC DRILL-DOWNS
        # ========================================================================
        
        if st.session_state.clicked_metric_tab1 == 'urgent':
            st.markdown("---")
            st.markdown("### 🚨 Categories Needing Immediate Action")
            
            st.markdown("""
            <div class="metric-explanation">
            <b>📖 Why Immediate Action?</b> These categories have the highest Business Priority scores, 
            combining both quality problems and merchant impact. Higher scores mean fixing these issues 
            will improve merchant success the most.
            </div>
            """, unsafe_allow_html=True)
            
            urgent_df = urgent_and_high.sort_values('Business Priority (0-100)', ascending=False)
            
            # Action cards
            for idx, row in urgent_df.iterrows():
                border_color = "#C0392B" if row['Priority Level (1-5)'] == 1 else "#E67E22" if row['Priority Level (1-5)'] == 2 else "#F39C12"
                priority_emoji = "🔴" if row['Priority Level (1-5)'] == 1 else "🟠" if row['Priority Level (1-5)'] == 2 else "🟡"
                
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
            
            # Use a gradient color scale based on priority level
            colors = urgent_df['Business Priority (0-100)'].apply(
                lambda x: f'rgb({int(192 - (x/100)*130)}, {int(57 + (x/100)*130)}, {int(43)})'
            )
            
            fig_urgent.add_trace(go.Bar(
                y=urgent_df['Feature Category'],
                x=urgent_df['Business Priority (0-100)'],
                orientation='h',
                marker=dict(
                    color=colors,
                    line=dict(color='white', width=1)
                ),
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
            st.markdown("### 🔥 Quality Severity Issues")
            
            st.markdown("""
            <div class="metric-explanation">
            <b>📖 Quality Severity Score:</b> Higher scores indicate more significant quality problems with apps 
            in this category, considering the size of the quality gap, percentage of low-rated apps, and 
            lack of high-quality alternatives.
            </div>
            """, unsafe_allow_html=True)
            
            severity_df = high_severity.sort_values('Quality Severity (0-100)', ascending=False)
            
            # Scatter: Severity vs Impact
            fig_sev = px.scatter(
                severity_df,
                x='Merchant Impact (0-100)',
                y='Quality Severity (0-100)',
                size='Business Priority (0-100)',
                color='Business Priority (0-100)',
                hover_name='Feature Category',
                text='Feature Category',
                hover_data={
                    'Current Avg Rating': ':.2f',
                    'Quality vs Median': ':.3f',
                    'Est. Merchants Affected': ':,',
                    'Predicted Churn %': ':.1f',
                    'Feature Category': False
                },
                color_continuous_scale='Reds',
                title="App Quality Issues by Category: Quality Severity vs Merchant Impact"
            )
            
            # Update text position to avoid overlap
            fig_sev.update_traces(
                textposition='top center',
                textfont_size=9
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
            st.markdown("### 📊 Very High Demand Categories: Revenue & Growth Opportunities")
            
            st.markdown("""
            <div class="metric-explanation">
            <b>📖 High-Value Categories:</b>
            These are the most heavily-used app categories by Shopify merchants, representing the highest 
            revenue potential and strategic importance. Success in these categories drives significant 
            merchant retention and platform growth.
            </div>
            """, unsafe_allow_html=True)
            
            vh_df = very_high_demand.sort_values('Business Priority (0-100)', ascending=False)
            
            # Summary metrics focused on opportunity
            col_vh1, col_vh2, col_vh3, col_vh4 = st.columns(4)
            
            with col_vh1:
                st.metric("High-Demand Categories", len(vh_df))
            with col_vh2:
                total_reviews_vh = vh_df['Total Reviews (Market Size)'].sum() if 'Total Reviews (Market Size)' in vh_df.columns else 0
                st.metric("Total Market Size", f"~{int(total_reviews_vh/1000)}K reviews")
            with col_vh3:
                avg_rating = vh_df['Current Avg Rating'].mean()
                st.metric("Average Quality", f"{avg_rating:.2f}★")
            with col_vh4:
                total_merchants_vh = vh_df['Est. Merchants Affected'].sum()
                st.metric("Active Merchants", f"~{int(total_merchants_vh/1000)}K")
            
            st.markdown("---")
            
            # Strategic insights
            st.markdown("### 💡 Strategic Insights for Merchant Success")
            
            col_insight1, col_insight2 = st.columns(2)
            
            with col_insight1:
                st.markdown("""
                <div class="info-box">
                <b>🎯 Revenue Drivers:</b><br>
                • High merchant adoption = Higher platform revenue<br>
                • Categories with most merchant activity<br>
                • Prime candidates for premium features<br>
                • Investment here has highest ROI
                </div>
                """, unsafe_allow_html=True)
            
            with col_insight2:
                st.markdown("""
                <div class="info-box">
                <b>📈 Growth Strategies:</b><br>
                • Focus developer resources on these categories<br>
                • Prioritize API improvements and documentation<br>
                • Enhance app discovery and recommendations<br>
                • Monitor for emerging quality issues early
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Category comparison by market size and quality
            st.markdown("### 📊 Market Opportunity by Category")
            
            fig_vh_comparison = px.bar(
                vh_df.sort_values('Total Reviews (Market Size)', ascending=True) if 'Total Reviews (Market Size)' in vh_df.columns else vh_df,
                y='Feature Category',
                x='Total Reviews (Market Size)' if 'Total Reviews (Market Size)' in vh_df.columns else 'Est. Merchants Affected',
                orientation='h',
                color='Est. Merchants Affected',
                color_continuous_scale='RdYlGn',
                hover_data={
                    'Current Avg Rating': ':.2f',
                    'Business Priority (0-100)': True,
                    'Est. Merchants Affected': ':,',
                    '# of Apps': True
                },
                title="High-Demand Categories by Market Size & Merchant Impact",
                labels={
                    'Total Reviews (Market Size)': 'Market Size (Reviews)',
                    'Est. Merchants Affected': 'Merchants Affected'
                }
            )
            
            fig_vh_comparison.update_layout(height=600)
            st.plotly_chart(fig_vh_comparison, use_container_width=True)
            
            st.markdown("""
            <div class="metric-explanation">
            <b>💡 Color coding:</b> Green = Higher merchant impact, Yellow = Moderate impact, Red = Lower merchant impact
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Full table
            st.markdown("#### 📋 All Very High Demand Categories")
            
            display_vh = vh_df[
                [
                    'Feature Category',
                    'Strategic Segment',
                    'Current Avg Rating',
                    'Total Reviews (Market Size)' if 'Total Reviews (Market Size)' in vh_df.columns else 'Est. Merchants Affected',
                    'Est. Merchants Affected',
                    '# of Apps'
                ]
            ].copy()
            
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
            
            affected_df = quality_gap_df.sort_values(
                'Est. Merchants Affected', ascending=False
            ).head(15)
            
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
        
        # ====================================================================
        # STRATEGIC SEGMENT OVERVIEW
        # ====================================================================
        st.markdown("### 🎯 Strategic Segment Overview")
        
        col_pie, col_explore = st.columns([1.2, 0.8])
        
        with col_pie:
            st.markdown("#### Category Distribution by Segment")
            
            # Get segment counts and combine similar categories
            segment_counts_raw = df_q1['Strategic Segment'].value_counts()
            
            # Combine Meeting Expectations and High Demand Good Quality
            combined_counts = {}
            for segment, count in segment_counts_raw.items():
                if segment in ['Meeting Expectations', 'High Demand, Good Quality']:
                    combined_counts['High Demand, Good Quality'] = combined_counts.get('High Demand, Good Quality', 0) + count
                else:
                    combined_counts[segment] = count
            
            segment_counts = pd.Series(combined_counts)
            
            # Create improved color mapping
            segment_color_map = {}
            for segment in segment_counts.index:
                segment_color_map[segment] = get_segment_color(segment)
            
            # Create pie chart with better formatting
            fig_pie = go.Figure(data=[go.Pie(
                labels=segment_counts.index,
                values=segment_counts.values,
                hole=0.4,
                marker=dict(colors=[segment_color_map[seg] for seg in segment_counts.index]),
                textposition='outside',
                textinfo='label+percent',
                textfont=dict(size=12),
                hovertemplate='<b>%{label}</b><br>Categories: %{value}<br>Percentage: %{percent}<extra></extra>'
            )])
            
            fig_pie.update_layout(
                showlegend=True,
                height=450,
                legend=dict(
                    orientation="v",
                    yanchor="middle",
                    y=0.5,
                    xanchor="left",
                    x=1.1
                )
            )
            
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col_explore:
            st.markdown("#### 🔍 Explore Segments:")
            
            # Order segments from negative to positive
            segment_order = [
                'Below Standard Performance',
                'Low Demand, Quality Gap',
                'High Demand, Minor Gap',
                'Underutilized Quality',
                'High Demand, Good Quality',
                'Meeting Expectations'
            ]
            
            # Filter to only segments that exist in data
            available_segments = [seg for seg in segment_order if seg in segment_counts.index]
            
            # Create colored buttons for each segment
            for segment in available_segments:
                count = segment_counts[segment]
                color = get_segment_color(segment)
                
                # Create button with colored background using markdown
                button_html = f"""
                <style>
                .segment-button-{segment.replace(' ', '-').replace(',', '')} {{
                    background-color: {color};
                    color: white;
                    padding: 15px;
                    border-radius: 8px;
                    margin: 8px 0;
                    text-align: center;
                    font-weight: 600;
                    cursor: pointer;
                    border: none;
                    width: 100%;
                    display: block;
                }}
                </style>
                """
                st.markdown(button_html, unsafe_allow_html=True)
                
                if st.button(
                    f"{segment} ({count} categories)",
                    key=f"seg_btn_{segment}",
                    use_container_width=True
                ):
                    st.session_state.current_view = 'segment_detail'
                    st.session_state.selected_segment = segment
                    st.rerun()
    
    # ========================================================================
    # TAB 2: PRIORITY ANALYSIS
    # ========================================================================
    with tabs[1]:
        st.markdown("### 🚨 Top Categories Requiring Attention")
        
        col_priority1, col_priority2 = st.columns(2)
        
        with col_priority1:
            st.markdown("#### 🔥 Top Problems by Business Priority")
            
            problems_df = df_q1[df_q1['Business Priority (0-100)'] > 0].nlargest(
                10, 'Business Priority (0-100)'
            )
            
            fig_problems = go.Figure()
            
            fig_problems.add_trace(go.Bar(
                y=problems_df['Feature Category'],
                x=problems_df['Business Priority (0-100)'],
                orientation='h',
                marker=dict(
                    color=problems_df['Business Priority (0-100)'],
                    colorscale='Reds',
                    showscale=False
                ),
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
            <b>Business Priority Score</b> combines Quality Severity (40%) and Merchant Impact (60%) to identify 
            which categories need immediate attention. Higher scores = more urgent intervention needed.
            </div>
            """, unsafe_allow_html=True)
        
        with col_priority2:
            st.markdown("#### ⚠️ Highest Quality Severity Issues")
            
            severity_chart_df = df_q1[df_q1['Quality Severity (0-100)'] >= 25].nlargest(
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
        
        # Combined View Details section
        st.markdown("---")
        st.markdown("### 🔍 View Details")
        
        # Category selector
        all_priority_cats = pd.concat([
            problems_df['Feature Category'],
            severity_chart_df['Feature Category']
        ]).unique().tolist()
        
        selected_cat = st.selectbox(
            "Select a category to view full analysis:",
            all_priority_cats,
            key='combined_cat_selector'
        )
        
        if st.button("View Full Analysis", key='view_combined'):
            st.session_state.current_view = 'category_detail'
            st.session_state.selected_category = selected_cat
            st.rerun()
    
    # ========================================================================
    # TAB 3: PERFORMANCE INSIGHTS
    # ========================================================================
    with tabs[2]:
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
            colorscale='RdYlGn_r',
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
        
        # ====================================================================
        # COMPLETE DATA TABLE
        # ====================================================================
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
        
        st.dataframe(table_df, use_container_width=True, height=600)
        
        # Download button
        csv = table_df.to_csv(index=False)
        st.download_button(
            label="📥 Download Full Analysis (CSV)",
            data=csv,
            file_name="shopify_quality_gap_analysis.csv",
            mime="text/csv"
        )
