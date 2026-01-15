from scripts.upload.supabase_client import supabase
import pandas as pd
from datetime import datetime

print("Fetching NDCP invoices data...")
all_data = []
offset = 0
chunk = 1000

while True:
    response = supabase.table('ndcp_invoices').select('*').range(offset, offset + chunk - 1).execute()
    if not response.data:
        break
    all_data.extend(response.data)
    offset += chunk
    print(f"Loaded {len(all_data)} records...")

df = pd.DataFrame(all_data)
print(f"\nTotal records: {len(df)}")

# Convert dates
df['invoice_date'] = pd.to_datetime(df['Invoice Date'], unit='s', errors='coerce')
df['order_date'] = pd.to_datetime(df['Order Date'], unit='s', errors='coerce')

print(f"\nInvoice Date range: {df['invoice_date'].min()} to {df['invoice_date'].max()}")
print(f"Order Date range: {df['order_date'].min()} to {df['order_date'].max()}")

unique_dates = sorted(df['invoice_date'].dt.date.dropna().unique())
print(f"\nUnique invoice dates ({len(unique_dates)} total):")
for date in unique_dates[:20]:
    print(f"  {date}")
if len(unique_dates) > 20:
    print(f"  ... and {len(unique_dates) - 20} more dates")

print(f"\nStores: {sorted(df['PC Number'].unique())}")
print(f"\nCategories: {sorted(df['Category Desc'].dropna().unique())}")
print(f"\nDivisions: {sorted(df['Division Desc'].dropna().unique())}")
