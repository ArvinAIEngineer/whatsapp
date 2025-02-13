import os
import sqlite3
from flask import Flask, request
from openai import OpenAI
from dotenv import load_dotenv
from twilio.twiml.messaging_response import MessagingResponse

load_dotenv()

app = Flask(__name__)

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def connect_to_db():
    return sqlite3.connect('phone.db')

def ensure_table_exists():
    conn = connect_to_db()
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS phone_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            phone_number TEXT UNIQUE,
            details TEXT
        )
    ''')
    conn.commit()
    conn.close()

def fetch_details_from_db(phone_number):
    try:
        if phone_number.startswith("whatsapp:"):
            phone_number = phone_number[9:]  # Remove 'whatsapp:' prefix

        conn = connect_to_db()
        cursor = conn.cursor()
        cursor.execute('SELECT details FROM phone_data WHERE phone_number = ?', (phone_number,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None
    except Exception as e:
        print(f"Database error: {e}")
        return None

def classify_query(query):
    prompt = f"""Classify the following query into one of two categories:
    1. Checking details - if the query is about verifying or retrieving employee specific details.
    2. Getting information - if the query is about general information or knowledge related to BFIL.

    Query: {query}

    Respond with only the category number (1 or 2)."""
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error classifying query: {e}")
        return None

def generate_response(query, context):
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful assistant. Keep responses concise and limited to 2 sentences."},
                {"role": "user", "content": f"Query: {query}\nContext: {context}"}
            ],
            max_tokens=300
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error generating response: {e}")
        return "There was an error processing your request."

ensure_table_exists()

@app.route('/twilio_webhook', methods=['POST'])
def twilio_webhook():
    print("Raw Twilio Request Data:")
    print(request.form)

    phone_number = request.form.get('From')
    message_body = request.form.get('Body')

    print(f"Phone number from request: {phone_number}")
    print(f"Message body from request: {message_body}")

    if not phone_number or not message_body:
        error_message = "<Response><Message>Error: Phone number and message are required.</Message></Response>"
        return error_message, 400, {'Content-Type': 'application/xml'}

    query_type = classify_query(message_body)
    print(f"Query type: {query_type}")

    if query_type == "1":
        details = fetch_details_from_db(phone_number)
        print(f"Details from database: {details}")

        if not details:
            response_text = "No details found for that number. Please make sure the number is registered."
        else:
            response_text = generate_response(message_body, details)
    elif query_type == "2":
        common_summary = """Bharat Financial Inclusion Limited (BFIL), a 100% subsidiary of IndusInd Bank, is a leading player in the financial services sector, offering a diverse range of banking and financial solutions aimed at fostering financial inclusion across India. Originally established in 1998 as a microfinance institution, BFIL became a wholly owned subsidiary of IndusInd Bank following its merger in 2019. As a Business Correspondent of the bank, BFIL provides microfinance loans, MSME loans, two-wheeler loans, merchant loans, and personal loans, along with savings and investment solutions such as recurring deposits, fixed deposits, and current accounts. Serving over 10 million customers across 1.34 lakh villages in 23 Indian states through a vast network of 3,178+ branches, BFIL plays a crucial role in enhancing financial accessibility in rural and semi-urban areas. Through Bharat Money Store and Bharat Super Shop, the company extends banking and transaction services to kirana merchants and small retailers, facilitating cash withdrawals, deposits, money transfers, bill payments, and digital transactions via mobile and WhatsApp banking. Its Aadhaar-enabled banking services further empower customers with seamless biometric-based transactions. BFIL has also established Customer Service Units (CSUs) to offer essential banking solutions at the doorstep, ensuring swift query resolution, access to government benefits, and improved financial literacy. With a commitment to innovation and digitization, BFIL continues to expand its footprint while driving financial empowerment, economic growth, and better livelihood opportunities for millions across India."""
        response_text = generate_response(message_body, common_summary)
    else:
        response_text = "Unable to classify your query."

    response = MessagingResponse()
    response.message(response_text)

    twiml_string = str(response)

    return twiml_string, 200, {'Content-Type': 'application/xml'}

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=4000, debug=False)