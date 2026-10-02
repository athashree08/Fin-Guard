from dashboard.db import fetch_data, fetch_value

def get_kpi_metrics():
    total_tx = fetch_value("SELECT COUNT(*) FROM transactions")
    high_risk = fetch_value("SELECT COUNT(*) FROM transactions WHERE final_risk_level = 'HIGH'")
    medium_risk = fetch_value("SELECT COUNT(*) FROM transactions WHERE final_risk_level = 'MEDIUM'")
    low_risk = fetch_value("SELECT COUNT(*) FROM transactions WHERE final_risk_level = 'LOW'")
    total_val = fetch_value("SELECT SUM(amount) FROM transactions")
    avg_val = fetch_value("SELECT AVG(amount) FROM transactions")
    
    return {
        "total_transactions": total_tx or 0,
        "high_risk": high_risk or 0,
        "medium_risk": medium_risk or 0,
        "low_risk": low_risk or 0,
        "total_value": total_val or 0.0,
        "avg_value": avg_val or 0.0
    }

def get_risk_distribution():
    return fetch_data("""
        SELECT final_risk_level as risk_level, COUNT(*) as count 
        FROM transactions 
        GROUP BY final_risk_level
    """)

def get_transaction_activity_over_time():
    return fetch_data("""
        SELECT date_trunc('minute', transaction_timestamp) as time, COUNT(*) as tx_count, SUM(amount) as tx_value
        FROM transactions
        GROUP BY time
        ORDER BY time DESC
        LIMIT 60
    """)

def get_recent_high_risk_transactions(limit=10):
    return fetch_data(f"""
        SELECT transaction_id, transaction_timestamp as time, customer_id, merchant_id, amount, transaction_type, payment_channel, final_risk_score, final_risk_level
        FROM transactions
        WHERE final_risk_level = 'HIGH'
        ORDER BY transaction_timestamp DESC
        LIMIT {limit}
    """)

def get_filtered_transactions(limit=50, filters=None):
    query = "SELECT * FROM transactions"
    conditions = []
    params = []
    
    if filters:
        if filters.get("risk_level"):
            conditions.append("final_risk_level = %s")
            params.append(filters["risk_level"])
        if filters.get("transaction_type"):
            conditions.append("transaction_type = %s")
            params.append(filters["transaction_type"])
        if filters.get("search_id"):
            search = f"%{filters['search_id']}%"
            conditions.append("(transaction_id LIKE %s OR customer_id LIKE %s OR merchant_id LIKE %s)")
            params.extend([search, search, search])
            
    if conditions:
        query += " WHERE " + " AND ".join(conditions)
        
    query += f" ORDER BY transaction_timestamp DESC LIMIT {limit}"
    return fetch_data(query, tuple(params) if params else None)

def get_transaction_detail(tx_id):
    df = fetch_data("SELECT * FROM transactions WHERE transaction_id = %s", (tx_id,))
    return df.iloc[0].to_dict() if not df.empty else None

def get_customer_metrics(search_id=None):
    query = """
        SELECT customer_id, customer_segment, 
               COUNT(*) as total_tx, SUM(amount) as total_val, AVG(amount) as avg_val,
               SUM(CASE WHEN final_risk_level = 'HIGH' THEN 1 ELSE 0 END) as high_risk_count
        FROM transactions
    """
    params = None
    if search_id:
        query += " WHERE customer_id LIKE %s"
        params = (f"%{search_id}%",)
        
    query += " GROUP BY customer_id, customer_segment ORDER BY total_tx DESC LIMIT 50"
    return fetch_data(query, params)

def get_merchant_metrics(search_id=None):
    query = """
        SELECT merchant_id, merchant_name, merchant_category, merchant_risk_level, merchant_blacklisted,
               COUNT(*) as total_tx, SUM(amount) as total_val,
               SUM(CASE WHEN final_risk_level = 'HIGH' THEN 1 ELSE 0 END) as high_risk_count
        FROM transactions
    """
    params = None
    if search_id:
        query += " WHERE merchant_name LIKE %s OR merchant_id LIKE %s"
        params = (f"%{search_id}%", f"%{search_id}%")
        
    query += " GROUP BY merchant_id, merchant_name, merchant_category, merchant_risk_level, merchant_blacklisted ORDER BY total_tx DESC LIMIT 50"
    return fetch_data(query, params)
