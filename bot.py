import json
import requests
import os
from flask import Flask, request, Response
from twilio.twiml.messaging_response import MessagingResponse

# --- SECURE API KEY LOAD ---
# This pulls the key from Render's Environment Variables instead of a file
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY")

app = Flask(__name__)

# Load restaurant data
try:
    with open("mama_pima.json", "r") as f:
        restaurant = json.load(f)
except FileNotFoundError:
    restaurant = {"restaurant_name": "Mama Pima", "menu": []}

system_prompt = f"""
You are the Lead Manager at {restaurant.get('restaurant_name', 'Mama Pima')}.
Location: Arusha, Tanzania.
Goal: Take orders, answer questions, and calculate totals in Swahili or English.
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
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}", 
                "Content-Type": "application/json"
            },
            json={
                "model": "google/gemini-2.0-flash-001",
                "messages": [{"role": "system", "content": system_prompt}] + user_histories[user_id][-6:]
            }
        )
        
        # Extract the AI reply
        data = response.json()
        if "choices" in data:
            reply = data["choices"][0]["message"]["content"]
            user_histories[user_id].append({"role": "assistant", "content": reply})
            return reply
        else:
            return "Samahani, kuna tatizo la kiufundi. Jaribu tena baadae."

    except Exception as e:
        print(f"Error: {e}")
        return "Samahani, naona mfumo una shida kidogo. Jaribu tena."

@app.route("/webhook", methods=["POST"])
def receive_message():
    sender = request.values.get('From', '')
    incoming_msg = request.values.get('Body', '')
    
    # Get AI response
    reply = ask_mama_pima(sender, incoming_msg)
    
    # Return TwiML response to Twilio
    resp = MessagingResponse()
    resp.message(reply)
    return Response(str(resp), mimetype='text/xml')

if __name__ == "__main__":
    # Render requires the bot to listen on a specific port
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
