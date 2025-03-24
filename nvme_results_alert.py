import json



def check_health(file_name):
    try:
        with open(file_name, "r") as json_file:
            smart_log = json.load(json_file)
        warnings = []
        if smart_log["critical_warning"] != 0:
            warnings.append("Critical warning detected!")
        if smart_log["temperature"] > 320:
            warnings.append(f"High temperature detected: {smart_log['temperature']}K")
        if smart_log["percent_used"] > 80:
            warnings.append(f"High usage detected: {smart_log['percent_used']}%")
        return warnings
    except Exception as e:
        print(f"Error: {str(e)}")
        return []

