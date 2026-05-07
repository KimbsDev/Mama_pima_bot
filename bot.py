import json
import requests
import os
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse
from config import OPENROUTER_API_KEY

app = Flask(__name__)

# Load restaurant data
try:
    with open("mama_pima.json", "r") as f:
        restaurant = json.load(f)
except FileNotFoundError:
    restaurant = {"restaurant_name": "Mama Pima", "menu": []}

system_prompt = f"""
You are the Lead Manager at {restaurant.get('restaurant_name', 'Mama Pima')}.
Location: Arusha.
Goal: Take orders, answer questions, and calculate totals.
Menu: {restaurant.get('menu', [])}
Always show the GRAND TOTAL for orders. 
"""

user_histories = {}

def ask_mama_pima(user_id, message):
    if user_id not in user_histories:
        user_histories[user_id] = []
    user_histories[user_id].append({"role": "user", "content": message})
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENROUTER_API_KEY}", "Content-Type": "application/json"},
            json={
                "model": "google/gemini-2.0-flash-001",
                "messages": [{"role": "system", "content": system_prompt}] + user_histories[user_id][-6:]
            }
        )
        reply = response.json()["choices"][0]["message"]["content"]
        user_histories[user_id].append({"role": "assistant", "content": reply})
        return reply
    except Exception as e:
        return "Samahani, jaribu tena."

@app.route("/webhook", methods=["POST"])
def receive_message():
    sender = request.values.get('From', '')
    incoming_msg = request.values.get('Body', '')
    reply = ask_mama_pima(sender, incoming_msg)
    
    resp = MessagingResponse()
    resp.message(reply)
    return Response(str(resp), mimetype='text/xml')

if __name__ == "__main__":
    # This 'port' part is CRITICAL for Render/Cloud hosting
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)