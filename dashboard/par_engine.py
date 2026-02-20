"""
Par Engine v2 (with Last Year comparison): Cycle-based Par Level calculations
- Pulls NDCP invoice history from Supabase (only required columns)
- Computes daily usage as: total_qty_shipped / window_days
- Computes SAME WINDOW LAST YEAR daily usage + par for reference
- Determines NEXT order + delivery for each store based on today's date
- Calculates cycle-based Par to cover: delivery -> next delivery window (3 or 4 days)
- Returns:
    - par_results_df (item-level, includes current + last year columns)
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
    select_str = ",".join([f'"{c}"' for c in select_cols])

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

        # supabase-py can return different response shapes; handle both
        chunk = getattr(resp, "data", None)
        if chunk is None and isinstance(resp, dict):
            chunk = resp.get("data")
        if not chunk:
            break

        all_data.extend(chunk)
        offset += chunk_size

    df = pd.DataFrame(all_data)
    if df.empty:
        return df

    # Normalize columns / types
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

    for col in ["qty_ordered", "qty_shipped", "item_number"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    def _parse_yyyymmdd(series: pd.Series) -> pd.Series:
        s = series.copy()
        s = s.astype("string")
        s = s.str.replace(r"\.0$", "", regex=True)
        s = s.str.zfill(8)
        return pd.to_datetime(s, format="%Y%m%d", errors="coerce")

    df["order_date"] = _parse_yyyymmdd(df["order_date_raw"]) if "order_date_raw" in df.columns else pd.NaT
    df["invoice_date"] = _parse_yyyymmdd(df["invoice_date_raw"]) if "invoice_date_raw" in df.columns else pd.NaT

    # Use invoice_date as "delivery-ish" date; fallback to order_date
    df["effective_date"] = df["invoice_date"].fillna(df["order_date"])

    df = df.dropna(subset=["pc_number", "item_number", "item_name", "effective_date"])

    # Effective quantity: prefer shipped, fallback ordered
    df["qty_effective"] = df["qty_shipped"].fillna(df["qty_ordered"])
    df["qty_effective"] = df["qty_effective"].fillna(0)

    return df


# ----------------------------
# Scheduling / cycle logic
# ----------------------------
ORDER_WEEKDAYS = {
    "TUE": 1,  # Monday=0
    "SAT": 5,
}

DELIVERY_FOR_ORDER = {
    1: 3,  # Tue -> Thu
    5: 0,  # Sat -> Mon
}

def _to_date(d):
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    return datetime.now().date()

def _next_weekday(from_date: date, target_weekday: int) -> date:
    days_ahead = (target_weekday - from_date.weekday()) % 7
    return from_date + timedelta(days=days_ahead)

def _compute_delivery_date(order_dt: date, order_weekday: int) -> date:
    if order_weekday == ORDER_WEEKDAYS["TUE"]:
        return order_dt + timedelta(days=2)  # Tue -> Thu
    return order_dt + timedelta(days=2)      # Sat -> Mon (wrap)

def _next_delivery_after(delivery_dt: date) -> date:
    wd = delivery_dt.weekday()
    if wd == 0:   # Monday -> Thursday
        return delivery_dt + timedelta(days=3)
    if wd == 3:   # Thursday -> Monday
        return delivery_dt + timedelta(days=4)

    # Robust fallback
    next_thu = _next_weekday(delivery_dt, 3)
    if next_thu == delivery_dt:
        next_thu = delivery_dt + timedelta(days=7)
    next_mon = _next_weekday(delivery_dt, 0)
    if next_mon == delivery_dt:
        next_mon = delivery_dt + timedelta(days=7)
    return min(next_thu, next_mon)

def get_order_context(today=None):
    today = _to_date(today)

    next_tue = _next_weekday(today, ORDER_WEEKDAYS["TUE"])
    next_sat = _next_weekday(today, ORDER_WEEKDAYS["SAT"])
    next_order_date = min(next_tue, next_sat)

    order_weekday = next_order_date.weekday()
    delivery_date = _compute_delivery_date(next_order_date, order_weekday)

    next_delivery_date = _next_delivery_after(delivery_date)
    cycle_days = max((next_delivery_date - delivery_date).days, 1)

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
# Metrics + Par calculation (current + last year)
# ----------------------------
def _compute_metrics_for_period(df: pd.DataFrame, start_dt: datetime, end_dt: datetime, window_days: int) -> pd.DataFrame:
    """
    Compute item-level metrics for a specific time window [start_dt, end_dt).
    Daily usage = total_qty_effective / window_days
    """
    if df.empty:
        return pd.DataFrame()

    dff = df[(df["effective_date"] >= start_dt) & (df["effective_date"] < end_dt)].copy()
    if dff.empty:
        return pd.DataFrame()

    g = dff.groupby(["pc_number", "item_number"], as_index=False).agg(
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
    pc_number=None,
    today=None,
    window_days: int = 90,
    safety_percent: float = 20.0,
):
    """
    Returns:
      par_df: item-level rows with par_quantity (current) + ly_par_quantity (same window last year)
      ctx_df: store-level order context (one row per store shown)
    """
    raw = _load_ndcp_data()
    if raw.empty:
        return pd.DataFrame(), pd.DataFrame()

    today_date = _to_date(today)
    today_dt = datetime.combine(today_date, datetime.min.time())

    # Current window: [today-window_days, today)
    current_end = today_dt
    current_start = today_dt - timedelta(days=window_days)

    # Same window last year (handles leap years correctly)
    ly_end = (pd.Timestamp(today_dt) - pd.DateOffset(years=1)).to_pydatetime()
    ly_start = ly_end - timedelta(days=window_days)

    cur_metrics = _compute_metrics_for_period(raw, current_start, current_end, window_days)
    ly_metrics = _compute_metrics_for_period(raw, ly_start, ly_end, window_days)

    if cur_metrics.empty and ly_metrics.empty:
        return pd.DataFrame(), pd.DataFrame()

    # Optional store filter
    if pc_number:
        if not cur_metrics.empty:
            cur_metrics = cur_metrics[cur_metrics["pc_number"] == pc_number].copy()
        if not ly_metrics.empty:
            ly_metrics = ly_metrics[ly_metrics["pc_number"] == pc_number].copy()

    # Order context (same for all stores for now)
    ctx = get_order_context(today=today_date)

    stores = set()
    if not cur_metrics.empty:
        stores.update(cur_metrics["pc_number"].unique().tolist())
    if not ly_metrics.empty:
        stores.update(ly_metrics["pc_number"].unique().tolist())
    stores = sorted(list(stores))

    ctx_df = pd.DataFrame([{"pc_number": s, **ctx} for s in stores])

    # Rename LY columns before merge
    if not ly_metrics.empty:
        ly_metrics = ly_metrics.rename(columns={
            "total_qty": "ly_total_qty",
            "avg_qty": "ly_avg_qty",
            "num_orders": "ly_num_orders",
            "first_date": "ly_first_date",
            "last_date": "ly_last_date",
            "daily_usage_rate": "ly_daily_usage_rate",
        })

    # Merge current + LY (outer keeps items that exist only in one period)
    if cur_metrics.empty:
        merged = ly_metrics.copy()
        for col in ["total_qty", "avg_qty", "num_orders", "daily_usage_rate", "window_days"]:
            if col not in merged.columns:
                merged[col] = np.nan
    elif ly_metrics.empty:
        merged = cur_metrics.copy()
        for col in ["ly_total_qty", "ly_avg_qty", "ly_num_orders", "ly_daily_usage_rate"]:
            if col not in merged.columns:
                merged[col] = np.nan
    else:
        merged = pd.merge(
            cur_metrics,
            ly_metrics[[
                "pc_number", "item_number",
                "ly_total_qty", "ly_avg_qty", "ly_num_orders",
                "ly_first_date", "ly_last_date", "ly_daily_usage_rate"
            ]],
            on=["pc_number", "item_number"],
            how="outer"
        )

    # Attach cycle days
    merged = merged.merge(ctx_df[["pc_number", "cycle_days"]], on="pc_number", how="left")

    safety_mult = 1.0 + (float(safety_percent) / 100.0)

    # Current par
    merged["par_quantity"] = np.ceil(merged["daily_usage_rate"].fillna(0) * merged["cycle_days"].fillna(0) * safety_mult)
    merged["par_quantity"] = merged["par_quantity"].fillna(0).clip(lower=0).astype(int)

    # Last-year par
    merged["ly_par_quantity"] = np.ceil(merged["ly_daily_usage_rate"].fillna(0) * merged["cycle_days"].fillna(0) * safety_mult)
    merged["ly_par_quantity"] = merged["ly_par_quantity"].fillna(0).clip(lower=0).astype(int)

    merged["safety_percent"] = float(safety_percent)
    merged["calculated_at"] = datetime.now().isoformat()

    # Window metadata (handy to display on the page)
    merged["current_window_start"] = current_start.date().isoformat()
    merged["current_window_end"] = current_end.date().isoformat()
    merged["ly_window_start"] = ly_start.date().isoformat()
    merged["ly_window_end"] = ly_end.date().isoformat()

    par_df = merged[[
        "pc_number",
        "item_number",
        "item_name",
        "category",
        "cycle_days",
        "daily_usage_rate",
        "par_quantity",
        "ly_daily_usage_rate",
        "ly_par_quantity",
        "num_orders",
        "ly_num_orders",
        "total_qty",
        "ly_total_qty",
        "window_days",
        "current_window_start",
        "current_window_end",
        "ly_window_start",
        "ly_window_end",
        "safety_percent",
        "calculated_at",
    ]].copy()

    return par_df, ctx_df
