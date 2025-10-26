import re
import json
from typing import Dict, Any, Optional
from simple_salesforce import Salesforce

def validate_salesforce_credentials(url: str, username: str, password: str, token: str) -> tuple[bool, str]:
    """
    Validate Salesforce credentials
    Returns: (is_valid, error_message)
    """
    if not url or not username or not password or not token:
        return False, "All Salesforce credentials are required"

    if not url.startswith("https://"):
        return False, "Instance URL must start with https://"

    if "@" not in username or "." not in username.split("@")[1]:
        return False, "Username must be a valid email address"

    return True, ""

def get_user_details(sf: Salesforce, user_id: str) -> dict:
    """
    Get detailed user information from Salesforce
    """
    try:
        if "@" in user_id:
            # Search by email
            soql = f"""
            SELECT Id, FirstName, LastName, Email, Username, IsActive,
                   Title, Phone, MobilePhone, Department
            FROM User
            WHERE Email = '{user_id}'
            """
        else:
            # Search by ID
            soql = f"""
            SELECT Id, FirstName, LastName, Email, Username, IsActive,
                   Title, Phone, MobilePhone, Department
            FROM User
            WHERE Id = '{user_id}'
            """

        result = sf.query(soql)

        if result["totalSize"] > 0:
            user = result["records"][0]
            return {
                "success": True,
                "user": user,
                "formatted": format_user_display(user)
            }
        else:
            return {"success": False, "error": "User not found"}

    except Exception as e:
        return {"success": False, "error": str(e)}

def format_user_display(user: dict) -> str:
    """
    Format user information for display in chat
    """
    lines = []
    lines.append(f"👤 **{user.get('FirstName', '')} {user.get('LastName', '')}**")
    lines.append(f"📧 Email: {user.get('Email', 'N/A')}")
    lines.append(f"🔑 Username: {user.get('Username', 'N/A')}")
    lines.append(f"📱 Status: {'Active' if user.get('IsActive', False) else 'Inactive'}")

    title = user.get('Title')
    if title:
        lines.append(f"🎯 Title: {title}")

    phone = user.get('Phone')
    if phone:
        lines.append(f"📞 Phone: {phone}")

    department = user.get('Department')
    if department:
        lines.append(f"🏢 Department: {department}")

    return "\n".join(lines)

def extract_command_type(command: str) -> str:
    """
    Extract the type of command from user input
    This is a fallback if LLM parsing fails
    """
    command_lower = command.lower()

    if any(word in command_lower for word in ["create", "new", "add", "hire"]):
        return "create_user"
    elif any(word in command_lower for word in ["update", "change", "modify", "edit"]):
        return "update_user"
    elif any(word in command_lower for word in ["deactivate", "disable", "remove", "delete"]):
        return "deactivate_user"
    elif any(word in command_lower for word in ["activate", "enable"]):
        return "activate_user"
    else:
        return "unknown"

def parse_create_user_command(command: str) -> dict:
    """
    Basic regex-based parsing for create user commands as fallback
    """
    # Try to extract name and email
    name_email_pattern = r"(?:create|new)\s+(?:user\s+)?([A-Za-z\s]+?)\s+([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})"
    match = re.search(name_email_pattern, command, re.IGNORECASE)

    if match:
        full_name = match.group(1).strip()
        email = match.group(2).strip()

        # Split name into first and last
        name_parts = full_name.split()
        first_name = name_parts[0] if name_parts else ""
        last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else ""

        return {
            "operation": "create_user",
            "firstName": first_name,
            "lastName": last_name,
            "email": email,
            "username": email  # Default username to email
        }

    return {}

def parse_update_user_command(command: str) -> dict:
    """
    Basic regex-based parsing for update user commands as fallback
    """
    # Pattern: update user [email/id] to have [field] [value]
    pattern = r"update\s+(?:user\s+)?([^\s]+)\s+to\s+have\s+([^\s]+)\s+(.+)"
    match = re.search(pattern, command, re.IGNORECASE)

    if match:
        user_id = match.group(1).strip()
        field = match.group(2).strip().title()  # Capitalize field name
        value = match.group(3).strip()

        return {
            "operation": "update_user",
            "user_id": user_id,
            "updates": {field: value}
        }

    return {}

def parse_deactivate_user_command(command: str) -> dict:
    """
    Basic regex-based parsing for deactivate user commands as fallback
    """
    pattern = r"(?:deactivate|disable)\s+(?:user\s+)?([^\s]+)"
    match = re.search(pattern, command, re.IGNORECASE)

    if match:
        user_id = match.group(1).strip()
        return {
            "operation": "deactivate_user",
            "user_id": user_id
        }

    return {}

def validate_parsed_command(command: dict) -> tuple[bool, str]:
    """
    Validate the parsed command structure
    """
    operation = command.get("operation", "")

    if not operation:
        return False, "No operation specified"

    if operation == "create_user":
        required = ["firstName", "lastName", "email", "username"]
        missing = [field for field in required if not command.get(field)]
        if missing:
            return False, f"Missing required fields for create_user: {', '.join(missing)}"

        if "@" not in command.get("email", ""):
            return False, "Invalid email format"

    elif operation == "update_user":
        if not command.get("user_id"):
            return False, "User ID is required for update"
        if not command.get("updates"):
            return False, "Updates are required for update operation"

    elif operation == "deactivate_user":
        if not command.get("user_id"):
            return False, "User ID is required for deactivate"

    else:
        return False, f"Unknown operation: {operation}"

    return True, ""

def get_available_user_fields() -> list:
    """
    Return list of commonly updatable user fields in Salesforce
    """
    return [
        "FirstName", "LastName", "Title", "Email", "Phone", "MobilePhone",
        "Department", "City", "Street", "PostalCode", "Country", "State",
        "ManagerId",  # This would require looking up the manager user
        # Note: Username changes might be restricted
    ]

def log_chat_history_to_file(message: str, response: str, filename: str = "chat_history.log"):
    """
    Log chat interactions to a file for audit purposes
    """
    import datetime
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] User: {message}\n")
        f.write(f"[{timestamp}] AdminX: {response}\n")
        f.write("-" * 50 + "\n")

def get_connection_health(sf: Salesforce) -> dict:
    """
    Check the health of Salesforce connection
    """
    try:
        # Simple query to test connection
        result = sf.query("SELECT Id FROM User LIMIT 1")
        return {"healthy": True, "user_count": result.get("totalSize", 0)}
    except Exception as e:
        return {"healthy": False, "error": str(e)}

def sanitize_string(input_str: str) -> str:
    """
    Sanitize string input to prevent SOQL injection
    """
    if not input_str:
        return ""

    # Remove potentially dangerous characters for SOQL
    # This is basic sanitization - in production, use parameterized queries
    return re.sub(r"['\"\\;]", "", input_str).strip()
