import json

def load_json(file_name):
    try:
        with open(file_name, "r") as json_file:
            return json.load(json_file)
    except Exception as e:
        print(f"Error loading JSON file: {str(e)}")
        return None

def check_health_from_object(smart_log):
    warnings = []
    try:
        if smart_log["critical_warning"] != 0:
            warnings.append("Critical warning detected!")
        if smart_log["temperature"] > 320:
            warnings.append(f"High temperature detected: {smart_log['temperature']}K")
        if smart_log["percent_used"] > 80:
            warnings.append(f"High usage detected: {smart_log['percent_used']}%")
        if smart_log["media_errors"] > 0:
            warnings.append(f"Media errors detected: {smart_log['media_errors']}")
        if smart_log["num_err_log_entries"] > 0:
            warnings.append(f"Error log entries detected: {smart_log['num_err_log_entries']}")
    except KeyError as e:
        warnings.append(f"Missing key in JSON object: {str(e)}")
    return warnings

def check_health(file_name):
    smart_log = load_json(file_name)
    if smart_log is None:
        return []
    return check_health_from_object(smart_log)

