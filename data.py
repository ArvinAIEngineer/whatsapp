import sqlite3
import pandas as pd
import streamlit as st

# Streamlit app title
st.title("Phone Database Viewer")

# Function to connect to SQLite database and fetch data
def get_data():
    try:
        conn = sqlite3.connect("phone.db")
        df = pd.read_sql_query("SELECT * FROM phone_data", conn)
        conn.close()
        return df
    except Exception as e:
        st.error(f"Error: {e}")
        return pd.DataFrame()

# Load data
data = get_data()

# Display data in Streamlit app
if not data.empty:
    st.dataframe(data)
else:
    st.write("No data found in the database.")
