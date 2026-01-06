#!/usr/bin/env python3
"""
HME Daily Task Automation
This script automates the complete HME pipeline:
1. Download HME reports from Gmail
2. Transform HME Excel files
3. Upload HME data to Supabase

Run this daily via scheduler (cron, Task Scheduler, etc.)
"""
import sys
import os
from pathlib import Path
from datetime import datetime
import subprocess
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hme_daily_task.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Get project root
SCRIPT_PATH = Path(__file__).resolve()
PROJECT_ROOT = SCRIPT_PATH.parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

def run_script(script_path: Path, description: str) -> bool:
    """Run a Python script and return True if successful."""
    logger.info(f"Starting: {description}")
    logger.info(f"Running: {script_path}")
    
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode == 0:
            logger.info(f"✅ Success: {description}")
            if result.stdout:
                logger.info(f"Output: {result.stdout[-500:]}")  # Last 500 chars
            return True
        else:
            logger.error(f"❌ Failed: {description}")
            logger.error(f"Return code: {result.returncode}")
            if result.stderr:
                logger.error(f"Error: {result.stderr}")
            if result.stdout:
                logger.error(f"Output: {result.stdout[-500:]}")
            return False
            
    except subprocess.TimeoutExpired:
        logger.error(f"❌ Timeout: {description} (exceeded 5 minutes)")
        return False
    except Exception as e:
        logger.error(f"❌ Exception running {description}: {e}")
        return False

def transform_hme_files():
    """Transform all HME Excel files in the raw directory."""
    from scripts.ingest.hme_transform import parse_hme_to_desired
    
    raw_dir = PROJECT_ROOT / "data" / "raw" / "hme"
    processed_dir = PROJECT_ROOT / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    if not raw_dir.exists():
        logger.warning(f"Raw HME directory does not exist: {raw_dir}")
        return False
    
    hme_files = list(raw_dir.glob("*.xlsx")) + list(raw_dir.glob("*.xls"))
    
    if not hme_files:
        logger.warning("No HME files found to transform")
        return True  # Not an error, just no files
    
    logger.info(f"Found {len(hme_files)} HME file(s) to transform")
    
    success_count = 0
    for hme_file in hme_files:
        try:
            logger.info(f"Transforming: {hme_file.name}")
            df = parse_hme_to_desired(str(hme_file))
            
            # Save transformed file
            output_name = f"hme_transformed_{hme_file.stem}.csv"
            output_path = processed_dir / output_name
            df.to_csv(output_path, index=False)
            
            logger.info(f"✅ Transformed: {output_path.name} ({len(df)} rows)")
            success_count += 1
            
        except Exception as e:
            logger.error(f"❌ Failed to transform {hme_file.name}: {e}")
    
    return success_count > 0

def upload_hme_data():
    """Upload transformed HME data to Supabase."""
    # Import upload function
    sys.path.insert(0, str(PROJECT_ROOT / "scripts" / "upload"))
    from supabase_client import supabase
    import pandas as pd
    
    processed_dir = PROJECT_ROOT / "data" / "processed"
    hme_csv_files = list(processed_dir.glob("hme_transformed_*.csv"))
    
    if not hme_csv_files:
        logger.warning("No transformed HME files found to upload")
        return True  # Not an error
    
    logger.info(f"Found {len(hme_csv_files)} transformed HME file(s) to upload")
    
    success_count = 0
    for csv_file in hme_csv_files:
        try:
            logger.info(f"Uploading: {csv_file.name}")
            df = pd.read_csv(csv_file)
            
            # Clean and prepare data
            df.columns = df.columns.str.strip().str.lower().str.replace(" ", "_")
            df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%Y-%m-%d")
            df["store"] = df["store"].astype(str)
            
            # Select only columns that exist in hme_report table
            required_cols = [
                "date", "store", "time_measure", "total_cars", "menu_all", "greet_all",
                "service", "lane_queue", "lane_total"
            ]
            available_cols = [col for col in required_cols if col in df.columns]
            df = df[available_cols]
            df = df.astype(object).where(pd.notnull(df), None)
            
            # Upload in batches
            records = df.to_dict(orient="records")
            records = [r for r in records if any(v is not None for v in r.values())]
            
            if not records:
                logger.warning(f"No valid records in {csv_file.name}")
                continue
            
            batch_size = 500
            total = len(records)
            for i in range(0, total, batch_size):
                batch = records[i:i + batch_size]
                supabase.table("hme_report").upsert(batch).execute()
            
            logger.info(f"✅ Uploaded {total} records from {csv_file.name}")
            success_count += 1
            
        except Exception as e:
            logger.error(f"❌ Failed to upload {csv_file.name}: {e}")
            import traceback
            logger.error(traceback.format_exc())
    
    return success_count > 0

def main():
    """Main execution function."""
    logger.info("=" * 80)
    logger.info("HME Daily Task Automation Started")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 80)
    
    results = {
        "download": False,
        "transform": False,
        "upload": False
    }
    
    # Step 1: Download HME from Gmail
    download_script = PROJECT_ROOT / "scripts" / "ingest" / "download_hme_attachments.py"
    if download_script.exists():
        results["download"] = run_script(download_script, "Download HME from Gmail")
    else:
        logger.warning(f"Download script not found: {download_script}")
    
    # Step 2: Transform HME files
    try:
        results["transform"] = transform_hme_files()
    except Exception as e:
        logger.error(f"Transform step failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Step 3: Upload HME to Supabase
    try:
        results["upload"] = upload_hme_data()
    except Exception as e:
        logger.error(f"Upload step failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
    
    # Summary
    logger.info("=" * 80)
    logger.info("HME Daily Task Summary")
    logger.info("=" * 80)
    logger.info(f"Download: {'✅ SUCCESS' if results['download'] else '❌ FAILED'}")
    logger.info(f"Transform: {'✅ SUCCESS' if results['transform'] else '❌ FAILED'}")
    logger.info(f"Upload: {'✅ SUCCESS' if results['upload'] else '❌ FAILED'}")
    
    if all(results.values()):
        logger.info("🎉 All steps completed successfully!")
        return 0
    else:
        logger.warning("⚠️ Some steps failed. Check logs above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())


