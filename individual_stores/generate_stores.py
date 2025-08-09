"""
Generate Individual Store Dashboards for Deployment
This script creates separate folders for each store with customized dashboard files
"""

import os
import shutil
from pathlib import Path
from store_config import STORE_CONFIG

def create_individual_store_dashboards():
    """Create individual dashboard folders for each store"""
    
    # Get the base directory
    base_dir = Path(__file__).parent
    template_dir = base_dir / "template"
    
    print("🏗️  Creating individual store dashboards...")
    
    for pc_number, config in STORE_CONFIG.items():
        store_name = config['name']
        store_dir = base_dir / f"store_{pc_number}_{store_name.lower()}"
        
        print(f"\n📁 Creating dashboard for {store_name} (PC: {pc_number})")
        
        # Create store directory
        store_dir.mkdir(exist_ok=True)
        
        # Copy template files
        shutil.copy2(template_dir / "requirements.txt", store_dir / "requirements.txt")
        
        # Read template dashboard and customize for this store
        with open(template_dir / "store_dashboard.py", 'r') as f:
            template_content = f.read()
        
        # Replace the store PC number in the template
        customized_content = template_content.replace(
            'STORE_PC_NUMBER = "357993"  # CHANGE THIS FOR EACH STORE',
            f'STORE_PC_NUMBER = "{pc_number}"  # {store_name} Store'
        )
        
        # Write the customized dashboard
        with open(store_dir / "streamlit_app.py", 'w') as f:
            f.write(customized_content)
        
        # Copy store config file
        shutil.copy2(base_dir / "store_config.py", store_dir / "store_config.py")
        
        # Create .streamlit directory and secrets template
        streamlit_dir = store_dir / ".streamlit"
        streamlit_dir.mkdir(exist_ok=True)
        
        # Create secrets template
        secrets_content = f"""# Streamlit Secrets for {store_name} Store
# Copy these to your Streamlit Cloud deployment

SUPABASE_URL = "your-supabase-url-here"
SUPABASE_KEY = "your-supabase-anon-key-here"

# Optional: Add any store-specific configurations
STORE_PC_NUMBER = "{pc_number}"
STORE_NAME = "{store_name}"
"""
        
        with open(streamlit_dir / "secrets.toml.template", 'w') as f:
            f.write(secrets_content)
        
        # Create README for this store
        readme_content = f"""# {store_name} Store Dashboard (PC: {pc_number})

This is the individual dashboard for the {store_name} Dunkin' location.

## Deployment Instructions

### 1. Deploy to Streamlit Cloud
1. Create a new repository for this store: `par-delta-{pc_number}-{store_name.lower()}`
2. Upload all files from this directory to the repository
3. Connect to Streamlit Cloud: https://share.streamlit.io/
4. Use subdomain: `{pc_number}` (will create: https://{pc_number}.streamlit.app)

### 2. Configure Secrets
In Streamlit Cloud, add these secrets:
```toml
SUPABASE_URL = "your-supabase-url"
SUPABASE_KEY = "your-supabase-anon-key"
```

### 3. Set Custom Domain (Optional)
- In Streamlit Cloud settings, you can set custom subdomain to {pc_number}
- This will make your dashboard accessible at: https://{pc_number}.streamlit.app

## Store Information
- **Store Name**: {store_name}
- **PC Number**: {pc_number}
- **Address**: {config['address']}
- **Target URL**: {config['full_url']}

## Features Included
- ✅ Daily sales tracking
- ✅ Donut waste analysis  
- ✅ Labor efficiency metrics
- ✅ Employee punctuality
- ✅ Inventory variance
- ✅ Interactive charts and graphs
- ✅ Real-time data from Supabase

## Data Sources
All data is filtered specifically for PC number {pc_number} from these tables:
- `donut_sales_hourly`
- `usage_overview` 
- `actual_table_labor`
- `schedule_table_labor`
- `ideal_table_labor`
- `employee_clockin`
- `employee_schedule`
- `employee_profile`
- `variance_report_summary`

## Support
For technical support, contact the Par Delta IT team.
"""
        
        with open(store_dir / "README.md", 'w') as f:
            f.write(readme_content)
        
        print(f"   ✅ Created files for {store_name}")
        print(f"   📂 Location: {store_dir}")
        print(f"   🌐 Target URL: {config['full_url']}")
    
    print(f"\n🎉 Successfully created {len(STORE_CONFIG)} individual store dashboards!")
    print(f"\n📋 Next Steps:")
    print("1. Review each store directory")
    print("2. Create separate GitHub repositories for each store")
    print("3. Deploy each to Streamlit Cloud with custom subdomains")
    print("4. Configure secrets for each deployment")

if __name__ == "__main__":
    create_individual_store_dashboards()
