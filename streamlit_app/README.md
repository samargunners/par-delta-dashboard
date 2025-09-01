# Par Delta Operational Dashboard

A modern Streamlit-based dashboard for Dunkin' operations at Par Delta, providing real-time analytics, labor management, inventory tracking, and more. Built for data-driven decision-making and operational excellence.

## Features

- **Modular Dashboard:**  
  Navigate through Donut Waste & Gap, Labor Punctuality, Ideal vs Actual Labor, Inventory Variance, Retail Merchandise, and more.
- **Live Data Integration:**  
  Connects to Supabase for real-time data updates.
- **Interactive Visualizations:**  
  Uses Plotly, Matplotlib, and Streamlit for rich, interactive charts.
- **Chat & AI Modules:**  
  Integrates OpenAI and LangChain for advanced analytics and conversational interfaces.
- **Extensible Architecture:**  
  Easily add new pages and data sources.

## Directory Structure

```
streamlit_app/
  ├── streamlit_app.py         # Main dashboard entry point
  ├── requirements.txt         # Python dependencies
  ├── TROUBLESHOOTING.md       # Common issues and solutions
  ├── pages/                   # Individual dashboard modules
  │     ├── Donut_Waste_&_Gap.py
  │     ├── Labor_Punctuality.py
  │     ├── Ideal_vs_Actual_Labor.py
  │     ├── Inventory_Variance.py
  │     ├── Retail_Merchandise.py
  │     └── ... (other modules)
  ├── scripts/                 # Utility scripts (e.g., test_connection.py)
  └── supabase/                # Database migrations and config
```

## Setup & Installation

1. **Clone the Repository**
   ```bash
   git clone https://github.com/samargunners/par-delta-dashboard.git
   cd par-delta-dashboard/streamlit_app
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Secrets**
   Create `.streamlit/secrets.toml`:
   ```toml
   SUPABASE_URL = "your-supabase-url"
   SUPABASE_KEY = "your-supabase-key"
   OPENAI_API_KEY = "your-openai-api-key"  # Optional
   ```

4. **Run the App**
   ```bash
   streamlit run streamlit_app.py
   ```

## Usage

- Select a module from the sidebar to view analytics.
- Data is loaded live from Supabase.
- Use chat modules for AI-powered insights.

## Troubleshooting

See [`TROUBLESHOOTING.md`](TROUBLESHOOTING.md) for common issues, health checks, and debugging steps.

## Technologies Used

- Python, Streamlit, Pandas, Plotly, Matplotlib
- Supabase (Postgres backend)
- OpenAI, LangChain (AI modules)
- SQLAlchemy, psycopg2

## Contributing

- Fork the repo and submit pull requests.
- Add new dashboard modules in `pages/`.
- Ensure code is PEP8-compliant and well-documented.

## License

[MIT License](LICENSE) (add your license file if missing)

## Screenshots

*(Add screenshots or demo GIFs here to showcase the dashboard UI and features.)*
