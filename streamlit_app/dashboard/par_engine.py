"""
Par Engine v2: Cycle-based Par Level calculations
- Pulls NDCP invoice history from Supabase (only required columns)
- Computes daily usage as: total_qty_shipped / window_days
- Determines NEXT order + delivery for each store based on today's date
- Calculates cycle-based Par to cover: delivery -> next delivery window (3 or 4 days)
- Returns:
    - par_results_df (item-level)
    - context_df (store-level order context)
"""

import pandas as pd
import numpy as np
import streamlit as st
from supabase import create_client
from datetime import datetime, timedelta, date

# ----------------------------
# Supabase loader
# ----------------------------
def _get_supabase_client():
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

@st.cache_data(ttl=3600)
def _load_ndcp_data():
    """
    Load ONLY needed columns from Supabase.
    NOTE: we still include both Order Date and Invoice Date so we can choose later.
    """
    supabase = _get_supabase_client()

    # Only the columns we need (plus item_number for proper grouping)
    select_cols = [
        'PC Number',
        'Item Number',
        'Item Description',
        'Qty Ordered',
        'Qty Shipped',
        'Order Date',
        'Invoice Date',
        'Category Desc',
    ]
    select_str = ",".join([f'"{c}"' for c in select_cols])  # keep exact case/spacing

    all_data = []
    chunk_size = 1000
    offset = 0

    while True:
        resp = (
            supabase.table("ndcp_invoices")
            .select(select_str)
            .range(offset, offset + chunk_size - 1)
            .execute()
        )
        chunk = resp.data
        if not chunk:
            break
        all_data.extend(chunk)
        offset += chunk_size

    df = pd.DataFrame(all_data)
    if df.empty:
        return df

    # ----------------------------
    # Normalize columns / types
    # ----------------------------
    df = df.rename(columns={
        "PC Number": "pc_number",
        "Item Number": "item_number",
        "Item Description": "item_name",
        "Qty Ordered": "qty_ordered",
        "Qty Shipped": "qty_shipped",
        "Order Date": "order_date_raw",
        "Invoice Date": "invoice_date_raw",
        "Category Desc": "category",
    })

    # Numeric safety
    for col in ["qty_ordered", "qty_shipped", "item_number"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Date parsing helper for YYYYMMDD stored as int/string
    def _parse_yyyymmdd(series: pd.Series) -> pd.Series:
        s = series.copy()
        s = s.astype("string")
        # Remove decimals like "20250101.0" if they appear
        s = s.str.replace(r"\.0$", "", regex=True)
        s = s.str.zfill(8)
        return pd.to_datetime(s, format="%Y%m%d", errors="coerce")

    df["order_date"] = _parse_yyyymmdd(df["order_date_raw"]) if "order_date_raw" in df.columns else pd.NaT
    df["invoice_date"] = _parse_yyyymmdd(df["invoice_date_raw"]) if "invoice_date_raw" in df.columns else pd.NaT

    # Prefer invoice_date as "receipt/delivery-ish" timestamp for demand modeling.
    # If invoice_date missing, fallback to order_date.
    df["effective_date"] = df["invoice_date"].fillna(df["order_date"])

    # Drop rows missing essentials
    df = df.dropna(subset=["pc_number", "item_number", "item_name", "effective_date"])

    # If qty_shipped missing, fallback to qty_ordered
    df["qty_effective"] = df["qty_shipped"].fillna(df["qty_ordered"])
    df["qty_effective"] = df["qty_effective"].fillna(0)

    return df


# ----------------------------
# Scheduling / cycle logic
# ----------------------------
# Twice-weekly stores (default):
# - Order Tuesday -> Delivery Thursday (same week)
# - Order Saturday -> Delivery Monday (next week)
#
# We treat "cycle par" as inventory needed AFTER the upcoming delivery to last until NEXT delivery.
# - Monday delivery -> next delivery Thursday => 3 days
# - Thursday delivery -> next delivery Monday => 4 days

ORDER_WEEKDAYS = {
    "TUE": 1,  # Monday=0, Tuesday=1
    "SAT": 5,  # Saturday=5
}

DELIVERY_FOR_ORDER = {
    1: 3,  # Tue(1) -> Thu(3)
    5: 0,  # Sat(5) -> Mon(0)
}

def _to_date(d):
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    return datetime.now().date()

def _next_weekday(from_date: date, target_weekday: int) -> date:
    """Return the next date that falls on target_weekday, including today if it matches."""
    days_ahead = (target_weekday - from_date.weekday()) % 7
    return from_date + timedelta(days=days_ahead)

def _compute_delivery_date(order_dt: date, order_weekday: int) -> date:
    """
    Compute delivery date given an order date and weekday.
    - Tue order -> Thu same week
    - Sat order -> Mon next week
    """
    delivery_weekday = DELIVERY_FOR_ORDER[order_weekday]
    if order_weekday == ORDER_WEEKDAYS["TUE"]:
        # Tuesday -> Thursday same week (+2 days)
        return order_dt + timedelta(days=(delivery_weekday - order_weekday))
    else:
        # Saturday -> Monday next week (+2 days, wraps)
        # Sat(5) to Mon(0): +2 days
        return order_dt + timedelta(days=2)

def _next_delivery_after(delivery_dt: date) -> date:
    """
    Next delivery after a given delivery date based on cadence:
    - If delivery is Monday -> next is Thursday same week (+3 days)
    - If delivery is Thursday -> next is Monday next week (+4 days)
    """
    wd = delivery_dt.weekday()
    if wd == 0:   # Monday
        return delivery_dt + timedelta(days=3)
    if wd == 3:   # Thursday
        return delivery_dt + timedelta(days=4)

    # If somehow not Mon/Thu, snap to next Thu if before Thu, else next Mon
    # (keeps system robust)
    next_thu = _next_weekday(delivery_dt, 3)
    if next_thu == delivery_dt:
        next_thu = delivery_dt + timedelta(days=7)
    next_mon = _next_weekday(delivery_dt, 0)
    if next_mon == delivery_dt:
        next_mon = delivery_dt + timedelta(days=7)
    return min(next_thu, next_mon)

def get_order_context(today=None):
    """
    Compute the "next order" context based on today's date.
    This is store-agnostic for the twice-weekly cadence.
    """
    today = _to_date(today)

    next_tue = _next_weekday(today, ORDER_WEEKDAYS["TUE"])
    next_sat = _next_weekday(today, ORDER_WEEKDAYS["SAT"])

    # Choose earliest upcoming order date (tie-breaker: today qualifies)
    next_order_date = min(next_tue, next_sat)

    order_weekday = next_order_date.weekday()
    delivery_date = _compute_delivery_date(next_order_date, order_weekday)

    next_delivery_date = _next_delivery_after(delivery_date)
    cycle_days = (next_delivery_date - delivery_date).days
    cycle_days = max(cycle_days, 1)

    return {
        "today": today,
        "next_order_date": next_order_date,
        "next_delivery_date_for_order": delivery_date,
        "next_delivery_after_that": next_delivery_date,
        "cycle_days": cycle_days,
        "cadence_type": "TWICE_WEEKLY",
        "order_weekday": order_weekday,
        "delivery_weekday": delivery_date.weekday(),
    }


# ----------------------------
# Metrics + Par calculation
# ----------------------------
def calculate_inventory_metrics(df: pd.DataFrame, window_days: int = 90) -> pd.DataFrame:
    """
    Computes item-level metrics per store.
    Daily usage = total_qty_effective / window_days (stable)
    """
    if df.empty:
        return pd.DataFrame()

    cutoff = datetime.now() - timedelta(days=window_days)
    dfw = df[df["effective_date"] >= cutoff].copy()
    if dfw.empty:
        return pd.DataFrame()

    # Group by store + item_number (stable key)
    g = dfw.groupby(["pc_number", "item_number"], as_index=False).agg(
        item_name=("item_name", "last"),
        category=("category", "last"),
        total_qty=("qty_effective", "sum"),
        avg_qty=("qty_effective", "mean"),
        num_orders=("qty_effective", "count"),
        first_date=("effective_date", "min"),
        last_date=("effective_date", "max"),
    )

    g["window_days"] = window_days
    g["daily_usage_rate"] = g["total_qty"] / float(window_days)

    return g


def get_par_for_next_order(
    pc_number: str | None = None,
    today=None,
    window_days: int = 90,
    safety_percent: float = 20.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Returns:
      par_df: item-level rows with par_quantity for the NEXT delivery cycle
      ctx_df: store-level order context (one row per store shown)
    """
    raw = _load_ndcp_data()
    if raw.empty:
        return pd.DataFrame(), pd.DataFrame()

    metrics = calculate_inventory_metrics(raw, window_days=window_days)
    if metrics.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Optionally filter store
    if pc_number:
        metrics = metrics[metrics["pc_number"] == pc_number].copy()

    if metrics.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Build store contexts (per store)
    # NOTE: currently cadence is same for all stores; later we can override per PC.
    ctx = get_order_context(today=today)

    stores = sorted(metrics["pc_number"].unique().tolist())
    ctx_rows = []
    for store in stores:
        row = {"pc_number": store, **ctx}
        ctx_rows.append(row)

    ctx_df = pd.DataFrame(ctx_rows)

    # Join context onto metrics
    metrics = metrics.merge(ctx_df[["pc_number", "cycle_days"]], on="pc_number", how="left")

    # Par for that specific upcoming delivery cycle
    safety_mult = 1.0 + (float(safety_percent) / 100.0)
    metrics["par_quantity"] = np.ceil(metrics["daily_usage_rate"] * metrics["cycle_days"] * safety_mult)
    metrics["par_quantity"] = metrics["par_quantity"].fillna(0).clip(lower=0).astype(int)

    # Helpful metadata
    metrics["safety_percent"] = float(safety_percent)
    metrics["calculated_at"] = datetime.now().isoformat()

    # Final columns
    par_df = metrics[[
        "pc_number",
        "item_number",
        "item_name",
        "category",
        "daily_usage_rate",
        "cycle_days",
        "par_quantity",
        "total_qty",
        "avg_qty",
        "num_orders",
        "window_days",
        "safety_percent",
        "calculated_at",
    ]].copy()

    return par_df, ctx_df
