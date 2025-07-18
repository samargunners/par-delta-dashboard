import subprocess
import logging
from datetime import datetime
import os

# --- CONFIG ---
UPLOAD_SCRIPTS = [
    "upload_employee_clockin.py",
    "upload_employee_schedule.py",
    "upload_labour.py",
    "upload_variance.py",
    "upload_to_db.py",
]

# Create logs directory if not exists
os.makedirs("logs", exist_ok=True)

# Set up logging
log_filename = f"logs/upload_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
logging.basicConfig(
    filename=log_filename,
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)

def run_script(script_name):
    try:
        logging.info(f"Running script: {script_name}")
        subprocess.run(["python", script_name], check=True)
        logging.info(f"✅ Successfully ran: {script_name}")
    except subprocess.CalledProcessError as e:
        logging.error(f"❌ Error running {script_name}: {e}")
    except Exception as e:
        logging.exception(f"❌ Unexpected error with {script_name}:")

if __name__ == "__main__":
    logging.info("--- Starting Upload Process ---")
    for script in UPLOAD_SCRIPTS:
        run_script(script)
    logging.info("--- Upload Process Complete ---")
    print(f"Upload process complete. Check logs in {log_filename}")
