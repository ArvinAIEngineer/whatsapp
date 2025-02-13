import streamlit as st
import requests
import xml.etree.ElementTree as ET

# Streamlit UI
st.title("BFIL Query Handler")

# Input fields
phone_number = st.text_input("Enter Phone Number:")
query = st.text_area("Enter Query:")

# Button to submit query
if st.button("Get Response"):
    if phone_number and query:
        # Send request to the Flask backend
        response = requests.post("http://127.0.0.1:4000/twilio_webhook", data={"From": phone_number, "Body": query})
        
        if response.status_code == 200:
            # Parse XML response and extract message
            root = ET.fromstring(response.text)
            message = root.find(".//Message").text if root.find(".//Message") is not None else "No message found."
            st.success("Response:")
            st.write(message)
        else:
            st.error("Error communicating with the backend.")
    else:
        st.warning("Please enter both phone number and query.")
