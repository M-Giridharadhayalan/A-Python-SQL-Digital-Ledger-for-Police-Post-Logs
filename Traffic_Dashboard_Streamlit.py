import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from datetime import datetime
import re

# PostgreSQL Connection
DB_URI = "postgresql://postgres:123@localhost:5432/postgres"
engine = create_engine(DB_URI)

# Vehicle number validation
def validate_vehicle_number(vehicle_num):
    """Basic validation for vehicle numbers (alphanumeric with 3-12 characters)"""
    pattern = r'^[A-Za-z0-9]{3,12}$'
    return re.match(pattern, vehicle_num) is not None

def store_record(stop_date, stop_time, country_name, driver_gender, driver_age, 
                violation, stop_duration, drugs_related_stop, vehicle_number):
    # Generate risk prediction
    if drugs_related_stop:
        risk_level = "high"
        risk_reason = "because this was a drug-related stop"
    elif driver_age < 25:
        risk_level = "medium"
        risk_reason = "due to the driver being under 25 years old"
    else:
        risk_level = "low"
        risk_reason = "as this appears to be a routine traffic stop"

    insert_query = text("""
        INSERT INTO traffic_stops 
        (stop_date, stop_time, country_name, driver_gender, driver_age, 
         violation, stop_duration, drugs_related_stop, vehicle_number) 
        VALUES 
        (:stop_date, :stop_time, :country_name, :driver_gender, :driver_age, 
         :violation, :stop_duration, :drugs_related_stop, :vehicle_number)
    """)

    try:
        with engine.connect() as connection:
            connection.execute(insert_query, {
                "stop_date": stop_date,
                "stop_time": stop_time.strftime('%H:%M:%S'),
                "country_name": country_name,
                "driver_gender": driver_gender,
                "driver_age": driver_age,
                "violation": violation,
                "stop_duration": stop_duration,
                "drugs_related_stop": drugs_related_stop,
                "vehicle_number": vehicle_number
            })
            connection.commit()
        return generate_prediction_report(
            stop_date, stop_time, country_name, driver_gender, driver_age,
            violation, stop_duration, drugs_related_stop, vehicle_number,
            risk_level, risk_reason
        )
    except Exception as e:
        st.error(f"Database error: {str(e)}")
        return None

def generate_prediction_report(stop_date, stop_time, country_name, driver_gender, 
                             driver_age, violation, stop_duration, drugs_related_stop,
                             vehicle_number, risk_level, risk_reason):
    """Generate a narrative prediction report in paragraph format"""
    report = f"""
    **Traffic Stop Prediction Report**  
    
    On {stop_date.strftime('%B %d, %Y')} at approximately {stop_time.strftime('%I:%M %p')}, 
    officers conducted a traffic stop in {country_name} involving vehicle {vehicle_number}. 
    The driver was identified as a {driver_age}-year-old {driver_gender.lower()} who was 
    stopped for {violation.lower()}. The duration of the stop was {stop_duration.lower()}.
    
    **Risk Assessment:**  
    This incident has been classified as **{risk_level} risk** {risk_reason}. 
    """
    
    if drugs_related_stop:
        report += "The presence of suspected drugs significantly increases the risk profile of this stop."
    elif driver_age < 25:
        report += "Younger drivers statistically show higher risk profiles in traffic stops."
    else:
        report += "No exceptional risk factors were identified in this routine traffic stop."
    
    report += "\n\n**Recommended Actions:** "
    
    if risk_level == "high":
        report += "Immediate supervisor notification recommended. Consider requesting backup if stop is ongoing."
    elif risk_level == "medium":
        report += "Standard protocols apply. Maintain heightened situational awareness."
    else:
        report += "Standard operating procedures are sufficient for this low-risk stop."
    
    return report

# Streamlit UI
st.title("🚔 Traffic Stop Analysis System")

with st.form("traffic_stop_form"):
    st.subheader("Enter Stop Details")
    
    col1, col2 = st.columns(2)
    with col1:
        stop_date = st.date_input("Stop Date*", datetime.now())
    with col2:
        stop_time = st.time_input("Stop Time*", datetime.now().time())
    
    country_name = st.text_input("Jurisdiction*", "USA")
    vehicle_number = st.text_input("Vehicle Number*", placeholder="ABC123", 
                                 help="Actual license plate number")
    
    col1, col2 = st.columns(2)
    with col1:
        driver_gender = st.selectbox("Driver Gender*", ["Male", "Female", "Other"])
    with col2:
        driver_age = st.number_input("Driver Age*", min_value=16, max_value=100, value=30)
    
    violation = st.selectbox("Violation*", ["Speeding", "Red Light", "Illegal Turn", 
                                          "Equipment Violation", "Other"])
    stop_duration = st.selectbox("Stop Duration*", ["0-15 minutes", "16-30 minutes", 
                                                  "Over 30 minutes"])
    drugs_related_stop = st.checkbox("Drug-related indicators present")
    
    submitted = st.form_submit_button("Generate Risk Assessment")
    
    if submitted:
        if not validate_vehicle_number(vehicle_number):
            st.error("Please enter a valid vehicle number (3-12 alphanumeric characters)")
        else:
            report = store_record(
                stop_date, stop_time, country_name, driver_gender, driver_age,
                violation, stop_duration, drugs_related_stop, vehicle_number
            )
            
            if report:
                st.success("Report generated successfully!")
                st.markdown("---")
                st.markdown(report)
                st.markdown("---")
                st.caption("This automated assessment is for officer safety purposes only")