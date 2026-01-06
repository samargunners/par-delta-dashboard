# HME Daily Task Automation - Fix for Dec 31 Issue

## Problem Identified

The HME automation stopped working after December 31, 2024. The issue was:

1. **Hardcoded date in download script**: The `SINCE_DATE` was hardcoded to `"28-Jul-2025"` which would stop working after that date
2. **Missing SCRIPT_PATH definition**: The download script referenced `SCRIPT_PATH` without defining it
3. **No HME-specific download script**: There was no dedicated script for downloading HME emails

## Solution

### Files Created/Updated

1. **`scripts/ingest/download_hme_attachments.py`** (NEW)
   - Dedicated script for downloading HME reports from Gmail
   - Uses dynamic date calculation (defaults to 30 days back)
   - Configurable via environment variables

2. **`scripts/automation/hme_daily_task.py`** (NEW)
   - Complete automation pipeline:
     - Downloads HME from Gmail
     - Transforms HME Excel files
     - Uploads to Supabase `hme_report` table
   - Includes logging and error handling

3. **`scripts/ingest/download_hourly_labour_attachments.py`** (FIXED)
   - Fixed `SCRIPT_PATH` undefined error
   - Changed hardcoded date to dynamic (30 days back)
   - Prevents future date-related failures

## Configuration

### Environment Variables (.env file)

Add these to your `.env` file:

```bash
# Gmail IMAP Settings (required)
IMAP_USER=your-email@gmail.com
IMAP_PASS=your-app-password

# HME-specific settings (optional)
HME_IMAP_SENDER=                  # Email sender (leave empty to search all)
HME_IMAP_SUBJECT_KEY=HME          # Subject keyword to search for
HME_IMAP_SINCE=                   # Override date (DD-MMM-YYYY format, e.g., "01-Jan-2025")
HME_IMAP_DAYS_BACK=30             # Days to look back (default: 30)
HME_IMAP_DEBUG_LIST=1             # Show debug info (1=yes, 0=no)
```

### Supabase Credentials

Make sure these are in your `.env`:
```bash
SUPABASE_URL=https://ertcdieopoecjddamgkx.supabase.co
SUPABASE_KEY=your-key-here
```

## Usage

### Manual Run

Run the complete pipeline:
```bash
python scripts/automation/hme_daily_task.py
```

Or run individual steps:
```bash
# Step 1: Download HME from Gmail
python scripts/ingest/download_hme_attachments.py

# Step 2: Transform HME files (manual or via automation script)
python scripts/ingest/hme_transform.py path/to/hme_file.xlsx

# Step 3: Upload to Supabase (via automation script)
```

### Automated Scheduling

#### Windows Task Scheduler
1. Open Task Scheduler
2. Create Basic Task
3. Set trigger: Daily at desired time
4. Action: Start a program
5. Program: `python`
6. Arguments: `C:\Projects\par-delta-dashboard\scripts\automation\hme_daily_task.py`
7. Start in: `C:\Projects\par-delta-dashboard`

#### Linux/Mac Cron
```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 2 AM)
0 2 * * * cd /path/to/par-delta-dashboard && /usr/bin/python3 scripts/automation/hme_daily_task.py >> logs/hme_cron.log 2>&1
```

## What Changed

### Before (Broken)
- Hardcoded date: `"28-Jul-2025"` → Would stop working after that date
- `SCRIPT_PATH` undefined → Script would crash
- No HME-specific download script

### After (Fixed)
- Dynamic date: Defaults to 30 days back, automatically updates
- `SCRIPT_PATH` properly defined
- Dedicated HME download script
- Complete automation pipeline with error handling

## Troubleshooting

### Check Logs
The automation script creates `hme_daily_task.log` with detailed information.

### Test Individual Steps
```bash
# Test download
python scripts/ingest/download_hme_attachments.py

# Check downloaded files
ls data/raw/hme/

# Test transform
python scripts/ingest/hme_transform.py data/raw/hme/2025-01-15__hme_report.xlsx

# Check transformed files
ls data/processed/hme_transformed_*.csv
```

### Common Issues

1. **No emails found**
   - Check `HME_IMAP_SUBJECT_KEY` matches email subject
   - Increase `HME_IMAP_DAYS_BACK` value
   - Check Gmail credentials

2. **Upload fails**
   - Verify Supabase credentials in `.env`
   - Check table name is `hme_report` (lowercase)
   - Verify network connection

3. **Transform fails**
   - Check Excel file format matches expected structure
   - Verify sheet name is "Paginated Summary Multi Store R"

## Next Steps

1. ✅ Update `.env` with HME-specific settings
2. ✅ Test the download script manually
3. ✅ Test the complete automation pipeline
4. ✅ Set up scheduled task (Task Scheduler or cron)
5. ✅ Monitor logs for first few days


