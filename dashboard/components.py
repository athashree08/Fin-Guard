import streamlit as st

def kpi_card(title, value, prefix="", suffix="", format_str=""):
    formatted_value = value
    if isinstance(value, (int, float)):
        if format_str:
            formatted_value = format_str.format(value)
        else:
            formatted_value = f"{value:,}"
            
    html = f"""
    <div class="kpi-card">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{prefix}{formatted_value}{suffix}</div>
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
        
def render_system_status(pg_connected, last_updated):
    pg_status = "status-ok" if pg_connected else "status-err"
    pg_text = "Connected" if pg_connected else "Disconnected"
    
    html = f"""
    <div class="system-status">
        <div style="font-weight: 600; margin-bottom: 0.5rem; color: var(--text-main);">System Status</div>
        <div style="margin-bottom: 0.25rem;">
            <span class="status-indicator {pg_status}"></span>
            PostgreSQL: {pg_text}
        </div>
        <div style="color: var(--text-muted); font-size: 0.75rem; margin-top: 0.5rem;">
            Last Updated: {last_updated}
        </div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)
