import re
from database import save_transaction, get_today_transactions, get_summary
from datetime import datetime

def parse_transaction(message):
    """
    Understand what client typed and extract amount
    
    Examples client can type:
    - "namenunua unga 5kg = 15000"
    - "nimemuza pilau 2 = 14000"
    - "expense: mafuta 8000"
    - "income: chips 4000"
    - "bought rice = 5000"
    - "sold juice = 2000"
    """
    message = message.lower().strip()

    # Detect transaction type
    income_keywords = ["nimemuza", "sold", "income", "mapato", "niliuza", "uza"]
    expense_keywords = ["namenunua", "bought", "expense", "matumizi", "niliununua", "nunua", "niliagiza"]

    transaction_type = None
    for word in income_keywords:
        if word in message:
            transaction_type = "income"
            break

    if not transaction_type:
        for word in expense_keywords:
            if word in message:
                transaction_type = "expense"
                break

    if not transaction_type:
        return None

    # Extract amount (any number in the message)
    amounts = re.findall(r'\d+(?:,\d+)?(?:\.\d+)?', message.replace(",", ""))
    if not amounts:
        return None

    amount = float(max(amounts, key=lambda x: float(x)))

    # Description is the full message
    description = message

    return {
        "type": transaction_type,
        "amount": amount,
        "description": description
    }


def handle_client_message(client_id, message):
    """
    Handle messages from the BUSINESS OWNER (client)
    Returns a reply to send back
    """
    message_lower = message.lower().strip()

    # Check if asking for today's report
    report_keywords = ["ripoti", "report", "summary", "muhtasari", "leo", "today", 
                      "faida", "profit", "hasara", "loss", "jumla", "total"]
    
    if any(word in message_lower for word in report_keywords):
        return get_today_report(client_id)

    # Try to parse as a transaction
    transaction = parse_transaction(message)
    
    if transaction:
        save_transaction(
            client_id,
            transaction["type"],
            transaction["description"],
            transaction["amount"]
        )
        
        if transaction["type"] == "income":
            return (
                f"✅ Mapato yamehifadhiwa!\n"
                f"💰 Kiasi: {transaction['amount']:,.0f} TZS\n"
                f"📝 {transaction['description']}\n\n"
                f"Type 'ripoti' kuona muhtasari wa leo."
            )
        else:
            return (
                f"✅ Matumizi yamehifadhiwa!\n"
                f"💸 Kiasi: {transaction['amount']:,.0f} TZS\n"
                f"📝 {transaction['description']}\n\n"
                f"Type 'ripoti' kuona muhtasari wa leo."
            )
    
    return None


def get_today_report(client_id):
    """Generate today's financial report"""
    today = datetime.now().strftime("%Y-%m-%d")
    summary = get_summary(client_id, today)
    transactions = get_today_transactions(client_id)

    # Build transaction list
    income_list = ""
    expense_list = ""
    
    for t in transactions:
        type_, desc, amount, time = t
        if type_ == "income":
            income_list += f"  ✅ {time[:5]} - {amount:,.0f} TZS\n"
        else:
            expense_list += f"  💸 {time[:5]} - {amount:,.0f} TZS\n"

    profit_emoji = "📈" if summary["profit"] >= 0 else "📉"
    profit_word = "FAIDA" if summary["profit"] >= 0 else "HASARA"

    report = f"""
📊 *RIPOTI YA LEO*
📅 {datetime.now().strftime("%d/%m/%Y")}
{'─' * 25}

💰 *MAPATO (Income)*
{income_list if income_list else '  Hakuna mapato bado\n'}
💸 *MATUMIZI (Expenses)*
{expense_list if expense_list else '  Hakuna matumizi bado\n'}
{'─' * 25}
💰 Jumla Mapato: {summary['income']:,.0f} TZS
💸 Jumla Matumizi: {summary['expenses']:,.0f} TZS
{profit_emoji} {profit_word}: {abs(summary['profit']):,.0f} TZS
{'─' * 25}
"""
    return report.strip()
