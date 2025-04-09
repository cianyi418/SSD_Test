import subprocess
import json
import time

def detect_nvme_device():
    # Detect the NVMe device using lsblk
    try:
        result = subprocess.run(
            ["lsblk", "-o", "NAME,TYPE,SIZE"],
            capture_output=True, 
            text=True
        )
        devices = result.stdout.strip().split("\n")
        for device in devices:
            name, dev_type, size = device.split()
            if dev_type == "disk" and "nvme" in name:
                return f"/dev/{name}" # Return the first NVMe device found
        raise Exception("No NVMe device found")
    except Exception as e:
        print(f"Error detecting NVMe device: {str(e)}")
        return None

# Aoutomatically detect the NVMe device
Device = detect_nvme_device()
if not Device:
    print("No NVMe device found. Exiting.")
    exit(1)

RunTime = 15
Results = {}

TESTS = [
    {"name": "randwrite_4K", "rw": "randwrite", "bs": "4K", "numjobs": 4, "iodepth": 32},
    {"name": "randread_4K", "rw": "randread", "bs": "4K", "numjobs": 4, "iodepth": 32},
    {"name": "randwrite_128k", "rw": "write", "bs": "128k", "numjobs": 1, "iodepth": 32},
    {"name": "randread_128k", "rw": "read", "bs": "128k", "numjobs": 1, "iodepth": 32}
]


def run_fio_test(test):
    print(f"Running FIO test: {test['name']}")
    fio_cmd = [
        # "sudo",
        "fio",
        "--name=fio_test",
        f"--filename={Device}",
        f"--rw={test['rw']}",
        f"--bs={test['bs']}",
        f"--numjobs={test['numjobs']}",
        f"--iodepth={test['iodepth']}",
        "--time_based",
        f"--runtime={RunTime}",
        "--size=100M",
        "--ioengine=libaio",
        "--output-format=json"
    ]

    try:
        result = subprocess.run(fio_cmd, capture_output=True, text=True)
        print(f"FIO command output: {result.stdout}")

        output = json.loads(result.stdout)
        job = output["jobs"][0]
        rw_type = "read" if "read" in test["rw"] else "write"

        if isinstance(job[rw_type], dict):
            iops = job[rw_type]["iops_mean"]
            bw = job[rw_type]["bw_mean"] / 1024 # Convert to MB/s
            lat = job[rw_type]["lat_ns"]["mean"] / 1000 # Convert to us

            return {
                "type": rw_type,
                "block_size": test["bs"],
                "IOPS": round(iops, 2),
                "Bandwidth_MBps": round(bw, 2),
                "Latency_us": round(lat, 2)
            }
        else:
            raise ValueError("Invalid output format from FIO")
    except subprocess.CalledProcessError as e:
        print(f"FIO command failed: {e.stderr}")
        return {"error": f"FIO command failed: {e.stderr}"}
    except json.JSONDecodeError as e:
        print(f"Failed to parse FIO output: {str(e)}")
        return {"error": f"Failed to parse FIO output: {str(e)}"}
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return {"error": f"Unexpected error: {str(e)}"}
    
    


def main():
    print("Starting NVMe SSD performance tests...")
    for test in TESTS:
        result = run_fio_test(test)
        Results[test["name"]] = result
        time.sleep(1)  # Sleep for 1 second between tests

    print("All tests completed.")


    # Print the results
    print("FIO Test Results:")
    for test_name, result in Results.items():
        print(f"\n Test item: {test_name}")
        if "error" in result:
            print("failure")
        else:
            print(f"Type: {result['type']}")
            print(f"Block Size: {result['block_size']}")
            print(f"IOPS: {result['IOPS']}")
            print(f"Bandwidth (MB/s): {result['Bandwidth_MBps']}")
            print(f"Latency (us): {result['Latency_us']}")


    # Save the results to a JSON file
    filename = f"ssd_perf_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(filename, "w") as json_file:
        json.dump(Results, json_file, indent=4)
    print(f"Results saved to {filename}")


if __name__ == "__main__":
    main()