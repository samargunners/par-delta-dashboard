# Individual Store Dashboard Deployment Guide

## Current Situation
- You have 1 main repository with all stores: `par-delta-dashboard`
- You want 7 separate URLs: `357993.streamlit.app`, `301290.streamlit.app`, etc.

## Deployment Options

### Option 1: Separate GitHub Repositories (Recommended)
Create individual repositories for each store:

#### Step 1: Create Individual Repositories
```bash
# For each store, create a new repository:
# par-delta-357993-enola
# par-delta-301290-paxton
# par-delta-343939-mountjoy
# par-delta-358529-columbia
# par-delta-359042-lititz
# par-delta-363271-marietta
# par-delta-364322-elizabethtown
```

#### Step 2: Copy Store-Specific Files
Each repository should contain:
```
store-357993/
├── streamlit_app.py           # Main dashboard file
├── requirements.txt           # Dependencies
├── .streamlit/
│   └── config.toml           # Streamlit config
└── README.md                 # Store info
```

#### Step 3: Deploy to Streamlit Cloud
1. Go to https://share.streamlit.io/
2. Connect each GitHub repository
3. Deploy each as separate app
4. Get URLs like: `https://your-app-name.streamlit.app/`

### Option 2: Custom Domains (Advanced)
If you want exact URLs like `357993.streamlit.com`:
1. Buy custom domains
2. Set up CNAME records pointing to Streamlit
3. Configure custom domain in Streamlit Cloud

### Option 3: Single Repository with Branches
Use the same repo but different branches:
- `store-357993` branch → deploys to one app
- `store-301290` branch → deploys to another app

## Automated Deployment Script

I can create a script that:
1. Creates separate GitHub repositories
2. Pushes store-specific code to each
3. Sets up Streamlit deployments via API

Would you like me to:
A) Create the automated deployment script?
B) Set up the individual store files first?
C) Show you manual deployment steps?

## Current Status
✅ Store mapping identified (7 stores)
⏳ Individual dashboard files need to be created
⏳ Repositories need to be created
⏳ Streamlit deployments need to be set up

## Next Steps
Choose your preferred approach:
1. **Manual**: Create repos manually, copy files, deploy each
2. **Semi-Automated**: Use script to generate files, manual deployment  
3. **Fully Automated**: Script handles repos, files, and deployment
