import streamlit as st
import streamlit.components.v1 as components
from database import db
import hashlib
import json
from datetime import datetime, date, time
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from PIL import Image
import io
import requests

# Configure page
st.set_page_config(
    page_title="EasyHealth Hospital Portal",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .service-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
        text-align: center;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    .status-badge {
        padding: 0.2rem 0.6rem;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: bold;
    }
    .status-scheduled { background-color: #fff3cd; color: #856404; }
    .status-completed { background-color: #d1ecf1; color: #0c5460; }
    .status-pending { background-color: #f8d7da; color: #721c24; }
    .status-confirmed { background-color: #d4edda; color: #155724; }
    .urgent-badge { background-color: #ff6b6b; color: white; }
    .sidebar-service { margin-bottom: 1rem; padding: 0.5rem; border-radius: 5px; cursor: pointer; }
    .sidebar-service:hover { background-color: #f0f0f0; }
</style>
""", unsafe_allow_html=True)

# Utility functions
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def check_password(password, hashed):
    return hash_password(password) == hashed

def format_datetime(datetime_str):
    if datetime_str:
        dt = datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
        return dt.strftime("%B %d, %Y at %I:%M %p")
    return "N/A"

def get_status_badge(status):
    status_classes = {
        'scheduled': 'status-scheduled',
        'confirmed': 'status-confirmed',
        'completed': 'status-completed',
        'cancelled': 'status-pending',
        'ordered': 'status-scheduled',
        'ready': 'status-confirmed',
        'picked_up': 'status-completed',
        'delivered': 'status-completed'
    }
    return f'<span class="status-badge {status_classes.get(status, "status-pending")}">{status.title()}</span>'

# Authentication functions
def login():
    st.sidebar.markdown("### 🔐 Login")
    email = st.sidebar.text_input("Email")
    password = st.sidebar.text_input("Password", type="password")

    if st.sidebar.button("Login", use_container_width=True):
        user = db.get_user_by_email(email)
        if user and check_password(password, user[2]):
            st.session_state.user = user
            st.success("Login successful!")
            st.rerun()
        else:
            st.error("Invalid credentials")

def register():
    st.sidebar.markdown("### 📝 Register")
    with st.sidebar.form("register_form"):
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm_password = st.text_input("Confirm Password", type="password")
        full_name = st.text_input("Full Name")
        phone = st.text_input("Phone (optional)")
        dob = st.date_input("Date of Birth (optional)", value=None, max_value=date.today())

        if st.form_submit_button("Register", use_container_width=True):
            if password != confirm_password:
                st.error("Passwords do not match")
                return

            user_id = db.create_user(email, hash_password(password), full_name, phone, dob)
            if user_id:
                st.success("Registration successful! Please login.")
            else:
                st.error("Email already exists")

def logout():
    if st.sidebar.button("Logout", use_container_width=True):
        st.session_state.user = None
        st.rerun()

# Innovative AI Symptom Checker
def ai_symptom_checker():
    st.markdown("### 🤖 AI Symptom Checker")
    st.markdown("Describe your symptoms to get preliminary health insights")

    symptoms = st.text_area("Describe your symptoms", height=100,
                           placeholder="E.g., I have a headache, fever, and sore throat for 2 days...")

    severity = st.selectbox("Severity level", ["Mild", "Moderate", "Severe", "Emergency"])
    duration = st.selectbox("How long have you had these symptoms?",
                           ["Less than 1 day", "1-3 days", "3-7 days", "More than 1 week"])

    if st.button("Analyze Symptoms", use_container_width=True):
        if symptoms.strip():
            # Mock AI analysis (in real app, this would call an AI service)
            analysis_results = {
                "possible_conditions": ["Common Cold", "Flu", "Migraine"],
                "urgency_level": "Low" if severity == "Mild" else "Medium" if severity == "Moderate" else "High",
                "recommendations": [
                    "Rest and stay hydrated",
                    "Take over-the-counter pain relief if needed",
                    "Monitor your temperature",
                    "Seek immediate medical attention if symptoms worsen"
                ],
                "suggested_department": "General Medicine"
            }

            st.markdown("#### 📊 Analysis Results")
            col1, col2 = st.columns(2)

            with col1:
                st.markdown("**Urgency Level:**")
                urgency_color = {"Low": "green", "Medium": "orange", "High": "red"}[analysis_results["urgency_level"]]
                st.markdown(f'<span style="color: {urgency_color}; font-weight: bold;">{analysis_results["urgency_level"]}</span>', unsafe_allow_html=True)

                st.markdown("**Suggested Department:**")
                st.info(analysis_results["suggested_department"])

            with col2:
                st.markdown("**Possible Conditions:**")
                for condition in analysis_results["possible_conditions"]:
                    st.write(f"• {condition}")

            st.markdown("**📋 Recommendations:**")
            for rec in analysis_results["recommendations"]:
                st.write(f"• {rec}")

            if analysis_results["urgency_level"] == "High":
                st.error("⚠️ This appears to be urgent. Please seek immediate medical attention!")

            st.markdown("---")
            st.markdown("**💡 Would you like to book an appointment with the recommended department?**")
            if st.button("Book Appointment Now", use_container_width=True):
                st.session_state.current_page = "Book Appointment"
                st.rerun()
        else:
            st.error("Please describe your symptoms")

# Health Monitoring Dashboard
def health_monitoring():
    st.markdown("### 📈 Health Monitoring Dashboard")

    if st.button("➕ Add Health Data", use_container_width=True):
        with st.form("health_form"):
            col1, col2, col3 = st.columns(3)

            with col1:
                weight = st.number_input("Weight (kg)", min_value=0.0, max_value=300.0, step=0.1)
                systolic = st.number_input("Blood Pressure Systolic", min_value=0, max_value=250)
                heart_rate = st.number_input("Heart Rate (bpm)", min_value=0, max_value=200)

            with col2:
                height = st.number_input("Height (cm)", min_value=0.0, max_value=250.0, step=0.1)
                diastolic = st.number_input("Blood Pressure Diastolic", min_value=0, max_value=150)
                temperature = st.number_input("Temperature (°C)", min_value=0.0, max_value=50.0, step=0.1)

            with col3:
                blood_glucose = st.number_input("Blood Glucose (mg/dL)", min_value=0.0, max_value=600.0, step=0.1)
                oxygen_sat = st.number_input("Oxygen Saturation (%)", min_value=0, max_value=100)
                notes = st.text_area("Additional Notes", height=100)

            if st.form_submit_button("Save Data", use_container_width=True):
                # In a real app, this would insert into health_monitoring table
                st.success("Health data saved successfully!")

    # Mock health data for demonstration
    health_data = {
        'Date': pd.date_range(start='2024-01-01', periods=30, freq='D'),
        'Weight': [75 + i*0.1 for i in range(-15, 15)],
        'Blood Pressure Sys': [120 + i for i in range(-10, 20)],
        'Blood Pressure Dia': [80 + i//2 for i in range(-10, 20)],
        'Heart Rate': [72 + i%10 for i in range(30)]
    }

    df = pd.DataFrame(health_data)

    # Charts
    col1, col2 = st.columns(2)

    with col1:
        fig = px.line(df, x='Date', y='Weight', title='Weight Trend')
        st.plotly_chart(fig, use_container_width=True)

        fig2 = px.line(df, x='Date', y=['Blood Pressure Sys', 'Blood Pressure Dia'],
                      title='Blood Pressure Trend')
        st.plotly_chart(fig2, use_container_width=True)

    with col2:
        fig3 = px.scatter(df, x='Date', y='Heart Rate', title='Heart Rate')
        st.plotly_chart(fig3, use_container_width=True)

        # Health score card
        st.markdown("### 🏥 Health Score")
        bmi = 75 / ((180/100)**2)  # Mock BMI calculation
        health_score = 85  # Mock health score

        fig4 = go.Figure(go.Indicator(
            mode="gauge+number",
            value=health_score,
            title={'text': "Overall Health Score"},
            gauge={'axis': {'range': [None, 100]},
                   'steps': [
                       {'range': [0, 50], 'color': "lightgray"},
                       {'range': [50, 80], 'color': "yellow"},
                       {'range': [80, 100], 'color': "green"}
                   ]}))
        st.plotly_chart(fig4, use_container_width=True)

# Main app
def main():
    # Initialize session state
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'current_page' not in st.session_state:
        st.session_state.current_page = "Dashboard"

    # Sidebar navigation
    st.sidebar.markdown("## 🏥 EasyHealth")
    st.sidebar.markdown("*Your Comprehensive Hospital Portal*")

    if st.session_state.user:
        st.sidebar.markdown(f"### 👋 Welcome, {st.session_state.user[3]}")
        logout()

        # Navigation menu
        st.sidebar.markdown("### 📋 Services")

        services = {
            "Dashboard": "🏠",
            "Book Appointment": "📅",
            "My Appointments": "📋",
            "Lab Services": "🧪",
            "Pharmacy": "💊",
            "Diagnostics": "🔬",
            "Physiotherapy": "🦴",
            "AI Symptom Checker": "🤖",
            "Health Monitoring": "📊",
            "Medication Reminders": "⏰"
        }

        for service, icon in services.items():
            if st.sidebar.button(f"{icon} {service}", use_container_width=True,
                               help=f"Access {service}"):
                st.session_state.current_page = service

        # Add Chatbot (AI Health Assistant) to navigation
        if st.sidebar.button("🤖 Chatbot", use_container_width=True,
                           help="AI Health Assistant for support and queries"):
            st.session_state.current_page = "Chatbot"

        # Quick check-in
        st.sidebar.markdown("### ⚡ Quick Check-in")
        checkin_options = ["Doctor Appointment", "Lab Test", "Diagnostic", "Physiotherapy"]
        checkin_type = st.sidebar.selectbox("Select service type", checkin_options)

        if st.sidebar.button("Check In Now", use_container_width=True):
            st.success(f"✅ Checked in for {checkin_type}!")
            st.balloons()

    else:
        login()
        st.sidebar.markdown("---")
        register()

    # Main content
    if st.session_state.user:
        display_current_page()
    else:
        display_landing_page()

def display_landing_page():
    st.markdown('<h1 class="main-header">🏥 Welcome to EasyHealth Hospital</h1>', unsafe_allow_html=True)
    st.markdown("## Your Complete Healthcare Solution")

    # Hero section with features
    col1, col2, col3 = st.columns([1, 2, 1])

    with col1:
        st.markdown("### 🚀 Features")
        st.markdown("• 24/7 Appointment Booking")
        st.markdown("• Advanced AI Health Assistant")
        st.markdown("• Comprehensive Lab Services")
        st.markdown("• Pharmacy & Medication Management")
        st.markdown("• Real-time Health Monitoring")

    with col2:
        # Add a nice image placeholder
        st.markdown("""
        <div style="text-align: center; padding: 2rem;">
            <div style="font-size: 5rem;">🏥</div>
            <p style="font-size: 1.2rem; color: #666;">Advanced Healthcare at Your Fingertips</p>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown("### 📈 Statistics")
        st.metric("Doctors Available", "25+")
        st.metric("Daily Appointments", "500+")
        st.metric("Lab Tests", "100+")
        st.metric("Success Rate", "98%")

    # Services overview
    st.markdown("---")
    st.markdown("### 🏥 Our Services")

    services = [
        {"name": "Doctor Appointments", "desc": "Book appointments with specialists", "icon": "👨‍⚕️"},
        {"name": "Lab Services", "desc": "Comprehensive diagnostic tests", "icon": "🧪"},
        {"name": "Pharmacy", "desc": "Medication ordering and delivery", "icon": "💊"},
        {"name": "Diagnostics", "desc": "X-Ray, CT, MRI services", "icon": "🔬"},
        {"name": "Physiotherapy", "desc": "Rehabilitation and therapy", "icon": "🦴"},
        {"name": "AI Health Assistant", "desc": "Smart symptom analysis", "icon": "🤖"}
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

def display_current_page():
    if st.session_state.current_page == "Dashboard":
        display_dashboard()
    elif st.session_state.current_page == "Book Appointment":
        display_book_appointment()
    elif st.session_state.current_page == "My Appointments":
        display_my_appointments()
    elif st.session_state.current_page == "Lab Services":
        display_lab_services()
    elif st.session_state.current_page == "Pharmacy":
        display_pharmacy()
    elif st.session_state.current_page == "Diagnostics":
        display_diagnostics()
    elif st.session_state.current_page == "Physiotherapy":
        display_physiotherapy()
    elif st.session_state.current_page == "AI Symptom Checker":
        ai_symptom_checker()
    elif st.session_state.current_page == "Health Monitoring":
        health_monitoring()
    elif st.session_state.current_page == "Medication Reminders":
        display_medication_reminders()
    elif st.session_state.current_page == "Chatbot":
        display_chatbot()

def display_dashboard():
    st.markdown('<h2 class="main-header">🏠 Dashboard</h2>', unsafe_allow_html=True)

    # Quick stats
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        appointments = db.get_user_appointments(st.session_state.user[0])
        st.metric("Total Appointments", len(appointments))

    with col2:
        lab_appointments = db.get_user_lab_appointments(st.session_state.user[0])
        st.metric("Lab Tests", len(lab_appointments))

    with col3:
        pharmacy_orders = db.get_user_pharmacy_orders(st.session_state.user[0])
        st.metric("Pharmacy Orders", len(pharmacy_orders))

    with col4:
        st.metric("Health Score", "85%")

    # Recent activity
    st.markdown("### 📝 Recent Activity")

    tab1, tab2, tab3, tab4 = st.tabs(["🗓️ Appointments", "🧪 Lab Results", "💊 Pharmacy", "🏃‍♂️ Activities"])

    with tab1:
        recent_appointments = appointments[:5] if appointments else []
        if recent_appointments:
            for appt in recent_appointments:
                st.markdown(f"""
                {get_status_badge(appt[6])} **{appt[-2]}** with {appt[-1]}
                - {appt[4]} at {appt[5]}
                """, unsafe_allow_html=True)
        else:
            st.info("No appointments scheduled")

    with tab2:
        st.info("No recent lab results")

    with tab3:
        if pharmacy_orders:
            st.markdown(f"Latest order: {pharmacy_orders[0][4]} - {get_status_badge(pharmacy_orders[0][5])}", unsafe_allow_html=True)

    with tab4:
        st.info("Track your daily health activities here")

def display_book_appointment():
    st.markdown("### 📅 Book Doctor Appointment")

    doctors = db.get_available_doctors()

    col1, col2 = st.columns(2)

    with col1:
        doctor_options = {f"{doc[1]} - {doc[2]}": doc[0] for doc in doctors}
        selected_doctor = st.selectbox("Select Doctor", list(doctor_options.keys()))

        appointment_type = st.selectbox("Appointment Type",
                                      ["Regular Checkup", "Consultation", "Follow-up", "Emergency"])

        appointment_date = st.date_input("Appointment Date", min_value=date.today())
        appointment_time = st.time_input("Appointment Time")

    with col2:
        symptoms = st.text_area("Describe your Symptoms (optional)", height=100)
        additional_notes = st.text_area("Additional Notes", height=80)

    if st.button("Book Appointment", use_container_width=True):
        if selected_doctor and appointment_date and appointment_time:
            doctor_id = doctor_options[selected_doctor]
            appointment_id = db.create_appointment(
                st.session_state.user[0],
                doctor_id,
                appointment_type,
                appointment_date,
                appointment_time,
                symptoms,
                additional_notes
            )
            if appointment_id:
                st.success("✅ Appointment booked successfully!")
                st.balloons()
            else:
                st.error("Failed to book appointment")
        else:
            st.error("Please fill all required fields")

def display_my_appointments():
    st.markdown("### 📋 My Appointments")

    appointments = db.get_user_appointments(st.session_state.user[0])

    if appointments:
        for appt in appointments:
            with st.expander(f"{appt[4]} - {appt[-2]} with {appt[-1]}"):
                col1, col2, col3 = st.columns(3)

                with col1:
                    st.markdown(f"**Date & Time:** {appt[4]} at {appt[5]}")
                    st.markdown(f"**Type:** {appt[3]}")

                with col2:
                    st.markdown(f"**Status:** {get_status_badge(appt[6])}", unsafe_allow_html=True)
                    if appt[7]:  # symptoms
                        st.markdown(f"**Symptoms:** {appt[7]}")

                with col3:
                    if appt[8]:  # notes
                        st.markdown(f"**Notes:** {appt[8]}")

                    if appt[6] == 'scheduled':
                        if st.button("Cancel Appointment", key=f"cancel_{appt[0]}"):
                            st.success("Appointment cancelled")
    else:
        st.info("No appointments found. Book your first appointment!")

def display_lab_services():
    st.markdown("### 🧪 Lab Services")

    lab_services = db.get_lab_services()

    col1, col2 = st.columns([2, 1])

    with col1:
        selected_service = st.selectbox("Select Lab Test", [service[1] for service in lab_services])

        service_details = next((s for s in lab_services if s[1] == selected_service), None)

        if service_details:
            st.markdown(f"**Description:** {service_details[2]}")
            st.markdown(f"**Price:** ${service_details[3]:.2f}")
            st.markdown(f"**Duration:** {service_details[4]} minutes")
            if service_details[5]:
                st.markdown(f"**Preparation:** {service_details[5]}")

    with col2:
        appointment_date = st.date_input("Test Date", min_value=date.today())
        appointment_time = st.time_input("Preferred Time")

        if st.button("Book Lab Test", use_container_width=True):
            if service_details and appointment_date and appointment_time:
                service_id = service_details[0]
                appointment_id = db.create_lab_appointment(
                    st.session_state.user[0],
                    service_id,
                    appointment_date,
                    appointment_time
                )
                if appointment_id:
                    st.success("✅ Lab test booked successfully!")
                else:
                    st.error("Failed to book lab test")
            else:
                st.error("Please select a service and date/time")

    # My lab appointments
    st.markdown("### My Lab Appointments")
    lab_appointments = db.get_user_lab_appointments(st.session_state.user[0])

    if lab_appointments:
        for appt in lab_appointments:
            st.markdown(f"""
            **{appt[-3]}** - ${appt[-1]:.2f}
            - Date: {appt[3]} at {appt[4]}
            - Status: {get_status_badge(appt[5])}""", unsafe_allow_html=True)
    else:
        st.info("No lab appointments")

def display_pharmacy():
    st.markdown("### 💊 Pharmacy Services")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("#### 📝 Order Medications")
        medications = st.text_area("List medications", height=100,
                                  placeholder="1. Aspirin 100mg - 30 tablets\n2. Vitamin D 1000IU - 60 capsules")

        delivery_option = st.radio("Pickup/Delivery", ["Pickup at Pharmacy", "Home Delivery"])

        if delivery_option == "Home Delivery":
            delivery_address = st.text_input("Delivery Address")
        else:
            delivery_address = None

        total_amount = st.number_input("Estimated Total ($)", min_value=0.0, step=0.01)

    with col2:
        st.markdown("#### 💳 Payment")
        payment_method = st.selectbox("Payment Method",
                                    ["Credit Card", "Insurance", "Cash on Pickup"])

        if payment_method == "Credit Card":
            with st.form("card_payment"):
                card_number = st.text_input("Card Number", max_chars=16)
                expiry = st.text_input("Expiry (MM/YY)", max_chars=5)
                cvv = st.text_input("CVV", max_chars=3, type="password")

                if st.form_submit_button("Process Payment"):
                    # Mock payment processing
                    if card_number and expiry and cvv:
                        st.success("✅ Payment processed successfully!")
                    else:
                        st.error("Invalid payment details")

        if st.button("Place Order", use_container_width=True):
            if medications.strip():
                order_id = db.create_pharmacy_order(
                    st.session_state.user[0],
                    medications,
                    total_amount,
                    "delivery" if delivery_option == "Home Delivery" else "pickup",
                    delivery_address
                )
                if order_id:
                    st.success("✅ Order placed successfully!")
                else:
                    st.error("Failed to place order")
            else:
                st.error("Please list your medications")

    # Order history
    st.markdown("### 📋 Order History")
    orders = db.get_user_pharmacy_orders(st.session_state.user[0])

    if orders:
        for order in orders:
            with st.expander(f"Order #{order[0]} - {format_datetime(order[10])}"):
                st.markdown(f"""
                **Medications:** {order[3]}
                **Total:** ${order[5]:.2f}
                **Option:** {order[7].title()}
                **Status:** {get_status_badge(order[4])}""", unsafe_allow_html=True)
    else:
        st.info("No pharmacy orders yet")

def display_diagnostics():
    st.markdown("### 🔬 Diagnostic Services")

    diagnostic_services = db.get_diagnostic_services()

    col1, col2 = st.columns([2, 1])

    with col1:
        selected_service = st.selectbox("Select Diagnostic Service",
                                      [service[1] for service in diagnostic_services])

        service_details = next((s for s in diagnostic_services if s[1] == selected_service), None)

        if service_details:
            st.markdown(f"**Category:** {service_details[2].title()}")
            st.markdown(f"**Description:** {service_details[3]}")
            st.markdown(f"**Price:** ${service_details[4]:.2f}")
            st.markdown(f"**Duration:** {service_details[5]} minutes")

    with col2:
        appointment_date = st.date_input("Appointment Date", min_value=date.today())
        appointment_time = st.time_input("Preferred Time")
        urgency = st.selectbox("Urgency", ["Routine", "Urgent", "Emergency"])

        if st.button("Book Diagnostic Test", use_container_width=True):
            if service_details and appointment_date and appointment_time:
                service_id = service_details[0]
                appointment_id = db.create_diagnostic_appointment(
                    st.session_state.user[0],
                    service_id,
                    appointment_date,
                    appointment_time,
                    urgency.lower()
                )
                if appointment_id:
                    st.success("✅ Diagnostic test booked successfully!")
                    if urgency.lower() == "emergency":
                        st.error("🚨 Emergency appointment - please proceed to hospital immediately!")
                else:
                    st.error("Failed to book diagnostic test")
            else:
                st.error("Please select a service and date/time")

def display_physiotherapy():
    st.markdown("### 🦴 Physiotherapy Services")

    col1, col2 = st.columns(2)

    with col1:
        session_type = st.selectbox("Session Type",
                                  ["Initial Assessment", "Physical Therapy", "Sports Injury Rehab",
                                   "Post-Surgery Rehab", "Pain Management", "Mobility Training"])

        duration_options = [30, 45, 60, 90]
        duration = st.selectbox("Session Duration (minutes)", duration_options)

        therapist_preferred = st.checkbox("Request Specific Therapist")
        special_requirements = st.text_area("Special Requirements or Notes", height=80)

    with col2:
        appointment_date = st.date_input("Session Date", min_value=date.today())
        appointment_time = st.time_input("Preferred Time")

    if st.button("Book Physiotherapy Session", use_container_width=True):
        st.success("✅ Physiotherapy session booked successfully!")

        # Mock session details
        st.markdown("### 📅 Session Details")
        st.markdown(f"**Type:** {session_type}")
        st.markdown(f"**Date & Time:** {appointment_date} at {appointment_time}")
        st.markdown(f"**Duration:** {duration} minutes")
        st.markdown(f"**Location:** Room 203, Physiotherapy Department")

        st.info("Please arrive 10 minutes early for your session. Bring comfortable clothing.")

def display_chatbot():
    st.markdown("### 🤖 AI Health Assistant Chatbot")
    st.markdown("*Your comprehensive healthcare companion - ask questions about appointments, medications, lab results, medical reports, and get personalized health guidance!*")

    # Initialize chat history in session state
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []

    # Get patient data for enhanced context
    patient_data = get_patient_data_for_context(st.session_state.user[0])

    # Chat interface
    chat_container = st.container(height=400)

    with chat_container:
        if st.session_state.chat_history:
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    with st.chat_message("user"):
                        st.write(message['content'])
                else:
                    with st.chat_message("assistant"):
                        st.write(message['content'])
        else:
            st.info("👋 Hi! I'm your AI Health Assistant. I can help you with:\n\n• 📅 Appointment information and reminders\n• 💊 Medication guidance and pharmacy questions\n• 🧪 Lab results and test information\n• 📋 Medical reports and health summaries\n• 🏥 Hospital services and requirements\n• 🤒 Symptom navigation and preparation instructions\n\nWhat can I help you with today?")

    # Chat input
    prompt = st.chat_input("Ask me anything about your healthcare...")

    if prompt:
        with st.chat_message("user"):
            st.write(prompt)

        # Add user message to history
        st.session_state.chat_history.append({
            'role': 'user',
            'content': prompt
        })

        with st.chat_message("assistant"):
            with st.spinner("Analyzing your question..."):
                assistant_response = generate_chatbot_response(prompt, patient_data)

            st.write(assistant_response)

        # Add assistant response to history
        st.session_state.chat_history.append({
            'role': 'assistant',
            'content': assistant_response
        })

    # Quick action buttons
    st.markdown("### ⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📅 My Next Appointment", use_container_width=True):
            prompt_next_appt = "When is my next appointment?"
            st.session_state.chat_history.append({
                'role': 'user',
                'content': prompt_next_appt
            })
            response = generate_chatbot_response(prompt_next_appt, patient_data)
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response
            })
            st.rerun()

    with col2:
        if st.button("💊 Current Medications", use_container_width=True):
            prompt_meds = "What medications am I currently taking?"
            st.session_state.chat_history.append({
                'role': 'user',
                'content': prompt_meds
            })
            response = generate_chatbot_response(prompt_meds, patient_data)
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response
            })
            st.rerun()

    with col3:
        if st.button("🧪 Recent Lab Results", use_container_width=True):
            prompt_lab = "What are my most recent lab results?"
            st.session_state.chat_history.append({
                'role': 'user',
                'content': prompt_lab
            })
            response = generate_chatbot_response(prompt_lab, patient_data)
            st.session_state.chat_history.append({
                'role': 'assistant',
                'content': response
            })
            st.rerun()

    # Clear chat button
    if st.button("🗑️ Clear Chat History"):
        st.session_state.chat_history = []
        st.success("Chat history cleared!")
        st.rerun()

def get_patient_data_for_context(user_id):
    """Get comprehensive patient data for enhanced chatbot context"""
    try:
        # Use the database functions to get relevant patient data
        appointments = db.get_user_appointments(user_id)
        lab_appointments = db.get_user_lab_appointments(user_id)
        pharmacy_orders = db.get_user_pharmacy_orders(user_id)

        # Get user info
        user = db.get_user_by_email(None)  # Need to modify to get by user_id
        # Note: This might need adjustment based on available db methods

        return {
            'appointments': appointments,
            'lab_appointments': lab_appointments,
            'pharmacy_orders': pharmacy_orders,
            'user_id': user_id,
            # Add more data as needed
        }
    except Exception as e:
        st.error(f"Error retrieving patient data: {e}")
        return {}

def generate_chatbot_response(user_query, patient_data):
    """Generate AI chatbot response with enhanced logic and risk-appropriate guidance"""
    user_query = user_query.lower().strip()

    # Phase 1: Basic Services (Office hours, symptom navigation, medication info, prep instructions)
    office_keywords = ['office', 'hours', 'open', 'when', 'time', 'schedule', 'operating', 'clinic']
    if any(keyword in user_query for keyword in office_keywords):
        return """🏥 **Hospital Operating Hours:**

**Monday - Friday:** 8:00 AM - 8:00 PM
**Saturday:** 9:00 AM - 5:00 PM
**Sunday:** Emergency services only (24/7)

**Emergency Department:** Available 24/7

**Note:** Appointments are available during regular business hours. Walk-in patients are seen based on urgency."""

    # Symptom navigation
    symptom_keywords = ['symptom', 'pain', 'headache', 'fever', 'cough', 'stomach', 'nausea', 'feeling sick']
    if any(keyword in user_query for keyword in symptom_keywords):
        return """🤒 **Symptom Navigation Guide:**

Based on your description, here's how to proceed:

1. **Assess Urgency Level:**
   - 🔴 Seek immediate emergency care if experiencing chest pain, difficulty breathing, severe bleeding, or confusion
   - 🟡 Visit urgent care within 24 hours for high fever, severe pain, or vision changes
   - 🟢 Schedule regular appointment for ongoing symptoms or routine check-ups

2. **Prepare for Your Visit:**
   - Bring any current medications
   - Note when symptoms started and what makes them better/worse
   - List any recent changes or new medications

3. **Suggested Department:**
   - General Medicine for general symptoms
   - Emergency for urgent cases
   - Specialized clinics for specific concerns

Would you like me to help you book an appointment?"""

    # Medication information
    med_keywords = ['medication', 'medicine', 'drug', 'pill', 'prescription', 'taking', 'dosage']
    if any(keyword in user_query for keyword in med_keywords):
        pharmacy_orders = patient_data.get('pharmacy_orders', [])
        if pharmacy_orders:
            response = "💊 **Your Current Medications:**\n\n"
            for order in pharmacy_orders[:3]:  # Show last 3 orders
                response += f"• {order[3]} (Order #{order[0]}) - Status: {order[4].title()}\n"
            response += "\n**Important Safety Information:**\n"
            response += "• Take medications exactly as prescribed\n"
            response += "• Never share prescriptions\n"
            response += "• Report any side effects immediately\n"
            response += "• Ask pharmacist about interactions"
            return response
        else:
            return "💊 **Medication Information:**\n\nYou don't have any recent pharmacy orders. If you're taking medications, please inform your healthcare provider.\n\n**General Medication Guidelines:**\n• Always follow prescription instructions\n• Take with food if stomach upset occurs\n• Use pill organizers for multiple medications"

    # Preparation instructions
    prep_keywords = ['prepare', 'preparation', 'before', 'appointment', 'test', 'exam', 'procedure', 'instructions']
    if any(keyword in user_query for keyword in prep_keywords):
        return """📋 **Appointment & Test Preparation Guidelines:**

**🩺 Doctor Appointments:**
• Arrive 15 minutes early with ID and insurance
• Bring list of current medications and allergies
• Prepare questions for your doctor
• Wear comfortable, modest clothing

**🧪 Lab Tests:**
• Most tests require fasting 8-12 hours beforehand
• Avoid alcohol 24 hours before blood work
• Bring valid photo ID
• Wear short sleeves for blood draws

**🔬 Diagnostic Imaging (X-Ray, CT, MRI):**
• Remove metal objects and jewelry
• Wear comfortable clothing
• Some tests require contrast dye (check for allergies)
• Follow specific preparation instructions provided

**💉 Other Procedures:**
• Follow any fasting requirements
• Arrange transportation if sedation is used
• Bring comfort items as allowed

*Specific instructions may vary - always follow the details sent to you.*

Would you like information about a specific appointment or test?"""

    # Appointment queries
    appt_keywords = ['appointment', 'booking', 'schedule', 'doctor', 'visit', 'next', 'upcoming']
    if any(keyword in user_query for keyword in appt_keywords):
        appointments = patient_data.get('appointments', [])
        upcoming = [a for a in appointments if a[6] == 'scheduled']

        if upcoming:
            response = "📅 **Your Upcoming Appointments:**\n\n"
            for appt in upcoming[:3]:
                response += f"• {appt[4]} at {appt[5]} - {appt[7]} with Dr. {appt[-2]}\n"
            response += "\n**Need to reschedule? Visit the Appointments page.**\n"
            return response
        else:
            return "📅 **No scheduled appointments found.**\n\nWould you like to book a new appointment?\n\n**How I can help:**\n• Book appointments with specialists\n• Reschedule existing appointments\n• Cancel if needed\n• Prepare you for your visit"

    # Lab results
    lab_keywords = ['lab', 'test', 'result', 'blood', 'urine', 'analysis', 'cbc', 'thyroid']
    if any(keyword in user_query for keyword in lab_keywords):
        lab_appointments = patient_data.get('lab_appointments', [])
        if lab_appointments:
            response = "🧪 **Your Recent Lab Tests:**\n\n"
            for lab in lab_appointments[:3]:
                status = "Results pending" if not lab[6] else f"Results available: {lab[6][:100]}..."
                response += f"• {lab[8]} - {lab[3]} ({status})\n"
            response += "\n**Doctor will review results and contact you if needed.**\n"
            return response
        else:
            return "🧪 **Lab Services Available:**\n\nWe offer comprehensive laboratory testing including:\n• Complete Blood Count (CBC)\n• Lipid Profile & Cholesterol\n• Thyroid Function Tests\n• Diabetes Screening\n• Liver & Kidney Function\n\nWould you like to schedule a lab test?"

    # Medical reports
    report_keywords = ['report', 'medical', 'history', 'diagnosis', 'treatment', 'record', 'chart']
    if any(keyword in user_query for keyword in report_keywords):
        return """📋 **Medical Records Access:**

Your medical reports include:
• Consultation summaries
• Diagnosis and treatment plans
• Medication history
• Lab and test results
• Progress notes from visits

**How to Access:**
1. Visit the Medical Reports page
2. Download or view your records
3. Share with other healthcare providers as needed

**Privacy Note:** Your medical information is protected by HIPAA regulations and only shared with your consent.

Would you like help accessing specific reports?"""

    # Billing and payments
    billing_keywords = ['bill', 'billing', 'payment', 'cost', 'insurance', 'fee', 'charge', 'money']
    if any(keyword in user_query for keyword in billing_keywords):
        return """💰 **Billing & Insurance Information:**

**Payment Methods Accepted:**
• Insurance (Major providers accepted)
• Credit/Debit Cards
• Cash
• FSA/HSA accounts

**Billing Questions?**
• Call Patient Financial Services: (555) 123-BILL
• Check statements in your patient portal
• Insurance claims take 2-4 weeks to process

**Common Services & Estimated Costs:**
• Office Visit: $150-$250
• Lab Tests: $50-$200
• Procedures: Varies by complexity

For detailed billing inquiries, please contact our billing department directly."""

    # General hospital information
    hospital_keywords = ['hospital', 'location', 'address', 'directions', 'parking', 'entrance', 'where']
    if any(keyword in user_query for keyword in hospital_keywords):
        return """🏥 **EasyHealth Hospital Information:**

**Address:** 123 Medical Center Drive, Healthcare City, HC 12345

**Directions:**
• From I-95: Exit 123, follow medical center signs
• Parking: Free patient parking available on levels 1-3
• Main Entrance: Through the Emergency Department entrance
• Visitor Parking: Level 4, $5/hour during business hours

**Department Locations:**
• Emergency: Ground floor
• Appointments: 2nd floor, Suite 200
• Lab: 1st floor, Room 150
• Pharmacy: Main floor, near cafeteria

**Contact Numbers:**
• Main: (555) 123-4567
• Appointments: (555) 123-4000
• Emergency: (555) 911-0000

Need specific directions or assistance?"""

    # Default response with helpful suggestions
    return f"""🤖 **I'm here to help with your healthcare needs!**

I didn't quite understand: "{user_query}"

**Here are some things I can assist with:**

📅 **Appointments & Scheduling**
• Check next appointment details
• Reschedule or cancel appointments
• Prepare for your visit

💊 **Medications & Pharmacy**
• Current medication lists
• Refill reminders
• Pharmacy hour information

🧪 **Lab & Test Results**
• View recent lab results
• Understand test preparations
• Schedule new tests

🏥 **Hospital Information**
• Operating hours & locations
• Services and departments
• Billing and insurance questions

📋 **Health Records**
• Access medical reports
• View health summaries
• Download records

Try asking me questions like:
• "When is my next appointment?"
• "What should I prepare for my lab test?"
• "What medications am I taking?"
• "What are the hospital hours?"

What would you like to know more about?"""

def display_medication_reminders():
    st.markdown("### ⏰ Medication Reminders")

    st.markdown("#### ➕ Add New Reminder")
    with st.form("reminder_form"):
        col1, col2 = st.columns(2)

        with col1:
            medication_name = st.text_input("Medication Name")
            dosage = st.text_input("Dosage (e.g., 500mg)")
            frequency = st.selectbox("Frequency", ["Once daily", "Twice daily", "Three times daily",
                                                 "Four times daily", "Every 8 hours", "Every 12 hours"])

        with col2:
            start_date = st.date_input("Start Date", value=date.today())
            end_date = st.date_input("End Date (optional)", value=None)
            notes = st.text_area("Additional Notes", height=80)

        if st.form_submit_button("Save Reminder", use_container_width=True):
            st.success("✅ Medication reminder saved!")

    st.markdown("### 📋 Active Reminders")

    # Mock reminders
    reminders = [
        {"name": "Aspirin", "dosage": "100mg", "frequency": "Twice daily", "start": "2024-01-01", "active": True},
        {"name": "Vitamin D", "dosage": "1000IU", "frequency": "Once daily", "start": "2024-01-10", "active": True},
    ]

    for reminder in reminders:
        with st.expander(f"💊 {reminder['name']} - {reminder['dosage']}"):
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Frequency:** {reminder['frequency']}")
                st.markdown(f"**Started:** {reminder['start']}")

            with col2:
                if st.button("Mark as Completed Today", key=f"complete_{reminder['name']}"):
                    st.success("✅ Marked as completed!")
                if st.button("Stop Reminder", key=f"stop_{reminder['name']}"):
                    st.warning("Reminder stopped")

if __name__ == "__main__":
