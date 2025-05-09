import subprocess
import json
from datetime import datetime
from nvme_results_alert import check_health


def get_nvme_ssd_health(nvme_device="/dev/nvme0"):
    try:
        # Run the command to get the health of the NVMe SSD
        cmd = f"/usr/sbin/nvme smart-log {nvme_device} -o json"
        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        
        # Check if the command executed successfully
        if result.returncode != 0:
            raise Exception(f"Command failed with error: {result.stderr.strip()}")
        
        # Parse the JSON output
        smart_log = json.loads(result.stdout)
        return smart_log
    
    except Exception as e:
        print(f"Error: {str(e)}")
        return None


if __name__ == "__main__":
    file_name = None # Initialize file_name to None
    
    # Call the function and print the result
    result = get_nvme_ssd_health()
    
    if result:
        current_date = datetime.now().strftime("%Y-%m-%d") # Get the current date in YYYY-MM-DD format
        file_name = f"nvme_health_{current_date}.json" # Create a file name with the current date

        # Save the result to a JSON file
        with open(file_name, "w") as json_file:
            json.dump(result, json_file, indent=4, ensure_ascii=False)

        print(f"NVMe SSD health information saved to {file_name}")

    # Check the health and print any warnings
    if file_name:    
        warnings = check_health(file_name)
        if warnings:
            print("Warnings detected:")
            for warning in warnings:
                print(f"- {warning}")
        else:
            print("No warnings detected.")