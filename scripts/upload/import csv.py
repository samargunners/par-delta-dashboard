import csv
import json
from collections import defaultdict
import matplotlib.pyplot as plt
import requests

#-- Stage 1: Data Acquisition

def fetch_data(api_url):
    """Fetches raw data from an external API."""
    print("Fetching data from API...")
    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        print("Data fetched successfully.")
        return data
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return None

#-- Stage 2: Data Cleaning and Transformation ---

def clean_data(raw_data):
    """Cleans and transforms raw data."""
    print("Cleaning data...")
    cleaned_records = []
    for record in raw_data:
        if 'value' in record and isinstance(record['value'], (int, float)):
            cleaned_records.append({
                'id': record.get('id', None),
                'value': record['value']
            })

    print(f"Cleaned {len(cleaned_records)} records.")
    return cleaned_records

class DataTransformer:
    """Transforms cleaned data into a structured format."""
    
    def __init__(self, cleaned_data):
        self.cleaned_data = cleaned_data

    def transform(self):
        print("Transforming data...")
        transformed_data = defaultdict(list)
        for record in self.cleaned_data:
            transformed_data['ids'].append(record['id'])
            transformed_data['values'].append(record['value'])
        
        print("Data transformation complete.")
        return transformed_data
    
#-- Stage 3: Data Visualization ---
def visualize_data(transformed_data):
    """Visualizes the transformed data using a bar chart."""
    print("Visualizing data...")
    plt.bar(transformed_data['ids'], transformed_data['values'])
    plt.xlabel('ID')
    plt.ylabel('Value')
    plt.title('Data Visualization')
    plt.show()
    print("Data visualization complete.")

#-- Main Execution Flow ---

def main():
    api_url = "https://api.example.com/data"  # Replace with a valid API endpoint
    raw_data = fetch_data(api_url)
    
    if raw_data:
        cleaned_data = clean_data(raw_data)
        transformer = DataTransformer(cleaned_data)
        transformed_data = transformer.transform()
        visualize_data(transformed_data)

if __name__ == "__main__":
    main()