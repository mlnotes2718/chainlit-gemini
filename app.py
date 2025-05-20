# app.py
# Single-service integration of Gemini API with Chainlit frontend and Flask backend.
# Deploy on Render.com with command:
#    chainlit run app.py --host 0.0.0.0 --port $PORT
# Ensure GEMINI_API_KEY  is set in environment.

import os
import threading
import time

from flask import Flask, request, jsonify
from google import genai

import chainlit as cl
import httpx

# Load OpenAI API key
gemini_api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=gemini_api_key)

# Create Flask backend
flask_app = Flask(__name__)
model = "gemini-2.0-flash"

@flask_app.route("/chat", methods=["POST"])
def chat_endpoint():
    data = request.get_json()
    user_msg = data.get("message", "")
    # Basic chat call to Response API
    response = client.models.generate_content(model=model,contents=user_msg,)
    reply = response.text
    return jsonify({"response": reply})

# Function to run Flask app in a background thread
def run_flask():
    port = int(os.getenv("FLASK_PORT", 5000))
    flask_app.run(host="0.0.0.0", port=port)

# Start Flask server
threading.Thread(target=run_flask, daemon=True).start()
# Give Flask a moment to start up
time.sleep(1)

# Chainlit message handler
def send_chainlit_message(content: str):
    return cl.Message(content=content)

@cl.on_message
async def handle_message(message: cl.Message):
    flask_port = os.getenv("FLASK_PORT", "5000")
    url = f"http://localhost:{flask_port}/chat"

    timeout = httpx.Timeout(read=30.0, connect=5.0, write=10.0, pool=5.0)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, json={"message": message.content})
        data = resp.json()
    await cl.Message(content=data["response"]).send()
