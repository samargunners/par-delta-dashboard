
"""
Par Engine: Centralized logic for Par Level calculations
Update DB_PATH to match your actual database location and connector.
"""
import pandas as pd
import sqlite3  # Replace with your actual DB connector if needed
import os

# Update this path to your actual database file
DB_PATH = os.path.join(os.path.dirname(__file__), '../database/your_database.db')

# --- Par Engine Functions ---
def get_par_methods():
    """Fetch available par calculation methods."""
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql('SELECT method_key, method_name, description FROM par_methods WHERE is_active = 1', conn)
    conn.close()
    return df

def get_par_results(method_key=None):
    """Fetch par results, optionally filtered by method."""
    conn = sqlite3.connect(DB_PATH)
    query = 'SELECT * FROM par_results'
    if method_key:
        query += f" WHERE method_key = '{method_key}'"
    df = pd.read_sql(query, conn)
    conn.close()
    return df

def get_inventory_metrics(item_number=None, pc_number=None):
    """Fetch inventory item metrics for explanation."""
    conn = sqlite3.connect(DB_PATH)
    query = 'SELECT * FROM inventory_item_metrics'
    filters = []
    if item_number:
        filters.append(f"item_number = '{item_number}'")
    if pc_number:
        filters.append(f"pc_number = '{pc_number}'")
    if filters:
        query += ' WHERE ' + ' AND '.join(filters)
    df = pd.read_sql(query, conn)
    conn.close()
    return df

# Add more functions for settings, recalculation, etc. as needed
