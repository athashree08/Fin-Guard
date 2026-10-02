import streamlit as st
import datetime
import pytz
import pandas as pd

def format_inr(value):
    if pd.isna(value) or value is None:
        return "₹0.00"
    try:
        value = float(value)
    except (ValueError, TypeError):
        return "₹0.00"
    
    is_negative = value < 0
    value = abs(value)
    s = f"{value:.2f}"
    parts = s.split('.')
    int_part = parts[0]
    dec_part = parts[1]
    
    if len(int_part) > 3:
        last_three = int_part[-3:]
        other = int_part[:-3]
        if other != '':
            other = ','.join([other[max(0, i-2):i] for i in range(len(other), 0, -2)][::-1])
            int_part = other + ',' + last_three
            
    res = f"₹{int_part}.{dec_part}"
    if is_negative:
        res = "-" + res
    return res

def format_timestamp(ts, compact=False):
    if pd.isna(ts) or ts is None:
        return ""
    if not isinstance(ts, pd.Timestamp) and not isinstance(ts, datetime.datetime):
        if isinstance(ts, str):
            try:
                ts = pd.to_datetime(ts)
            except:
                return str(ts)
        else:
            return str(ts)
    
    ist = pytz.timezone('Asia/Kolkata')
    if ts.tzinfo is None:
        ts = ist.localize(ts)
    else:
        ts = ts.astimezone(ist)
        
    if compact:
        return ts.strftime("%d %b %Y %H:%M:%S IST")
    return ts.strftime("%d %b %Y, %H:%M:%S IST")

def kpi_card(title, value, is_currency=False):
    if is_currency:
        formatted_value = format_inr(value)
    else:
        if isinstance(value, (int, float)):
            formatted_value = f"{value:,}"
        else:
            formatted_value = value
            
    html = f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{formatted_value}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)

def risk_badge(risk_level):
    level = str(risk_level).upper()
    if level == 'HIGH':
        return '<span class="badge badge-high">HIGH</span>'
    elif level == 'MEDIUM':
        return '<span class="badge badge-medium">MEDIUM</span>'
    else:
        return '<span class="badge badge-low">LOW</span>'
        
def render_system_status(pg_connected, tx_count, last_updated_ts):
    pg_status = "status-ok" if pg_connected else "status-err"
    pg_text = "Connected" if pg_connected else "Disconnected"
    
    dash_status = "status-ok"
    dash_text = "Online"
    
    formatted_ts = format_timestamp(last_updated_ts) if last_updated_ts else "N/A"
    formatted_tx = f"{tx_count:,}" if tx_count is not None else "0"
    
    html = f"""
    <div class="system-status">
        <div style="font-weight: 600; margin-bottom: 0.5rem; color: var(--text-main);">SYSTEM STATUS</div>
        <div style="margin-bottom: 0.25rem;">
            <span class="status-indicator {pg_status}"></span>
            PostgreSQL: {pg_text}
        </div>
        <div style="margin-bottom: 0.5rem;">
            <span class="status-indicator {dash_status}"></span>
            Dashboard: {dash_text}
        </div>
        <div style="color: var(--text-main); font-size: 0.85rem;">
            Transactions: {formatted_tx}<br/>
            Last Updated: {formatted_ts}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
