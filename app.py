from __future__ import annotations

import csv
import io
import json
import os
import random
import sqlite3
from datetime import datetime
from fractions import Fraction
from pathlib import Path
from typing import Dict, List

from flask import Flask, Response, g, redirect, render_template, request, session, url_for

BASE_DIR = Path(__file__).resolve().parent
DATABASE = BASE_DIR / "game.db"

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-me")

# สามารถแก้ผ่าน Environment Variables ตอน Deploy ได้
GOOGLE_FORM_URL = os.environ.get("GOOGLE_FORM_URL", "https://forms.gle/CHANGE_ME")
PUBLIC_GAME_URL = os.environ.get("PUBLIC_GAME_URL", "")

CHARACTER_BONUS = {
    "Knight": {"emoji": "⚔️", "label": "นักรบ", "desc": "เริ่มต้น +5 Crystal", "bonus": "starter"},
    "Wizard": {"emoji": "🧙", "label": "จอมเวท", "desc": "เวลาเพิ่ม 5 วินาทีต่อข้อ", "bonus": "extra_time"},
    "Priest": {"emoji": "✨", "label": "นักบวช", "desc": "ตอบผิดได้ฟรี 1 ครั้งต่อด่าน", "bonus": "shield"},
    "Archer": {"emoji": "🏹", "label": "นักธนู", "desc": "ตอบไวภายใน 5 วินาที +2 Crystal", "bonus": "speed"},
}

DIFFICULTY_LABELS = {
    "Easy": "Easy - ตัวส่วนเท่ากัน",
    "Normal": "Normal - ผสมตัวส่วนเท่ากัน/ต่างกัน",
    "Hard": "Hard - ตัวส่วนต่างกันและโจทย์ประยุกต์",
}

STAGE_TITLES = {
    1: "ด่านที่ 1: บวกเศษส่วนตัวส่วนเท่ากัน",
    2: "ด่านที่ 2: ลบเศษส่วนตัวส่วนเท่ากัน",
    3: "ด่านที่ 3: บวกเศษส่วนต่างส่วน",
    4: "ด่านที่ 4: ลบเศษส่วนต่างส่วน",
    5: "ด่านที่ 5: โจทย์ปัญหาเศษส่วน",
}

STAGE_SCENES = {
    1: {"emoji": "🌿", "place": "ป่าแห่งตัวส่วนเท่ากัน"},
    2: {"emoji": "🧊", "place": "ถ้ำน้ำแข็งแห่งการลบ"},
    3: {"emoji": "🌉", "place": "สะพาน ค.ร.น."},
    4: {"emoji": "🔥", "place": "ภูเขาไฟเศษส่วน"},
    5: {"emoji": "🏰", "place": "ปราสาทโจทย์ปัญหา"},
}


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        DATABASE.parent.mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(DATABASE)
        g.db.row_factory = sqlite3.Row
    return g.db


@app.teardown_appcontext
def close_db(exception=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db() -> None:
    with sqlite3.connect(DATABASE) as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS players (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gender TEXT NOT NULL,
                age INTEGER NOT NULL,
                grade TEXT NOT NULL,
                character TEXT NOT NULL,
                difficulty TEXT NOT NULL,
                total_crystal INTEGER DEFAULT 0,
                created_at TEXT NOT NULL
            )
        """)
        db.execute("""
            CREATE TABLE IF NOT EXISTS stage_scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_id INTEGER NOT NULL,
                stage INTEGER NOT NULL,
                crystal INTEGER NOT NULL,
                correct_count INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(player_id) REFERENCES players(id)
            )
        """)
        db.commit()


def make_fraction_text(frac: Fraction) -> str:
    if frac.denominator == 1:
        return str(frac.numerator)
    return f"{frac.numerator}/{frac.denominator}"


def build_choices(answer: Fraction) -> List[str]:
    choices = {make_fraction_text(answer)}
    attempts = 0
    while len(choices) < 4 and attempts < 100:
        attempts += 1
        wrong = answer + Fraction(random.choice([-3, -2, -1, 1, 2, 3]), random.randint(2, 8))
        if wrong > 0:
            choices.add(make_fraction_text(wrong))
    result = list(choices)
    random.shuffle(result)
    return result


def same_den_question(is_add: bool) -> Dict:
    d = random.randint(3, 12)
    if is_add:
        a = random.randint(1, d - 2)
        b = random.randint(1, d - a - 1)
        ans = Fraction(a, d) + Fraction(b, d)
        symbol = "+"
    else:
        a = random.randint(2, d - 1)
        b = random.randint(1, a - 1)
        ans = Fraction(a, d) - Fraction(b, d)
        symbol = "-"
    return {"question": f"{a}/{d} {symbol} {b}/{d} = ?", "answer": make_fraction_text(ans), "choices": build_choices(ans)}


def diff_den_question(is_add: bool) -> Dict:
    d1 = random.randint(2, 9)
    d2 = random.randint(3, 12)
    while d1 == d2:
        d2 = random.randint(3, 12)
    if is_add:
        a = random.randint(1, d1 - 1)
        b = random.randint(1, d2 - 1)
        ans = Fraction(a, d1) + Fraction(b, d2)
        symbol = "+"
    else:
        f1 = Fraction(random.randint(1, d1 - 1), d1)
        f2 = Fraction(random.randint(1, d2 - 1), d2)
        if f1 < f2:
            f1, f2 = f2, f1
        a, d1 = f1.numerator, f1.denominator
        b, d2 = f2.numerator, f2.denominator
        ans = f1 - f2
        symbol = "-"
    return {"question": f"{a}/{d1} {symbol} {b}/{d2} = ?", "answer": make_fraction_text(ans), "choices": build_choices(ans)}


def word_problem() -> Dict:
    problems = [
        ("แม่มีพิซซ่า 3/4 ถาด กินไป 1/8 ถาด เหลือพิซซ่าเท่าไร?", Fraction(3, 4) - Fraction(1, 8)),
        ("น้องมีน้ำผลไม้ 1/2 แก้ว เติมเพิ่มอีก 1/3 แก้ว รวมเป็นเท่าไร?", Fraction(1, 2) + Fraction(1, 3)),
        ("อ่านหนังสือไปแล้ว 2/5 เล่ม และอ่านเพิ่มอีก 1/5 เล่ม รวมอ่านไปเท่าไร?", Fraction(2, 5) + Fraction(1, 5)),
        ("มีริบบิ้นยาว 5/6 เมตร ตัดไป 1/3 เมตร เหลือเท่าไร?", Fraction(5, 6) - Fraction(1, 3)),
        ("ปลูกต้นไม้เสร็จ 1/4 แปลง และปลูกเพิ่ม 2/4 แปลง รวมปลูกแล้วเท่าไร?", Fraction(1, 4) + Fraction(2, 4)),
        ("มีเค้ก 7/8 ก้อน แบ่งให้เพื่อนไป 3/8 ก้อน เหลือเท่าไร?", Fraction(7, 8) - Fraction(3, 8)),
        ("เดินทางไปแล้ว 2/3 กิโลเมตร เดินต่ออีก 1/6 กิโลเมตร รวมเดินเท่าไร?", Fraction(2, 3) + Fraction(1, 6)),
        ("มีน้ำ 5/6 ขวด เทออกไป 1/2 ขวด เหลือเท่าไร?", Fraction(5, 6) - Fraction(1, 2)),
    ]
    q, ans = random.choice(problems)
    return {"question": q, "answer": make_fraction_text(ans), "choices": build_choices(ans)}


def generate_stage_questions(stage: int, difficulty: str) -> List[Dict]:
    qs = []
    for _ in range(10):
        if difficulty == "Easy":
            qs.append(same_den_question(is_add=stage in [1, 3, 5]))
        elif difficulty == "Normal":
            if stage in [1, 2]:
                qs.append(same_den_question(is_add=stage == 1))
            elif stage in [3, 4]:
                qs.append(diff_den_question(is_add=stage == 3))
            else:
                qs.append(word_problem())
        else:
            if stage == 5:
                qs.append(word_problem())
            else:
                qs.append(diff_den_question(is_add=stage in [1, 3]))
    return qs


def current_player():
    pid = session.get("player_id")
    if not pid:
        return None
    return get_db().execute("SELECT * FROM players WHERE id = ?", (pid,)).fetchone()


def leaderboard_rows(limit=100):
    return get_db().execute("""
        SELECT p.id, p.name, p.gender, p.age, p.grade, p.character, p.difficulty,
               p.total_crystal, p.created_at,
               COUNT(s.id) AS completed_stage,
               COALESCE(SUM(s.correct_count), 0) AS correct_total
        FROM players p
        LEFT JOIN stage_scores s ON p.id = s.player_id
        GROUP BY p.id
        ORDER BY p.total_crystal DESC, correct_total DESC, p.created_at ASC
        LIMIT ?
    """, (limit,)).fetchall()


@app.route("/")
def index():
    return render_template("index.html", characters=CHARACTER_BONUS)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        gender = request.form.get("gender", "").strip()
        age = int(request.form.get("age", "0") or 0)
        grade = request.form.get("grade", "").strip()
        character = request.form.get("character", "Knight")
        difficulty = request.form.get("difficulty", "Easy")
        if not name or not gender or age <= 0 or not grade:
            return render_template("register.html", error="กรุณากรอกข้อมูลให้ครบ", characters=CHARACTER_BONUS, difficulties=DIFFICULTY_LABELS)
        starter_bonus = 5 if character == "Knight" else 0
        db = get_db()
        cur = db.execute("""
            INSERT INTO players(name, gender, age, grade, character, difficulty, total_crystal, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (name, gender, age, grade, character, difficulty, starter_bonus, datetime.now().isoformat(timespec="seconds")))
        db.commit()
        session["player_id"] = cur.lastrowid
        return redirect(url_for("select_stage"))
    return render_template("register.html", characters=CHARACTER_BONUS, difficulties=DIFFICULTY_LABELS)


@app.route("/select")
def select_stage():
    player = current_player()
    if not player:
        return redirect(url_for("register"))
    completed = get_db().execute("SELECT stage, crystal, correct_count FROM stage_scores WHERE player_id = ? ORDER BY stage", (player["id"],)).fetchall()
    completed_stages = {r["stage"] for r in completed}
    return render_template("select.html", player=player, completed=completed, completed_stages=completed_stages,
                           stage_titles=STAGE_TITLES, scenes=STAGE_SCENES, characters=CHARACTER_BONUS)


@app.route("/stage/<int:stage>")
def stage(stage: int):
    player = current_player()
    if not player:
        return redirect(url_for("register"))
    if stage not in STAGE_TITLES:
        return redirect(url_for("select_stage"))
    questions = generate_stage_questions(stage, player["difficulty"])
    seconds = 35 if player["character"] == "Wizard" else 30
    return render_template("stage.html", player=player, stage=stage, title=STAGE_TITLES[stage], scene=STAGE_SCENES[stage],
                           questions_json=json.dumps(questions, ensure_ascii=False), seconds=seconds,
                           character_bonus=CHARACTER_BONUS[player["character"]], characters=CHARACTER_BONUS)


@app.route("/submit_stage", methods=["POST"])
def submit_stage():
    player = current_player()
    if not player:
        return redirect(url_for("register"))
    stage_no = int(request.form.get("stage", "1"))
    crystal = int(request.form.get("crystal", "0"))
    correct_count = int(request.form.get("correct_count", "0"))
    db = get_db()
    existing = db.execute("SELECT id, crystal FROM stage_scores WHERE player_id = ? AND stage = ?", (player["id"], stage_no)).fetchone()
    if existing:
        if crystal > existing["crystal"]:
            diff = crystal - existing["crystal"]
            db.execute("UPDATE stage_scores SET crystal = ?, correct_count = ?, created_at = ? WHERE id = ?",
                       (crystal, correct_count, datetime.now().isoformat(timespec="seconds"), existing["id"]))
            db.execute("UPDATE players SET total_crystal = total_crystal + ? WHERE id = ?", (diff, player["id"]))
    else:
        db.execute("INSERT INTO stage_scores(player_id, stage, crystal, correct_count, created_at) VALUES (?, ?, ?, ?, ?)",
                   (player["id"], stage_no, crystal, correct_count, datetime.now().isoformat(timespec="seconds")))
        db.execute("UPDATE players SET total_crystal = total_crystal + ? WHERE id = ?", (crystal, player["id"]))
    db.commit()
    return redirect(url_for("result", stage=stage_no))


@app.route("/result/<int:stage>")
def result(stage: int):
    player = current_player()
    if not player:
        return redirect(url_for("register"))
    score = get_db().execute("SELECT * FROM stage_scores WHERE player_id = ? AND stage = ?", (player["id"], stage)).fetchone()
    updated = current_player()
    next_stage = stage + 1 if stage < 5 else None
    return render_template("result.html", player=updated, score=score, stage=stage, next_stage=next_stage, form_url=GOOGLE_FORM_URL, characters=CHARACTER_BONUS)


@app.route("/leaderboard")
def leaderboard():
    return render_template("leaderboard.html", rows=leaderboard_rows(50), characters=CHARACTER_BONUS)


@app.route("/dashboard")
def dashboard():
    rows = leaderboard_rows(500)
    total_players = get_db().execute("SELECT COUNT(*) AS c FROM players").fetchone()["c"]
    total_attempts = get_db().execute("SELECT COUNT(*) AS c FROM stage_scores").fetchone()["c"]
    avg_score = get_db().execute("SELECT ROUND(AVG(total_crystal), 1) AS a FROM players").fetchone()["a"] or 0
    return render_template("dashboard.html", rows=rows, total_players=total_players, total_attempts=total_attempts, avg_score=avg_score, characters=CHARACTER_BONUS)


@app.route("/export_scores.csv")
def export_scores_csv():
    rows = leaderboard_rows(10000)
    out = io.StringIO()
    writer = csv.writer(out)
    writer.writerow(["Rank", "Name", "Gender", "Age", "Grade", "Character", "Difficulty", "Total Crystal", "Completed Stage", "Correct Total", "Created At"])
    for i, r in enumerate(rows, 1):
        writer.writerow([i, r["name"], r["gender"], r["age"], r["grade"], r["character"], r["difficulty"], r["total_crystal"], r["completed_stage"], r["correct_total"], r["created_at"]])
    data = "\ufeff" + out.getvalue()
    return Response(data, mimetype="text/csv; charset=utf-8", headers={"Content-Disposition": "attachment; filename=fraction_adventure_scores.csv"})


@app.route("/qr")
def qr_page():
    public_url = PUBLIC_GAME_URL or request.url_root.rstrip("/")
    return render_template("qr.html", public_url=public_url)


@app.route("/qr.png")
def qr_png():
    public_url = PUBLIC_GAME_URL or request.url_root.rstrip("/")
    try:
        import qrcode
        img = qrcode.make(public_url)
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        return Response(buffer.getvalue(), mimetype="image/png")
    except Exception:
        # fallback: return empty PNG error as text if qrcode package is missing
        return Response("QR generation failed. Please install qrcode[pil].", mimetype="text/plain", status=500)


@app.route("/reset")
def reset_session():
    session.clear()
    return redirect(url_for("index"))


# Initialize database both for local run and production WSGI/Gunicorn
with app.app_context():
    init_db()


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "1") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
