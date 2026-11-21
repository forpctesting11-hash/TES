
@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username","").strip()
        password = request.form.get("password","")
        with db() as con:
            user = con.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if user and check_password_hash(user["password"], password):
            session["user_id"], session["username"] = user["id"], user["username"]
            return redirect(url_for("dashboard"))
        flash("Incorrect username or password.")
    content = """<section class="section" style="max-width:520px;margin:auto"><div class="panel"><div class="eyebrow">Welcome back</div><h2>Log in</h2><form method="post"><label>Username</label><input name="username" required><label>Password</label><input name="password" type="password" required><button class="btn" type="submit">Log in</button></form><p class="muted">New here? <a href="/register">Create an account</a>.</p></div></section>"""
    return page("Log in", content)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/dashboard")
@login_required
def dashboard():
    with db() as con:
        results = con.execute("SELECT level,score,total,created_at FROM results WHERE user_id=? ORDER BY id DESC LIMIT 8", (session["user_id"],)).fetchall()
    content = f'<section class="section"><div class="eyebrow">Your workspace</div><h1 style="font-size:42px">Welcome, {session["username"]}.</h1><p class="lead">Keep building your English skills one practice session at a time.</p><a class="btn" href="/practice">Start a mock test</a><div class="section"><h2>Recent results</h2>'
    if results:
        content += '<div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(190px,1fr))">'
        for r in results:
            pct = round(100*r["score"]/r["total"]) if r["total"] else 0
            content += f'<div class="card"><div class="level"><h3>{r["level"]}</h3><span class="tag">{pct}%</span></div><b>{r["score"]}/{r["total"]} correct</b><p class="muted">{r["created_at"][:10]}</p></div>'
        content += '</div>'
    else:
        content += '<p class="muted">No results yet. Complete your first mock test to see your progress here.</p>'
    content += '</div></section>'
    return page("Dashboard", content)

@app.route("/practice", methods=["GET","POST"])
def practice():
    level = request.args.get("level","B1").upper()
    if level not in QUESTION_BANK:
        level = "B1"
    if request.method == "POST":
        level = request.form.get("level","B1").upper()
        if level not in QUESTION_BANK:
            level = "B1"
        questions = QUESTION_BANK[level]
        score = 0
        review = ""
        for i, q in enumerate(questions):
            try:
                chosen = int(request.form.get(f"q{i}", "-1"))
            except ValueError:
                chosen = -1
            correct = chosen == q["a"]
            if correct:
                score += 1
            chosen_text = q["opts"][chosen] if 0 <= chosen < len(q["opts"]) else "Not answered"
            review += f'<div class="question"><b>{i+1}. {q["q"]}</b><p class="{"notice" if correct else "muted"}">Your answer: {chosen_text} · {"Correct" if correct else "Review this one"}</p><p class="muted">Correct answer: <b>{q["opts"][q["a"]]}</b>. {q["why"]}</p></div>'
        if "user_id" in session:
            with db() as con:
                con.execute("INSERT INTO results(user_id,level,score,total,created_at) VALUES(?,?,?,?,?)", (session["user_id"],level,score,len(questions),datetime.utcnow().isoformat(timespec="seconds")))
        pct = round(100*score/len(questions))
        content = f'<section class="section"><div class="panel"><div class="eyebrow">Test completed · {level}</div><h1 style="font-size:48px">{score}/{len(questions)}</h1><h2>{pct}% correct</h2><p class="muted">Use the explanations below to review your answers. This short practice set is not an official CEFR score.</p><div class="actions"><a class="btn" href="/practice?level={level}">Try again</a><a class="btn secondary" href="/dashboard">Dashboard</a></div></div><div class="section"><h2>Answer review</h2>{review}</div></section>'
        return page("Results", content)

    qs = QUESTION_BANK[level]
    shuffled = []
    for q in qs:
        order = list(range(len(q["opts"])))
        random.shuffle(order)
        shuffled.append((q, order))
    content = f'<section class="section"><div class="eyebrow">CEFR-style practice</div><h1 style="font-size:42px">Mock test</h1><p class="muted">Choose a level and answer all five questions. Your result and explanations appear at the end.</p><form method="get" action="/practice"><label for="level">Your level</label><select id="level" name="level" onchange="this.form.submit()">'
    for lev in QUESTION_BANK:
        content += f'<option value="{lev}" {"selected" if lev==level else ""}>{lev}</option>'
    content += '</select></form><form method="post"><input type="hidden" name="level" value="'+level+'">'
    for i,(q,order) in enumerate(shuffled):
        content += f'<div class="question"><h3>{i+1}. {q["q"]}</h3>'
        for j, original_index in enumerate(order):
            content += f'<label class="option"><input type="radio" name="q{i}" value="{original_index}" required>{q["opts"][original_index]}</label>'
        content += '</div>'
    content += '<div class="actions"><button class="btn" type="submit">Submit answers</button></div></form></section>'
    return page("CEFR Mock", content)

@app.route("/writing", methods=["GET","POST"])
@login_required
def writing():
    if request.method == "POST":
        text = request.form.get("answer","").strip()
        if len(text) < 20:
            flash("Please write at least 20 characters.")
        else:
            flash("Your writing has been received in this session. Ask a teacher or trusted reviewer for detailed feedback.")
    content = """<section class="section"><div class="eyebrow">Writing practice</div><h1 style="font-size:42px">Develop your ideas.</h1><div class="panel"><h2>Practice prompt</h2><p>Some people believe that students should learn practical skills at school, while others think traditional academic subjects are more important. Discuss both views and give your opinion.</p><form method="post"><label>Your response</label><textarea name="answer" rows="12" placeholder="Write your response here..." required></textarea><button class="btn" type="submit">Submit writing</button></form><p class="muted">This demo stores no writing history and does not provide automatic scoring.</p></div></section>"""
    return page("Writing", content)

@app.route("/speaking")
@login_required
def speaking():
    content = """<section class="section"><div class="eyebrow">Speaking practice</div><h1 style="font-size:42px">Speak with confidence.</h1><div class="panel"><h2>Part 1 · Familiar topics</h2><p>Describe a hobby you enjoy. How did you become interested in it?</p><h2>Part 2 · Long turn</h2><p>Describe a place you would recommend to a visitor. Say where it is, what people can do there, and why you recommend it.</p><h2>Part 3 · Discussion</h2><p>How has technology changed the way people communicate?</p><p class="muted">Use your device's voice recorder if you want to review your practice. This page does not upload or record audio.</p></div></section>"""
    return page("Speaking", content)

@app.errorhandler(404)
def not_found(_):
    return page("Not found", '<section class="section"><h1 style="font-size:42px">Page not found</h1><a class="btn" href="/">Go home</a></section>'), 404

init_db()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
