import streamlit as st
import pandas as pd
import datetime
import os
import plotly.express as px
from dotenv import load_dotenv

# Load environment variables for local development
load_dotenv()

from dashboard.db import get_db_connection
from dashboard.queries import (
    get_kpi_metrics, get_risk_distribution, get_transaction_activity_over_time,
    get_recent_high_risk_transactions, get_filtered_transactions,
    get_transaction_detail, get_customer_metrics, get_merchant_metrics
)
from dashboard.components import kpi_card, risk_badge, render_system_status
from dashboard.styles import get_styles

# Page configuration
st.set_page_config(
    page_title="FIN-GUARD | Risk Monitoring",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply styles
st.markdown(get_styles(), unsafe_allow_html=True)

# Auto-refresh logic placeholder if needed, though for now we rely on a manual button 
# or st.rerun via button to not overload the DB in a simple way
def format_inr(value):
    return f"₹{value:,.2f}"

def main():
    # Sidebar Navigation
    st.sidebar.markdown('<div class="sidebar-logo">FIN-GUARD</div>', unsafe_allow_html=True)
    
    page = st.sidebar.radio(
        "Navigation",
        ["Overview", "Transactions", "Customers", "Merchants"]
    )
    
    st.sidebar.markdown("---")
    if st.sidebar.button("↻ Refresh Data", use_container_width=True):
        st.rerun()
    
    # Check DB Connection
    pg_connected = False
    with get_db_connection() as conn:
        if conn is not None:
            pg_connected = True
            
    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    render_system_status(pg_connected, now)
    
    if not pg_connected:
        st.error("DATABASE CONNECTION\nUnable to connect to PostgreSQL.")
        return
        
    # Router
    if page == "Overview":
        render_overview()
    elif page == "Transactions":
        render_transactions()
    elif page == "Customers":
        render_customers()
    elif page == "Merchants":
        render_merchants()

def render_overview():
    st.markdown("<h2>Transaction Risk Monitoring</h2>", unsafe_allow_html=True)
    st.markdown("<p style='color: var(--text-muted);'>Real-time payment transaction surveillance</p>", unsafe_allow_html=True)
    st.markdown("<hr/>", unsafe_allow_html=True)
    
    metrics = get_kpi_metrics()
    
    # Check if we have data
    if metrics['total_transactions'] == 0:
        st.warning("NO TRANSACTION DATA\nThe monitoring database currently contains no processed transactions.")
        return
        
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        kpi_card("Total Transactions", metrics['total_transactions'])
    with c2:
        kpi_card("High Risk", metrics['high_risk'])
    with c3:
        kpi_card("Total Value", metrics['total_value'], prefix="₹", format_str="{:,.2f}")
    with c4:
        kpi_card("Average Value", metrics['avg_value'], prefix="₹", format_str="{:,.2f}")
        
    st.markdown("<br/>", unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.markdown("<h4>Risk Distribution</h4>", unsafe_allow_html=True)
        risk_dist = get_risk_distribution()
        if not risk_dist.empty:
            color_map = {'HIGH': '#dc3545', 'MEDIUM': '#ffc107', 'LOW': '#28a745'}
            fig = px.pie(
                risk_dist, 
                names='risk_level', 
                values='count', 
                hole=0.4,
                color='risk_level',
                color_discrete_map=color_map
            )
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
            st.plotly_chart(fig, use_container_width=True)
            
    with col2:
        st.markdown("<h4>Transaction Activity (Last Hour)</h4>", unsafe_allow_html=True)
        activity = get_transaction_activity_over_time()
        if not activity.empty:
            fig2 = px.line(
                activity, 
                x='time', 
                y='tx_count',
                labels={'time': 'Time', 'tx_count': 'Volume'}
            )
            fig2.update_traces(line_color='#0f4c81')
            fig2.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=300)
            st.plotly_chart(fig2, use_container_width=True)
            
    st.markdown("<hr/>", unsafe_allow_html=True)
    st.markdown("<h4>Recent High-Risk Transactions</h4>", unsafe_allow_html=True)
    
    high_risk_tx = get_recent_high_risk_transactions(10)
    if not high_risk_tx.empty:
        # Format display dataframe
        display_df = high_risk_tx.copy()
        display_df['amount'] = display_df['amount'].apply(lambda x: f"₹{x:,.2f}")
        display_df['final_risk_level'] = display_df['final_risk_level'].apply(lambda x: '🚨 HIGH')
        st.dataframe(display_df, use_container_width=True, hide_index=True)
    else:
        st.info("No high risk transactions detected recently.")

def render_transactions():
    st.markdown("<h2>Transactions Explorer</h2>", unsafe_allow_html=True)
    
    with st.expander("Filters & Search", expanded=True):
        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            search_id = st.text_input("Search ID (Tx, Customer, Merchant)")
        with f_col2:
            risk_level = st.selectbox("Risk Level", ["All", "HIGH", "MEDIUM", "LOW"])
        with f_col3:
            tx_type = st.selectbox("Transaction Type", ["All", "PURCHASE", "TRANSFER", "WITHDRAWAL"])
            
    filters = {}
    if search_id:
        filters['search_id'] = search_id
    if risk_level != "All":
        filters['risk_level'] = risk_level
    if tx_type != "All":
        filters['transaction_type'] = tx_type
        
    transactions = get_filtered_transactions(limit=50, filters=filters)
    
    if not transactions.empty:
        # Display as a table with selectable rows via index if possible, but st.dataframe selection is limited in pure Streamlit unless using ag-grid.
        # We'll use a simpler approach: list them, let user input an ID to inspect.
        display_df = transactions[['transaction_id', 'transaction_timestamp', 'customer_id', 'merchant_id', 'amount', 'final_risk_level']].copy()
        display_df['amount'] = display_df['amount'].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)
        
        st.markdown("<h4>Transaction Investigation</h4>", unsafe_allow_html=True)
        inspect_id = st.text_input("Enter Transaction ID to inspect details:")
        
        if inspect_id:
            detail = get_transaction_detail(inspect_id)
            if detail:
                render_transaction_detail(detail)
            else:
                st.warning("Transaction not found.")
    else:
        st.info("No transactions match the criteria.")

def render_transaction_detail(detail):
    st.markdown(f"**Transaction:** `{detail['transaction_id']}` | **Time:** `{detail['transaction_timestamp']}`")
    
    c1, c2, c3 = st.columns(3)
    
    with c1:
        st.markdown("##### Core Details")
        st.markdown(f"**Amount:** ₹{detail['amount']:,.2f}")
        st.markdown(f"**Type:** {detail['transaction_type']}")
        st.markdown(f"**Channel:** {detail['payment_channel']}")
        st.markdown(f"**City:** {detail['city']}")
        
    with c2:
        st.markdown("##### Entities")
        st.markdown(f"**Customer:** `{detail['customer_id']}`")
        st.markdown(f"Segment: {detail['customer_segment']}")
        st.markdown(f"**Merchant:** `{detail['merchant_id']}`")
        st.markdown(f"Name: {detail['merchant_name']}")
        
    with c3:
        st.markdown("##### Risk Analysis")
        st.markdown(f"**Final Score:** `{detail['final_risk_score']}`")
        st.markdown(f"**Level:** {risk_badge(detail['final_risk_level'])}", unsafe_allow_html=True)
        st.markdown(f"**Base Score:** {detail['base_risk_score']}")
        st.markdown(f"**Velocity Risk:** {detail['velocity_risk']}")
        st.markdown(f"**Amount Ratio:** {detail['amount_ratio']}x")
        
    if detail['final_risk_score'] > 0:
        st.markdown("##### Risk Factors Breakdown")
        factors = []
        if detail['merchant_blacklisted']:
            factors.append("- Merchant Blacklisted (+50)")
        if detail['merchant_risk_level'] == 'HIGH':
            factors.append("- Merchant Risk High (+30)")
        elif detail['merchant_risk_level'] == 'MEDIUM':
            factors.append("- Merchant Risk Medium (+15)")
            
        if detail['amount_ratio'] >= 5:
            factors.append(f"- Amount Anomaly >= 5x (+20)")
        elif detail['amount_ratio'] >= 3:
            factors.append(f"- Amount Anomaly >= 3x (+10)")
            
        if detail['city'] != detail['customer_city']:
            factors.append("- Location Mismatch (+10)")
            
        if detail['velocity_risk'] == 20:
            factors.append("- High Velocity >= 5 tx/min (+20)")
        elif detail['velocity_risk'] == 10:
            factors.append("- Elevated Velocity >= 3 tx/min (+10)")
            
        for f in factors:
            st.markdown(f)

def render_customers():
    st.markdown("<h2>Customer Analytics</h2>", unsafe_allow_html=True)
    search_id = st.text_input("Search Customer ID")
    
    customers = get_customer_metrics(search_id)
    if not customers.empty:
        display_df = customers.copy()
        display_df['total_val'] = display_df['total_val'].apply(lambda x: f"₹{x:,.2f}")
        display_df['avg_val'] = display_df['avg_val'].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

def render_merchants():
    st.markdown("<h2>Merchant Analytics</h2>", unsafe_allow_html=True)
    search_id = st.text_input("Search Merchant ID or Name")
    
    merchants = get_merchant_metrics(search_id)
    if not merchants.empty:
        display_df = merchants.copy()
        display_df['total_val'] = display_df['total_val'].apply(lambda x: f"₹{x:,.2f}")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

if __name__ == "__main__":
    main()
