import subprocess
import json


def get_nvme_ssd_health(nvme_device="/dev/nvme0"):
    try:
        # Run the command to get the health of the NVMe SSD
        cmd = f"sudo nvme smart-log {nvme_device} -o json"
        result = subprocess.run(cmd.split(), capture_output=True, text=True)
        
        # Check if the command executed successfully
        if result.returncode != 0:
            raise Exception(f"Command failed with error: {result.stderr.strip()}")
        
        # Parse the JSON output
        smart_log = json.loads(result.stdout)
        return smart_log
    
    except Exception as e:
        print(f"Error: {str(e)}")


if __name__ == "__main__":
    # Call the function and print the result
    result = get_nvme_ssd_health()
    print(json.dumps(result, indent=4))