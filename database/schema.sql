# Updated schema with notes integrated into SQL comments and formatting improvements
updated_schema_sql = """
-- ===============================
-- Par Delta Dashboard: Database Schema (Updated)
-- ===============================

-- 1. Stores Table
CREATE TABLE stores (
    pc_number VARCHAR(6) UNIQUE NOT NULL, -- 6-digit store code
    name TEXT,
    address TEXT
);

-- 2. Product Types Table
CREATE TABLE product_types (
    product_type_id SERIAL PRIMARY KEY,
    name TEXT UNIQUE
);

-- 3. Products Table
CREATE TABLE products (
    product_id SERIAL PRIMARY KEY,
    name TEXT,
    product_type_id INT REFERENCES product_types(product_type_id),
    supplier TEXT CHECK (supplier IN ('CML', 'NDCP')),
    unit TEXT
);

-- 4. Usage Overview Table
CREATE TABLE usage_overview (
    store_id INT REFERENCES stores(pc_number),
    date DATE,
    product_type_id INT REFERENCES product_types(product_type_id),
    ordered_qty NUMERIC,
    wasted_qty NUMERIC,
    waste_percent NUMERIC,
    waste_dollar NUMERIC, -- in currency
    expected_consumption NUMERIC,
    product_type TEXT
);

-- 5. Donut Sales Hourly Table
CREATE TABLE donut_sales_hourly (
    store_id INT REFERENCES stores(pc_number),
    sale_datetime TIMESTAMP,
    product_name TEXT,
    product_type_id INT REFERENCES product_types(product_type_id),
    quantity NUMERIC,
    value NUMERIC -- in currency
);

-- 6. Employee Clockins Table
CREATE TABLE employee_clockins (
    employee_id VARCHAR(20),
    employee_name TEXT,
    store_id INT REFERENCES stores(pc_number),
    date DATE,
    time_in TIME,
    time_out TIME,
    total_time NUMERIC,
    rate NUMERIC,
    regular_hours NUMERIC,
    regular_wages NUMERIC, -- in currency
    ot_hours NUMERIC,
    ot_wages NUMERIC, -- in currency
    total_wages NUMERIC -- in currency
);

-- 7. Employee Schedules Table
CREATE TABLE employee_schedules (
    employee_id VARCHAR(20),
    date DATE,
    start_time TIME,
    end_time TIME
);

-- 8. Hourly Labor Summary Table
CREATE TABLE hourly_labor_summary (
    store_id INT REFERENCES stores(pc_number),
    date DATE,
    hour_range TEXT,
    forecasted_checks NUMERIC,
    forecasted_sales NUMERIC, -- in currency
    ideal_hours NUMERIC,
    scheduled_hours NUMERIC,
    actual_hours NUMERIC,
    actual_labor NUMERIC, -- in currency
    sales_value NUMERIC, -- in currency
    check_count NUMERIC
);

-- 9. Variance Report Summary Table
CREATE TABLE variance_report_summary (
    store_id INT REFERENCES stores(pc_number),
    product_name TEXT,
    subcategory TEXT,
    unit TEXT,
    qty_variance NUMERIC,
    dollar_variance NUMERIC, -- in currency
    cogs NUMERIC, -- in currency
    units_sold NUMERIC,
    theoretical_qty NUMERIC,
    theoretical_value NUMERIC, -- in currency
    beginning_qty NUMERIC,
    purchase_qty NUMERIC,
    ending_qty NUMERIC,
    beginning_value NUMERIC,
    purchase_value NUMERIC, -- in currency
    waste_qty NUMERIC,
    ending_value NUMERIC, -- in currency
    transfer_in NUMERIC,
    transfer_out NUMERIC
);
"""

# Save updated schema.sql
updated_schema_path = "/mnt/data/schema_updated.sql"
with open(updated_schema_path, "w") as f:
    f.write(updated_schema_sql)

updated_schema_path
