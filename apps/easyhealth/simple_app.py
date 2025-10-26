import streamlit as st
import sqlite3
import hashlib
from datetime import date, time
import json

# Configure page
st.set_page_config(
    page_title="EasyHealth Hospital Portal",
    page_icon="🏥",
    layout="wide"
)

# Database setup
def init_db():
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()

    # Only drop tables if they don't exist - don't drop existing user data
    # Keep existing users table intact
    # c.execute('DROP TABLE IF EXISTS medical_reports')
    # c.execute('DROP TABLE IF EXISTS physiotherapy_sessions')
    # c.execute('DROP TABLE IF EXISTS pharmacy_orders')
    # c.execute('DROP TABLE IF EXISTS lab_appointments')
    # c.execute('DROP TABLE IF EXISTS lab_tests')
    # c.execute('DROP TABLE IF EXISTS appointments')
    # c.execute('DROP TABLE IF EXISTS doctors')
    # c.execute('DROP TABLE IF EXISTS users')

    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY, email TEXT UNIQUE, password TEXT, name TEXT, phone TEXT)''')

    c.execute('''CREATE TABLE IF NOT EXISTS doctors
                 (id INTEGER PRIMARY KEY, name TEXT, specialization TEXT, phone TEXT, rating REAL DEFAULT 4.5)''')

    c.execute('''CREATE TABLE IF NOT EXISTS appointments
                 (id INTEGER PRIMARY KEY, user_id INTEGER, doctor_id INTEGER,
                  appointment_date DATE, appointment_time TIME, status TEXT DEFAULT 'scheduled',
                  appointment_type TEXT DEFAULT 'Regular Checkup', symptoms TEXT, notes TEXT)''')

    # Lab Services
    c.execute('''CREATE TABLE IF NOT EXISTS lab_tests
                 (id INTEGER PRIMARY KEY, test_name TEXT, description TEXT, price REAL, duration INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS lab_appointments
                 (id INTEGER PRIMARY KEY, user_id INTEGER, test_id INTEGER,
                  appointment_date DATE, appointment_time TIME, status TEXT DEFAULT 'scheduled',
                  results TEXT, result_date DATE)''')

    # Pharmacy
    c.execute('''CREATE TABLE IF NOT EXISTS medications
                 (id INTEGER PRIMARY KEY, name TEXT, description TEXT, price REAL, requires_prescription INTEGER)''')

    c.execute('''CREATE TABLE IF NOT EXISTS pharmacy_orders
                 (id INTEGER PRIMARY KEY, user_id INTEGER, medications TEXT,
                  total_amount REAL, status TEXT DEFAULT 'ordered', order_date DATE,
                  delivery_option TEXT DEFAULT 'pickup', prescription_id TEXT)''')

    # Physiotherapy
    c.execute('''CREATE TABLE IF NOT EXISTS physiotherapy_sessions
                 (id INTEGER PRIMARY KEY, user_id INTEGER, session_date DATE, session_time TIME,
                  session_type TEXT, duration INTEGER DEFAULT 45, status TEXT DEFAULT 'scheduled',
                  therapist_notes TEXT)''')

    # Medical Reports
    c.execute('''CREATE TABLE IF NOT EXISTS medical_reports
                 (id INTEGER PRIMARY KEY, user_id INTEGER, report_type TEXT, report_date DATE,
                  doctor_name TEXT, diagnosis TEXT, treatment TEXT, recommendations TEXT,
                  file_path TEXT, created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')

    # Insert sample data
    # Doctors
    c.execute("INSERT OR IGNORE INTO doctors VALUES (1, 'Dr. Sarah Johnson', 'Cardiology', '+1-555-0101', 4.8)")
    c.execute("INSERT OR IGNORE INTO doctors VALUES (2, 'Dr. Michael Chen', 'Neurology', '+1-555-0102', 4.9)")
    c.execute("INSERT OR IGNORE INTO doctors VALUES (3, 'Dr. Emily Rodriguez', 'Dermatology', '+1-555-0103', 4.7)")

    # Lab Tests
    c.execute("INSERT OR IGNORE INTO lab_tests VALUES (1, 'Complete Blood Count (CBC)', 'Comprehensive blood analysis', 75.00, 30)")
    c.execute("INSERT OR IGNORE INTO lab_tests VALUES (2, 'Lipid Profile', 'Cholesterol and triglyceride analysis', 85.00, 20)")
    c.execute("INSERT OR IGNORE INTO lab_tests VALUES (3, 'Thyroid Function Test', 'TSH, T3, T4 levels', 95.00, 25)")

    # Medications
    c.execute("INSERT OR IGNORE INTO medications VALUES (1, 'Aspirin 100mg', 'Pain relief and anti-inflammatory', 15.99, 0)")
    c.execute("INSERT OR IGNORE INTO medications VALUES (2, 'Lisinopril 10mg', 'Blood pressure medication', 12.50, 1)")
    c.execute("INSERT OR IGNORE INTO medications VALUES (3, 'Vitamin D3 1000IU', 'Vitamin supplement', 8.99, 0)")

    # Sample medical reports
    c.execute("INSERT OR IGNORE INTO medical_reports VALUES (1, 1, 'Consultation Report', '2024-10-15', 'Dr. Sarah Johnson', 'Hypertension', 'Lisinopril 10mg daily', 'Follow up in 3 months, reduce salt intake', NULL, '2024-10-15 10:30:00')")

    conn.commit()
    conn.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def create_user(email, password, name):
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO users (email, password, name) VALUES (?, ?, ?)",
                 (email, hash_password(password), name))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        return user_id
    except:
        conn.close()
        return None

def get_user(email, password):
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email=? AND password=?",
             (email, hash_password(password)))
    user = c.fetchone()
    conn.close()
    return user

def get_doctors():
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()
    c.execute("SELECT * FROM doctors ORDER BY rating DESC")
    doctors = c.fetchall()
    conn.close()
    return doctors

def create_appointment(user_id, doctor_id, app_date, app_time, app_type="Regular Checkup", symptoms="", notes=""):
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()
    c.execute("""INSERT INTO appointments
                 (user_id, doctor_id, appointment_date, appointment_time, appointment_type, symptoms, notes)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
             (user_id, doctor_id, str(app_date), str(app_time), app_type, symptoms, notes))
    conn.commit()
    appointment_id = c.lastrowid
    conn.close()
    return appointment_id

def update_appointment(appointment_id, app_date, app_time, app_type, symptoms, notes):
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()
    c.execute("""UPDATE appointments SET appointment_date=?, appointment_time=?,
                 appointment_type=?, symptoms=?, notes=? WHERE id=?""",
             (str(app_date), str(app_time), app_type, symptoms, notes, appointment_id))
    conn.commit()
    conn.close()

def cancel_appointment(appointment_id):
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()
    c.execute("UPDATE appointments SET status='cancelled' WHERE id=?", (appointment_id,))
    conn.commit()
    conn.close()

def get_user_appointments(user_id):
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()
    c.execute("""SELECT a.*, d.name, d.specialization, d.rating
                 FROM appointments a
                 JOIN doctors d ON a.doctor_id = d.id
                 WHERE a.user_id=? ORDER BY a.appointment_date DESC""", (user_id,))
    appointments = c.fetchall()
    conn.close()
    return appointments

# Lab Services Functions
def get_lab_tests():
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()
    c.execute("SELECT * FROM lab_tests ORDER BY test_name")
    tests = c.fetchall()
    conn.close()
    return tests

def create_lab_appointment(user_id, test_id, app_date, app_time):
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()
    c.execute("""INSERT INTO lab_appointments (user_id, test_id, appointment_date, appointment_time)
                 VALUES (?, ?, ?, ?)""", (user_id, test_id, str(app_date), str(app_time)))
    conn.commit()
    appointment_id = c.lastrowid
    conn.close()
    return appointment_id

def get_user_lab_appointments(user_id):
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()
    c.execute("""SELECT la.*, lt.test_name, lt.description, lt.price
                 FROM lab_appointments la
                 JOIN lab_tests lt ON la.test_id = lt.id
                 WHERE la.user_id=? ORDER BY la.appointment_date DESC""", (user_id,))
    appointments = c.fetchall()
    conn.close()
    return appointments

# Pharmacy Functions
def get_medications():
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()
    c.execute("SELECT * FROM medications ORDER BY name")
    medications = c.fetchall()
    conn.close()
    return medications

def create_pharmacy_order(user_id, medications_list, total_amount, delivery_option="pickup", prescription_id=""):
    medications_str = ", ".join(medications_list)
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()
    c.execute("""INSERT INTO pharmacy_orders
                 (user_id, medications, total_amount, order_date, delivery_option, prescription_id)
                 VALUES (?, ?, ?, ?, ?, ?)""",
             (user_id, medications_str, total_amount, str(date.today()), delivery_option, prescription_id))
    conn.commit()
    order_id = c.lastrowid
    conn.close()
    return order_id

def get_user_pharmacy_orders(user_id):
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()
    c.execute("SELECT * FROM pharmacy_orders WHERE user_id=? ORDER BY order_date DESC", (user_id,))
    orders = c.fetchall()
    conn.close()
    return orders

# Physiotherapy Functions
def create_physiotherapy_session(user_id, session_date, session_time, session_type, duration=45):
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()
    c.execute("""INSERT INTO physiotherapy_sessions
                 (user_id, session_date, session_time, session_type, duration)
                 VALUES (?, ?, ?, ?, ?)""",
             (user_id, str(session_date), str(session_time), session_type, duration))
    conn.commit()
    session_id = c.lastrowid
    conn.close()
    return session_id

def get_user_physiotherapy_sessions(user_id):
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()
    c.execute("SELECT * FROM physiotherapy_sessions WHERE user_id=? ORDER BY session_date DESC", (user_id,))
    sessions = c.fetchall()
    conn.close()
    return sessions

# Medical Reports Functions
def get_user_medical_reports(user_id):
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()
    c.execute("SELECT * FROM medical_reports WHERE user_id=? ORDER BY report_date DESC", (user_id,))
    reports = c.fetchall()
    conn.close()
    return reports

def add_medical_report(user_id, report_type, report_date, doctor_name, diagnosis, treatment, recommendations):
    conn = sqlite3.connect('hospital_portal.db')
    c = conn.cursor()
    c.execute("""INSERT INTO medical_reports
                 (user_id, report_type, report_date, doctor_name, diagnosis, treatment, recommendations)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
             (user_id, report_type, str(report_date), doctor_name, diagnosis, treatment, recommendations))
    conn.commit()
    report_id = c.lastrowid
    conn.close()
    return report_id

# LLM Response Generation using Ollama MCP
def generate_llm_response(user_query, context, model_name):
    """Generate response using Ollama LLM via MCP server"""
    try:
        # Create comprehensive system prompt with patient context
        system_prompt = f"""You are a helpful healthcare assistant chatbot. You have access to the patient's complete medical data and can answer questions about their appointments, medical reports, lab results, prescriptions, and physiotherapy sessions.

IMPORTANT SAFETY GUIDELINES:
- You can ONLY discuss and provide information about the patient's OWN medical data below
- Do NOT provide general medical advice, diagnosis, or treatment recommendations outside of their records
- Stick strictly to the facts from the patient's records
- If information is not available in their records, say so clearly
- Be HIPAA compliant - maintain patient privacy

PATIENT MEDICAL DATA CONTEXT:
{context}

RESPONSE GUIDELINES:
- Be concise and helpful
- Only reference data that actually exists in the patient's records
- Format responses clearly and readably
- If asked about something not in their records, redirect to appropriate hospital services
- Focus on facts from their health records
- Do not make assumptions or provide external medical knowledge

User Question: {user_query}
"""

        # Use Ollama MCP server to generate response
        response = use_mcp_tool("ollama", "generate", {
            "model": model_name,
            "prompt": system_prompt,
            "temperature": 0.3,  # Lower temperature for more factual responses
            "num_predict": 300   # Reasonable response length
        })

        return response.get('response', 'I apologize, but I was unable to generate a response at this time.')

    except Exception as e:
        return f'Sorry, I encountered an error connecting to the AI model: {str(e)}. Please try the rule-based mode instead.'

# Rule-based Response Generation (backup when LLM unavailable)
def generate_rule_based_response(user_question, appointments, lab_appointments, pharmacy_orders, physio_sessions, medical_reports):
    """Generate rule-based response using patient data"""

    if "appointment" in user_question and "next" in user_question:
        upcoming_appts = [a for a in appointments if a[6] == 'scheduled']
        if upcoming_appts:
            # Sort by date and get next one
            upcoming_appts.sort(key=lambda x: (x[3], x[4]))
            next_appt = upcoming_appts[0]
            return f"Your next appointment is on {next_appt[3]} at {next_appt[4]} with Dr. {next_appt[8]} ({next_appt[9]} specialization) for a {next_appt[7]}."
        else:
            return "You don't have any scheduled appointments."

    elif "medication" in user_question or "prescription" in user_question:
        if pharmacy_orders:
            last_order = pharmacy_orders[0]  # Most recent first
            return f"Your most recent medication order (#{last_order[0]}) was placed on {last_order[4]} for: {last_order[3]}. Status: {last_order[6]}."
        else:
            return "You don't have any medication orders in your records."

    elif "lab" in user_question and "result" in user_question:
        completed_labs = [l for l in lab_appointments if l[6]]
        if completed_labs:
            last_result = completed_labs[0]
            return f"Your most recent lab result is for {last_result[8]} from {last_result[3]}: {last_result[6]}"
        else:
            return "You don't have any completed lab results yet."

    elif "medical report" in user_question or "report" in user_question:
        if medical_reports:
            last_report = medical_reports[0]
            return f"Your most recent medical report from {last_report[3]} by Dr. {last_report[4]} shows: Diagnosis - {last_report[5]}, Treatment - {last_report[6]}."
        else:
            return "You don't have any medical reports in your records."

    elif "physiotherapy" in user_question or "therapy" in user_question:
        if physio_sessions:
            last_session = physio_sessions[0]
            return f"Your most recent physiotherapy session was on {last_session[2]} at {last_session[3]} for {last_session[4]} (Status: {last_session[6]})."
        else:
            return "You don't have any physiotherapy sessions in your records."

    elif "all" in user_question and ("data" in user_question or "records" in user_question):
        summary = f"**Your Health Records Summary:**\n\n"
        summary += f"📅 Appointments: {len(appointments)}\n"
        summary += f"🧪 Lab Tests: {len(lab_appointments)}\n"
        summary += f"💊 Medications: {len(pharmacy_orders)}\n"
        summary += f"🦴 Physiotherapy: {len(physio_sessions)}\n"
        summary += f"📋 Medical Reports: {len(medical_reports)}\n\n"
        summary += "Would you like details about any specific category?"
        return summary

    elif "summary" in user_question:
        return "I'll provide your complete health records summary below."

    else:
        return f"I'm here to help with your health records! You can ask me about your appointments, medications, lab results, medical reports, physiotherapy sessions, or provide a health summary. Your question was: '{user_question}'"

# Helper function to use MCP tool (placeholder - replace with actual MCP integration)
def use_mcp_tool(server, tool, args):
    """Placeholder for MCP tool usage - replace with actual MCP integration"""
    # In a real implementation, this would call the MCP server
    # For now, return a mock response to demonstrate the interface

    prompt = args.get('prompt', '')
    model = args.get('model', 'rule-based')

    if "next appointment" in prompt.lower():
        return {
            'response': "Based on your records, your next scheduled appointment is tomorrow at 10:00 AM with Dr. Sarah Johnson for a regular checkup."
        }
    elif "medication" in prompt.lower():
        return {
            'response': "Your records show you have an active prescription for Lisinopril 10mg, which was filled on October 15th, 2024."
        }
    else:
        return {
            'response': f"I understand you're asking about your health records. Using {model} model, I can help you navigate your healthcare data safely and privately."
        }

# Initialize database
init_db()

# Session state
if 'user' not in st.session_state:
    st.session_state.user = None

# Custom CSS
st.markdown("""
<style>
    .main-header {font-size: 2.5rem; color: #1f77b4; text-align: center; margin-bottom: 2rem;}
    .service-card {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;
                   padding: 1.5rem; border-radius: 10px; margin: 0.5rem 0;}
    .status-scheduled {background-color: #d4edda; color: #155724; padding: 0.2rem 0.6rem; border-radius: 12px;}
    .status-completed {background-color: #cce7ff; color: #0056b3; padding: 0.2rem 0.6rem; border-radius: 12px;}
    .status-cancelled {background-color: #f8d7da; color: #721c24; padding: 0.2rem 0.6rem; border-radius: 12px;}
    .report-card {border: 1px solid #dee2e6; border-radius: 8px; padding: 1rem; margin: 0.5rem 0; background: #f8f9fa;}
</style>
""", unsafe_allow_html=True)

# Main app
if st.session_state.user:
    st.sidebar.markdown(f"### 👋 Welcome, {st.session_state.user[3]}")

    st.sidebar.markdown("### 📋 Services")
    page = st.sidebar.radio("Navigate", ["Dashboard", "Book Appointment", "My Appointments",
                                        "Lab Services", "Pharmacy", "Physiotherapy", "Medical Reports", "Chatbot"])

    if st.sidebar.button("Logout"):
        st.session_state.user = None
        st.rerun()

    if page == "Dashboard":
        st.markdown('<h1 class="main-header">🏠 Dashboard</h1>', unsafe_allow_html=True)

        # Quick stats
        col1, col2, col3 = st.columns(3)
        with col1:
            appointments = get_user_appointments(st.session_state.user[0])
            st.metric("Total Appointments", len(appointments))

        with col2:
            st.metric("Health Score", "85%")

        with col3:
            st.metric("Unread Messages", "2")

        # Services overview
        st.markdown("### 🏥 Our Services")
        services = [
            {"name": "Doctor Appointments", "desc": "Book appointments with specialists", "icon": "👨‍⚕️"},
            {"name": "Lab Services", "desc": "Comprehensive diagnostic tests", "icon": "🧪"},
            {"name": "Pharmacy", "desc": "Medication ordering and delivery", "icon": "💊"}
        ]

        cols = st.columns(3)
        for i, service in enumerate(services):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="service-card">
                    <h3>{service['icon']} {service['name']}</h3>
                    <p>{service['desc']}</p>
                </div>
                """, unsafe_allow_html=True)

    elif page == "Book Appointment":
        st.markdown("### 📅 Book Doctor Appointment")

        doctors = get_doctors()
        doctor_options = {f"{doc[1]} - {doc[2]}": doc[0] for doc in doctors}

        selected_doctor = st.selectbox("Select Doctor", list(doctor_options.keys()))
        appointment_date = st.date_input("Appointment Date", min_value=date.today())
        appointment_time = st.time_input("Appointment Time")
        appointment_type = st.selectbox("Type", ["Regular Checkup", "Consultation", "Follow-up"])

        if st.button("Book Appointment"):
            if selected_doctor and appointment_date and appointment_time:
                doctor_id = doctor_options[selected_doctor]
                appointment_id = create_appointment(
                    st.session_state.user[0],
                    doctor_id,
                    appointment_date,
                    appointment_time
                )
                if appointment_id:
                    st.success("✅ Appointment booked successfully!")
                    st.balloons()
                else:
                    st.error("Failed to book appointment")
            else:
                st.error("Please fill all fields")

    elif page == "My Appointments":
        st.markdown("### 📋 My Appointments")

        appointments = get_user_appointments(st.session_state.user[0])

        if appointments:
            for appt in appointments:
                status_class = f"status-{appt[6]}"
                with st.expander(f"📅 {appt[3]} at {appt[4]} - {appt[7]} with {appt[8]}"):
                    col1, col2 = st.columns([2, 1])

                    with col1:
                        st.markdown(f"**Status:** <span class='{status_class}'>{appt[6].title()}</span>", unsafe_allow_html=True)
                        st.markdown(f"**Type:** {appt[7]}")
                        st.markdown(f"**Doctor:** {appt[8]} ({appt[9]}⭐)")
                        if appt[10]:  # symptoms
                            st.markdown(f"**Symptoms:** {appt[10]}")
                        if appt[11]:  # notes
                            st.markdown(f"**Notes:** {appt[11]}")

                    with col2:
                        if appt[6] == 'scheduled':
                            if st.button("Modify", key=f"modify_{appt[0]}"):
                                st.session_state[f"edit_{appt[0]}"] = True

                            if st.button("Cancel", key=f"cancel_{appt[0]}"):
                                cancel_appointment(appt[0])
                                st.success("Appointment cancelled!")
                                st.rerun()

                        # Edit form (when modify is clicked)
                        if st.session_state.get(f"edit_{appt[0]}", False):
                            with st.form(f"edit_form_{appt[0]}"):
                                new_date = st.date_input("New Date", value=date.fromisoformat(appt[3]), min_value=date.today())
                                new_time = st.time_input("New Time", value=time.fromisoformat(appt[4]))
                                new_type = st.selectbox("Type", ["Regular Checkup", "Consultation", "Follow-up"], index=["Regular Checkup", "Consultation", "Follow-up"].index(appt[7]) if appt[7] in ["Regular Checkup", "Consultation", "Follow-up"] else 0)
                                new_symptoms = st.text_area("Symptoms", value=appt[10] or "")
                                new_notes = st.text_area("Notes", value=appt[11] or "")

                                if st.form_submit_button("Update"):
                                    update_appointment(appt[0], new_date, new_time, new_type, new_symptoms, new_notes)
                                    st.session_state[f"edit_{appt[0]}"] = False
                                    st.success("Appointment updated!")
                                    st.rerun()
        else:
            st.info("No appointments found. Book your first appointment!")

    elif page == "Lab Services":
        st.markdown("### 🧪 Lab Services")

        tab1, tab2 = st.tabs(["📋 Book Lab Test", "📊 My Lab Tests"])

        with tab1:
            lab_tests = get_lab_tests()

            col1, col2 = st.columns([2, 1])

            with col1:
                selected_test = st.selectbox("Select Lab Test",
                                           [f"{test[1]} - ${test[3]:.2f}" for test in lab_tests])

                test_details = next((t for t in lab_tests if f"{t[1]} - ${t[3]:.2f}" == selected_test), None)

                if test_details:
                    st.markdown(f"**Description:** {test_details[2]}")
                    st.markdown(f"**Duration:** {test_details[4]} minutes")
                    st.markdown("**Preparation Instructions:**")
                    if "frequent" in test_details[1].lower() or "blood" in test_details[1].lower():
                        st.info("• Fasting may be required for 12 hours\n• Avoid alcohol 24 hours before\n• Bring valid ID")
                    else:
                        st.info("• No special preparation needed\n• Bring valid ID")

            with col2:
                appointment_date = st.date_input("Test Date", min_value=date.today())
                appointment_time = st.time_input("Preferred Time")

                if st.button("Book Lab Test", use_container_width=True):
                    if test_details and appointment_date and appointment_time:
                        test_id = test_details[0]
                        appointment_id = create_lab_appointment(
                            st.session_state.user[0],
                            test_id,
                            appointment_date,
                            appointment_time
                        )
                        if appointment_id:
                            st.success("✅ Lab test booked successfully!")
                            st.info("Please arrive 10 minutes early with your ID. Payment will be collected at the lab.")
                        else:
                            st.error("Failed to book lab test")
                    else:
                        st.error("Please select a test and date/time")

        with tab2:
            lab_appointments = get_user_lab_appointments(st.session_state.user[0])

            if lab_appointments:
                for appt in lab_appointments:
                    with st.expander(f"🧪 {appt[8]} - {appt[3]} at {appt[4]}"):
                        col1, col2 = st.columns([2, 1])

                        with col1:
                            st.markdown(f"**Test:** {appt[8]}")
                            st.markdown(f"**Description:** {appt[9]}")
                            st.markdown(f"**Price:** ${float(appt[10]):.2f}")
                            st.markdown(f"**Date & Time:** {appt[3]} at {appt[4]}")

                        with col2:
                            status_class = f"status-{appt[5].lower()}"
                            st.markdown(f"**Status:** <span class='{status_class}'>{appt[5].title()}</span>", unsafe_allow_html=True)

                            if appt[6]:  # results
                                st.markdown("**Results:**")
                                st.info(appt[6])

                            if appt[5] == 'scheduled' and st.button("Cancel Test", key=f"cancel_lab_{appt[0]}"):
                                st.warning("Please call the lab directly to cancel: +1-555-LAB01")
            else:
                st.info("No lab appointments found")

    elif page == "Pharmacy":
        st.markdown("### 💊 Pharmacy Services")

        tab1, tab2 = st.tabs(["🛒 Order Medications", "📦 My Orders"])

        with tab1:
            medications = get_medications()

            col1, col2 = st.columns(2)

            with col1:
                st.markdown("#### Available Medications")

                selected_meds = []
                for med in medications:
                    if st.checkbox(f"{med[1]} - ${med[3]:.2f}", key=f"med_{med[0]}"):
                        selected_meds.append(med[1])

                        if med[4]:  # requires prescription
                            st.warning(f"⚠️ {med[1]} requires a prescription")

            with col2:
                st.markdown("#### Order Details")

                if selected_meds:
                    total_amount = sum(next((m[3] for m in medications if m[1] == med_name), 0) for med_name in selected_meds)

                    st.markdown(f"**Selected Medications:** {', '.join(selected_meds)}")
                    st.markdown(f"**Total Amount:** ${total_amount:.2f}")

                    delivery_option = st.radio("Pickup/Delivery", ["Pickup at Pharmacy", "Home Delivery"])
                    prescription_id = st.text_input("Prescription ID (if required)", placeholder="Enter prescription number")

                    if st.button("Place Order", use_container_width=True):
                        order_id = create_pharmacy_order(
                            st.session_state.user[0],
