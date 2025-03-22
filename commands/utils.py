from datetime import datetime

def log_command(user, command, details=None):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [COMMAND] {command} | User: {user} | Details: {details}")

def log_error(error_type, user, command, error_details):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [ERROR] {error_type} | User: {user} | Command: {command} | Details: {error_details}")

def log_info(info_type, user, command, info_details):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] [INFO] {info_type} | User: {user} | Command: {command} | Details: {info_details}") 