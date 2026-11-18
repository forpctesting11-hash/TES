      utterance.rate=0.88;
      utterance.onstart=()=>document.getElementById('audioStatus').textContent='Playing audio...';
      utterance.onend=()=>document.getElementById('audioStatus').textContent='Audio finished.';
      window.speechSynthesis.speak(utterance);
    }}
    function stopAudio(){{window.speechSynthesis.cancel();document.getElementById('audioStatus').textContent='Audio stopped.';}}
    window.addEventListener('beforeunload',()=>window.speechSynthesis.cancel());
    </script>
    """
    return page(html)


@app.route("/practice/CEFR/Writing", methods=["GET", "POST"])
def cefr_writing():
    user = current_user()
    if not user:
        return redirect("/login")
    prompt = WRITING_PROMPTS[(user["id"] - 1) % len(WRITING_PROMPTS)]
    if request.method == "POST":
        answer = request.form.get("answer", "").strip()
        if len(answer.split()) < 10:
            return page(f'<div class="card"><h2>Please write at least 10 words.</h2><a href="/practice/CEFR/Writing">Go back</a></div>')
        db = connect()
        db.execute("INSERT INTO writing_submissions (user_id,prompt,answer) VALUES (?,?,?)",
                   (user["id"], prompt, answer))
        db.commit()
        db.close()
        return page(f'<div class="card"><h1>Writing submitted</h1><p>Your response has been saved.</p><p>Word count: {len(answer.split())}</p><p>It has not been automatically graded.</p><a href="/exam/CEFR">Back to CEFR</a></div>')
    return page(f"""
    <div class="card"><h1>CEFR Writing</h1><p>Write your response to the topic below.</p>
    <h3>{prompt}</h3>
    <form method="post">
      <textarea name="answer" placeholder="Write your answer here..." required></textarea>
      <button>Submit Writing</button>
    </form></div>
    """)


@app.route("/practice/CEFR/Speaking")
def cefr_speaking():
    user = current_user()
    if not user:
        return redirect("/login")
    prompt = SPEAKING_PROMPTS[(user["id"] - 1) % len(SPEAKING_PROMPTS)]
    safe_prompt = prompt.replace("\\", "\\\\").replace("'", "\\'")
    return page(f"""
    <div class="card">
      <h1>CEFR Speaking Practice</h1>
      <p>Read the topic, then record your answer using your microphone.</p>
      <h3>{prompt}</h3>
      <button type="button" onclick="speakPrompt()">🔊 Read topic aloud</button>
      <button type="button" class="secondary" onclick="startRecording()">Start recording</button>
      <button type="button" class="secondary" onclick="stopRecording()">Stop recording</button>
      <p id="status">Recording has not started.</p>
      <audio id="player" controls></audio>
      <p><small>The recording stays in this browser tab. It is not uploaded or saved to your account.</small></p>
      <a href="/exam/CEFR">Back to CEFR</a>
    </div>
    <script>
    let recorder, chunks=[];
    function speakPrompt(){{
      if(!('speechSynthesis' in window)){{alert('Text-to-speech is not supported.');return;}}
      speechSynthesis.cancel();
      let u=new SpeechSynthesisUtterance('{safe_prompt}');
      u.lang='en-US';speechSynthesis.speak(u);
    }}
    async function startRecording(){{
      try{{
        let stream=await navigator.mediaDevices.getUserMedia({{audio:true}});
        chunks=[];
        recorder=new MediaRecorder(stream);
        recorder.ondataavailable=e=>{{if(e.data.size)chunks.push(e.data);}};
        recorder.onstop=()=>{{
          let blob=new Blob(chunks,{{type:'audio/webm'}});
          document.getElementById('player').src=URL.createObjectURL(blob);
          stream.getTracks().forEach(t=>t.stop());
          document.getElementById('status').textContent='Recording ready. Use the audio player to listen.';
        }};
        recorder.start();
        document.getElementById('status').textContent='Recording...';
      }}catch(e){{document.getElementById('status').textContent='Microphone permission was not granted or is unavailable.';}}
    }}
    function stopRecording(){{
      if(recorder && recorder.state!=='inactive')recorder.stop();
    }}
    </script>
    """)


@app.route("/results")
def results():
    user = current_user()
    if not user:
        return redirect("/login")
    db = connect()
    rows = db.execute("SELECT * FROM results WHERE user_id=? ORDER BY id DESC",
                      (user["id"],)).fetchall()
    writing_count = db.execute(
        "SELECT COUNT(*) AS n FROM writing_submissions WHERE user_id=?",
        (user["id"],)
    ).fetchone()["n"]
    db.close()
    html = f'<div class="card"><h1>My Results</h1><p>Writing submissions: {writing_count}</p>'
    if not rows:
        html += '<p>No test results yet.</p>'
    for row in rows:
        html += f'<div class="card"><h3>{row["exam"]} - {row["skill"]}</h3><p>Score: {row["score"]}/{row["total"]}</p><small>{row["date"]}</small></div>'
    html += '<a href="/dashboard">Back to dashboard</a></div>'
    return page(html)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
