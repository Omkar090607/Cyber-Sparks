import os
import sqlite3
import random
import io
import requests
from datetime import datetime, timedelta
from flask import Flask, jsonify, send_from_directory, request, g, session, make_response

app = Flask(__name__)
app.secret_key = 'public_ledger_secure_key_2026'
DATABASE = 'ledger.db'

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
        db.row_factory = sqlite3.Row 
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def init_db():
    with app.app_context():
        db = get_db()
        cursor = db.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY, name TEXT, sector TEXT, ministry TEXT,
                state TEXT, alloc REAL, spent REAL, status TEXT,
                pct REAL, cmp REAL, start_date TEXT, end_date TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT, project_id TEXT,
                issue_type TEXT, description TEXT, evidence_link TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS national_schemes (
                id TEXT PRIMARY KEY, name TEXT, sector TEXT, launch_year INTEGER,
                alloc REAL, spent REAL, time_taken TEXT, status TEXT, pct REAL, website_url TEXT
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT, mobile TEXT UNIQUE, role TEXT DEFAULT 'admin'
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS otp_logs (
                mobile TEXT, otp TEXT, expiry DATETIME
            )
        ''')
        
        cursor.execute('SELECT COUNT(*) FROM projects')
        if cursor.fetchone()[0] == 0:
            print("\n[SYSTEM] Attempting to connect to LIVE data.gov.in servers...")
            try:
                api_url = "https://api.data.gov.in/resource/projects?api-key=YOUR_API_KEY&format=json"
                response = requests.get(api_url, timeout=3)
                response.raise_for_status() 
                pass 
            except Exception as e:
                print(f"[SYSTEM] ⚠️ Live API connection skipped ({e}).")
                print("[SYSTEM] 🟢 Engaging Secure Local Ledger (41 Verified Projects)...")
                
                initial_projects = [
                    ("P001", "Delhi-Mumbai Expressway", "Infrastructure", "MoRTH", "Multi-State", 98000, 72000, "active", 73, 65, "Mar 2019", "Dec 2024"),
                    ("P002", "BharatNet Phase 3", "IT/Telecom", "MoC", "National", 45000, 12000, "delayed", 26, 20, "Jun 2021", "Mar 2025"),
                    ("P003", "AIIMS Madurai Construction", "Healthcare", "MoHFW", "Tamil Nadu", 1977, 400, "review", 20, 15, "Dec 2020", "Oct 2026"),
                    ("P004", "Gaganyaan Manned Mission", "Science/Space", "Dept of Space", "Karnataka", 9023, 6500, "active", 72, 68, "Aug 2018", "Dec 2025"),
                    ("P005", "Mumbai-Ahmedabad Bullet Train", "Railways", "MoR", "Multi-State", 108000, 45000, "active", 41, 35, "Sep 2017", "Dec 2026"),
                    ("P006", "Chenab River Railway Bridge", "Railways", "MoR", "J&K", 1400, 1350, "complete", 96, 100, "Jan 2004", "Aug 2022"),
                    ("P007", "Navi Mumbai Int. Airport", "Aviation", "MoCA", "Maharashtra", 16000, 8000, "active", 50, 45, "Aug 2021", "Mar 2025"),
                    ("P008", "Polavaram Irrigation", "Agriculture", "MoWR", "Andhra Pradesh", 55000, 20000, "delayed", 36, 40, "Apr 2004", "Dec 2025"),
                    ("P009", "Zojila Tunnel", "Infrastructure", "MoRTH", "Ladakh", 6800, 3000, "active", 44, 40, "May 2018", "Dec 2026"),
                    ("P010", "Ken-Betwa River Link", "Water", "MoJS", "MP/UP", 44605, 5000, "review", 11, 5, "Mar 2021", "Dec 2029"),
                    ("P011", "Jewar International Airport", "Aviation", "MoCA", "UP", 29560, 12000, "active", 40, 38, "Nov 2021", "Dec 2024"),
                    ("P012", "Pune Metro Rail Project", "Urban Transport", "MoHUA", "Maharashtra", 11420, 8500, "active", 74, 80, "Dec 2016", "Mar 2025"),
                    ("P013", "Kashi Vishwanath Corridor", "Tourism", "MoT", "UP", 800, 800, "complete", 100, 100, "Mar 2019", "Dec 2021"),
                    ("P014", "Central Vista Redevelopment", "Urban Dev", "MoHUA", "Delhi", 20000, 15000, "active", 75, 80, "Feb 2021", "Dec 2026"),
                    ("P015", "Char Dham Highway", "Infrastructure", "MoRTH", "Uttarakhand", 12000, 9000, "active", 75, 78, "Dec 2016", "Dec 2024"),
                    ("P016", "Bengaluru Suburban Railway", "Railways", "MoR", "Karnataka", 15767, 2000, "delayed", 12, 10, "Oct 2020", "Dec 2026"),
                    ("P017", "Kudankulam Nuclear U3&4", "Energy", "DAE", "Tamil Nadu", 39849, 25000, "active", 62, 60, "Jun 2017", "Mar 2025"),
                    ("P018", "Subansiri Hydroelectric", "Energy", "MoP", "Arunachal/Assam", 20000, 18000, "active", 90, 95, "Jan 2005", "Mar 2024"),
                    ("P019", "Eastern Dedicated Freight", "Railways", "MoR", "Multi-State", 81459, 75000, "active", 92, 95, "Oct 2006", "Jun 2024"),
                    ("P020", "Western Dedicated Freight", "Railways", "MoR", "Multi-State", 100000, 85000, "active", 85, 90, "Oct 2006", "Dec 2024"),
                    ("P021", "Sagarmala Port Dev", "Shipping", "MoPSW", "Coastal", 800000, 200000, "active", 25, 20, "Jul 2015", "Dec 2035"),
                    ("P022", "Mumbai Trans Harbour Link", "Infrastructure", "MoRTH", "Maharashtra", 17843, 17843, "complete", 100, 100, "Apr 2018", "Jan 2024"),
                    ("P023", "Narmada Valley Project", "Water", "MoJS", "MP/Gujarat", 50000, 40000, "active", 80, 85, "Apr 1987", "Dec 2025"),
                    ("P024", "Kudankulam Nuclear U5&6", "Energy", "DAE", "Tamil Nadu", 50000, 10000, "review", 20, 15, "Jun 2021", "Mar 2027"),
                    ("P025", "Samruddhi Mahamarg", "Infrastructure", "MoRTH", "Maharashtra", 55000, 50000, "active", 90, 95, "Jan 2019", "Jul 2024"),
                    ("P026", "Delhi-Meerut RRTS", "Urban Transport", "MoHUA", "Delhi/UP", 30274, 18000, "active", 59, 60, "Mar 2019", "Jun 2025"),
                    ("P027", "Vizhinjam Seaport", "Shipping", "MoPSW", "Kerala", 7700, 6000, "active", 77, 80, "Dec 2015", "Dec 2024"),
                    ("P028", "Ahmedabad Metro Phase 2", "Urban Transport", "MoHUA", "Gujarat", 5384, 1500, "delayed", 27, 25, "Mar 2019", "Dec 2025"),
                    ("P029", "Patna Metro Rail", "Urban Transport", "MoHUA", "Bihar", 13365, 3000, "delayed", 22, 20, "Feb 2019", "Mar 2027"),
                    ("P030", "AIIMS Awantipora", "Healthcare", "MoHFW", "J&K", 1828, 500, "review", 27, 20, "Jan 2019", "Dec 2025"),
                    ("P031", "AIIMS Bilaspur", "Healthcare", "MoHFW", "Himachal", 1471, 1400, "complete", 95, 100, "Oct 2017", "Dec 2022"),
                    ("P032", "Great Nicobar Dev", "Urban Dev", "MHA", "A&N Islands", 72000, 1000, "review", 1, 1, "Mar 2021", "Dec 2030"),
                    ("P033", "Dibang Multipurpose", "Energy", "MoP", "Arunachal", 31876, 5000, "active", 15, 10, "Jul 2019", "Dec 2028"),
                    ("P034", "North East Gas Grid", "Energy", "MoPNG", "North East", 9265, 4000, "active", 43, 45, "Aug 2018", "Mar 2026"),
                    ("P035", "Ganga Expressway", "Infrastructure", "MoRTH", "UP", 36230, 15000, "active", 41, 40, "Dec 2021", "Dec 2025"),
                    ("P036", "Chennai-Bengaluru Exp", "Infrastructure", "MoRTH", "Multi-State", 18000, 6000, "active", 33, 30, "Jan 2021", "Dec 2024"),
                    ("P037", "Hyderabad Pharma City", "Industrial", "MoCI", "Telangana", 19000, 3000, "delayed", 15, 10, "Mar 2018", "Dec 2025"),
                    ("P038", "Dholera Smart City", "Urban Dev", "MoHUA", "Gujarat", 20000, 8000, "active", 40, 45, "Jan 2016", "Dec 2026"),
                    ("P039", "Bogibeel Bridge", "Railways", "MoR", "Assam", 5920, 5920, "complete", 100, 100, "Apr 2002", "Dec 2018"),
                    ("P040", "Atal Tunnel Rohtang", "Infrastructure", "MoRTH", "Himachal", 3200, 3200, "complete", 100, 100, "Jun 2010", "Oct 2020"),
                    ("P041", "Navi Mumbai Metro Line 1", "Urban Transport", "MoHUA", "Maharashtra", 3400, 3400, "complete", 100, 100, "May 2011", "Nov 2023")
                ]
                cursor.executemany('INSERT INTO projects VALUES (?,?,?,?,?,?,?,?,?,?,?,?)', initial_projects)
                db.commit()

        cursor.execute('SELECT COUNT(*) FROM national_schemes')
        if cursor.fetchone()[0] == 0:
            try:
                api_url_schemes = "https://api.data.gov.in/resource/schemes?api-key=YOUR_API_KEY&format=json"
                response = requests.get(api_url_schemes, timeout=3)
                response.raise_for_status()
                pass
            except Exception:
                schemes_data = [
                    ("S001", "Make in India", "Manufacturing", 2014, 15000, 12500, "Ongoing (10+ Yrs)", "Active", 83, "https://www.makeinindia.com/"),
                    ("S002", "Swachh Bharat Mission", "Sanitation", 2014, 130000, 128500, "5 Years", "Phase 1 Complete", 98, "https://swachhbharatmission.gov.in/"),
                    ("S003", "Smart Cities Mission", "Urban Dev", 2015, 48000, 39000, "9 Years", "Delayed", 81, "https://smartcities.gov.in/"),
                    ("S004", "Digital India", "IT/Telecom", 2015, 100000, 85000, "Ongoing", "Active", 85, "https://digitalindia.gov.in/"),
                    ("S005", "PM Awas Yojana (PMAY)", "Housing", 2015, 250000, 210000, "Ongoing", "Active", 84, "https://pmay-urban.gov.in/"),
                    ("S006", "Bharatmala Pariyojana", "Infrastructure", 2015, 535000, 380000, "9 Yrs (Target 2027)", "Delayed", 71, "https://morth.nic.in/bharatmala-pariyojana"),
                    ("S007", "PM Fasal Bima Yojana", "Agriculture", 2016, 136000, 130000, "Ongoing", "Active", 95, "https://pmfby.gov.in/"),
                    ("S008", "Ayushman Bharat", "Healthcare", 2018, 35000, 28000, "Ongoing", "Active", 80, "https://nha.gov.in/PM-JAY"),
                    ("S009", "PM-KISAN", "Agriculture", 2019, 320000, 315000, "Ongoing", "Active", 98, "https://pmkisan.gov.in/"),
                    ("S010", "Jal Jeevan Mission", "Water", 2019, 360000, 250000, "5 Years", "Active", 69, "https://jaljeevanmission.gov.in/"),
                    ("S011", "PM SVANidhi", "Microfinance", 2020, 10000, 8500, "4 Years", "Active", 85, "https://pmsvanidhi.mohua.gov.in/"),
                    ("S012", "PM Gati Shakti", "Infrastructure", 2021, 1000000, 450000, "3 Years", "Active", 45, "https://dpiit.gov.in/"),
                    ("S013", "Vibrant Villages", "Rural Dev", 2023, 4800, 1200, "1 Year", "Active", 25, "https://vibrantvillages.gov.in/"),
                    ("S014", "PM Mudra Yojana", "Finance", 2015, 300000, 280000, "Ongoing", "Active", 93, "https://www.mudra.org.in/"),
                    ("S015", "Startup India", "Business", 2016, 10000, 8500, "Ongoing", "Active", 85, "https://www.startupindia.gov.in/"),
                    ("S016", "PM Ujjwala Yojana", "Energy", 2016, 12800, 12500, "Ongoing", "Active", 97, "https://www.pmuy.gov.in/"),
                    ("S017", "UDAN Scheme", "Aviation", 2016, 4500, 3800, "Ongoing", "Active", 84, "https://www.aai.aero/en/services/udan"),
                    ("S018", "Khelo India", "Sports", 2018, 3165, 2900, "Ongoing", "Active", 91, "https://kheloindia.gov.in/"),
                    ("S019", "Poshan Abhiyaan", "Health", 2018, 9000, 7500, "Ongoing", "Active", 83, "https://poshanabhiyaan.gov.in/"),
                    ("S020", "PM KUSUM", "Agriculture", 2019, 34000, 15000, "Ongoing", "Delayed", 44, "https://pmkusum.mnre.gov.in/"),
                    ("S021", "PLI Scheme", "Manufacturing", 2020, 197000, 110000, "5 Years", "Active", 55, "https://www.investindia.gov.in/production-linked-incentives-schemes-india"),
                    ("S022", "PM Vishwakarma", "Skill Dev", 2023, 13000, 3000, "Ongoing", "Active", 23, "https://pmvishwakarma.gov.in/"),
                    ("S023", "e-Sanjeevani", "Healthcare", 2019, 1200, 1000, "Ongoing", "Active", 83, "https://esanjeevaniopd.in/"),
                    ("S024", "Samagra Shiksha", "Education", 2018, 37000, 32000, "Ongoing", "Active", 86, "https://samagra.education.gov.in/"),
                    ("S025", "AMRUT", "Urban Dev", 2015, 50000, 45000, "Ongoing", "Active", 90, "https://amrut.gov.in/"),
                    ("S026", "HRIDAY", "Urban Dev", 2015, 500, 480, "4 Years", "Complete", 96, "https://mohua.gov.in/"),
                    ("S027", "Beti Bachao Beti Padhao", "Women Emp", 2015, 1200, 1100, "Ongoing", "Active", 91, "https://wcd.nic.in/bbbp-schemes"),
                    ("S028", "Skill India Mission", "Skill Dev", 2015, 12000, 10500, "Ongoing", "Active", 87, "https://www.skillindiadigital.gov.in/"),
                    ("S029", "PM Jan Dhan Yojana", "Finance", 2014, 5000, 4800, "Ongoing", "Active", 96, "https://pmjdy.gov.in/"),
                    ("S030", "Atal Pension Yojana", "Finance", 2015, 2500, 2300, "Ongoing", "Active", 92, "https://npscra.nsdl.co.in/scheme-details.php"),
                    ("S031", "PM Jeevan Jyoti Bima", "Insurance", 2015, 1500, 1400, "Ongoing", "Active", 93, "https://financialservices.gov.in/beta/en/pmjjby"),
                    ("S032", "PM Suraksha Bima", "Insurance", 2015, 1000, 950, "Ongoing", "Active", 95, "https://financialservices.gov.in/beta/en/pmsby"),
                    ("S033", "Namami Gange", "Environment", 2014, 20000, 18000, "Ongoing", "Active", 90, "https://nmcg.nic.in/"),
                    ("S034", "Mission Indradhanush", "Healthcare", 2014, 8000, 7600, "Ongoing", "Active", 95, "https://nhm.gov.in/"),
                    ("S035", "Soil Health Card", "Agriculture", 2015, 568, 520, "Ongoing", "Active", 91, "https://soilhealth.dac.gov.in/"),
                    ("S036", "e-NAM", "Agriculture", 2016, 2000, 1800, "Ongoing", "Active", 90, "https://enam.gov.in/"),
                    ("S037", "PM Matsya Sampada", "Fisheries", 2020, 20050, 12000, "5 Years", "Active", 59, "https://pmmsy.dof.gov.in/"),
                    ("S038", "National Green Hydrogen", "Energy", 2023, 19744, 2000, "Ongoing", "Active", 10, "https://nghm.mnre.gov.in/"),
                    ("S039", "Stand-Up India", "Finance", 2016, 10000, 8500, "Ongoing", "Active", 85, "https://www.standupmitra.in/"),
                    ("S040", "Garib Kalyan Rojgar", "Employment", 2020, 50000, 39000, "1 Year", "Complete", 78, "https://rural.gov.in/"),
                    ("S041", "Deep Ocean Mission", "Science", 2021, 4077, 1200, "5 Years", "Active", 29, "https://moes.gov.in/"),
                    ("S042", "National Quantum Mission", "Science", 2023, 6003, 500, "8 Years", "Active", 8, "https://dst.gov.in/")
                ]
                cursor.executemany('INSERT INTO national_schemes VALUES (?,?,?,?,?,?,?,?,?,?)', schemes_data)
                db.commit()

def analyze_leakage(projects):
    anomalies = []
    for p in projects:
        if p['spent'] > p['alloc']:
            anomalies.append({"id": p['id'], "reason": "Over-budget Leakage", "severity": "High"})
        if p['spent'] > (p['alloc'] * 0.5) and p['cmp'] < 30:
            anomalies.append({"id": p['id'], "reason": "Fund Mismanagement Detected", "severity": "Critical"})
    return anomalies

@app.route('/api/ai/audit')
def ai_audit():
    db = get_db()
    projects = [dict(row) for row in db.execute('SELECT * FROM projects').fetchall()]
    anomalies = analyze_leakage(projects)
    return jsonify({"status": "AI Audit Complete", "anomalies_found": len(anomalies), "anomalies": anomalies, "trust_score": max(0, 100 - (len(anomalies) * 5))})

@app.route('/api/export/csv')
def export_data():
    db = get_db()
    projects = db.execute('SELECT * FROM projects').fetchall()
    output = "Project ID,Name,Ministry,State,Allocated Budget (Cr),Spent (Cr),Status,Completion %\n"
    for p in projects:
        output += f"{p['id']},{p['name']},{p['ministry']},{p['state']},{p['alloc']},{p['spent']},{p['status']},{p['cmp']}%\n"
    response = make_response(output)
    response.headers["Content-Disposition"] = "attachment; filename=PublicLedger_Audit_Report.csv"
    response.headers["Content-type"] = "text/csv"
    return response

@app.route('/api/ai/chat', methods=['POST'])
def ai_chat():
    data = request.get_json()
    user_msg = data.get('message', '').lower()
    db = get_db()
    projects = [dict(row) for row in db.execute('SELECT * FROM projects').fetchall()]
    schemes = [dict(row) for row in db.execute('SELECT * FROM national_schemes').fetchall()]

    if any(word in user_msg for word in ['csv', 'download', 'export', 'data file']):
        return jsonify({
            "response": "Here is the latest data export ready for you. 📥 <a href='/api/export/csv' style='color:var(--teal); font-weight:bold; text-decoration:underline;'>Click here to download the CSV ledger</a>."
        })

    if any(word in user_msg for word in ['graph', 'chart', 'visual', 'analytics']):
        return jsonify({
            "response": "I can show you advanced visual analytics for budget distribution and efficiency! Taking you to the Analytics Dashboard now...",
            "action": "NAVIGATE_ANALYTICS"
        })

    if any(word in user_msg for word in ['problem', 'issue', 'report', 'complain', 'fraud', 'leakage']):
        return jsonify({
            "response": "Transparency is our priority. If you have found a discrepancy, please file an official report. Navigating you to the Citizen Reporting Portal...",
            "action": "NAVIGATE_REPORT"
        })

    if any(word in user_msg for word in ['highest', 'top', 'most expensive', 'biggest']):
        sorted_p = sorted(projects, key=lambda x: x['alloc'], reverse=True)[:3]
        res = "Here are the top 3 highest budgeted projects currently active:<br><br>"
        for p in sorted_p:
            res += f"• **{p['name']}**: ₹{p['alloc']:,.0f} Cr<br>"
        return jsonify({"response": res})

    if "total budget" in user_msg or "total amount" in user_msg or "how much money" in user_msg:
        total_proj = sum(p['alloc'] for p in projects)
        total_sch = sum(s['alloc'] for s in schemes)
        return jsonify({
            "response": f"The total allocated budget for Government Projects is **₹{total_proj:,.0f} Cr** and for National Schemes is **₹{total_sch:,.0f} Cr**."
        })

    for p in projects:
        if p['name'].lower() in user_msg or (len(user_msg) > 4 and user_msg in p['name'].lower()):
            response_text = f"📊 **{p['name']}** ({p['sector']}): Managed by {p['ministry']} in {p['state']}.<br><br>💰 **Financials:** Allocated ₹{p['alloc']} Cr, Spent ₹{p['spent']} Cr.<br>📈 **Status:** Currently marked as **{p['status'].upper()}** with physical completion at {p['cmp']}%."
            return jsonify({"response": response_text})

    for s in schemes:
        if s['name'].lower() in user_msg or (len(user_msg) > 4 and user_msg in s['name'].lower()):
            response_text = f"🏛️ **{s['name']}** ({s['sector']}): Launched in {s['launch_year']}.<br><br>💰 **Financials:** Allocated ₹{s['alloc']} Cr, Spent ₹{s['spent']} Cr.<br>📈 **Status:** {s['status']} ({s['time_taken']})."
            return jsonify({"response": response_text})

    return jsonify({
        "response": "I can help you analyze data. You can ask me to 'download CSV', 'show graphs', 'find the highest budget', or 'report a problem'."
    })

@app.route('/api/auth/request-otp', methods=['POST'])
def request_otp():
    data = request.get_json()
    name = data.get('name')
    mobile = data.get('mobile')
    otp = str(random.randint(100000, 999999))
    expiry = datetime.now() + timedelta(minutes=5)
    db = get_db()
    db.execute('INSERT OR IGNORE INTO users (name, mobile) VALUES (?, ?)', (name, mobile))
    db.execute('INSERT INTO otp_logs (mobile, otp, expiry) VALUES (?, ?, ?)', (mobile, otp, expiry))
    db.commit()
    print(f"\n---> ADMIN LOGIN OTP FOR {mobile}: {otp} <---\n") 
    return jsonify({"status": "success", "message": "OTP sent"})

@app.route('/api/auth/verify-otp', methods=['POST'])
def verify_otp():
    data = request.get_json()
    mobile = data.get('mobile')
    otp_input = data.get('otp')
    db = get_db()
    cursor = db.execute('SELECT * FROM otp_logs WHERE mobile = ? AND otp = ? AND expiry > ?', (mobile, otp_input, datetime.now()))
    if cursor.fetchone():
        user = db.execute('SELECT * FROM users WHERE mobile = ?', (mobile,)).fetchone()
        session['user'] = {"name": user['name'], "mobile": user['mobile']}
        return jsonify({"status": "success", "user": dict(user)})
    else:
        return jsonify({"status": "error", "message": "Invalid OTP"}), 401

@app.route('/')
def index(): return send_from_directory('.', 'index.html')

@app.route('/<path:filename>')
def serve_static(filename): return send_from_directory('.', filename)

@app.route('/api/summary')
def api_summary():
    db = get_db()
    rows = db.cursor().execute('SELECT * FROM projects').fetchall()
    projects = []
    total_alloc, total_spent, completed_count = 0, 0, 0
    for row in rows:
        total_alloc += row['alloc']
        total_spent += row['spent']
        if row['status'] == 'complete': completed_count += 1
        projects.append(dict(row))
    return jsonify({"data": {"kpis": {"total_budget_cr": total_alloc, "total_spent_cr": total_spent, "projects_completed": completed_count, "projects_total": len(projects), "unspent_cr": total_alloc - total_spent, "fiscal_year": "FY 2025-26", "quarter": "Q1"}, "projects": projects}})

@app.route('/api/schemes')
def api_schemes():
    rows = get_db().cursor().execute('SELECT * FROM national_schemes ORDER BY launch_year DESC').fetchall()
    return jsonify({"data": [dict(row) for row in rows]})

@app.route('/api/report', methods=['POST'])
def submit_report():
    data = request.get_json()
    db = get_db()
    db.execute('INSERT INTO reports (project_id, issue_type, description, evidence_link) VALUES (?, ?, ?, ?)', (data.get('project_id'), data.get('issue_type'), data.get('description'), data.get('evidence_link', '')))
    db.commit()
    return jsonify({"status": "success", "message": "Report saved"}), 201

if __name__ == '__main__':
    init_db()
    print("\n--- PUBLIC LEDGER SERVER ACTIVE ---")
    app.run(debug=True, port=5000)