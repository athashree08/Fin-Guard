import os
import psycopg2
from psycopg2 import pool
import streamlit as st
from contextlib import contextmanager
import pandas as pd

@st.cache_resource
def get_connection_pool():
    host = os.environ.get("POSTGRES_HOST", "localhost")
    port = os.environ.get("POSTGRES_PORT", "5432")
    database = os.environ.get("POSTGRES_DB", "finguard")
    user = os.environ.get("POSTGRES_USER", "postgres")
    password = os.environ.get("POSTGRES_PASSWORD", "")
    
    try:
        connection_pool = pool.SimpleConnectionPool(
            1, 10,
            user=user,
            password=password,
            host=host,
            port=port,
            database=database
        )
        return connection_pool
    except Exception as e:
        return None

@contextmanager
def get_db_connection():
    pool = get_connection_pool()
    if pool:
        conn = pool.getconn()
        try:
            yield conn
        finally:
            pool.putconn(conn)
    else:
        yield None

def fetch_data(query, params=None):
    with get_db_connection() as conn:
        if conn is None:
            st.error("DATABASE CONNECTION\nUnable to connect to PostgreSQL.")
            return pd.DataFrame()
        try:
            return pd.read_sql_query(query, conn, params=params)
        except Exception as e:
            st.error(f"Error executing query: {e}")
            return pd.DataFrame()

def fetch_value(query, params=None):
    with get_db_connection() as conn:
        if conn is None:
            return None
        with conn.cursor() as cur:
            try:
                cur.execute(query, params)
                result = cur.fetchone()
                return result[0] if result else None
            except Exception as e:
                st.error(f"Error executing query: {e}")
                return None
