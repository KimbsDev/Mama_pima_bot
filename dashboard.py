from flask import Blueprint, render_template_string, request, session, redirect, url_for
from database import get_today_transactions, get_summary, get_monthly_transactions
from datetime import datetime, timedelta
import json

dashboard = Blueprint('dashboard', __name__)

# Client passwords - add each client here
CLIENT_PASSWORDS = {
    "mama_pima_owner": "mama1234",
    # "pharmacy_client": "dawa1234",
}

DASHBOARD_HTML = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ business_name }} — Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #f0f2f5; color: #333; }
        
        .header {
            background: linear-gradient(135deg, #1a1a2e, #16213e);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .header h1 { font-size: 22px; }
        .header p { font-size: 12px; opacity: 0.7; margin-top: 5px; }

        .cards {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            padding: 20px;
        }

        .card {
            background: white;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }
        .card .label { font-size: 11px; color: #888; text-transform: uppercase; }
        .card .value { font-size: 20px; font-weight: bold; margin-top: 8px; }
        .card.income .value { color: #2e7d32; }
        .card.expense .value { color: #c62828; }
        .card.profit .value { color: #1565c0; }

        .section {
            background: white;
            margin: 0 20px 20px;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        }
        .section h2 {
            font-size: 14px;
            color: #1a1a2e;
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .transaction {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 0;
            border-bottom: 1px solid #f0f0f0;
            font-size: 13px;
        }
        .transaction:last-child { border-bottom: none; }
        .transaction .desc { color: #555; flex: 1; }
        .transaction .time { color: #aaa; font-size: 11px; margin: 0 10px; }
        .transaction .amount { font-weight: bold; }
        .transaction.income .amount { color: #2e7d32; }
        .transaction.expense .amount { color: #c62828; }
        .transaction .badge {
            font-size: 10px;
            padding: 2px 8px;
            border-radius: 20px;
            margin-right: 8px;
        }
        .badge.income { background: #e8f5e9; color: #2e7d32; }
        .badge.expense { background: #fce4ec; color: #c62828; }

        .empty { text-align: center; color: #aaa; padding: 20px; font-size: 13px; }

        .chart-container { position: relative; height: 200px; }

        .footer {
            text-align: center;
            padding: 20px;
            font-size: 11px;
            color: #aaa;
        }
    </style>
</head>
<body>

<div class="header">
    <h1>{{ business_name }}</h1>
    <p>📅 {{ today }} — Live Dashboard</p>
</div>

<!-- Summary Cards -->
<div class="cards">
    <div class="card income">
        <div class="label">💰 Mapato</div>
        <div class="value">{{ "{:,.0f}".format(summary.income) }}</div>
        <div class="label">TZS</div>
    </div>
    <div class="card expense">
        <div class="label">💸 Matumizi</div>
        <div class="value">{{ "{:,.0f}".format(summary.expenses) }}</div>
        <div class="label">TZS</div>
    </div>
    <div class="card profit">
        <div class="label">📈 {{ "Faida" if summary.profit >= 0 else "Hasara" }}</div>
        <div class="value">{{ "{:,.0f}".format(summary.profit|abs) }}</div>
        <div class="label">TZS</div>
    </div>
</div>

<!-- Chart -->
<div class="section">
    <h2>📊 Weekly Overview</h2>
    <div class="chart-container">
        <canvas id="weeklyChart"></canvas>
    </div>
</div>

<!-- Today's Transactions -->
<div class="section">
    <h2>📋 Today's Transactions</h2>
    {% if transactions %}
        {% for t in transactions %}
        <div class="transaction {{ t.type }}">
            <span class="badge {{ t.type }}">{{ "IN" if t.type == "income" else "OUT" }}</span>
            <span class="desc">{{ t.description|capitalize }}</span>
            <span class="time">{{ t.time[:5] }}</span>
            <span class="amount">{{ "{:,.0f}".format(t.amount) }} TZS</span>
        </div>
        {% endfor %}
    {% else %}
        <div class="empty">Hakuna transactions leo bado.</div>
    {% endif %}
</div>

<div class="footer">
    Powered by Kimbs Bot Business • Auto-refreshes every 60 seconds
</div>

<script>
// Weekly chart data
const weeklyData = {{ weekly_data | tojson }};

const ctx = document.getElementById('weeklyChart').getContext('2d');
new Chart(ctx, {
    type: 'bar',
    data: {
        labels: weeklyData.labels,
        datasets: [
            {
                label: 'Income',
                data: weeklyData.income,
                backgroundColor: 'rgba(46, 125, 50, 0.7)',
                borderRadius: 6,
            },
            {
                label: 'Expenses',
                data: weeklyData.expenses,
                backgroundColor: 'rgba(198, 40, 40, 0.7)',
                borderRadius: 6,
            }
        ]
    },
    options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { position: 'bottom' } },
        scales: { y: { beginAtZero: true } }
    }
});

// Auto refresh every 60 seconds
setTimeout(() => location.reload(), 60000);
</script>

</body>
</html>
'''

LOGIN_HTML = '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login — Kimbs Bot Business</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: 'Segoe UI', sans-serif; background: #1a1a2e; display: flex; justify-content: center; align-items: center; height: 100vh; }
        .box { background: white; padding: 40px; border-radius: 16px; width: 320px; text-align: center; }
        h2 { color: #1a1a2e; margin-bottom: 5px; }
        p { color: #888; font-size: 13px; margin-bottom: 25px; }
        input { width: 100%; padding: 12px; margin-bottom: 15px; border: 1px solid #ddd; border-radius: 8px; font-size: 14px; }
        button { width: 100%; padding: 12px; background: #1a1a2e; color: white; border: none; border-radius: 8px; font-size: 14px; cursor: pointer; }
        .error { color: #c62828; font-size: 12px; margin-bottom: 10px; }
    </style>
</head>
<body>
<div class="box">
    <h2>🤖 Kimbs Bot</h2>
    <p>Business Dashboard Login</p>
    {% if error %}<div class="error">{{ error }}</div>{% endif %}
    <form method="POST">
        <input type="text" name="client_id" placeholder="Client ID" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Login</button>
    </form>
</div>
</body>
</html>
'''


@dashboard.route('/dashboard/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        client_id = request.form.get('client_id')
        password = request.form.get('password')
        if client_id in CLIENT_PASSWORDS and CLIENT_PASSWORDS[client_id] == password:
            session['client_id'] = client_id
            return redirect(url_for('dashboard.show_dashboard'))
        error = "Invalid Client ID or Password"
    return render_template_string(LOGIN_HTML, error=error)


@dashboard.route('/dashboard')
def show_dashboard():
    if 'client_id' not in session:
        return redirect(url_for('dashboard.login'))

    client_id = session['client_id']
    today = datetime.now().strftime("%Y-%m-%d")
    summary_data = get_summary(client_id, today)

    # Get transactions
    raw_transactions = get_today_transactions(client_id)
    transactions = [
        {"type": t[0], "description": t[1], "amount": t[2], "time": t[3]}
        for t in raw_transactions
    ]

    # Weekly data for chart
    labels = []
    income_data = []
    expense_data = []

    for i in range(6, -1, -1):
        day = datetime.now() - timedelta(days=i)
        day_str = day.strftime("%Y-%m-%d")
        day_summary = get_summary(client_id, day_str)
        labels.append(day.strftime("%a"))
        income_data.append(day_summary["income"])
        expense_data.append(day_summary["expenses"])

    weekly_data = {
        "labels": labels,
        "income": income_data,
        "expenses": expense_data
    }

    class Summary:
        def __init__(self, d):
            self.income = d["income"]
            self.expenses = d["expenses"]
            self.profit = d["profit"]

    return render_template_string(
        DASHBOARD_HTML,
        business_name="Mama Pima Restaurant",
        today=datetime.now().strftime("%d %B %Y"),
        summary=Summary(summary_data),
        transactions=transactions,
        weekly_data=weekly_data
    )
