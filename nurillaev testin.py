
from flask import Flask, request, redirect, session, render_template_string, flash
import sqlite3
import os
import time
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.environ.get("TES_SECRET_KEY", "tes-demo-change-this-secret")

DB = "tes_database.db"

# ================= DATABASE =================

def connect():
    db = sqlite3.connect(DB)
    db.row_factory = sqlite3.Row
    return db

def init_db():
    db = connect()
    db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)
    db.execute("""
        CREATE TABLE IF NOT EXISTS results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            exam TEXT,
            skill TEXT,
            score INTEGER,
            total INTEGER,
            date TEXT DEFAULT CURRENT_TIMESTAMP
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

# ================= CEFR READING PASSAGES =================

PASSAGES = [
    {
        "title": "Passage 1: The Importance of Libraries",
        "text": """
        Libraries have changed significantly over the last few decades.
        In the past, people mainly visited libraries to borrow printed books
        or read newspapers. Today, many libraries also provide computers,
        internet access and digital books.

        Libraries remain important because they offer a quiet place to study.
        They also organise events for children and adults. Some libraries
        provide language courses and workshops that help people develop
        useful skills.

        Although technology has changed how people find information,
        libraries continue to support education and local communities.
        """
    },
    {
        "title": "Passage 2: Urban Gardens",
        "text": """
        Urban gardening is becoming popular in many cities. People use
        balconies, rooftops and empty spaces to grow vegetables and flowers.
        These gardens can make neighbourhoods more attractive.

        Growing food locally may also reduce the distance that vegetables
        travel before reaching consumers. Gardeners can learn about nature
        and understand how food is produced.

        However, urban gardens need regular care. Plants require enough
        sunlight and water, and gardeners must protect them from insects.
        Despite these challenges, many communities believe the benefits
        are worth the effort.
        """
    },
    {
        "title": "Passage 3: Learning a New Language",
        "text": """
        Learning a foreign language takes time and patience. Students often
        begin by memorising vocabulary and studying grammar. However,
        regular practice is essential for making progress.

        Listening to podcasts, reading short articles and speaking with
        other learners can improve language skills. Making mistakes is
        a normal part of learning and should not discourage students.

        Setting realistic goals can also help. For example, a learner might
        study ten new words each day or read one short article every week.
        Small steps can lead to significant improvement over time.
        """
    },
    {
        "title": "Passage 4: Public Transport",
        "text": """
        Public transport plays an important role in modern cities.
        Buses, trains and underground systems help people travel to work,
        school and other places.

        When more people use public transport, there may be fewer cars
        on the roads. This can help reduce traffic congestion and air
        pollution. Public transport can also be less expensive than
        owning and maintaining a private car.

        Nevertheless, transport systems need investment. Reliable services,
        clean vehicles and convenient routes are important if cities want
        more residents to use them.
        """
    },
    {
        "title": "Passage 5: The Future of Work",
        "text": """
        Technology is changing the way people work. Many companies now
        use digital tools to communicate with employees and manage projects.
        Some workers can complete their tasks from home.

        Remote work can save commuting time and provide greater flexibility.
        However, it may also make communication more difficult. Workers
        sometimes miss direct conversations with colleagues.

        Experts believe that future workplaces will combine different
        working styles. Employees may spend some days at home and other
        days in an office. Adaptability and digital skills will remain
        important in many professions.
        """
    }
]

# Each question: passage number, question, options, correct answer

CEFR_QUESTIONS = [
    (0, "What was the main purpose of libraries in the past?",
     ["A. To provide language courses", "B. To lend printed books", "C. To sell computers", "D. To organise sports"],
     1),
    (0, "Which service do many modern libraries provide?",
     ["A. Internet access", "B. Free accommodation", "C. Medical treatment", "D. Private transport"],
     0),
    (0, "Why do people still visit libraries?",
     ["A. To buy food", "B. To find jobs", "C. To study quietly", "D. To watch films"],
     2),
    (0, "What can libraries organise?",
     ["A. Car races", "B. Events and workshops", "C. Shopping trips", "D. Football matches"],
     1),
    (0, "The passage suggests that technology has...",
     ["A. Made libraries unnecessary", "B. Changed how information is found", "C. Removed the need for education", "D. Stopped people reading"],
     1),
    (0, "Who can benefit from library events?",
     ["A. Only teachers", "B. Only children", "C. Children and adults", "D. Only tourists"],
     2),
    (0, "What is the main idea of the passage?",
     ["A. Libraries continue to be useful", "B. Books are becoming expensive", "C. Computers should replace schools", "D. Newspapers are no longer printed"],
     0),

    (1, "Where can people create urban gardens?",
     ["A. Only in forests", "B. On rooftops and balconies", "C. Inside shopping centres", "D. Only on farms"],
     1),
    (1, "What can urban gardens make more attractive?",
     ["A. Neighbourhoods", "B. Airports", "C. Factories", "D. Highways"],
     0),
    (1, "What may growing food locally reduce?",
     ["A. The need for water", "B. The number of plants", "C. The distance food travels", "D. The amount of sunlight"],
     2),
    (1, "What can gardeners learn about?",
     ["A. Space travel", "B. Nature and food production", "C. Car repair", "D. Computer programming"],
     1),
    (1, "What do plants need?",
     ["A. Sunlight and water", "B. Only cold weather", "C. Artificial light all day", "D. No care"],
     0),
    (1, "What is one challenge of urban gardening?",
     ["A. Finding books", "B. Protecting plants from insects", "C. Building roads", "D. Learning mathematics"],
     1),
    (1, "How do many communities feel about urban gardens?",
     ["A. The benefits are worthwhile", "B. They are always dangerous", "C. They are impossible", "D. They have no benefits"],
     0),

    (2, "What does learning a foreign language require?",
     ["A. Luck only", "B. Time and patience", "C. Expensive equipment", "D. No practice"],
     1),
    (2, "What do students often study at the beginning?",
     ["A. History and science", "B. Music and art", "C. Vocabulary and grammar", "D. Geography only"],
     2),
    (2, "Which activity can improve language skills?",
     ["A. Listening to podcasts", "B. Avoiding books", "C. Sleeping all day", "D. Watching without listening"],
     0),
    (2, "How should learners feel about mistakes?",
     ["A. They should stop learning", "B. Mistakes are normal", "C. Mistakes are impossible", "D. They should never speak"],
     1),
    (2, "Why are realistic goals useful?",
     ["A. They make learning impossible", "B. They remove all grammar", "C. They help learners make progress", "D. They replace practice"],
     2),
    (2, "How many new words might a learner study each day?",
     ["A. Ten", "B. One hundred", "C. One thousand", "D. None"],
     0),
    (2, "What is the main message?",
     ["A. Language learning requires regular effort", "B. Grammar is never useful", "C. Only adults can learn languages", "D. Mistakes must be avoided completely"],
     0),

    (3, "What is the role of public transport?",
     ["A. To help people travel", "B. To sell houses", "C. To produce food", "D. To build computers"],
     0),
    (3, "What may happen when more people use public transport?",
     ["A. More private cars appear", "B. Traffic may decrease", "C. Roads disappear", "D. Cities become smaller"],
     1),
    (3, "What can public transport help reduce?",
     ["A. Education", "B. Air pollution", "C. Employment", "D. Communication"],
     1),
    (3, "Why can public transport be less expensive?",
     ["A. It removes all travel", "B. It can cost less than owning a car", "C. It is always free", "D. It requires no workers"],
     1),
    (3, "What do transport systems need?",
     ["A. Investment", "B. Fewer routes", "C. More traffic", "D. Less maintenance"],
     0),
    (3, "Which feature is important for public transport?",
     ["A. Unreliable services", "B. Convenient routes", "C. Dirty vehicles", "D. Expensive tickets only"],
     1),
    (3, "What is the main idea?",
     ["A. Public transport benefits cities but needs investment", "B. Cars should be used everywhere", "C. Trains are always empty", "D. Roads are unnecessary"],
     0),

    (4, "What is changing the way people work?",
     ["A. Agriculture only", "B. Technology", "C. Weather", "D. Tourism"],
     1),
    (4, "Where can some workers complete their tasks?",
     ["A. From home", "B. Only in airports", "C. Only in schools", "D. In public parks"],
     0),
    (4, "What is one advantage of remote work?",
     ["A. More commuting", "B. Saving commuting time", "C. No need to communicate", "D. Less flexibility"],
     1),
    (4, "What can make remote work difficult?",
     ["A. Communication", "B. Having a computer", "C. Saving time", "D. Working from home"],
     0),
    (4, "What might workers miss?",
     ["A. Direct conversations with colleagues", "B. Their computers", "C. Their homes", "D. Their holidays"],
     0),
    (4, "What may future workplaces combine?",
     ["A. Only outdoor work", "B. Different working styles", "C. Only office work", "D. No technology"],
     1),
    (4, "Which skills will remain important?",
     ["A. Digital skills and adaptability", "B. Driving only", "C. Cooking only", "D. Painting only"],
     0)
]

# ================= OTHER PRACTICE QUESTIONS =================

OTHER_QUESTIONS = {
    "Reading": [
        {
            "q": "What is the capital city of the United Kingdom?",
            "options": ["London", "Paris", "Rome", "Madrid"],
            "answer": 0
        },
        {
            "q": "Choose the correct meaning of 'rapid'.",
            "options": ["Slow", "Fast", "Quiet", "Weak"],
            "answer": 1
        },
        {
            "q": "Which word is a synonym of 'begin'?",
            "options": ["Finish", "Start", "Close", "Stop"],
            "answer": 1
        }
    ],
    "Listening": [
        {
            "q": "Choose the correct spelling.",
            "options": ["Necessary", "Neccessary", "Necesary", "Neccesary"],
            "answer": 0
        },
        {
            "q": "What is the opposite of 'early'?",
            "options": ["Quick", "Late", "Soon", "Fast"],
            "answer": 1
        },
        {
            "q": "Which number comes after nineteen?",
            "options": ["Eighteen", "Twenty", "Thirty", "Ninety"],
            "answer": 1
        }
    ]
}

# ================= HTML TEMPLATE =================

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>TES - Testing Education System</title>
<style>
*{box-sizing:border-box}
body{
    margin:0;
    font-family:Arial,sans-serif;
    background:#0b1020;
    color:white;
}
header{
    background:#111a31;
    padding:18px;
    border-bottom:1px solid #263653;
}
header h2{margin:0;color:#60a5fa}
.container{
    max-width:900px;
    margin:25px auto;
    padding:15px;
}
.card{
    background:#151f36;
    border:1px solid #293957;
    border-radius:14px;
    padding:20px;
    margin-bottom:15px;
}
h1,h2,h3{color:#60a5fa}
p{line-height:1.7}
input,button,select{
    width:100%;
    padding:13px;
    margin:8px 0;
    border-radius:8px;
    border:1px solid #40516f;
    font-size:16px;
}
input{background:#0b1020;color:white}
button{
    background:#2563eb;
    color:white;
    border:0;
    cursor:pointer;
    font-weight:bold;
}
button:hover{background:#1d4ed8}
a{color:#93c5fd;text-decoration:none}
.option{
    display:block;
    padding:10px;
    margin:7px 0;
    background:#202d48;
    border-radius:8px;
}
.option input{width:auto}
.timer{
    position:sticky;
    top:5px;
    background:#7f1d1d;
    padding:13px;
    text-align:center;
    border-radius:10px;
    font-size:20px;
    font-weight:bold;
    z-index:10;
}
.nav a{
    display:inline-block;
    margin:6px;
    padding:10px;
    background:#202d48;
    border-radius:8px;
}
small{color:#aab8d0}
</style>
</head>
<body>
<header>
<h2>TES | Testing Education System</h2>
</header>
<div class="container">
{{ content|safe }}
</div>
</body>
</html>
"""

def page(content):
    return render_template_string(TEMPLATE, content=content)

# ================= HOME =================

@app.route("/")
def home():
    user = current_user()
    if user:
        return redirect("/dashboard")

    return page("""
    <div class="card">
        <h1>Welcome to TES</h1>
        <p>Testing Education System</p>
        <p>IELTS va CEFR uchun online practice platformasi.</p>
        <a href="/register"><button>Register</button></a>
        <a href="/login"><button>Login</button></a>
    </div>
    """)

# ================= REGISTER =================

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        if len(username) < 3 or len(password) < 6:
            return page("""
            <div class="card">
            <h2>Username kamida 3 ta, parol 6 ta belgidan iborat bo‘lsin.</h2>
            <a href="/register">Back</a>
            </div>
            """)

        db = connect()
        try:
            db.execute(
                "INSERT INTO users (username,password) VALUES (?,?)",
                (username, generate_password_hash(password))
            )
            db.commit()
        except sqlite3.IntegrityError:
            db.close()
            return page("""
            <div class="card">
            <h2>Bu username band.</h2>
            <a href="/register">Try again</a>
            </div>
            """)
        db.close()

        return redirect("/login")

    return page("""
    <div class="card">
    <h1>Create account</h1>
    <form method="POST">
        <input name="username" placeholder="Username" required>
        <input name="password" type="password" placeholder="Password" required>
        <button type="submit">Register</button>
    </form>
    <a href="/login">Already have an account? Login</a>
    </div>
    """)

# ================= LOGIN =================

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")

        db = connect()
        user = db.execute(
            "SELECT * FROM users WHERE username=?",
            (username,)
        ).fetchone()
        db.close()

        if user and check_password_hash(user["password"], password):
            session.clear()
            session["user_id"] = user["id"]
            return redirect("/dashboard")

        return page("""
        <div class="card">
        <h2>Username yoki parol xato.</h2>
        <a href="/login">Try again</a>
        </div>
        """)

    return page("""
    <div class="card">
    <h1>Login</h1>
    <form method="POST">
        <input name="username" placeholder="Username" required>
        <input name="password" type="password" placeholder="Password" required>
        <button type="submit">Login</button>
    </form>
    <a href="/register">Create account</a>
    </div>
    """)

# ================= LOGOUT =================

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ================= DASHBOARD =================

@app.route("/dashboard")
def dashboard():
    user = current_user()
    if not user:
        return redirect("/login")

    return page(f"""
    <div class="card">
        <h1>Welcome, {user['username']}!</h1>
        <p>Testing Education System</p>
        <div class="nav">
            <a href="/exam/CEFR">CEFR</a>
            <a href="/exam/IELTS">IELTS</a>
            <a href="/results">My Results</a>
            <a href="/logout">Logout</a>
        </div>
    </div>
    """)

# ================= EXAM MENU =================

@app.route("/exam/<exam>")
def exam(exam):
    if not current_user():
        return redirect("/login")

    exam = exam.upper()
    if exam not in ["CEFR", "IELTS"]:
        return redirect("/dashboard")

    return page(f"""
    <div class="card">
        <h1>{exam} Practice</h1>
        <p>Choose a skill:</p>
        <a href="/practice/{exam}/Reading"><button>Reading</button></a>
        <a href="/practice/{exam}/Listening"><button>Listening</button></a>
        <a href="/practice/{exam}/Writing"><button>Writing</button></a>
        <a href="/practice/{exam}/Speaking"><button>Speaking</button></a>
        <a href="/dashboard">Back to dashboard</a>
    </div>
    """)

# ================= PRACTICE =================

@app.route("/practice/<exam>/<skill>", methods=["GET", "POST"])
def practice(exam, skill):
    user = current_user()
    if not user:
        return redirect("/login")

    exam = exam.upper()
    skill = skill.capitalize()

    if exam not in ["CEFR", "IELTS"]:
        return redirect("/dashboard")

    if skill not in ["Reading", "Listening", "Writing", "Speaking"]:
        return redirect("/exam/" + exam)

    # CEFR READING: 35 QUESTIONS, 60 MINUTES

    if exam == "CEFR" and skill == "Reading":

        if request.method == "POST":
            start = session.get("cefr_reading_start", time.time())
            expired = time.time() - start > 3600

            score = 0
            for i, question in enumerate(CEFR_QUESTIONS):
                answer = request.form.get(f"q{i}")
                if answer is not None and answer.isdigit():
                    if int(answer) == question[3]:
                        score += 1

            db = connect()
            db.execute(
                "INSERT INTO results (user_id,exam,skill,score,total) VALUES (?,?,?,?,?)",
                (user["id"], exam, skill, score, len(CEFR_QUESTIONS))
            )
            db.commit()
            db.close()

            session.pop("cefr_reading_start", None)

            return page(f"""
            <div class="card">
                <h1>Reading Result</h1>
                <h2>{score} / {len(CEFR_QUESTIONS)}</h2>
                <p>{"Time is over. Your submitted answers were checked." if expired else "Test completed!"}</p>
                <a href="/results"><button>View results</button></a>
                <a href="/dashboard">Dashboard</a>
            </div>
            """)

        if "cefr_reading_start" not in session:
            session["cefr_reading_start"] = time.time()

        remaining = max(
            0,
            3600 - int(time.time() - session["cefr_reading_start"])
        )

        content = f"""
        <div class="card">
            <h1>CEFR Reading Practice</h1>
            <p>35 questions | 60 minutes</p>
            <div class="timer" id="timer">60:00</div>
        </div>
        <form method="POST" id="testForm">
        """

        for p_index, passage in enumerate(PASSAGES):
            content += f"""
            <div class="card">
                <h2>{passage['title']}</h2>
                <p>{passage['text']}</p>
            </div>
            """

            for i, question in enumerate(CEFR_QUESTIONS):
                if question[0] != p_index:
                    continue

                q_index = CEFR_QUESTIONS.index(question)
                content += f"""
                <div class="card">
                    <h3>Question {q_index + 1}</h3>
                    <p>{question[1]}</p>
                """

                for option_index, option in enumerate(question[2]):
                    content += f"""
                    <label class="option">
                        <input type="radio" name="q{q_index}" value="{option_index}">
                        {option}
                    </label>
                    """

                content += "</div>"

        content += """
        <div class="card">
            <button type="submit">Submit Test</button>
        </div>
        </form>

        <script>
        let seconds = REMAINING;
        const timer = document.getElementById("timer");

        function updateTimer() {
            let minutes = Math.floor(seconds / 60);
            let secs = seconds % 60;
            timer.textContent =
                String(minutes).padStart(2, "0") + ":" +
                String(secs).padStart(2, "0");

            if (seconds <= 0) {
                document.getElementById("testForm").submit();
                return;
            }

            seconds--;
        }

        updateTimer();
        setInterval(updateTimer, 1000);
        </script>
        """

        content = content.replace("REMAINING", str(remaining))
        return page(content)

    # OTHER SKILLS

    if skill in ["Writing", "Speaking"]:
        return page(f"""
        <div class="card">
            <h1>{exam} {skill}</h1>
            <p>Bu bo‘lim hozircha tayyorlanmoqda.</p>
            <p>Keyingi yangilanishda topshiriqlar va baholash tizimi qo‘shiladi.</p>
            <a href="/exam/{exam}">Back</a>
        </div>
        """)

    questions = OTHER_QUESTIONS.get(skill, [])

    if request.method == "POST":
        score = 0

        for i, question in enumerate(questions):
            answer = request.form.get(f"q{i}")
            if answer is not None and answer.isdigit():
                if int(answer) == question["answer"]:
                    score += 1

        db = connect()
        db.execute(
            "INSERT INTO results (user_id,exam,skill,score,total) VALUES (?,?,?,?,?)",
            (user["id"], exam, skill, score, len(questions))
        )
        db.commit()
        db.close()

        return page(f"""
        <div class="card">
            <h1>Your Result</h1>
            <h2>{score} / {len(questions)}</h2>
            <a href="/results"><button>My Results</button></a>
            <a href="/dashboard">Dashboard</a>
        </div>
        """)

    content = f"<div class='card'><h1>{exam} {skill}</h1></div><form method='POST'>"

    for i, question in enumerate(questions):
        content += f"""
        <div class="card">
            <h3>Question {i + 1}</h3>
            <p>{question['q']}</p>
        """

        for j, option in enumerate(question["options"]):
            content += f"""
            <label class="option">
                <input type="radio" name="q{i}" value="{j}">
                {option}
            </label>
            """

        content += "</div>"

    content += """
    <div class="card">
        <button type="submit">Submit</button>
    </div>
    </form>
    """

    return page(content)

# ================= RESULTS =================

@app.route("/results")
def results():
    user = current_user()
    if not user:
        return redirect("/login")

    db = connect()
    data = db.execute(
        "SELECT * FROM results WHERE user_id=? ORDER BY id DESC",
        (user["id"],)
    ).fetchall()
    db.close()

    content = """
    <div class="card">
        <h1>My Results</h1>
    """

    if not data:
        content += "<p>You have no results yet.</p>"

    for result in data:
        content += f"""
        <div class="card">
            <h3>{result['exam']} - {result['skill']}</h3>
            <p>Score: {result['score']} / {result['total']}</p>
            <small>{result['date']}</small>
        </div>
        """

    content += """
        <a href="/dashboard">Back to dashboard</a>
    </div>
    """

    return page(content)

# ================= RUN =================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
