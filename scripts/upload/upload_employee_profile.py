import pandas as pd
import os
from pathlib import Path
from supabase_client import supabase

def clean_employee_data(df):
    """Clean and prepare employee data for database upload"""
    # Remove the header rows and empty rows
    df = df.dropna(how='all')
    
    # Find the actual header row (contains "Employee #")
    header_row = None
    for idx, row in df.iterrows():
        if 'Employee #' in str(row.iloc[0]):
            header_row = idx
            break
    
    if header_row is None:
        raise ValueError("Could not find header row with 'Employee #'")
    
    # Set the correct header and remove extra rows
    df.columns = df.iloc[header_row]
    df = df.iloc[header_row + 1:].reset_index(drop=True)
    
    # Remove rows that contain summary information or are empty
    df = df[~df['Employee #'].str.contains('Filtered By:', na=True)]
    df = df.dropna(subset=['Employee #'])
    
    # Clean column names and map to database schema
    df_clean = pd.DataFrame()
    df_clean['employee_number'] = df['Employee #'].astype(str).str.strip()
    df_clean['first_name'] = df['First Name'].str.strip()
    df_clean['last_name'] = df['Last Name'].str.strip()
    df_clean['primary_position'] = df['Primary Position'].str.strip()
    df_clean['primary_location'] = df['Primary Location'].str.strip()
    
    # Convert hired date to proper format
    df_clean['hired_date'] = pd.to_datetime(df['Hired Date'], errors='coerce').dt.strftime('%Y-%m-%d')
    
    # Clean status field
    df_clean['status'] = df['Status'].str.strip().str.lower()
    
    # Remove any rows with missing employee numbers
    df_clean = df_clean.dropna(subset=['employee_number'])
    
    # Replace NaN values with None for proper database handling
    df_clean = df_clean.where(pd.notnull(df_clean), None)
    
    return df_clean

def batch_upsert(df, table_name, batch_size=100):
    """Upload data to Supabase in batches"""
    records = df.to_dict(orient="records")
    total = len(records)
    print(f"\n📦 Uploading {total} employee records to '{table_name}' in batches of {batch_size}...")

    successful_uploads = 0
    for i in range(0, total, batch_size):
        batch = records[i:i + batch_size]
        try:
            supabase.table(table_name).upsert(batch).execute()
            successful_uploads += len(batch)
            print(f"✅ Uploaded records {i+1} to {i+len(batch)}")
        except Exception as e:
            print(f"❌ Error uploading records {i+1} to {i+len(batch)}: {e}")
            # Try individual uploads for this batch to identify problematic records
            for j, record in enumerate(batch):
                try:
                    supabase.table(table_name).upsert(record).execute()
                    successful_uploads += 1
                except Exception as individual_error:
                    print(f"⛔ Failed to upload record {i+j+1}: {individual_error}")
                    print(f"   Record: {record}")
    
    print(f"\n🎉 Successfully uploaded {successful_uploads}/{total} employee records")

def upload_employee_profile(file_path):
    """Main function to process and upload employee profile data"""
    print(f"📁 Reading employee data from: {file_path}")
    
    # Read CSV file
    df = pd.read_csv(file_path)
    
    # Clean and prepare data
    df_clean = clean_employee_data(df)
    
    print(f"📊 Processed {len(df_clean)} employee records")
    print("📋 Sample of cleaned data:")
    print(df_clean.head())
    
    # Upload to database
    batch_upsert(df_clean, "employee_profile")

if __name__ == "__main__":
    # Get the project root directory (2 levels up from current script location)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    # File location
    file_path = project_root / "data" / "raw" / "labour" / "consolidated_employee.csv"
    
    if not file_path.exists():
        print("❌ Could not find consolidated_employee.csv file")
        print(f"📍 Expected location: {file_path}")
        print("\n💡 Please ensure the file is saved in data/raw/labour/consolidated_employee.csv")
    else:
        upload_employee_profile(file_path)
