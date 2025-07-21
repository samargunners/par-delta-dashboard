import pandas as pd
from pathlib import Path

def clean_consolidated_employee_csv(input_path, output_path):
    """
    Clean the consolidated employee CSV file by:
    1. Removing the first row (header with timestamp)
    2. Keeping only specific columns: Employee #, Last Name, First Name, Primary Position, Hired Date, Status
    3. Removing the last row that contains filter information
    """
    print(f"📁 Reading CSV file from: {input_path}")
    
    # Read the CSV file
    df = pd.read_csv(input_path)
    
    print(f"📊 Original data shape: {df.shape}")
    print("🔍 Original columns:", df.columns.tolist())
    
    # Remove the first row (index 0 - contains timestamp header)
    df = df.drop(index=0).reset_index(drop=True)
    print(f"✂️ Removed first row. New shape: {df.shape}")
    
    # Define the columns we want to keep
    # Based on the CSV structure: Employee #, Last Name, First Name, [empty], Middle Name, Primary Position, Primary Location, Hired Date, [empty], Last Edit Date, Status
    columns_to_keep = []
    column_mapping = {}
    
    if len(df.columns) > 0:
        columns_to_keep.append(df.columns[0])  # Employee #
        column_mapping[df.columns[0]] = 'Employee #'
    if len(df.columns) > 1:
        columns_to_keep.append(df.columns[1])  # Last Name  
        column_mapping[df.columns[1]] = 'Last Name'
    if len(df.columns) > 2:
        columns_to_keep.append(df.columns[2])  # First Name
        column_mapping[df.columns[2]] = 'First Name'
    if len(df.columns) > 5:
        columns_to_keep.append(df.columns[5])  # Primary Position
        column_mapping[df.columns[5]] = 'Primary Position'
    if len(df.columns) > 7:
        columns_to_keep.append(df.columns[7])  # Hired Date
        column_mapping[df.columns[7]] = 'Hired Date'
    if len(df.columns) > 10:
        columns_to_keep.append(df.columns[10])  # Status
        column_mapping[df.columns[10]] = 'Status'
    
    print(f"� Keeping columns: {columns_to_keep}")
    
    # Keep only the desired columns
    df = df[columns_to_keep]
    
    # Rename columns for clarity
    df = df.rename(columns=column_mapping)
    
    # Remove rows that contain filter information (last row)
    # Look for rows containing "Filtered By:" in any column
    filter_mask = df.astype(str).apply(lambda x: x.str.contains('Filtered By:', na=False)).any(axis=1)
    rows_to_remove = df[filter_mask].index.tolist()
    
    if rows_to_remove:
        print(f"🗑️ Removing filter rows at indices: {rows_to_remove}")
        df = df.drop(index=rows_to_remove).reset_index(drop=True)
    
    # Remove any completely empty rows
    df = df.dropna(how='all').reset_index(drop=True)
    
    print(f"✅ Final cleaned data shape: {df.shape}")
    print("📋 Final columns:", df.columns.tolist())
    
    # Save the cleaned file
    print(f"💾 Saving cleaned data to: {output_path}")
    
    # Create output directory if it doesn't exist
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    
    print(f"🎉 Successfully saved cleaned data!")
    print(f"📊 Final record count: {len(df)} rows")
    
    # Show a sample of the cleaned data
    print("\n📋 Sample of cleaned data:")
    print(df.head())
    
    return df

if __name__ == "__main__":
    # Get the project root directory (2 levels up from current script location)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent.parent
    
    # Define input and output paths
    input_path = project_root / "data" / "raw" / "labour" / "consolidated_employee.csv"
    output_path = project_root / "data" / "processed" / "clean_consolidated_employee.csv"
    
    # Check if input file exists
    if not input_path.exists():
        print("❌ Could not find consolidated_employee.csv file")
        print(f"📍 Expected location: {input_path}")
        print("\n💡 Please ensure the file is saved in data/raw/labour/consolidated_employee.csv")
    else:
        # Clean the file
        clean_consolidated_employee_csv(input_path, output_path)
