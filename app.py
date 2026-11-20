import os
import sqlite3
from functools import wraps
from flask import Flask, request, redirect, url_for, session, flash, render_template_string, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-production")
DATABASE = os.environ.get("DATABASE_PATH", "tes.db")

def db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(error=None):
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()

def init_db():
    conn = sqlite3.connect(DATABASE)
    conn.execute("""CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS writing_submissions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        prompt TEXT NOT NULL,
        answer TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )""")
    conn.commit()
    conn.close()

def current_user():
    if "user_id" not in session:
        return None
    return db().execute("SELECT id, username FROM users WHERE id = ?", (session["user_id"],)).fetchone()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not current_user():
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

BASE = """
<!doctype html>
<html lang="uz">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{ title }} | TES</title>
<style>
:root{--bg:#0b1020;--panel:#141c32;--panel2:#1b2742;--text:#eef3ff;--muted:#aab6d3;--accent:#7c9cff;--line:#2b3858}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(135deg,#0b1020,#111b32);color:var(--text);font-family:Arial,sans-serif;min-height:100vh}
nav{display:flex;justify-content:space-between;align-items:center;padding:18px max(5%,calc((100% - 1100px)/2));border-bottom:1px solid var(--line);background:#0b1020}
.brand{font-size:22px;font-weight:800;color:white;text-decoration:none}.brand span{color:var(--accent)}
nav a{color:var(--muted);text-decoration:none;margin-left:16px}.wrap{max-width:1000px;margin:34px auto;padding:0 18px}
.card{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:24px;margin:16px 0;box-shadow:0 12px 35px #0003}
h1,h2,h3{margin-top:0}p{color:var(--muted);line-height:1.6}
.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
.btn,button{display:inline-block;background:var(--accent);color:#081126;border:0;border-radius:10px;padding:12px 17px;font-weight:700;text-decoration:none;cursor:pointer}
.btn.secondary{background:var(--panel2);color:var(--text);border:1px solid var(--line)}
input,textarea{width:100%;padding:13px;border-radius:10px;border:1px solid var(--line);background:#0d1528;color:white;margin:8px 0 16px;font:inherit}
textarea{min-height:190px;resize:vertical}label{font-weight:700}
.notice{background:#263653;padding:12px;border-radius:10px;margin:12px 0;color:#fff}
.q{padding:16px;background:#10192d;border:1px solid var(--line);border-radius:12px;margin:14px 0}
.q label{display:block;font-weight:400;margin:9px 0;color:var(--muted)}
small,.muted{color:var(--muted)}.topline{display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap}
@media(max-width:600px){nav{padding:14px;align-items:flex-start}nav a{margin-left:8px;font-size:13px}.card{padding:18px}.wrap{margin:20px auto}}
</style>
</head>
<body>
<nav><a class="brand" href="{{ url_for('home') }}">TES<span>.</span></a>
<div>{% if user %}<a href="{{ url_for('home') }}">Bosh sahifa</a><a href="{{ url_for('logout') }}">Chiqish</a>{% else %}<a href="{{ url_for('login') }}">Kirish</a><a href="{{ url_for('register') }}">Ro‘yxatdan o‘tish</a>{% endif %}</div>
</nav>
<div class="wrap">
{% with messages = get_flashed_messages() %}{% for message in messages %}<div class="notice">{{ message }}</div>{% endfor %}{% endwith %}
{{ content|safe }}
</div>
</body></html>
"""

def page(title, body):
    return render_template_string(BASE, title=title, content=body, user=current_user())

READING = [
("The city library has extended its opening hours. It now closes at 8 pm on weekdays.", "What changed at the library?", ["It opens later","It closes later","It moved location","It is free"], 1),
("Maya cycles to work because it is cheaper than taking the bus and helps her stay active.", "Why does Maya cycle to work?", ["It is faster than a train","It is required by her job","It saves money and keeps her active","Her bus route stopped"], 2),
("The museum's photography exhibition will remain open until 14 June.", "When does the exhibition end?", ["4 June","14 June","24 June","14 July"], 1),
("Students should submit their projects through the online portal, not by email.", "How should students submit projects?", ["By post","In person","By email","Through the online portal"], 3),
("Although the weather was cold, the outdoor concert attracted a large crowd.", "What happened at the concert?", ["Few people attended","It was cancelled","Many people attended","It moved indoors"], 2),
("The new café offers discounts to customers who bring a reusable cup.", "Who can receive a discount?", ["Customers with reusable cups","All new customers","Only staff","People ordering tea"], 0),
("The train to Oxford is delayed because of engineering work near the station.", "Why is the train delayed?", ["Bad weather","Engineering work","A staff meeting","An accident on the road"], 1),
("Lena chose the evening course because she works during the day.", "Why did Lena choose the evening course?", ["It is cheaper","Her friends attend","She works in the daytime","She prefers online lessons"], 2),
("The sports centre will be closed on Monday for routine maintenance.", "When will the sports centre be closed?", ["Sunday","Monday","Tuesday","All week"], 1),
("Visitors are advised to book tickets online to avoid waiting at the entrance.", "Why book online?", ["Tickets are always free","The entrance is closed","To avoid waiting","To get a guided tour"], 2),
("The school garden project encourages pupils to grow vegetables and learn about nature.", "What is the project designed to do?", ["Teach cooking only","Encourage gardening and learning about nature","Raise money for sports","Replace science lessons"], 1),
("A local bus service has added two routes to connect villages with the hospital.", "What is the purpose of the new routes?", ["To connect villages to the hospital","To take tourists to the beach","To replace trains","To serve the airport"], 0),
("The book club meets on the first Thursday of every month in Room 12.", "Where does the book club meet?", ["Room 2","The library café","Room 12","The main hall"], 2),
("Customers can return unused items within 30 days if they keep the receipt.", "What is needed to return an item?", ["Original packaging only","A receipt","A membership card","A bank statement"], 1),
("The science centre is offering free workshops during the school holidays.", "When are the workshops available?", ["Every weekend","During school holidays","Only in winter","After school on Fridays"], 1),
("Nadia downloaded the app to track her spending and plan a monthly budget.", "What does Nadia use the app for?", ["Learning languages","Tracking spending and budgeting","Finding a job","Booking flights"], 1),
("The park's lake is temporarily closed while workers repair the walking path.", "Why is the lake area closed?", ["The water is polluted","A festival is taking place","Workers are repairing a path","There are no staff"], 2),
("The language exchange pairs local learners with international students for conversation practice.", "What is the main activity?", ["Written exams","Conversation practice","Sports training","Music lessons"], 1),
("The company introduced flexible start times to help employees manage family responsibilities.", "Why were flexible start times introduced?", ["To reduce office space","To help with family responsibilities","To increase travel","To shorten lunch breaks"], 1),
("The community centre needs volunteers to help organise its annual book fair.", "What help is needed?", ["Painting classrooms","Organising a book fair","Teaching swimming","Repairing computers"], 1),
("Researchers found that short breaks can help people maintain concentration during long tasks.", "What can short breaks help people do?", ["Work without sleep","Maintain concentration","Finish every task instantly","Avoid learning"], 1),
("The coastal path offers excellent views, but walkers should check the tide times before setting out.", "What should walkers check?", ["Bus timetables","The weather forecast only","Tide times","Museum opening hours"], 2),
("The restaurant has introduced a separate menu for customers who do not eat meat.", "What is new at the restaurant?", ["A larger dining room","A vegetarian menu","A breakfast service","A delivery charge"], 1),
("After the first trial, the school decided to make the reading programme available to all year groups.", "What did the school decide?", ["End the programme","Limit it to older pupils","Offer it to all year groups","Move it online"], 2),
("The travel grant covers transport costs, but students must pay for their own accommodation.", "What does the grant pay for?", ["Accommodation","Meals","Transport","Books"], 2),
("The town's new recycling centre accepts paper, glass, metal and small electrical items.", "Which item can be recycled there?", ["Large furniture","Small electrical items","Food leftovers","Clothing only"], 1),
("Amir prefers studying in the morning because he finds it easier to remember new information then.", "Why does Amir study in the morning?", ["The library is quieter","He remembers information more easily","His classes are cancelled","His friends study then"], 1),
("The festival organisers moved the event indoors due to the forecast of heavy rain.", "Why was the event moved indoors?", ["The venue was cheaper","Heavy rain was expected","There were too few visitors","The performers requested it"], 1),
("The online course includes weekly quizzes, recorded lessons and a discussion forum.", "Which feature is included?", ["Daily face-to-face classes","A discussion forum","Free accommodation","Printed newspapers"], 1),
("Passengers travelling with bicycles must use the designated carriage near the rear of the train.", "Where should cyclists go?", ["The front carriage","Any empty seat","The designated rear carriage","The station office"], 2),
("The charity shop uses its profits to fund after-school activities for children.", "What are the profits used for?", ["Buying new cars","After-school activities","Building a hospital","Paying travel costs"], 1),
("The report recommends planting more trees along busy streets to improve air quality.", "What does the report recommend?", ["Closing all streets","Planting more trees","Building more car parks","Removing public transport"], 1),
("The hotel offers guests a free shuttle to the airport every hour between 5 am and 10 am.", "How often does the shuttle run?", ["Every 30 minutes","Every hour","Every two hours","Only once"], 1),
("The university postponed the lecture because the guest speaker's flight was cancelled.", "Why was the lecture postponed?", ["The room was unavailable","The speaker's flight was cancelled","Students requested a change","The topic changed"], 1),
("The gardening course is suitable for beginners and does not require any previous experience.", "Who can join the course?", ["Experienced gardeners only","People with a degree","Beginners","Professional farmers only"], 2),
]

WRITING_PROMPTS = [
    "Some people believe that students should do more group projects. Do you agree or disagree?",
    "Describe a skill you would like to learn and explain why it is useful.",
    "Many people prefer studying online, while others prefer classroom learning. Discuss both views."
]

@app.route("/")
def home():
    user = current_user()
    if not user:
        body = """
        <div class="card"><h1>Testing Education System</h1>
        <p>CEFR va IELTS tayyorgarligi uchun qulay platforma.</p>
        <a class="btn" href="/register">Boshlash</a>
        <a class="btn secondary" href="/login">Kirish</a></div>"""
    else:
        body = f"""
        <div class="card"><div class="topline"><div><h1>Salom, {user['username']}!</h1><p>Bugun qaysi bo‘limda mashq qilamiz?</p></div><div class="muted">TES • Practice</div></div></div>
        <div class="grid">
          <div class="card"><h2>CEFR Reading</h2><p>35 ta savol · 60 daqiqa</p><a class="btn" href="/practice/CEFR/Reading">Boshlash</a></div>
          <div class="card"><h2>CEFR Listening</h2><p>Matnni tinglab mashq qiling.</p><a class="btn" href="/practice/CEFR/Listening">Boshlash</a></div>
          <div class="card"><h2>CEFR Writing</h2><p>Yozma javobingizni saqlang.</p><a class="btn" href="/practice/CEFR/Writing">Boshlash</a></div>
          <div class="card"><h2>CEFR Speaking</h2><p>Mikrofon orqali mashqni yozib oling.</p><a class="btn" href="/practice/CEFR/Speaking">Boshlash</a></div>
          <div class="card"><h2>IELTS</h2><p>Bu bo‘lim keyingi bosqichda to‘ldiriladi.</p><span class="muted">Tez orada</span></div>
        </div>"""
    return page("Bosh sahifa", body)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if len(username) < 3 or len(password) < 6:
            flash("Login kamida 3 ta, parol kamida 6 ta belgidan iborat bo‘lsin.")
        else:
            try:
                db().execute("INSERT INTO users(username,password_hash) VALUES(?,?)",
                             (username, generate_password_hash(password)))
                db().commit()
                flash("Hisob yaratildi. Endi tizimga kiring.")
                return redirect(url_for("login"))
            except sqlite3.IntegrityError:
                flash("Bu login band. Boshqasini tanlang.")
    body = """<div class="card"><h1>Ro‘yxatdan o‘tish</h1><form method="post">
    <label>Login</label><input name="username" required minlength="3" autocomplete="username">
    <label>Parol</label><input name="password" type="password" required minlength="6" autocomplete="new-password">
    <button>Hisob yaratish</button></form></div>"""
    return page("Ro‘yxatdan o‘tish", body)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = db().execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            return redirect(url_for("home"))
        flash("Login yoki parol noto‘g‘ri.")
    body = """<div class="card"><h1>Kirish</h1><form method="post">
    <label>Login</label><input name="username" required autocomplete="username">
    <label>Parol</label><input name="password" type="password" required autocomplete="current-password">
    <button>Kirish</button></form></div>"""
    return page("Kirish", body)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/practice/CEFR/Reading", methods=["GET", "POST"])
@login_required
def reading():
    if request.method == "POST":
        score = 0
        for i, item in enumerate(READING):
            if request.form.get(f"q{i}") == str(item[3]):
                score += 1
        body = f"""<div class="card"><h1>Reading natijasi</h1><h2>{score} / {len(READING)}</h2>
        <p>Natija saqlandi emas, faqat shu urinish uchun ko‘rsatildi.</p><a class="btn" href="/practice/CEFR/Reading">Qayta ishlash</a>
        <a class="btn secondary" href="/">Bosh sahifa</a></div>"""
        return page("Reading natijasi", body)
    questions = ""
    for i, (passage, question, options, answer) in enumerate(READING):
        questions += f'<div class="q"><p><b>Matn:</b> {passage}</p><p><b>{i+1}. {question}</b></p>'
        for j, option in enumerate(options):
            questions += f'<label><input style="width:auto;margin:0 8px 0 0" type="radio" name="q{i}" value="{j}" required> {option}</label>'
        questions += '</div>'
    body = f"""<div class="card"><div class="topline"><h1>CEFR Reading</h1><h2 id="timer">60:00</h2></div>
    <p>35 ta savol. Vaqt tugashidan oldin javoblarni yuboring.</p>
    <form method="post" id="testForm">{questions}<button type="submit">Testni yakunlash</button></form></div>
    <script>
    let seconds=3600; const timer=document.getElementById('timer');
    const interval=setInterval(()=>{{seconds--;timer.textContent=Math.floor(seconds/60)+':'+String(seconds%60).padStart(2,'0');
    if(seconds<=0){{clearInterval(interval);document.getElementById('testForm').submit();}}}},1000);
    </script>"""
    return page("CEFR Reading", body)

@app.route("/practice/CEFR/Listening")
@login_required
def listening():
    script = """<div class="card"><h1>CEFR Listening</h1>
    <p>Quyidagi matnni tinglang. Brauzer ovozi qurilmangiz sozlamalariga bog‘liq.</p>
    <div class="q" id="listeningText">Good communication is an important skill in everyday life. It helps people share ideas, solve problems and understand different points of view. Students can improve communication by listening carefully, asking clear questions and practising regularly.</div>
    <button onclick="playAudio()">Tinglash</button> <button class="btn secondary" onclick="stopAudio()">To‘xtatish</button>
    <p id="audioStatus" class="muted">Audio tayyor.</p></div>
    <script>
    function playAudio(){
      if(!('speechSynthesis' in window)){document.getElementById('audioStatus').textContent='Bu brauzer ovozli o‘qishni qo‘llamaydi.';return;}
      window.speechSynthesis.cancel();
      const utterance=new SpeechSynthesisUtterance(document.getElementById('listeningText').textContent);
      utterance.lang='en-US'; utterance.rate=0.88;
      utterance.onstart=()=>document.getElementById('audioStatus').textContent='Audio ijro etilmoqda...';
      utterance.onend=()=>document.getElementById('audioStatus').textContent='Audio tugadi.';
      window.speechSynthesis.speak(utterance);
    }
    function stopAudio(){window.speechSynthesis.cancel();document.getElementById('audioStatus').textContent='Audio to‘xtatildi.';}
    window.addEventListener('beforeunload',()=>window.speechSynthesis.cancel());
    </script>"""
    return page("CEFR Listening", script)

@app.route("/practice/CEFR/Writing", methods=["GET", "POST"])
@login_required
def writing():
    user = current_user()
    prompt = WRITING_PROMPTS[(user["id"] - 1) % len(WRITING_PROMPTS)]
    if request.method == "POST":
        answer = request.form.get("answer", "").strip()
        if len(answer.split()) < 10:
            flash("Iltimos, kamida 10 ta so‘z yozing.")
        else:
            db().execute("INSERT INTO writing_submissions(user_id,prompt,answer) VALUES(?,?,?)",
                         (user["id"], prompt, answer))
            db().commit()
            flash("Writing javobingiz saqlandi. U avtomatik baholanmaydi.")
            return redirect(url_for("home"))
    body = f"""<div class="card"><h1>CEFR Writing</h1><p>Quyidagi mavzu bo‘yicha javob yozing.</p>
    <div class="q">{prompt}</div><form method="post"><label>Javobingiz</label>
    <textarea name="answer" placeholder="Write your answer here..." required></textarea>
    <button type="submit">Javobni saqlash</button></form></div>"""
    return page("CEFR Writing", body)

@app.route("/practice/CEFR/Speaking")
@login_required
def speaking():
    body = """<div class="card"><h1>CEFR Speaking</h1>
    <p>Quyidagi mavzu bo‘yicha gapiring. Yozuv brauzeringizda vaqtincha saqlanadi va serverga yuborilmaydi.</p>
    <div class="q"><b>Topic:</b> Describe a place you enjoy visiting. Explain why you like it.</div>
    <button id="start">Yozishni boshlash</button> <button class="btn secondary" id="stop" disabled>To‘xtatish</button>
    <p id="status" class="muted">Mikrofon ruxsati talab qilinadi. Sayt HTTPS orqali ochilishi kerak.</p>
    <audio id="audio" controls style="width:100%;display:none"></audio></div>
    <script>
    let recorder, chunks=[];
    const start=document.getElementById('start'), stop=document.getElementById('stop');
    start.onclick=async()=>{
      try{
        const stream=await navigator.mediaDevices.getUserMedia({audio:true});
        chunks=[]; recorder=new MediaRecorder(stream);
        recorder.ondataavailable=e=>{if(e.data.size)chunks.push(e.data)};
        recorder.onstop=()=>{
          const blob=new Blob(chunks,{type:'audio/webm'}); const url=URL.createObjectURL(blob);
          const audio=document.getElementById('audio'); audio.src=url; audio.style.display='block';
          stream.getTracks().forEach(t=>t.stop());
          document.getElementById('status').textContent='Yozuv tayyor. Uni shu yerda tinglashingiz mumkin.';
        };
        recorder.start(); start.disabled=true; stop.disabled=false;
        document.getElementById('status').textContent='Yozilmoqda...';
      }catch(e){document.getElementById('status').textContent='Mikrofon ochilmadi. Ruxsat va HTTPS ni tekshiring.';}
    };
    stop.onclick=()=>{if(recorder && recorder.state!=='inactive'){recorder.stop();start.disabled=false;stop.disabled=true;}};
    </script>"""
    return page("CEFR Speaking", body)

@app.errorhandler(404)
def not_found(error):
    return page("Sahifa topilmadi", '<div class="card"><h1>404</h1><p>Sahifa topilmadi.</p><a class="btn" href="/">Bosh sahifa</a></div>'), 404

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
