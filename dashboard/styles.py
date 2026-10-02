def get_styles():
    return """
    <style>
        /* Professional FinGuard Theme */
        :root {
            --primary-bg: #f8f9fa;
            --sidebar-bg: #ffffff;
            --text-main: #212529;
            --text-muted: #6c757d;
            --accent: #0f4c81;
            
            --risk-high-bg: #fff0f0;
            --risk-high-text: #dc3545;
            --risk-high-border: #f5c6cb;
            
            --risk-medium-bg: #fff8e6;
            --risk-medium-text: #d39e00;
            --risk-medium-border: #ffeeba;
            
            --risk-low-bg: #e6f7ec;
            --risk-low-text: #28a745;
            --risk-low-border: #c3e6cb;
            
            --card-border: #e9ecef;
            --card-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }
        

        
        /* Typography */
        h1, h2, h3 {
            color: var(--accent);
            font-weight: 600;
            letter-spacing: -0.5px;
        }
        
        /* KPI Cards */
        .kpi-card {
            background: white;
            padding: 1.2rem;
            border-radius: 4px;
            border: 1px solid var(--card-border);
            box-shadow: var(--card-shadow);
            margin-bottom: 1rem;
        }
        .kpi-title {
            color: var(--text-muted);
            font-size: 0.85rem;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 0.5rem;
            font-weight: 600;
        }
        .kpi-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: var(--text-main);
        }
        
        /* Risk Badges */
        .badge {
            padding: 0.25em 0.6em;
            font-size: 0.75rem;
            font-weight: 700;
            border-radius: 0.25rem;
            display: inline-block;
            text-transform: uppercase;
            border: 1px solid transparent;
        }
        .badge-high {
            background-color: var(--risk-high-bg);
            color: var(--risk-high-text);
            border-color: var(--risk-high-border);
        }
        .badge-medium {
            background-color: var(--risk-medium-bg);
            color: var(--risk-medium-text);
            border-color: var(--risk-medium-border);
        }
        .badge-low {
            background-color: var(--risk-low-bg);
            color: var(--risk-low-text);
            border-color: var(--risk-low-border);
        }
        
        /* Table overrides */
        .stDataFrame {
            border: 1px solid var(--card-border);
            border-radius: 4px;
        }
        
        /* Sidebar styling */
        [data-testid="stSidebar"] {
            background-color: var(--sidebar-bg);
            border-right: 1px solid var(--card-border);
        }
        .sidebar-logo {
            font-size: 1.5rem;
            font-weight: 800;
            color: var(--accent);
            letter-spacing: -0.5px;
            margin-bottom: 2rem;
            border-bottom: 1px solid var(--card-border);
            padding-bottom: 1rem;
        }
        .system-status {
            margin-top: 2rem;
            padding-top: 1rem;
            border-top: 1px solid var(--card-border);
            font-size: 0.85rem;
        }
        .status-indicator {
            display: inline-block;
            width: 8px;
            height: 8px;
            border-radius: 50%;
            margin-right: 5px;
        }
        .status-ok { background-color: #28a745; }
        .status-err { background-color: #dc3545; }
    </style>
    """
