from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from twilio.rest import Client
from accounts import get_today_report
from datetime import datetime
import config

# List of all your clients
# Add each client here as you onboard them
CLIENTS = [
    {
        "id": "mama_pima_owner",        # Unique ID for this client
        "phone": "+255749594915",        # Client's WhatsApp number
        "name": "Mama Pima Restaurant",  # Business name
        "report_hour": 21,               # Send report at 9PM
        "report_minute": 0
    },
    # Add more clients here:
    # {
    #     "id": "pharmacy_client",
    #     "phone": "+255XXXXXXXXX",
    #     "name": "Dawa Plus Pharmacy",
    #     "report_hour": 20,
    #     "report_minute": 0
    # },
]


def send_whatsapp_message(to, message):
    """Send WhatsApp message via Twilio"""
    client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)
    client.messages.create(
        from_="whatsapp:+14155238886",
        body=message,
        to=f"whatsapp:{to}"
    )


def send_daily_report(client_id, phone, name):
    """Generate and send daily report to client"""
    print(f"📊 Sending daily report to {name}...")
    try:
        report = get_today_report(client_id)
        header = f"🌙 *RIPOTI YA USIKU — {name}*\n\n"
        send_whatsapp_message(phone, header + report)
        print(f"✅ Report sent to {name} ({phone})")
    except Exception as e:
        print(f"❌ Error sending report to {name}: {e}")


def start_scheduler():
    """Start the background scheduler for all clients"""
    scheduler = BackgroundScheduler()

    for client in CLIENTS:
        scheduler.add_job(
            func=send_daily_report,
            trigger=CronTrigger(
                hour=client["report_hour"],
                minute=client["report_minute"]
            ),
            args=[client["id"], client["phone"], client["name"]],
            id=f"report_{client['id']}",
            name=f"Daily Report — {client['name']}",
            replace_existing=True
        )
        print(f"⏰ Scheduled daily report for {client['name']} at {client['report_hour']}:{str(client['report_minute']).zfill(2)}")

    scheduler.start()
    print("✅ Scheduler started!")
    return scheduler
