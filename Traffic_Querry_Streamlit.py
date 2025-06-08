import streamlit as st
from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime

# Database connection function using SQLAlchemy
def get_db_connection():
    engine = create_engine('postgresql://postgres:123@localhost:5432/postgres')
    return engine.connect()
st.set_page_config(layout="wide")
st.title("🚓 Traffic Stop Analysis Dashboard")
st.markdown("Analyzing traffic stop data from multiple countries")
conn = get_db_connection()

# Create dropdown menu
query_options = {
    "1. Top 10 vehicles in drug-related stops": """
        SELECT vehicle_number, COUNT(*) as stop_count 
        FROM traffic_stops 
        WHERE drugs_related_stop = TRUE 
        GROUP BY vehicle_number 
        ORDER BY stop_count DESC 
        LIMIT 10;
    """,
    "2. Most frequently searched vehicles": """
        SELECT vehicle_number, COUNT(*) as search_count 
        FROM traffic_stops 
        WHERE search_conducted = TRUE 
        GROUP BY vehicle_number 
        ORDER BY search_count DESC 
        LIMIT 10;
    """,
    "3. Arrest rates by age group": """
        WITH age_groups AS (
            SELECT 
                CASE 
                    WHEN driver_age < 20 THEN 'Under 20'
                    WHEN driver_age BETWEEN 20 AND 29 THEN '20-29'
                    WHEN driver_age BETWEEN 30 AND 39 THEN '30-39'
                    WHEN driver_age BETWEEN 40 AND 49 THEN '40-49'
                    WHEN driver_age BETWEEN 50 AND 59 THEN '50-59'
                    ELSE '60+'
                END as age_group,
                is_arrested
            FROM traffic_stops 
        )
        SELECT 
            age_group,
            COUNT(*) as total_stops,
            SUM(CASE WHEN is_arrested THEN 1 ELSE 0 END) as arrests,
            ROUND(SUM(CASE WHEN is_arrested THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as arrest_rate
        FROM age_groups
        GROUP BY age_group
        ORDER BY arrest_rate DESC;
    """,
    "4. Gender distribution by country": """
        SELECT 
            country_name,
            driver_gender,
            COUNT(*) as count,
            ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY country_name), 2) as percentage
        FROM traffic_stops
        GROUP BY country_name, driver_gender
        ORDER BY country_name, driver_gender;
    """,
    "5. Highest search rate by race/gender": """
        SELECT 
            driver_race,
            driver_gender,
            COUNT(*) as total_stops,
            SUM(CASE WHEN search_conducted THEN 1 ELSE 0 END) as searches,
            ROUND(SUM(CASE WHEN search_conducted THEN 1 ELSE 0 END) * 100.0 / COUNT(*), 2) as search_rate
        FROM traffic_stops 
        GROUP BY driver_race, driver_gender
        ORDER BY search_rate DESC
        LIMIT 1;
    """,
    "6. Random stop example": "RANDOM_STOP_QUERY"
}

selected_query = st.selectbox("Select a query to run:", list(query_options.keys()))

# Display results based on selection
if selected_query:
    if selected_query == "6. Random stop example":
        # Special handling for the random stop example
        query = text("SELECT * FROM traffic_stops ORDER BY RANDOM() LIMIT 1;")
        df = pd.read_sql(query, conn)
        
        if not df.empty:
            record = df.iloc[0]
            stop_time = datetime.strptime(str(record['stop_time']), '%H:%M:%S').strftime('%I:%M %p')
            
            st.subheader("Sample Traffic Stop Record")
            st.markdown(f"""
            A {record['driver_age']}-year-old {record['driver_gender']} driver was stopped for {record['violation']} at {stop_time}.
            
            - **Country:** {record['country_name']}
            - **Race:** {record['driver_race']}
            - **Original Violation:** {record['violation_raw']}
            - **Search Conducted:** {'Yes' + (' (' + record['search_type'] + ')') if record['search_conducted'] else 'No'}
            - **Outcome:** {record['stop_outcome']} {'(Arrest made)' if record['is_arrested'] else ''}
            - **Duration:** {record['stop_duration']}
            - **Drug-Related Stop:** {'Yes' if record['drugs_related_stop'] else 'No'}
            - **Vehicle Number:** {record['vehicle_number']}
            """)
            
            with st.expander("View Raw Data"):
                st.table(df)
    else:
        # Execute the selected query
        query = text(query_options[selected_query])
        df = pd.read_sql(query, conn)
        
        st.subheader(selected_query)
        st.table(df)

# Close connection
conn.close()