import os
import requests
from flask import Flask, request, jsonify
from google import genai
from google.genai import types

app = Flask(__name__)

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
WHATSAPP_TOKEN = os.environ.get("WHATSAPP_TOKEN")
PHONE_NUMBER_ID = os.environ.get("PHONE_NUMBER_ID")
VERIFY_TOKEN = os.environ.get("VERIFY_TOKEN", "my_verify_token_123")

client = genai.Client(api_key=GEMINI_API_KEY)
SYSTEM_PROMPT = "ເຈົ້າແມ່ນ AI Agent ຜູ້ຊ່ວຍຕອບແຊັດລູກຄ້າທາງ WhatsApp. ຕອບດ້ວຍພາສາລາວທີ່ສຸພາບ, ກະທັດຮັດ ແລະ ເປັນມິດ."
chat_sessions = {}

@app.route("/", methods=["GET"])
def home():
    return "WhatsApp AI Agent is Online 24/7!", 200

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.verify_token") == VERIFY_TOKEN:
        return request.args.get("hub.challenge"), 200
    return "Verification failed", 403

@app.route("/webhook", methods=["POST"])
def receive_message():
    data = request.get_json()
    try:
        entry = data["entry"][0]["changes"][0]["value"]
        if "messages" in entry:
            msg = entry["messages"][0]
            sender = msg["from"]
            if msg["type"] == "text":
                user_text = msg["text"]["body"]
                if sender not in chat_sessions:
                    chat_sessions[sender] = client.chats.create(
                        model="gemini-3.1-flash-lite",
                        config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT)
                    )
                reply = chat_sessions[sender].send_message(user_text).text
                
                requests.post(
                    f"https://graph.facebook.com/v21.0/{PHONE_NUMBER_ID}/messages",
                    headers={"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"},
                    json={"messaging_product": "whatsapp", "to": sender, "type": "text", "text": {"body": reply}}
                )
    except Exception as e:
        print(f"Error: {e}")
    return jsonify({"status": "ok"}), 200
