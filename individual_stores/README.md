# Par Delta Individual Store Dashboards

This directory contains the setup for creating individual store-specific dashboards that can be deployed to separate Streamlit hosting environments.

## 🏪 Available Stores

| PC Number | Store Name | Target URL | Address |
|-----------|------------|------------|---------|
| 357993 | Enola | https://357993.streamlit.app | 423 N Enola Rd |
| 301290 | Paxton | https://301290.streamlit.app | TBD |
| 343939 | Mount Joy | https://343939.streamlit.app | 807 E Main St |
| 358529 | Columbia | https://358529.streamlit.app | 3929 Columbia Avenue |
| 359042 | Lititz | https://359042.streamlit.app | TBD |
| 363271 | Marietta | https://363271.streamlit.app | TBD |
| 364322 | Elizabethtown | https://364322.streamlit.app | TBD |

## 🚀 Quick Start

### Step 1: Generate Store Dashboards
```bash
cd individual_stores
python generate_stores.py
```

This will create separate directories for each store with customized dashboard files.

### Step 2: Create GitHub Repositories
For each store, create a new GitHub repository:
- Repository name: `par-delta-{PC_NUMBER}-{STORE_NAME}`
- Example: `par-delta-357993-enola`

### Step 3: Deploy to Streamlit Cloud

1. **Go to [Streamlit Cloud](https://share.streamlit.io/)**
2. **Connect your GitHub repository**
3. **Set custom subdomain to the PC number** (e.g., `357993`)
4. **Configure secrets** (see below)
5. **Deploy**

### Step 4: Configure Secrets

In each Streamlit Cloud deployment, add these secrets:

```toml
SUPABASE_URL = "your-supabase-url-here"
SUPABASE_KEY = "your-supabase-anon-key-here"
```

## 📊 Dashboard Features

Each individual store dashboard includes:

### Key Metrics
- 🍩 **Today's Donut Sales** - Real-time sales with day-over-day comparison
- 📉 **Waste Rate** - Average waste percentage with color-coded alerts
- 💼 **Labor Efficiency** - Actual vs ideal hours performance
- ⏰ **Punctuality Rate** - Employee attendance compliance
- 👥 **Active Staff Count** - Current workforce status

### Interactive Charts
- 📈 **Daily Sales Trend** - 7-day sales volume tracking
- 🗑️ **Waste Analysis** - Daily waste rate visualization
- 💼 **Labor Hours Comparison** - Scheduled vs actual hours
- 📅 **Schedule Compliance** - Attendance tracking

### Data Analysis
- 📦 **Inventory Variance** - Recent inventory discrepancies
- 📋 **Raw Data Tables** - Detailed data exploration
- 🕐 **Real-time Updates** - 30-minute data refresh

## 🏗️ Technical Architecture

### Data Flow
```
Supabase Database → Store-Specific Filtering → Individual Dashboard → Streamlit Cloud
```

### Filtering Logic
Each dashboard automatically filters all data by the store's PC number, ensuring complete data isolation between stores.

### Caching Strategy
- Data cached for 30 minutes to balance freshness and performance
- Separate cache for each store deployment

## 📁 Directory Structure

```
individual_stores/
├── store_config.py           # Master store configuration
├── generate_stores.py        # Dashboard generation script
├── template/                 # Template files
│   ├── store_dashboard.py    # Main dashboard template
│   └── requirements.txt      # Python dependencies
├── store_357993_enola/       # Generated store directories
│   ├── streamlit_app.py      # Customized dashboard
│   ├── store_config.py       # Store configuration
│   ├── requirements.txt      # Dependencies
│   ├── .streamlit/
│   │   └── secrets.toml.template
│   └── README.md             # Store-specific instructions
└── ... (other stores)
```

## 🔒 Security Considerations

### Data Isolation
- Each dashboard only accesses data for its specific PC number
- No cross-store data exposure
- Supabase Row Level Security can be implemented for additional protection

### Access Control
- Each deployment uses the same Supabase credentials but filters data
- Consider implementing store-specific API keys if needed

## 🚀 Deployment Workflow

### Automated Deployment (Recommended)
1. Run `python generate_stores.py` to create all store directories
2. Create GitHub repositories for each store
3. Set up GitHub Actions for automated deployment (optional)
4. Deploy to Streamlit Cloud with custom subdomains

### Manual Deployment
1. Generate individual store directories
2. Manually create and configure each Streamlit Cloud deployment
3. Set custom subdomains and secrets

## 🔧 Customization Options

### Per-Store Customization
Modify `store_config.py` to add store-specific:
- Branding colors
- Contact information
- Special metrics
- Custom alerts

### Dashboard Modifications
Edit `template/store_dashboard.py` to:
- Add new metrics
- Modify chart types
- Change layout
- Add store-specific features

## 📈 Monitoring & Analytics

### Performance Tracking
- Each store dashboard tracks its own usage
- Monitor load times and user engagement
- Set up alerts for data issues

### Data Quality
- Automated data validation
- Missing data alerts
- Error reporting

## 🆘 Troubleshooting

### Common Issues
1. **No Data Showing**: Check PC number configuration and Supabase connectivity
2. **Secrets Not Working**: Verify Supabase URL and key in Streamlit Cloud secrets
3. **Deployment Errors**: Check requirements.txt and Python version compatibility
4. **Custom Subdomain Issues**: Ensure PC number is available as subdomain

### Support Contacts
- **Technical Issues**: Contact Par Delta IT team
- **Data Issues**: Contact operations team
- **Streamlit Cloud Issues**: Check Streamlit documentation

## 🔄 Updates & Maintenance

### Template Updates
1. Modify `template/store_dashboard.py`
2. Run `generate_stores.py` to regenerate all stores
3. Deploy updates to each Streamlit Cloud instance

### Data Schema Changes
Update the dashboard template if database schema changes occur.

---

**Created for Par Delta Dunkin' Operations**  
*Individual store dashboards for enhanced operational visibility*
