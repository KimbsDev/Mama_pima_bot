import json
import os
import requests
from flask import Flask, request
from config import OPENROUTER_API_KEY, WHATSAPP_TOKEN, PHONE_NUMBER_ID, VERIFY_TOKEN
from database import init_db
from accounts import handle_client_message
from dashboard import dashboard
from scheduler import start_scheduler

app = Flask(__name__)
app.secret_key = "mamapima_secret_key_2026"

# Register dashboard blueprint
app.register_blueprint(dashboard)

# Initialize database
init_db()

# Start scheduler for automatic reports
start_scheduler()

# Load restaurant data
with open("mama_pima.json", "r") as f:
    restaurant = json.load(f)

# Create system prompt
system_prompt = f"""
You are a friendly WhatsApp assistant for {restaurant['restaurant_name']}.
Location: {restaurant['location']}
Phone: {restaurant['phone']}
Open: {restaurant['open']} to {restaurant['close']}
Delivery available: {restaurant['delivery']}
Delivery areas: {', '.join(restaurant['delivery_areas'])}
Delivery fee: {restaurant['delivery_fee']} TZS
Today's special: {restaurant['daily_special']}

Menu:
{chr(10).join([f"- {item['name']}: {item['price']:,} TZS" for item in restaurant['menu']])}

Rules:
- Always reply in Swahili or English depending on the customer
- If asked for totals, calculate them accurately
- Be friendly and professional
- If customer wants to order, confirm their order and total price
- Always mention delivery fee when customer orders for delivery
"""

# Store chat history per user
user_histories = {}

# Owner phone number — messages from this number go to accounting
OWNER_PHONE = "+255749594915"

# Owner client ID
OWNER_CLIENT_ID = "mama_pima_owner"


def ask_mama_pima(user_id, message):
    if user_id not in user_histories:
        user_histories[user_id] = []

    user_histories[user_id].append({"role": "user", "content": message})

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json"
        },
        json={
            "model": "openai/gpt-4o-mini",
            "messages": [
                {"role": "system", "content": system_prompt},
                *user_histories[user_id]
            ]
        }
    )

    reply = response.json()["choices"][0]["message"]["content"]
    user_histories[user_id].append({"role": "assistant", "content": reply})
    return reply


def send_meta_reply(to, message):
    """Send reply back to customer via Meta Cloud API"""
    url = f"https://graph.facebook.com/v18.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": to,
        "type": "text",
        "text": {"body": message}
    }
    response = requests.post(url, headers=headers, json=payload)
    print(f"📤 Meta API response: {response.status_code}")


# ── Combined Webhook Route ──
@app.route("/webhook", methods=["GET", "POST"])
def webhook():

    # ── GET: Webhook Verification (Meta checks this first) ──
    if request.method == "GET":
        mode = request.args.get("hub.mode")
        token = request.args.get("hub.verify_token")
        challenge = request.args.get("hub.challenge")

        if mode == "subscribe" and token == VERIFY_TOKEN:
            print("✅ Webhook verified by Meta!")
            return challenge, 200
        else:
            print("❌ Webhook verification failed!")
            return "Forbidden", 403

    # ── POST: Receive Messages from WhatsApp ──
    elif request.method == "POST":
        try:
            data = request.get_json()

            entry = data["entry"][0]
            changes = entry["changes"][0]
            value = changes["value"]

            # Ignore non-message events
            if "messages" not in value:
                return "ok", 200

            message = value["messages"][0]

            # Only handle text messages
            if message.get("type") != "text":
                return "ok", 200

            sender = message["from"]
            text = message["text"]["body"]

            print(f"📩 From {sender}: {text}")

            # Check if message is from the OWNER (business accounting)
            if sender == OWNER_PHONE:
                reply = handle_client_message(OWNER_CLIENT_ID, text)
                if reply:
                    print(f"💼 Owner accounting reply: {reply}")
                    send_meta_reply(sender, reply)
                    return "ok", 200

            # Otherwise treat as customer message
            reply = ask_mama_pima(sender, text)
            print(f"🤖 Reply: {reply}")
            send_meta_reply(sender, reply)

        except Exception as e:
            print(f"Error: {e}")

        return "ok", 200


if __name__ == "__main__":
    print(f"🍽️  {restaurant['restaurant_name']} WhatsApp Bot is running!")
    print("🌐 Server started!")
    print("📊 Dashboard: /dashboard")
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
