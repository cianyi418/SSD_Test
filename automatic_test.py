
from datetime import datetime
import json
import os
import subprocess
import time
from email.message import EmailMessage
from config_helper import load_config
from nvme_health import get_nvme_ssd_health
from nvme_results_alert import check_health_from_object
from nvme_perf import detect_nvme_device
from nvme_perf import run_fio_test

#deployment
if os.geteuid() == 0:
    LOG_DIR = "/var/log/nvme_test_logs"
else:
    LOG_DIR = os.path.expanduser("~/nvme_test_logs")

if not isinstance(LOG_DIR, str):
    raise ValueError(f"LOG_DIR must be a string, but got {type(LOG_DIR)}: {LOG_DIR}")

EMAIL_ON_ERROR = True
RunTime = 15
Results = {}


TESTS = [
    {"name": "randwrite_4K", "rw": "randwrite", "bs": "4K", "numjobs": 4, "iodepth": 32},
    {"name": "randread_4K", "rw": "randread", "bs": "4K", "numjobs": 4, "iodepth": 32},
    {"name": "randwrite_128k", "rw": "write", "bs": "128k", "numjobs": 1, "iodepth": 32},
    {"name": "randread_128k", "rw": "read", "bs": "128k", "numjobs": 1, "iodepth": 32}
]

# Load configuration
config = load_config()

EMAIL_FROM = config.get("email_from", "default_from@example.com")
EMAIL_TO = config.get("email_to", "default_to@example.com")

# create folder
def ensure_log_directory():
    try:
        if not os.path.exists(LOG_DIR):
            os.makedirs(LOG_DIR, exist_ok=True)
            print(f"Log directory created: {LOG_DIR}")
        else:
            print(f"Log directory already exists: {LOG_DIR}")

        if not os.access(LOG_DIR, os.W_OK):
            raise PermissionError(f"Log directory is not writable: {LOG_DIR}")
    except PermissionError as e:
        print(f"Permission error: {str(e)}")
        print("please check the directory permission or run the script with sudo.")
        exit(1)
    except Exception as e:
        print(f"Unexpected error while creating or accessing log directory: {str(e)}")
        exit(1)
    
    
# Send email alert
def send_error_email(error_msg):
    if not EMAIL_ON_ERROR:
        return
    msg = EmailMessage()
    msg.set_content(error_msg)
    msg['Subject'] = 'SSD Test Error Alert'
    msg['From'] = EMAIL_FROM
    msg['To'] = EMAIL_TO

    try:
        subprocess.run(
            ["msmtp", "-t"],
            input=msg.as_bytes(),
            check=True,
            text=False
        )
        print("Error email sent successfully.")
    except subprocess.CalledProcessError as e:
        print(f"Failed to send error email: {e}")
    except Exception as e:
        print(f"Unexpected error while sending email: {e}")
    finally:
        print("Email sending process completed.")


def print_results(results):
    print("FIO Test Results:")
    for test_name, result in results.items():
        print(f"\n Test item: {test_name}")
        if isinstance(result, dict): # Check if result is a dictionary
            if "error" in result:
                print("Status Failure")
                print(f"Error: {result['error']}")
            elif "block_size" in result:  # FIO test result structure
                print(f"Type: {result['type']}")
                print(f"Block Size: {result['block_size']}")
                print(f"IOPS: {result['IOPS']}")
                print(f"Bandwidth (MB/s): {result['Bandwidth_MBps']}")
                print(f"Latency (us): {result['Latency_us']}")
            elif "type" in result and result["type"] == "health_status":  # Health status structure
                print("Health Status Details:")
                for key, value in result["details"].items():
                    print(f"{key}: {value}")
            else:  # Unexpected structure
                print("Details:")
                for key, value in result.items():
                    print(f"{key}: {value}")
        else:
            print("Unexpected result format.")


# Main function
def main():
    ensure_log_directory() # Ensure the log directory exists and is writable
    Device = detect_nvme_device()
    if not Device:
        print("No NVMe device found. Exiting.")
        exit(1)

    try:
        # Get NVMe SSD health status
        health_status = get_nvme_ssd_health(Device)
        if health_status is None:
            raise ValueError("Health status is None. Unable to proceed.")
        Results["health_status"] = {
            "type": "health_status",
            "details": health_status
        }

        # Check health status
        health_check_result = check_health_from_object(health_status)
        if health_check_result:
            warnings = []
            for warning in health_check_result:
                warnings.append(warning)
            print("Warnings detected:\n" + "\n".join(warnings))
            # Send email alert if warnings are detected
            if EMAIL_ON_ERROR:
                send_error_email("NVMe SSD health alert detected:\n" + "\n".join(warnings))
        else:
            print("No warnings detected. Health status is normal.")

        # Run FIO tests
        for test in TESTS:
            result = run_fio_test(test)

            if "error" in result:
                error_msg = result.get("error", "Unknown error")
                print(f"Test {test['name']} failed: {result['error']}")
                send_error_email(f"Test {test['name']} failed: {result['error']}")
                continue
            
            print(f"Test {test['name']} completed successfully.")
            print(f"Type: {result['type']}")
            print(f"Block Size: {result['block_size']}")
            print(f"IOPS: {result['IOPS']}")
            print(f"Bandwidth (MB/s): {result['Bandwidth_MBps']}")
            print(f"Latency (us): {result['Latency_us']}")
            Results[test["name"]] = result

        print("All tests completed successfully.")

        # print_results(Results) # Check if results are empty
        
        # Save results to a JSON file
        if not isinstance(Results, dict) or not Results:
            raise ValueError(f"Results must be a dictionary, but got {type(Results)}: {Results}")

        filename = os.path.join(LOG_DIR, f"nvme_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        print(f"Saving results to: {filename}")

        try:
            with open(filename, "w") as f:
                json.dump(Results, f, indent=4)
        except Exception as e:
            print(f"Error saving results to JSON file: {str(e)}")
            raise
        
    except Exception as e:
        error_msg = f"Error during SSD test: {str(e)}"
        print(error_msg)
        send_error_email(f"Error during health check: {error_msg}")
        raise

if __name__ == "__main__":
    main()