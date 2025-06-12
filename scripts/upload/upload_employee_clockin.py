import pandas as pd
from supabase_client import supabase

def clean_df(df):
    df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
    df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["employee_id"] = df["employee_id"].astype(str)
    df = df.astype(object).where(pd.notnull(df), None)
    return df

def upsert_to_supabase(df, table_name):
    records = df.to_dict(orient="records")
    records = [r for r in records if any(r.values())]
    print(f"✅ Upserting {len(records)} records to {table_name}")
    for i, record in enumerate(records):
        try:
            supabase.table(table_name).upsert(record).execute()
        except Exception as e:
            print(f"❌ Error on record {i+1}: {e}")
            print("⛔ Record:", record)

def main():
    file_path = "/Users/samarpatel/Desktop/samar/Dunkin/par-delta-dashboard/data/processed/employee_clockin.xlsx"
    df = pd.read_excel(file_path)
    df = clean_df(df)
    upsert_to_supabase(df, "employee_clockin")

if __name__ == "__main__":
    main()
