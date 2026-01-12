"""
Par Delta Dashboard - Project Documentation Generator
Generates a comprehensive PDF documenting all database tables, columns, and analysis features
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, Image, KeepTogether
)
from reportlab.lib.colors import HexColor
from datetime import datetime

# Define colors
PRIMARY_COLOR = HexColor("#FF6600")  # Dunkin' Orange
SECONDARY_COLOR = HexColor("#663399")
TABLE_HEADER_BG = HexColor("#FF6600")
TABLE_ALT_ROW = HexColor("#FFF5EE")

def create_pdf():
    # Create PDF
    filename = f"Par_Delta_Dashboard_Documentation_{datetime.now().strftime('%Y%m%d')}.pdf"
    doc = SimpleDocTemplate(
        filename,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=1*inch,
        bottomMargin=0.75*inch
    )
    
    # Container for PDF elements
    story = []
    
    # Define styles
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=PRIMARY_COLOR,
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    heading1_style = ParagraphStyle(
        'CustomHeading1',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=PRIMARY_COLOR,
        spaceAfter=12,
        spaceBefore=12,
        fontName='Helvetica-Bold'
    )
    
    heading2_style = ParagraphStyle(
        'CustomHeading2',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=SECONDARY_COLOR,
        spaceAfter=10,
        spaceBefore=10,
        fontName='Helvetica-Bold'
    )
    
    heading3_style = ParagraphStyle(
        'CustomHeading3',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.black,
        spaceAfter=8,
        spaceBefore=8,
        fontName='Helvetica-Bold'
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=10,
        spaceAfter=6,
        alignment=TA_JUSTIFY
    )
    
    # Cover Page
    story.append(Spacer(1, 2*inch))
    story.append(Paragraph("Par Delta Dashboard", title_style))
    story.append(Spacer(1, 0.3*inch))
    story.append(Paragraph("Complete Technical Documentation", heading2_style))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Database Schema, Tables, Columns & Analysis Features", body_style))
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y')}", body_style))
    story.append(PageBreak())
    
    # Table of Contents
    story.append(Paragraph("Table of Contents", heading1_style))
    story.append(Spacer(1, 0.2*inch))
    
    toc_data = [
        ["Section", "Page"],
        ["1. Project Overview", "3"],
        ["2. Database Schema", "4"],
        ["3. Data Tables & Columns", "5"],
        ["4. Dashboard Analysis Features", "12"],
        ["5. Data Ingestion Pipeline", "20"],
        ["6. Technical Architecture", "22"],
    ]
    
    toc_table = Table(toc_data, colWidths=[5*inch, 1*inch])
    toc_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, TABLE_ALT_ROW]),
    ]))
    story.append(toc_table)
    story.append(PageBreak())
    
    # ====== 1. PROJECT OVERVIEW ======
    story.append(Paragraph("1. Project Overview", heading1_style))
    story.append(Spacer(1, 0.1*inch))
    
    overview_text = """
    The Par Delta Dashboard is a modern Streamlit-based operational analytics platform designed for 
    Dunkin' locations managed by Par Delta. The system provides real-time analytics across multiple 
    operational domains including labor management, inventory tracking, donut waste analysis, 
    employee performance monitoring, and variance reporting.
    """
    story.append(Paragraph(overview_text, body_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("Key Features:", heading3_style))
    features = [
        "Real-time data integration with Supabase (PostgreSQL backend)",
        "Interactive visualizations using Plotly and Matplotlib",
        "Modular dashboard architecture with 10+ analysis modules",
        "AI-powered chat interface for conversational analytics",
        "Automated data ingestion from multiple sources (CrunchTime, Labour systems)",
        "Comprehensive labor and inventory variance analysis",
        "Multi-store operational comparison and monitoring"
    ]
    for feature in features:
        story.append(Paragraph(f"• {feature}", body_style))
    
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("Technology Stack:", heading3_style))
    tech_data = [
        ["Component", "Technology"],
        ["Frontend", "Streamlit"],
        ["Backend Database", "Supabase (PostgreSQL)"],
        ["Data Visualization", "Plotly, Matplotlib"],
        ["AI Integration", "OpenAI GPT, LangChain"],
        ["Data Processing", "Pandas, NumPy"],
        ["Language", "Python 3.x"],
    ]
    
    tech_table = Table(tech_data, colWidths=[2*inch, 4*inch])
    tech_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, TABLE_ALT_ROW]),
    ]))
    story.append(tech_table)
    story.append(PageBreak())
    
    # ====== 2. DATABASE SCHEMA ======
    story.append(Paragraph("2. Database Schema Overview", heading1_style))
    story.append(Spacer(1, 0.1*inch))
    
    schema_text = """
    The database consists of 9 primary tables organized to track store operations, inventory, 
    labor management, and sales data. All tables are interconnected through foreign key relationships, 
    primarily using store identifiers (pc_number) and product type references.
    """
    story.append(Paragraph(schema_text, body_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Database schema diagram text
    story.append(Paragraph("Database Entity Relationships:", heading3_style))
    er_text = """
    <b>Core Entities:</b><br/>
    • <b>stores</b> → Referenced by all operational tables via pc_number<br/>
    • <b>product_types</b> → Referenced by products, usage_overview, donut_sales_hourly<br/>
    • <b>products</b> → Catalog of all products with supplier information<br/>
    <br/>
    <b>Operational Data:</b><br/>
    • <b>employee_clockins</b> → Actual work hours and wages<br/>
    • <b>employee_schedules</b> → Planned work schedules<br/>
    • <b>hourly_labor_summary</b> → Aggregated labor metrics by hour<br/>
    <br/>
    <b>Inventory & Sales:</b><br/>
    • <b>usage_overview</b> → Daily product usage, waste, and ordering<br/>
    • <b>donut_sales_hourly</b> → Hourly donut sales transactions<br/>
    • <b>variance_report_summary</b> → Inventory variance and theoretical vs actual analysis<br/>
    """
    story.append(Paragraph(er_text, body_style))
    story.append(PageBreak())
    
    # ====== 3. DATA TABLES & COLUMNS ======
    story.append(Paragraph("3. Data Tables & Columns", heading1_style))
    story.append(Spacer(1, 0.1*inch))
    
    # Table 1: Stores
    story.append(Paragraph("3.1 stores", heading2_style))
    story.append(Paragraph("Store location master data", body_style))
    
    stores_data = [
        ["Column Name", "Data Type", "Description", "Constraints"],
        ["pc_number", "VARCHAR(6)", "6-digit store code", "UNIQUE, NOT NULL"],
        ["name", "TEXT", "Store name", ""],
        ["address", "TEXT", "Store address", ""],
    ]
    
    create_table_section(story, stores_data)
    story.append(Spacer(1, 0.2*inch))
    
    # Table 2: Product Types
    story.append(Paragraph("3.2 product_types", heading2_style))
    story.append(Paragraph("Product category classifications", body_style))
    
    product_types_data = [
        ["Column Name", "Data Type", "Description", "Constraints"],
        ["product_type_id", "SERIAL", "Auto-increment ID", "PRIMARY KEY"],
        ["name", "TEXT", "Product type name (e.g., Donut, Coffee)", "UNIQUE"],
    ]
    
    create_table_section(story, product_types_data)
    story.append(Spacer(1, 0.2*inch))
    
    # Table 3: Products
    story.append(Paragraph("3.3 products", heading2_style))
    story.append(Paragraph("Complete product catalog with supplier information", body_style))
    
    products_data = [
        ["Column Name", "Data Type", "Description", "Constraints"],
        ["product_id", "SERIAL", "Auto-increment ID", "PRIMARY KEY"],
        ["name", "TEXT", "Product name", ""],
        ["product_type_id", "INT", "Foreign key to product_types", "REFERENCES product_types"],
        ["supplier", "TEXT", "Supplier name", "CHECK IN ('CML', 'NDCP')"],
        ["unit", "TEXT", "Unit of measurement", ""],
    ]
    
    create_table_section(story, products_data)
    story.append(PageBreak())
    
    # Table 4: Usage Overview
    story.append(Paragraph("3.4 usage_overview", heading2_style))
    story.append(Paragraph("Daily product usage, waste, and consumption tracking", body_style))
    story.append(Paragraph("<b>Used in:</b> Donut Waste & Gap Analysis", body_style))
    
    usage_data = [
        ["Column Name", "Data Type", "Description", "Analysis Use"],
        ["store_id", "INT", "Store identifier", "Filter by location"],
        ["date", "DATE", "Date of record", "Time series analysis"],
        ["product_type_id", "INT", "Product type reference", "Category filtering"],
        ["ordered_qty", "NUMERIC", "Quantity ordered", "Supply calculation"],
        ["wasted_qty", "NUMERIC", "Quantity wasted", "Waste analysis"],
        ["waste_percent", "NUMERIC", "Waste percentage", "Efficiency metrics"],
        ["waste_dollar", "NUMERIC", "Waste cost in dollars", "Financial impact"],
        ["expected_consumption", "NUMERIC", "Expected usage", "Variance calculation"],
        ["product_type", "TEXT", "Product type name", "Display/filtering"],
    ]
    
    create_table_section(story, usage_data)
    story.append(Spacer(1, 0.2*inch))
    
    # Table 5: Donut Sales Hourly
    story.append(Paragraph("3.5 donut_sales_hourly", heading2_style))
    story.append(Paragraph("Hourly donut sales transaction data", body_style))
    story.append(Paragraph("<b>Used in:</b> Donut Waste & Gap, Hourly Sales", body_style))
    
    donut_sales_data = [
        ["Column Name", "Data Type", "Description", "Analysis Use"],
        ["store_id", "INT", "Store identifier", "Location filtering"],
        ["sale_datetime", "TIMESTAMP", "Sale timestamp", "Hourly aggregation"],
        ["product_name", "TEXT", "Product name", "Product-level analysis"],
        ["product_type_id", "INT", "Product type reference", "Category analysis"],
        ["quantity", "NUMERIC", "Units sold", "Sales volume tracking"],
        ["value", "NUMERIC", "Sales value in dollars", "Revenue analysis"],
    ]
    
    create_table_section(story, donut_sales_data)
    story.append(PageBreak())
    
    # Table 6: Employee Clockins
    story.append(Paragraph("3.6 employee_clockins", heading2_style))
    story.append(Paragraph("Actual employee work hours and payroll data", body_style))
    story.append(Paragraph("<b>Used in:</b> Labor Punctuality, Employee Performance, Ideal vs Actual Labor", body_style))
    
    clockin_data = [
        ["Column Name", "Data Type", "Description", "Analysis Use"],
        ["employee_id", "VARCHAR(20)", "Employee identifier", "Employee tracking"],
        ["employee_name", "TEXT", "Employee name", "Display/reporting"],
        ["store_id", "INT", "Store reference", "Location filtering"],
        ["date", "DATE", "Work date", "Time analysis"],
        ["time_in", "TIME", "Clock in time", "Punctuality analysis"],
        ["time_out", "TIME", "Clock out time", "Shift duration"],
        ["total_time", "NUMERIC", "Total hours worked", "Labor hours calculation"],
        ["rate", "NUMERIC", "Hourly pay rate", "Wage calculation"],
        ["regular_hours", "NUMERIC", "Regular work hours", "Standard pay calculation"],
        ["regular_wages", "NUMERIC", "Regular wages paid", "Labor cost"],
        ["ot_hours", "NUMERIC", "Overtime hours", "OT analysis"],
        ["ot_wages", "NUMERIC", "Overtime wages", "OT cost analysis"],
        ["total_wages", "NUMERIC", "Total wages", "Total labor cost"],
    ]
    
    create_table_section(story, clockin_data)
    story.append(Spacer(1, 0.2*inch))
    
    # Table 7: Employee Schedules
    story.append(Paragraph("3.7 employee_schedules", heading2_style))
    story.append(Paragraph("Planned employee work schedules", body_style))
    story.append(Paragraph("<b>Used in:</b> Labor Punctuality, Ideal vs Actual Labor", body_style))
    
    schedule_data = [
        ["Column Name", "Data Type", "Description", "Analysis Use"],
        ["employee_id", "VARCHAR(20)", "Employee identifier", "Schedule tracking"],
        ["date", "DATE", "Scheduled date", "Time analysis"],
        ["start_time", "TIME", "Scheduled start", "Punctuality comparison"],
        ["end_time", "TIME", "Scheduled end", "Shift planning"],
    ]
    
    create_table_section(story, schedule_data)
    story.append(PageBreak())
    
    # Table 8: Hourly Labor Summary
    story.append(Paragraph("3.8 hourly_labor_summary", heading2_style))
    story.append(Paragraph("Aggregated hourly labor and sales metrics", body_style))
    story.append(Paragraph("<b>Used in:</b> Ideal vs Actual Labor, Hourly Sales", body_style))
    
    labor_summary_data = [
        ["Column Name", "Data Type", "Description", "Analysis Use"],
        ["store_id", "INT", "Store identifier", "Location filtering"],
        ["date", "DATE", "Record date", "Time series analysis"],
        ["hour_range", "TEXT", "Hour range (e.g., 06:00-07:00)", "Hourly analysis"],
        ["forecasted_checks", "NUMERIC", "Predicted customer count", "Demand planning"],
        ["forecasted_sales", "NUMERIC", "Predicted sales value", "Revenue forecasting"],
        ["ideal_hours", "NUMERIC", "Optimal labor hours", "Efficiency target"],
        ["scheduled_hours", "NUMERIC", "Planned labor hours", "Planning analysis"],
        ["actual_hours", "NUMERIC", "Actual labor hours", "Performance tracking"],
        ["actual_labor", "NUMERIC", "Actual labor cost", "Cost analysis"],
        ["sales_value", "NUMERIC", "Actual sales value", "Revenue tracking"],
        ["check_count", "NUMERIC", "Actual customer count", "Traffic analysis"],
    ]
    
    create_table_section(story, labor_summary_data)
    story.append(Spacer(1, 0.2*inch))
    
    # Table 9: Variance Report Summary
    story.append(Paragraph("3.9 variance_report_summary", heading2_style))
    story.append(Paragraph("Inventory variance and theoretical vs actual analysis", body_style))
    story.append(Paragraph("<b>Used in:</b> Inventory Variance, Retail Merchandise", body_style))
    
    variance_data = [
        ["Column Name", "Data Type", "Description", "Analysis Use"],
        ["store_id", "INT", "Store identifier", "Location filtering"],
        ["product_name", "TEXT", "Product name", "Item-level analysis"],
        ["subcategory", "TEXT", "Product subcategory", "Category filtering"],
        ["unit", "TEXT", "Unit of measurement", "Quantity tracking"],
        ["qty_variance", "NUMERIC", "Quantity variance", "Shrinkage analysis"],
        ["dollar_variance", "NUMERIC", "Dollar variance", "Financial impact"],
        ["cogs", "NUMERIC", "Cost of goods sold", "Cost analysis"],
        ["units_sold", "NUMERIC", "Units sold", "Sales volume"],
        ["theoretical_qty", "NUMERIC", "Expected quantity", "Variance calculation"],
        ["theoretical_value", "NUMERIC", "Expected value", "Expected cost"],
        ["beginning_qty", "NUMERIC", "Starting inventory", "Inventory flow"],
        ["purchase_qty", "NUMERIC", "Purchases made", "Inventory additions"],
        ["ending_qty", "NUMERIC", "Ending inventory", "Inventory balance"],
        ["beginning_value", "NUMERIC", "Starting value", "Financial tracking"],
        ["purchase_value", "NUMERIC", "Purchase cost", "Cost tracking"],
        ["waste_qty", "NUMERIC", "Waste quantity", "Waste analysis"],
        ["ending_value", "NUMERIC", "Ending value", "Asset value"],
        ["transfer_in", "NUMERIC", "Transfers in", "Inter-store movement"],
        ["transfer_out", "NUMERIC", "Transfers out", "Inter-store movement"],
    ]
    
    create_table_section(story, variance_data)
    story.append(PageBreak())
    
    # ====== 4. DASHBOARD ANALYSIS FEATURES ======
    story.append(Paragraph("4. Dashboard Analysis Features", heading1_style))
    story.append(Spacer(1, 0.1*inch))
    
    analysis_intro = """
    The Par Delta Dashboard consists of 10 analytical modules, each providing specific operational 
    insights. Below is a comprehensive breakdown of each module, the tables it uses, and the 
    analyses performed.
    """
    story.append(Paragraph(analysis_intro, body_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Feature 1: Donut Waste & Gap
    story.append(Paragraph("4.1 Donut Waste & Gap Analysis", heading2_style))
    
    feature_data = [
        ["Aspect", "Details"],
        ["Tables Used", "• usage_overview\n• donut_sales_hourly"],
        ["Key Columns", "• ordered_qty, wasted_qty, SalesQty\n• date, pc_number, product_type"],
        ["Calculations", "• CalculatedWaste = ordered_qty - SalesQty\n• Gap = CalculatedWaste - wasted_qty\n• DonutCost = wasted_qty × $0.36"],
        ["Visualizations", "• Ordered vs Sales vs Waste trend line chart\n• Daily waste comparison charts\n• Cost impact analysis"],
        ["Business Value", "Identifies discrepancies between reported and calculated waste, helping reduce losses and improve ordering accuracy"],
    ]
    
    create_feature_table(story, feature_data)
    story.append(Spacer(1, 0.2*inch))
    
    # Feature 2: Ideal vs Actual Labor
    story.append(Paragraph("4.2 Ideal vs Actual Labor", heading2_style))
    
    labor_data = [
        ["Aspect", "Details"],
        ["Tables Used", "• hourly_labor_summary\n• actual_table_labor\n• ideal_table_labor\n• schedule_table_labor"],
        ["Key Columns", "• ideal_hours, scheduled_hours, actual_hours\n• actual_labor, sales_value\n• date, hour_range, pc_number"],
        ["Calculations", "• actual_labor_pct_sales = (actual_labor / sales_value) × 100\n• Weekly aggregations\n• Variance: actual vs ideal"],
        ["Visualizations", "• Labor % of Sales line chart\n• Ideal vs Scheduled vs Actual hours comparison\n• Weekly trend analysis"],
        ["Business Value", "Monitors labor efficiency, identifies over/under-staffing, and tracks labor cost as percentage of sales"],
    ]
    
    create_feature_table(story, labor_data)
    story.append(PageBreak())
    
    # Feature 3: Labor Punctuality
    story.append(Paragraph("4.3 Labor Punctuality Report", heading2_style))
    
    punctuality_data = [
        ["Aspect", "Details"],
        ["Tables Used", "• employee_clockins\n• employee_schedules\n• stores"],
        ["Key Columns", "• employee_id, time_in, start_time\n• date, pc_number, employee_name"],
        ["Calculations", "• Late = time_in > (start_time + threshold)\n• Early = time_in < (start_time - threshold)\n• On Time = within threshold\n• Absent = scheduled but no clock-in\n• On Call = clock-in without schedule"],
        ["Visualizations", "• Punctuality status breakdown (pie/bar charts)\n• Employee-level punctuality table\n• Time-based trends"],
        ["Business Value", "Tracks employee attendance reliability, identifies chronic lateness, supports performance management"],
    ]
    
    create_feature_table(story, punctuality_data)
    story.append(Spacer(1, 0.2*inch))
    
    # Feature 4: Inventory Variance
    story.append(Paragraph("4.4 Inventory Variance Analysis", heading2_style))
    
    inventory_data = [
        ["Aspect", "Details"],
        ["Tables Used", "• variance_report_summary"],
        ["Key Columns", "• qty_variance, variance (dollar)\n• theoretical_qty, theoretical_value\n• cogs, units_sold\n• subcategory, product_name"],
        ["Calculations", "• Theoretical Cost Variance = theoretical_value - cogs\n• Unit Gap = theoretical_qty - units_sold\n• Variance percentage calculations"],
        ["Visualizations", "• Top 10 variance by quantity\n• Top 10 variance by dollar value\n• Category-level summaries\n• Period-over-period comparisons"],
        ["Business Value", "Identifies inventory shrinkage, theft, or recording errors; highlights high-variance products for investigation"],
    ]
    
    create_feature_table(story, inventory_data)
    story.append(PageBreak())
    
    # Feature 5: Employee Performance
    story.append(Paragraph("4.5 Employee Performance Overview", heading2_style))
    
    performance_data = [
        ["Aspect", "Details"],
        ["Tables Used", "• employee_profile\n• employee_clockins\n• employee_schedules"],
        ["Key Columns", "• employee_id, employee_name\n• total_wages, total_time\n• status, hired_date, primary_location"],
        ["Calculations", "• Total hours worked\n• Total wages paid\n• Attendance rate\n• Punctuality metrics\n• Employee tenure"],
        ["Visualizations", "• Individual employee performance cards\n• Attendance and punctuality trends\n• Wage and hours comparisons\n• Status breakdowns"],
        ["Business Value", "Comprehensive employee analytics for performance reviews, identifying top performers and problem areas"],
    ]
    
    create_feature_table(story, performance_data)
    story.append(Spacer(1, 0.2*inch))
    
    # Feature 6: Hourly Sales
    story.append(Paragraph("4.6 Hourly Sales & Labor", heading2_style))
    
    hourly_sales_data = [
        ["Aspect", "Details"],
        ["Tables Used", "• hourly_labor_summary"],
        ["Key Columns", "• hour_range, sales_value, check_count\n• actual_hours, actual_labor\n• forecasted_sales, forecasted_checks"],
        ["Calculations", "• Sales per hour\n• Checks per hour\n• Labor cost per hour\n• Forecast vs actual variance\n• Sales per labor hour"],
        ["Visualizations", "• Hourly sales trend charts\n• Labor vs sales correlation\n• Forecast accuracy analysis\n• Peak hour identification"],
        ["Business Value", "Identifies peak sales hours for optimal staffing, validates forecasting models, optimizes labor scheduling"],
    ]
    
    create_feature_table(story, hourly_sales_data)
    story.append(PageBreak())
    
    # Feature 7: Retail Merchandise
    story.append(Paragraph("4.7 Retail Merchandise Analysis", heading2_style))
    
    retail_data = [
        ["Aspect", "Details"],
        ["Tables Used", "• variance_report_summary (filtered)"],
        ["Key Columns", "• Subcategories: Retail Coffee, Mugs & Tumblers, Holiday & Gift Baskets\n• qty_variance, variance, units_sold\n• cogs, purchases_qty, purchases_value"],
        ["Calculations", "• Theoretical Cost Variance\n• Unit Gap\n• Sales performance by category\n• Purchase efficiency"],
        ["Visualizations", "• Top 10 retail variance charts\n• Category performance comparison\n• Purchase vs sales analysis"],
        ["Business Value", "Monitors retail merchandise performance, identifies slow-moving items, optimizes retail inventory levels"],
    ]
    
    create_feature_table(story, retail_data)
    story.append(Spacer(1, 0.2*inch))
    
    # Feature 8: Inventory QA
    story.append(Paragraph("4.8 Inventory Quality Assurance", heading2_style))
    
    qa_text = """
    <b>Purpose:</b> Validates inventory data quality and identifies data inconsistencies.<br/>
    <b>Tables Used:</b> variance_report_summary, usage_overview<br/>
    <b>Checks Performed:</b><br/>
    • Missing or null critical values<br/>
    • Negative quantities where not expected<br/>
    • Unusually high variance percentages<br/>
    • Inconsistent date ranges<br/>
    • Product name standardization issues<br/>
    """
    story.append(Paragraph(qa_text, body_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Feature 9: Chat Interface
    story.append(Paragraph("4.9 AI-Powered Chat Interface", heading2_style))
    
    chat_text = """
    <b>Purpose:</b> Conversational analytics using OpenAI and LangChain.<br/>
    <b>Capabilities:</b><br/>
    • Natural language queries about operational data<br/>
    • Automated insight generation<br/>
    • Data trend explanations<br/>
    • Recommendations based on patterns<br/>
    <b>Integration:</b> Connects to all database tables for comprehensive query responses.<br/>
    """
    story.append(Paragraph(chat_text, body_style))
    story.append(PageBreak())
    
    # ====== 5. DATA INGESTION PIPELINE ======
    story.append(Paragraph("5. Data Ingestion Pipeline", heading1_style))
    story.append(Spacer(1, 0.1*inch))
    
    ingestion_intro = """
    The data ingestion pipeline consists of two main phases: data ingestion/cleaning and 
    database upload. The system processes data from multiple sources including CrunchTime 
    (inventory/variance reports) and labour management systems.
    """
    story.append(Paragraph(ingestion_intro, body_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Ingestion Scripts
    story.append(Paragraph("5.1 Data Ingestion Scripts", heading2_style))
    
    ingestion_data = [
        ["Script", "Source Data", "Output", "Tables Populated"],
        ["combined_labour.py", "Schedule TXT files\nConsolidated time CSV", "Clean employee\nschedules & clockins", "employee_schedules\nemployee_clockins"],
        ["variance_report.py", "CrunchTime variance\nreport Excel", "Formatted variance\ndata", "variance_report_summary"],
        ["combine_hourly_labour.py", "Hourly labor CSV\nHourly sales data", "Merged hourly\nmetrics", "hourly_labor_summary"],
        ["clean_consolidated_employee.py", "Employee CSV", "Clean employee\nprofiles", "employee_profile"],
        ["download_hourly_labour_attachments.py", "Email attachments", "Raw hourly\nlabour files", "Raw data folder"],
    ]
    
    pipeline_table = Table(ingestion_data, colWidths=[1.8*inch, 1.5*inch, 1.3*inch, 1.4*inch])
    pipeline_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(pipeline_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Upload Scripts
    story.append(Paragraph("5.2 Database Upload Scripts", heading2_style))
    
    upload_data = [
        ["Script", "Target Table", "Upload Method", "Key Features"],
        ["upload_employee_clockin.py", "employee_clockins", "UPSERT", "Incremental updates\nDuplicate prevention"],
        ["upload_employee_profile.py", "employee_profile", "UPSERT", "Batch processing\nProfile updates"],
        ["upload_employee_schedule.py", "employee_schedules", "UPSERT", "Schedule sync\nConflict resolution"],
        ["upload_hourly_labour.py", "hourly_labor_summary", "UPSERT/INSERT", "Hourly aggregation\nConflict handling"],
        ["upload_variance.py", "variance_report_summary", "UPSERT", "Weekly variance\nPeriod tracking"],
        ["upload_labour.py", "Multiple labor tables", "UPSERT", "Comprehensive labor\ndata sync"],
    ]
    
    upload_table = Table(upload_data, colWidths=[1.8*inch, 1.5*inch, 1.2*inch, 1.5*inch])
    upload_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(upload_table)
    story.append(PageBreak())
    
    # ====== 6. TECHNICAL ARCHITECTURE ======
    story.append(Paragraph("6. Technical Architecture", heading1_style))
    story.append(Spacer(1, 0.1*inch))
    
    arch_text = """
    The Par Delta Dashboard follows a three-tier architecture with clear separation of concerns:
    """
    story.append(Paragraph(arch_text, body_style))
    story.append(Spacer(1, 0.2*inch))
    
    story.append(Paragraph("6.1 Architecture Layers", heading2_style))
    
    arch_data = [
        ["Layer", "Components", "Responsibilities"],
        ["Presentation Layer", "• Streamlit web interface\n• Page modules\n• Interactive visualizations", "• User interaction\n• Data visualization\n• Filtering and navigation"],
        ["Business Logic Layer", "• Data processing functions\n• Analysis calculations\n• Aggregation logic", "• Metrics calculation\n• Data transformation\n• Business rule enforcement"],
        ["Data Layer", "• Supabase PostgreSQL\n• Table schemas\n• Foreign key relationships", "• Data persistence\n• Query optimization\n• Data integrity"],
        ["Integration Layer", "• Ingestion scripts\n• Upload utilities\n• API connections", "• Data extraction\n• Data cleaning\n• ETL processes"],
    ]
    
    arch_table = Table(arch_data, colWidths=[1.5*inch, 2.5*inch, 2*inch])
    arch_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(arch_table)
    story.append(Spacer(1, 0.2*inch))
    
    # Data Flow
    story.append(Paragraph("6.2 Data Flow", heading2_style))
    
    flow_text = """
    <b>1. Data Collection:</b><br/>
    • CrunchTime exports (variance reports, inventory data)<br/>
    • Labour system exports (schedules, clock-ins, employee profiles)<br/>
    • Email attachments (hourly labour reports)<br/>
    <br/>
    <b>2. Data Processing:</b><br/>
    • Scripts clean and standardize data formats<br/>
    • Validation checks ensure data quality<br/>
    • Transformations prepare data for database schema<br/>
    <br/>
    <b>3. Database Upload:</b><br/>
    • UPSERT operations prevent duplicates<br/>
    • Batch processing for efficiency<br/>
    • Error handling and logging<br/>
    <br/>
    <b>4. Dashboard Consumption:</b><br/>
    • Streamlit pages query Supabase<br/>
    • Data cached for performance (TTL: 1 hour)<br/>
    • Real-time filtering and aggregation<br/>
    • Interactive visualizations rendered<br/>
    """
    story.append(Paragraph(flow_text, body_style))
    story.append(PageBreak())
    
    # Key Metrics Summary
    story.append(Paragraph("6.3 Key Performance Metrics Tracked", heading2_style))
    
    metrics_data = [
        ["Category", "Metrics", "Tables Used"],
        ["Labor Efficiency", "• Labor % of Sales\n• Ideal vs Actual hours\n• Scheduled adherence", "hourly_labor_summary\nemployee_clockins\nemployee_schedules"],
        ["Inventory Management", "• Waste quantity & cost\n• Variance (qty & $)\n• Theoretical vs actual", "usage_overview\nvariance_report_summary"],
        ["Employee Performance", "• Punctuality rate\n• Attendance rate\n• Total hours worked", "employee_clockins\nemployee_schedules\nemployee_profile"],
        ["Sales Analytics", "• Hourly sales value\n• Check count\n• Forecast accuracy", "donut_sales_hourly\nhourly_labor_summary"],
    ]
    
    metrics_table = Table(metrics_data, colWidths=[1.5*inch, 2.8*inch, 1.7*inch])
    metrics_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(metrics_table)
    story.append(Spacer(1, 0.3*inch))
    
    # Conclusion
    story.append(Paragraph("Summary", heading2_style))
    conclusion_text = """
    The Par Delta Dashboard provides comprehensive operational analytics across 9 database tables 
    containing labor, inventory, sales, and employee data. The system processes data from multiple 
    sources, maintains data quality through validation pipelines, and presents actionable insights 
    through 10+ interactive dashboard modules. This architecture enables data-driven decision-making 
    for store operations, labor optimization, inventory management, and employee performance tracking.
    """
    story.append(Paragraph(conclusion_text, body_style))
    story.append(Spacer(1, 0.2*inch))
    
    # Footer
    footer_text = f"""
    <i>Document generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</i><br/>
    <i>Par Delta Dashboard - Technical Documentation v1.0</i>
    """
    story.append(Paragraph(footer_text, body_style))
    
    # Build PDF
    doc.build(story)
    print(f"\n✅ PDF generated successfully: {filename}")
    return filename


def create_table_section(story, data):
    """Helper function to create consistent table sections"""
    table = Table(data, colWidths=[1.5*inch, 1.2*inch, 2*inch, 1.3*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(table)


def create_feature_table(story, data):
    """Helper function to create feature detail tables"""
    table = Table(data, colWidths=[1.5*inch, 4.5*inch])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_BG),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.white),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, TABLE_ALT_ROW]),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(table)


if __name__ == "__main__":
    print("🚀 Generating Par Delta Dashboard Documentation PDF...")
    print("=" * 60)
    filename = create_pdf()
    print("=" * 60)
    print(f"📄 PDF saved as: {filename}")
    print("✨ Documentation complete!")
