
from flask import Flask, request, redirect, session, render_template_string, flash
import sqlite3
import os
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.environ.get("TES_SECRET_KEY", "tes-demo-change-this-secret")

DB = "tes_database.db"

QUESTIONS = {
    "Reading": [
        {
            "q": "What is the main purpose of education?",
            "options": ["Earn money only", "Develop knowledge and skills", "Travel", "Sleep"],
            "answer": 1
        },
        {
            "q": "What does improve mean?",
            "options": ["Make better", "Make worse", "Forget", "Stop"],
            "answer": 0
        },
        {
            "q": "Which skill helps us understand written texts?",
            "options": ["Listening", "Speaking", "Reading", "Swimming"],
            "answer": 2
        }
    ],
    "Listening": [
        {
            "q": "The meeting starts at nine. When does it start?",
            "options": ["8:00", "9:00", "10:00", "11:00"],
            "answer": 1
        },
        {
            "q": "I would like a cup of tea. What does the speaker want?",
            "options": ["Coffee", "Water", "Tea", "Juice"],
            "answer": 2
        },
        {
            "q": "The library is next to the bank. Where is it?",
            "options": ["Behind school", "Next to the bank", "At the airport", "At home"],
            "answer": 1
        }
    ]
}

def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = connect()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            created_at TEXT
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            exam TEXT,
            skill TEXT,
            score INTEGER,
            total INTEGER,
            created_at TEXT
        )
    """)
    db.commit()
    db.close()

init_db()

def current_user():
    if "user_id" not in session:
        return None
    db = connect()
    user = db.execute(
        "SELECT * FROM users WHERE id=?",
        (session["user_id"],)
    ).fetchone()
    db.close()
    return user

def page(content, title="TES", **kwargs):
    user = current_user()
    return render_template_string(TEMPLATE,
        content=content,
        title=title,
        user=user,
        **kwargs
    )

TEMPLATE = """
<!DOCTYPE html>
<html lang="uz">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} | TES</title>
<style>
*{box-sizing:border-box}
body{margin:0;background:#f3f6fc;color:#17243b;font-family:Arial,sans-serif}
nav{background:#10264a;color:white;padding:17px 6%;display:flex;
justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px}
.logo{font-size:27px;font-weight:900;color:white;text-decoration:none}
.logo span{color:#60a5fa}
nav a{color:white;text-decoration:none;margin-left:16px;font-size:14px}
.hero{background:linear-gradient(120deg,#10264a,#2563a9);
color:white;padding:75px 8%;min-height:310px}
.hero h1{font-size:clamp(34px,5vw,55px);max-width:700px;margin:15px 0}
.hero p{color:#dbeafe;font-size:18px;max-width:600px}
.container{max-width:1100px;margin:35px auto;padding:0 20px}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:20px}
.card{background:white;padding:24px;border-radius:17px;
border:1px solid #e3e9f3;box-shadow:0 5px 20px #17243b08}
.card h2,.card h3{margin-top:5px}
.btn{display:inline-block;background:#2563eb;color:white;padding:12px 19px;
border:0;border-radius:9px;text-decoration:none;cursor:pointer;font-weight:bold}
.btn:hover{background:#1d4ed8}
.light{background:#eaf1ff;color:#1d4ed8}
input,textarea,select{width:100%;padding:13px;margin:8px 0 16px;
border:1px solid #d8e1ee;border-radius:9px;font-size:15px}
textarea{min-height:180px}
label{font-weight:600}
.option{display:block;padding:12px;background:#f4f7fc;
border-radius:9px;margin:8px 0;cursor:pointer}
.option input{width:auto;margin:0 8px 0 0}
footer{text-align:center;background:#10264a;color:#cbd5e1;padding:30px;margin-top:70px}
.muted{color:#64748b}
.stat{font-size:30px;font-weight:bold;color:#2563eb}
.flash{background:#fff1f2;color:#be123c;padding:12px;border-radius:9px;margin:10px 0}
.badge{color:#2563eb;font-weight:bold;font-size:13px}
@media(max-width:600px){nav{padding:15px}nav a{margin-left:7px}.hero{padding:50px 7%}}
</style>
</head>
<body>
<nav>
<a href="/" class="logo">TES<span>.</span></a>
<div>
{% if user %}
<a href="/dashboard">Dashboard</a>
<a href="/results">Natijalar</a>
<a href="/logout">Chiqish</a>
{% else %}
<a href="/">Bosh sahifa</a>
<a href="/login">Kirish</a>
<a href="/register">Ro'yxatdan o'tish</a>
{% endif %}
</div>
</nav>
{% with messages = get_flashed_messages() %}
{% if messages %}
<div class="container">
{% for message in messages %}<div class="flash">{{ message }}</div>{% endfor %}
</div>
{% endif %}
{% endwith %}
{{ content|safe }}
<footer>
<h2>TES — TESTING EDUCATION SYSTEM</h2>
<p>Test. Learn. Achieve.</p>
<p>IELTS • CEFR • MOCK EXAMS</p>
</footer>
</body>
</html>
"""

@app.route("/")
def home():
    content = """
    <section class="hero">
      <div class="badge" style="color:#bfdbfe">IELTS • CEFR • MOCK EXAMS</div>
      <h1>Welcome to TES!</h1>
      <p>Ingliz tilini o'rganing, bilimingizni sinang va maqsadingizga erishing.</p>
      <a class="btn" href="/register">Boshlash →</a>
    </section>
    <div class="container">
      <h2 style="text-align:center">Bizning imtihonlarimiz</h2>
      <div class="grid">
        <div class="card"><h2>🌍 IELTS</h2>
        <p>Academic va General tayyorgarlik.</p>
        <a class="btn" href="/register">Tanlash</a></div>
        <div class="card"><h2>🎓 CEFR</h2>
        <p>A1, A2, B1, B2 va C1 darajalariga tayyorgarlik.</p>
        <a class="btn" href="/register">Tanlash</a></div>
      </div>
      <h2 style="margin-top:45px">4 ta asosiy ko'nikma</h2>
      <div class="grid">
        <div class="card">📖 <h3>Reading</h3><p>Matnni tushunish.</p></div>
        <div class="card">🎧 <h3>Listening</h3><p>Eshitib tushunish.</p></div>
        <div class="card">✍️ <h3>Writing</h3><p>Yozma nutq.</p></div>
        <div class="card">🎙️ <h3>Speaking</h3><p>Og'zaki nutq.</p></div>
      </div>
    </div>
    """
    return page(content, "Bosh sahifa")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not name or not email or len(password) < 8:
            flash("Ma'lumotlarni to'ldiring. Parol kamida 8 ta belgi bo'lsin.")
            return redirect("/register")

        db = connect()
        try:
            cur = db.execute(
                "INSERT INTO users(name,email,password,created_at) VALUES(?,?,?,?)",
                (name, email, generate_password_hash(password),
                 datetime.now().isoformat())
            )
            db.commit()
            session.clear()
            session["user_id"] = cur.lastrowid
            return redirect("/dashboard")
        except sqlite3.IntegrityError:
            flash("Bu email allaqachon ro'yxatdan o'tgan.")
        finally:
            db.close()

    content = """
    <div class="container" style="max-width:450px">
    <div class="card">
    <h2>TES hisob yaratish</h2>
    <p class="muted">Platformadan foydalanish uchun ro'yxatdan o'ting.</p>
    <form method="POST">
    <label>Ism va familiya</label>
    <input name="name" required placeholder="Ismingiz">
    <label>Email</label>
    <input name="email" type="email" required placeholder="Email">
    <label>Parol</label>
    <input name="password" type="password" minlength="8" required placeholder="Kamida 8 belgi">
    <button class="btn" style="width:100%">Ro'yxatdan o'tish</button>
    </form>
    <p>Hisobingiz bormi? <a href="/login">Kirish</a></p>
    </div></div>
    """
    return page(content, "Ro'yxatdan o'tish")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        db = connect()
        user = db.execute(
            "SELECT * FROM users WHERE email=?", (email,)
        ).fetchone()
        db.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            return redirect("/dashboard")

        flash("Email yoki parol noto'g'ri.")

    content = """
    <div class="container" style="max-width:450px">
    <div class="card">
    <h2>TES hisobiga kirish</h2>
    <form method="POST">
    <label>Email</label><input name="email" type="email" required>
    <label>Parol</label><input name="password" type="password" required>
    <button class="btn" style="width:100%">Kirish</button>
    </form>
    <p>Hisobingiz yo'qmi? <a href="/register">Ro'yxatdan o'tish</a></p>
    </div></div>
    """
    return page(content, "Login")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect("/login")

    content = f"""
    <div class="container">
    <h1>Xush kelibsiz, {user['name']}!</h1>
    <p class="muted">TES shaxsiy kabinetingiz</p>
    <h2 style="margin-top:35px">Imtihonni tanlang</h2>
    <div class="grid">
    <div class="card"><h2>🌍 IELTS</h2>
    <p>IELTS imtihoniga tayyorgarlik.</p>
    <a class="btn" href="/exam/IELTS">Boshlash</a></div>
    <div class="card"><h2>🎓 CEFR</h2>
    <p>CEFR darajalari bo'yicha tayyorgarlik.</p>
    <a class="btn" href="/exam/CEFR">Boshlash</a></div>
    </div>
    <div class="card" style="margin-top:25px">
    <h2>⭐ Premium</h2>
    <p>Premium imkoniyatlar tez orada qo'shiladi.</p>
    <span class="badge">COMING SOON</span>
    </div>
    </div>
    """
    return page(content, "Dashboard")

@app.route("/exam/<exam>")
def exam(exam):
    if not current_user():
        return redirect("/login")
    if exam not in ["IELTS", "CEFR"]:
        return redirect("/dashboard")

    skills = [
        ("Reading", "📖", "Matnlarni o'qish va tushunish"),
        ("Listening", "🎧", "Eshitib tushunish"),
        ("Writing", "✍️", "Yozma topshiriqlar"),
        ("Speaking", "🎙️", "Og'zaki nutq")
    ]
    cards = ""
    for skill, icon, desc in skills:
        cards += f"""
        <div class="card">
        <h2>{icon} {skill}</h2><p>{desc}</p>
        <a class="btn" href="/practice/{exam}/{skill}">Boshlash</a>
        </div>
        """

    content = f"""
    <div class="container">
    <a href="/dashboard">← Orqaga</a>
    <h1>{exam} tayyorgarlik</h1>
    <div class="grid">{cards}</div>
    </div>
    """
    return page(content, exam)

@app.route("/practice/<exam>/<skill>", methods=["GET", "POST"])
def practice(exam, skill):
    user = current_user()
    if not user:
        return redirect("/login")

    if exam not in ["IELTS", "CEFR"]:
        return redirect("/dashboard")

    if skill not in ["Reading", "Listening", "Writing", "Speaking"]:
        return redirect("/dashboard")

    if skill in ["Reading", "Listening"]:
        questions = QUESTIONS[skill]

        if request.method == "POST":
            score = 0
            for i, q in enumerate(questions):
                selected = request.form.get(f"q{i}")
                if selected is not None and selected.isdigit():
                    if int(selected) == q["answer"]:
                        score += 1

            db = connect()
            db.execute(
                """INSERT INTO results(user_id,exam,skill,score,total,created_at)
                VALUES(?,?,?,?,?,?)""",
                (user["id"], exam, skill, score, len(questions),
                 datetime.now().isoformat())
            )
            db.commit()
            db.close()

            session["last_result"] = {
                "exam": exam, "skill": skill,
                "score": score, "total": len(questions)
            }
            return redirect("/result")

        question_html = ""
        for i, q in enumerate(questions):
            options = ""
            for j, option in enumerate(q["options"]):
                options += f"""
                <label class="option">
                <input type="radio" name="q{i}" value="{j}" required>
                {chr(65+j)}. {option}
                </label>
                """
            question_html += f"""
            <div class="card" style="margin:18px 0">
            <h3>{i+1}. {q['q']}</h3>{options}
            </div>
            """

        content = f"""
        <div class="container">
        <a href="/exam/{exam}">← Orqaga</a>
        <h1>{exam} — {skill}</h1>
        <p class="muted">Barcha savollarga javob bering.</p>
        <form method="POST">
        {question_html}
        <button class="btn">Testni yakunlash</button>
        </form>
        </div>
        """
        return page(content, skill)

    if skill == "Writing":
        prompt = "Some people believe that online education is better than traditional education. Discuss both views and give your opinion."
    else:
        prompt = "Describe a skill you would like to learn. Explain why you want to learn it and how you would learn it."

    content = f"""
    <div class="container">
    <a href="/exam/{exam}">← Orqaga</a>
    <div class="card">
    <h1>{exam} — {skill}</h1>
    <h3>Topshiriq</h3>
    <p>{prompt}</p>
    {"<textarea placeholder='Essay yozing...'></textarea>" if skill == "Writing" else "<p>Speaking uchun ushbu mavzu bo'yicha ovoz chiqarib javob bering.</p>"}
    <p class="muted">Bu demo versiyada AI baholash va javoblarni saqlash hali ulanmagan.</p>
    </div></div>
    """
    return page(content, skill)

@app.route("/result")
def result():
    user = current_user()
    if not user:
        return redirect("/login")

    data = session.get("last_result")
    if not data:
        return redirect("/results")

    content = f"""
    <div class="container" style="max-width:600px">
    <div class="card" style="text-align:center">
    <h1>🎉 Test yakunlandi!</h1>
    <p>{data['exam']} • {data['skill']}</p>
    <div class="stat">{data['score']} / {data['total']}</div>
    <p>To'g'ri javoblar</p>
    <a class="btn" href="/results">Natijalarim</a>
    <a class="btn light" href="/dashboard">Kabinet</a>
    </div></div>
    """
    return page(content, "Natija")

@app.route("/results")
def results():
    user = current_user()
    if not user:
        return redirect("/login")

    db = connect()
    rows = db.execute(
        "SELECT * FROM results WHERE user_id=? ORDER BY id DESC",
        (user["id"],)
    ).fetchall()
    db.close()

    records = ""
    for row in rows:
        records += f"""
        <div class="card">
        <b>{row['exam']} — {row['skill']}</b>
        <p class="stat">{row['score']} / {row['total']}</p>
        <small>{row['created_at'][:16]}</small>
        </div>
        """

    content = f"""
    <div class="container">
    <h1>Mening natijalarim</h1>
    <div class="grid">{records or '<p>Hozircha natijalar mavjud emas.</p>'}</div>
    </div>
    """
    return page(content, "Natijalar")

if __name__ == "__main__":
    app.run(debug=True, port=5000)
