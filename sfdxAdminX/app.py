import streamlit as st
import openai
import json
from simple_salesforce import Salesforce
import requests
from oauthlib.oauth2 import WebApplicationClient
from requests_oauthlib import OAuth2Session
from typing import Dict, Any, Optional, Tuple
import re
from utils import (
    validate_salesforce_credentials, get_user_details, format_user_display,
    extract_command_type, parse_create_user_command, parse_update_user_command,
    parse_deactivate_user_command, validate_parsed_command, get_available_user_fields,
    log_chat_history_to_file, get_connection_health, sanitize_string
)

# Page configuration
st.set_page_config(
    page_title="SFDC AdminX - Salesforce LLM Chatbot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for rich UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2563eb;
        margin-bottom: 2rem;
        text-align: center;
    }
    .stTextInput > div > div > input {
        font-size: 16px;
    }
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin-bottom: 1rem;
        border: 1px solid #e5e7eb;
    }
    .user-message {
        background-color: #f3f4f6;
        border-left: 4px solid #2563eb;
    }
    .assistant-message {
        background-color: #eff6ff;
        border-left: 4px solid #16a34a;
    }
    .status-success {
        color: #16a34a;
        font-weight: bold;
    }
    .status-error {
        color: #dc2626;
        font-weight: bold;
    }
    .status-info {
        color: #2563eb;
        font-weight: bold;
    }
    .sidebar-divider {
        margin: 1rem 0;
        border-bottom: 2px solid #e5e7eb;
    }
</style>
""", unsafe_allow_html=True)

def create_salesforce_connection_oauth(url: str, consumer_key: str, consumer_secret: str) -> Optional[Salesforce]:
    """Create Salesforce connection using OAuth 2.0 Client Credentials Flow"""
    try:
        # Determine the oauth token endpoint
        if url.endswith('.my.salesforce.com') or url.endswith('.salesforce.com'):
            token_url = url + '/services/oauth2/token'
        else:
            token_url = url.rstrip('/') + '/services/oauth2/token'

        # OAuth 2.0 Client Credentials flow
        data = {
            'grant_type': 'client_credentials',
            'client_id': consumer_key,
            'client_secret': consumer_secret
        }

        response = requests.post(token_url, data=data, timeout=30)
        response.raise_for_status()

        token_data = response.json()
        access_token = token_data['access_token']
        instance_url = token_data['instance_url']

        # Create Salesforce instance with access token as session_id
        sf = Salesforce(instance_url=instance_url, session_id=access_token, client_id=consumer_key)
        return sf
    except Exception as e:
        st.error(f"Failed to connect to Salesforce via OAuth: {str(e)}")
        return None

def parse_command_with_llm(command: str, api_key: str) -> dict:
    """Parse natural language command using LLM"""
    try:
        client = openai.OpenAI(api_key=api_key)

        prompt = f"""
You are an AI assistant that parses natural language commands related to Salesforce User administration.
Convert the user's command into a structured JSON format.

Available operations: create_user, update_user, deactivate_user

For each operation, extract the following information:

For create_user:
{{"operation": "create_user", "firstName": "...", "lastName": "...", "email": "...", "username": "..." }}

For update_user:
{{"operation": "update_user", "user_id": "...", "updates": {{"field": "value", ...}} }}

For deactivate_user:
{{"operation": "deactivate_user", "user_id": "..." }}

IMPORTANT: For "user_id" in update_user and deactivate_user operations, use the email address if an email is mentioned, otherwise use the user identifier provided.

User command: "{command}"

Respond with ONLY the JSON object, no additional text.

Examples:

Create user commands:
Input: "Create a new user named John Doe with email john@example.com"
Output: {{"operation": "create_user", "firstName": "John", "lastName": "Doe", "email": "john@example.com", "username": "john@example.com"}}

Input: "Add employee Jane Smith, her email is jane.smith@company.com"
Output: {{"operation": "create_user", "firstName": "Jane", "lastName": "Smith", "email": "jane.smith@company.com", "username": "jane.smith@company.com"}}

Input: "Hire Bob Johnson with email bob@company.com as new user"
Output: {{"operation": "create_user", "firstName": "Bob", "lastName": "Johnson", "email": "bob@company.com", "username": "bob@company.com"}}

Input: "Create account for Sarah Wilson - sarah.wilson@email.org"
Output: {{"operation": "create_user", "firstName": "Sarah", "lastName": "Wilson", "email": "sarah.wilson@email.org", "username": "sarah.wilson@email.org"}}

Update user commands:
Input: "Update user with email john@example.com to have last name Smith"
Output: {{"operation": "update_user", "user_id": "john@example.com", "updates": {{"LastName": "Smith"}} }}

Input: "Change John Doe's email to john.doe@newcompany.com"
Output: {{"operation": "update_user", "user_id": "john@example.com", "updates": {{"Email": "john.doe@newcompany.com"}} }}

Input: "Set the phone number for user jane@company.com to 555-1234"
Output: {{"operation": "update_user", "user_id": "jane@company.com", "updates": {{"Phone": "555-1234"}} }}

Input: "Update bob@company.com's department to Engineering"
Output: {{"operation": "update_user", "user_id": "bob@company.com", "updates": {{"Department": "Engineering"}} }}

Input: "Make sarah.wilson@org.com the manager, set her title to Senior Manager"
Output: {{"operation": "update_user", "user_id": "sarah.wilson@org.com", "updates": {{"Title": "Senior Manager"}} }}

Input: "Change mike@corp.com's city to San Francisco and state to CA"
Output: {{"operation": "update_user", "user_id": "mike@corp.com", "updates": {{"City": "San Francisco", "State": "CA"}} }}

Input: "Set john.doe@company.com's role to System Administrator"
Output: {{"operation": "update_user", "user_id": "john.doe@company.com", "updates": {{"UserRoleId": "System Administrator"}} }}

Input: "Change mary@org.com's time zone to Pacific Standard Time"
Output: {{"operation": "update_user", "user_id": "mary@org.com", "updates": {{"TimeZoneSidKey": "America/Los_Angeles"}} }}

Input: "Update bob.smith@enterprise.com's locale to English (United States)"
Output: {{"operation": "update_user", "user_id": "bob.smith@enterprise.com", "updates": {{"LocaleSidKey": "en_US"}} }}

Input: "Set sarah.jones@corp.com's manager to mike.wilson@corp.com"
Output: {{"operation": "update_user", "user_id": "sarah.jones@corp.com", "updates": {{"ManagerId": "mike.wilson@corp.com"}} }}

Input: "Change david.lee@startup.com's department to Sales"
Output: {{"operation": "update_user", "user_id": "david.lee@startup.com", "updates": {{"Department": "Sales"}} }}

Input: "Update lisa@company.com's phone to +1-555-0123"
Output: {{"operation": "update_user", "user_id": "lisa@company.com", "updates": {{"Phone": "+1-555-0123"}} }}

Input: "Set tom.brown@firm.com's mobile number to 555-0456"
Output: {{"operation": "update_user", "user_id": "tom.brown@firm.com", "updates": {{"MobilePhone": "555-0456"}} }}

Input: "Change jane.davis@tech.com's title to Senior Software Engineer"
Output: {{"operation": "update_user", "user_id": "jane.davis@tech.com", "updates": {{"Title": "Senior Software Engineer"}} }}

Input: "Update mark@agency.com's address - 123 Main St, Springfield, IL 62701"
Output: {{"operation": "update_user", "user_id": "mark@agency.com", "updates": {{"Street": "123 Main St", "City": "Springfield", "State": "IL", "PostalCode": "62701"}} }}

Input: "Set karen@consulting.com's country to Canada"
Output: {{"operation": "update_user", "user_id": "karen@consulting.com", "updates": {{"Country": "Canada"}} }}

Input: "Change steve@retail.com's employee number to EMP12345"
Output: {{"operation": "update_user", "user_id": "steve@retail.com", "updates": {{"EmployeeNumber": "EMP12345"}} }}

Input: "Update nancy@hr.com's start date to 2024-01-15"
Output: {{"operation": "update_user", "user_id": "nancy@hr.com", "updates": {{"HireDate": "2024-01-15"}} }}

Input: "Set paul@finance.com's currency to CAD"
Output: {{"operation": "update_user", "user_id": "paul@finance.com", "updates": {{"DefaultCurrencyIsoCode": "CAD"}} }}

Input: "Change rachel@marketing.com's language to French"
Output: {{"operation": "update_user", "user_id": "rachel@marketing.com", "updates": {{"LanguageLocaleKey": "fr"}} }}

Input: "Update chris@support.com's extension number to 1234"
Output: {{"operation": "update_user", "user_id": "chris@support.com", "updates": {{"Extension": "1234"}} }}

Input: "Set amy@operations.com's federation ID to AMY123"
Output: {{"operation": "update_user", "user_id": "amy@operations.com", "updates": {{"FederationIdentifier": "AMY123"}} }}

Input: "Change mike@engineering.com's company name to Tech Innovations Inc"
Output: {{"operation": "update_user", "user_id": "mike@engineering.com", "updates": {{"CompanyName": "Tech Innovations Inc"}} }}

Input: "Update sara@legal.com's division to Corporate"
Output: {{"operation": "update_user", "user_id": "sara@legal.com", "updates": {{"Division": "Corporate"}} }}

Input: "Set john@executive.com's employee type to Full-time"
Output: {{"operation": "update_user", "user_id": "john@executive.com", "updates": {{"Employee_Type__c": "Full-time"}} }}

Deactivate user commands:
Input: "Deactivate the user john@example.com"
Output: {{"operation": "deactivate_user", "user_id": "john@example.com"}}

Input: "Remove user jane@company.com from the system"
Output: {{"operation": "deactivate_user", "user_id": "jane@company.com"}}

Input: "Disable account for bob@company.com"
Output: {{"operation": "deactivate_user", "user_id": "bob@company.com"}}
"""

        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant that parses Salesforce commands into structured JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )

        result = response.choices[0].message.content.strip()
        return json.loads(result)

    except Exception as e:
        st.error(f"Error parsing command: {str(e)}")
        return {}

def generate_soql(parsed_command: dict) -> str:
    """Generate SOQL query from parsed command"""
    operation = parsed_command.get("operation", "")

    if operation == "create_user":
        # For create_user, we don't need SOQL as we'll use the SOAP API
        return "INSERT User"
    elif operation == "deactivate_user":
        user_id = parsed_command.get("user_id", "")
        if "@" in user_id:
            # Assume it's email
            return f"SELECT Id, IsActive FROM User WHERE Email = '{user_id}'"
        else:
            # Assume it's user id
            return f"SELECT Id, IsActive FROM User WHERE Id = '{user_id}'"
    elif operation == "update_user":
        user_id = parsed_command.get("user_id", "")
        if "@" in user_id:
            return f"SELECT Id, Email FROM User WHERE Email = '{user_id}'"
        else:
            return f"SELECT Id, Email FROM User WHERE Id = '{user_id}'"
    else:
        return ""

def execute_soql(sf: Salesforce, soql: str) -> dict:
    """Execute SOQL query"""
    try:
        result = sf.query(soql)
        return {"success": True, "records": result.get("records", []), "total_size": result.get("totalSize", 0)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_user_in_salesforce(sf: Salesforce, parsed_command: dict) -> dict:
    """Create user in Salesforce"""
    try:
        first_name = parsed_command.get("firstName", "")
        last_name = parsed_command.get("lastName", "")
        email = parsed_command.get("email", "")
        username = parsed_command.get("username", "")

        user_data = {
            "FirstName": first_name,
            "LastName": last_name,
            "Email": email,
            "Username": username,
            "IsActive": True
        }

        result = sf.User.create(user_data)
        # Handle different response types from Salesforce API
        if isinstance(result, dict) and "success" in result:
            return {"success": result["success"], "id": result.get("id", "")}
        elif isinstance(result, int):
            # HTTP status code returned on error
            return {"success": False, "error": f"HTTP {result}: User creation failed"}
        else:
            # Try to get the ID from other possible formats
            return {"success": True, "id": str(result)}
    except Exception as e:
        return {"success": False, "error": str(e)}

def update_user_in_salesforce(sf: Salesforce, parsed_command: dict, user_id: str) -> dict:
    """Update user in Salesforce"""
    try:
        updates = parsed_command.get("updates", {})

        result = sf.User.update(user_id, updates)
        # Handle different response types from Salesforce API
        if isinstance(result, dict) and "success" in result:
            return {"success": result["success"], "id": user_id}
        elif isinstance(result, int):
            # HTTP status codes - 2xx range indicates success
            if 200 <= result < 300:
                return {"success": True, "id": user_id}
            else:
                # Other status codes indicate error
                return {"success": False, "error": f"HTTP {result}: Update failed"}
        else:
            # Assume success if not an error
            return {"success": True, "id": user_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

def deactivate_user_in_salesforce(sf: Salesforce, user_id: str) -> dict:
    """Deactivate user in Salesforce"""
    try:
        result = sf.User.update(user_id, {"IsActive": False})
        # Handle different response types from Salesforce API
        if isinstance(result, dict) and "success" in result:
            return {"success": result["success"], "id": user_id}
        elif isinstance(result, int):
            # HTTP status code returned on error
            return {"success": False, "error": f"HTTP {result}: Failed to deactivate user"}
        else:
            # Assume success if not an error
            return {"success": True, "id": user_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

def main():
    # Main header
    st.markdown('<h1 class="main-header">⚡ SFDC AdminX</h1>', unsafe_allow_html=True)
    st.markdown("**Salesforce Administration Chatbot powered by LLM**")

    # Initialize session state
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'salesforce_connected' not in st.session_state:
        st.session_state.salesforce_connected = False

    # Sidebar configuration
    with st.sidebar:
        st.markdown("### 🔧 Configuration")

        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        # LLM Configuration
        st.markdown("#### 🤖 LLM Settings")
        llm_provider = st.selectbox("LLM Provider", ["OpenAI"], index=0)
        api_key = st.text_input("API Key", type="password", help="Enter your OpenAI API key")

        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        # Salesforce Configuration
        st.markdown("#### ☁️ Salesforce Connection")
        sf_url = st.text_input("Instance URL", placeholder="https://your-org.salesforce.com",
                             help="Salesforce instance URL")
        sf_consumer_key = st.text_input("Consumer Key", type="password",
                                      help="Connected app consumer key (Client ID)")
        sf_consumer_secret = st.text_input("Consumer Secret", type="password",
                                         help="Connected app consumer secret (Client Secret)")

        connect_button = st.button("🔗 Connect to Salesforce", type="primary")

        if connect_button:
            # Validate OAuth credentials
            if not all([sf_url, sf_consumer_key, sf_consumer_secret]):
                st.error("❌ All Salesforce OAuth credentials are required (Instance URL, Consumer Key, Consumer Secret)")
                st.session_state.salesforce_connected = False
            elif not sf_url.startswith("https://"):
                st.error("❌ Instance URL must start with https://")
                st.session_state.salesforce_connected = False
            else:
                with st.spinner("Connecting to Salesforce via OAuth Client Credentials..."):
                    sf = create_salesforce_connection_oauth(sf_url, sf_consumer_key, sf_consumer_secret)
                    if sf:
                        # Test connection health
                        health = get_connection_health(sf)
                        if health["healthy"]:
                            st.session_state.salesforce_connection = sf
                            st.session_state.salesforce_connected = True
                            st.success(f"✅ Connected to Salesforce via OAuth Client Credentials! ({health['user_count']} users found)")
                        else:
                            st.error(f"❌ OAuth connection successful but unhealthy: {health['error']}")
                            st.session_state.salesforce_connected = False
                    else:
                        st.session_state.salesforce_connected = False

        # Connection status and user list
        if st.session_state.salesforce_connected:
            st.markdown('<p class="status-success">● Connected to Salesforce</p>', unsafe_allow_html=True)

            # User List Section
            with st.expander("👥 User Directory", expanded=False):
                st.markdown("### 📋 Current Users")
                try:
                    # Query all active users
                    soql = """
                    SELECT Id, FirstName, LastName, Email, Username, IsActive,
                           Title, Department, Phone, MobilePhone
                    FROM User
                    WHERE IsActive = true
                    ORDER BY LastName, FirstName
                    LIMIT 200
                    """
                    user_result = st.session_state.salesforce_connection.query(soql)

                    if user_result["totalSize"] > 0:
                        # Prepare data for display
                        users_data = []
                        for user in user_result["records"]:
                            full_name = f"{user.get('FirstName', '')} {user.get('LastName', '')}".strip()
                            users_data.append({
                                "Name": full_name,
                                "Email": user.get("Email", ""),
                                "Username": user.get("Username", ""),
                                "Title": user.get("Title", ""),
                                "Department": user.get("Department", ""),
                                "Phone": user.get("Phone", ""),
                                "Mobile": user.get("MobilePhone", ""),
                                "Status": "Active" if user.get("IsActive", False) else "Inactive"
                            })

                        # Display as table
                        st.dataframe(users_data, use_container_width=True)

                        if user_result["totalSize"] >= 200:
                            st.info("ℹ️ Showing first 200 users. Use SOQL queries for larger datasets.")
                        else:
                            st.info(f"📊 Showing {len(users_data)} active users")
                    else:
                        st.info("📭 No active users found")

                except Exception as e:
                    st.error(f"❌ Failed to load user directory: {str(e)}")

        else:
            st.markdown('<p class="status-error">● Not Connected</p>', unsafe_allow_html=True)

        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)

        # Available Commands
        st.markdown("#### 📋 Available Commands")
        st.markdown("""
        **User Administration:**
        - Create a new user [name, email]
        - Update user [email/id] [field: value]
        - Deactivate user [email/id]

        **Examples:**
        - "Create user John Doe john@email.com"
        - "Update user john@email.com to have last name Smith"
        - "Deactivate user john@email.com"
        """)

        # Available User Fields
        with st.expander("🔍 Available User Fields"):
            fields = get_available_user_fields()
            for field in fields:
                st.markdown(f"• **{field}**")
            st.markdown("*Note: Some fields may require additional permissions*")

    # Main chat interface
    col1, col2 = st.columns([4, 1])

    with col2:
        if st.button("🗑️ Clear Chat"):
            st.session_state.messages = []
            st.rerun()

    # Display chat messages
    chat_container = st.container()

    with chat_container:
        st.markdown("### 💬 Chat History")

        for message in st.session_state.messages:
            if message["role"] == "user":
                st.markdown(f'<div class="chat-message user-message"><strong>You:</strong> {message["content"]}</div>',
                          unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message assistant-message"><strong>AdminX:</strong> {message["content"]}</div>',
                          unsafe_allow_html=True)

    # Chat input
    st.markdown("---")
    chat_input = st.text_input("Enter your command:", key="chat_input",
                              placeholder="Type a user administration command...")
    send_button = st.button("📤 Send", type="primary")

    if send_button and chat_input.strip():
        if not api_key:
            st.error("Please provide an OpenAI API key in the sidebar")
            return

        if not st.session_state.salesforce_connected:
            st.error("Please connect to Salesforce first")
            return

        # Add user message
        st.session_state.messages.append({"role": "user", "content": chat_input})

        # Process command
        with st.spinner("Processing your command..."):
            # Try LLM parsing first
            parsed_command = parse_command_with_llm(chat_input, api_key)

            # If LLM parsing fails, use fallback regex parsing
            if not parsed_command:
                command_type = extract_command_type(chat_input)
                if command_type == "create_user":
                    parsed_command = parse_create_user_command(chat_input)
                elif command_type == "update_user":
                    parsed_command = parse_update_user_command(chat_input)
                elif command_type == "deactivate_user":
                    parsed_command = parse_deactivate_user_command(chat_input)

            # Validate parsed command
            if parsed_command:
                is_valid, validation_error = validate_parsed_command(parsed_command)
                if not is_valid:
                    response = f"❌ Invalid command format: {validation_error}"
                    # Add assistant response and skip further processing
                    st.session_state.messages.append({"role": "assistant", "content": response})
                    log_chat_history_to_file(chat_input, response)
                    st.rerun()
                    return

            if not parsed_command:
                response = "❌ I couldn't understand your command. Please try rephrasing or using one of the example formats shown in the sidebar."
            else:
                # Execute command
                operation = parsed_command.get("operation", "")
                sf = st.session_state.salesforce_connection

                if operation == "create_user":
                    result = create_user_in_salesforce(sf, parsed_command)
                    if result["success"]:
                        # Get user details for confirmation
                        user_details = get_user_details(sf, result['id'])
                        if user_details["success"]:
                            response = f"✅ User created successfully!\n\n{user_details['formatted']}"
                        else:
                            response = f"✅ User created successfully! ID: {result['id']}"
                    else:
                        response = f"❌ Failed to create user: {result.get('error', 'Unknown error')}"

                elif operation == "deactivate_user":
                    user_id = parsed_command.get("user_id", "")
                    # Sanitize user ID
                    safe_user_id = sanitize_string(user_id)

                    # Get user details first
                    soql = generate_soql(parsed_command)
                    user_result = execute_soql(sf, soql)

                    if user_result["success"] and user_result["records"]:
                        actual_user_id = user_result["records"][0]["Id"]
                        result = deactivate_user_in_salesforce(sf, actual_user_id)
                        if result["success"]:
                            response = f"✅ User deactivated successfully! User {user_id} has been disabled."
                        else:
                            response = f"❌ Failed to deactivate user: {result.get('error', 'Unknown error')}"
                    else:
                        response = f"❌ User not found: {safe_user_id}"

                elif operation == "update_user":
                    user_id = parsed_command.get("user_id", "")
                    safe_user_id = sanitize_string(user_id)

                    soql = generate_soql(parsed_command)
                    user_result = execute_soql(sf, soql)

                    if user_result["success"] and user_result["records"]:
                        actual_user_id = user_result["records"][0]["Id"]
                        result = update_user_in_salesforce(sf, parsed_command, actual_user_id)
                        if result["success"]:
                            # Verify the update by querying the user again
                            updated_user_details = get_user_details(sf, actual_user_id)
                            if updated_user_details["success"]:
                                # Make response more innovative and show verification
                                updates_made = list(parsed_command.get("updates", {}).keys())
                                update_summary = ", ".join(updates_made)
                                response = f"🎉 **Mission Accomplished!** 🚀\n\n"
                                response += f"✅ Successfully updated **{updated_user_details['user']['FirstName']} {updated_user_details['user']['LastName']}**\n"
                                response += f"📝 **Changes Applied:** {update_summary}\n\n"
                                response += f"**🔍 Verified Updated Details:**\n{updated_user_details['formatted']}\n\n"
                                response += f"💡 *All changes have been saved and verified in Salesforce!*"
                            else:
                                response = f"✅ User updated successfully! (Could not verify details due to API limitations)"
                        else:
                            response = f"❌ Failed to update user: {result.get('error', 'Unknown error')}"
                    else:
                        response = f"❌ User not found: {safe_user_id}"

                else:
                    available_commands = [
                        "Create user [name] [email]",
                        "Update user [email] [field: value]",
                        "Deactivate user [email]"
                    ]
                    response = f"❌ Unsupported operation. Available commands:\n" + "\n".join(f"• {cmd}" for cmd in available_commands)

        # Add assistant response
        st.session_state.messages.append({"role": "assistant", "content": response})

        # Rerun to update the display
        st.rerun()

if __name__ == "__main__":
    main()
