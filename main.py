from flask import Flask, redirect, request, session, render_template, url_for, jsonify
import json
import random
import sqlite3
from argon2 import PasswordHasher

app = Flask(__name__)
app.secret_key = '1111'

global current_streak
current_streak = 0

def db_izveide():
    select_sql('''CREATE TABLE IF NOT EXISTS users (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               username TEXT UNIQUE NOT NULL,
               password TEXT NOT NULL,
               sentence_count INTEGER DEFAULT 0,
               best_streak INTEGER DEFAULT 0)''')

    is_admin = select_sql("SELECT * FROM users WHERE username = 'Admin'")
    if not is_admin:
        password = b'qwerty321'
        hash = PasswordHasher().hash(password)
        select_sql('INSERT INTO users (username, password) VALUES (?, ?)', ("Admin", hash))

with open('data/sentences.json', 'r', encoding = "utf-8") as s:
    x = s.read()
    sentences = json.loads(x)


@app.route('/uzdevums')
def uzdevums():
    return render_template('uzdevums.html')


@app.route('/new_sentence', methods=['POST', 'GET'])
def new_sentence():
    
    if request.method == 'POST':
        level = request.form['level']
        global sentences
        sentences = sentences[level]
        session['level'] = level

        return redirect(url_for('uzdevums'))
            
    level = session['level']
    while True:
        i = random.randrange(len(sentences))

        if f"used_sentences_{level}" not in session:
            session[f"used_sentences_{level}"] = []
        
        if i not in session[f"used_sentences_{level}"]:
            session['curr_sentence'] = i
            session[f"used_sentences_{level}"].append(i)

            if len(session[f"used_sentences_{level}"]) == len(sentences):
                session[f"used_sentences_{level}"].clear()
            
            sentence = sentences[i]
            return jsonify(sentence)


@app.route('/input_check', methods=['POST'])
def input_check():
    data = request.get_json()

    user_input = data.get('answer', '').strip()
    curr_sentence_data = sentences[session['curr_sentence']]
    correct_word = curr_sentence_data['words'][curr_sentence_data['word_index']]

    global current_streak

    if user_input.lower() == correct_word.lower():
        if 'user_id' in session:
            select_sql('UPDATE users SET sentence_count = sentence_count + 1 WHERE id = ?', (session['user_id'],))
            current_streak += 1
        return jsonify({'result': 'correct'})
    else:
        if 'user_id' in session:
            best_streak = select_sql('SELECT best_streak FROM users WHERE id = ?', (session['user_id'],))
            if current_streak > best_streak[0][0]:
                select_sql('UPDATE users SET best_streak = ? WHERE id = ?', (current_streak, session['user_id'],))
                current_streak = 0
        return jsonify({'result': 'incorrect'})


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = PasswordHasher().hash(bytes(request.form['password'], "utf-8"))
        select_sql('INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)', (username, password))
        return redirect('/')
    return render_template('login_signup.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hash_password = select_sql('SELECT password FROM users WHERE username = ?', (username,))

        if hash_password:
            hash_pw_bytes = bytes(''.join(hash_password[0]), "utf-8")
            pw_bytes = bytes(password, "utf-8")

            try:
                PasswordHasher().verify(hash_pw_bytes, pw_bytes)
            except:
                return render_template('login_signup.html')

            user_id = select_sql('SELECT id FROM users WHERE username = ?', (username,))

            session['user_id'] = user_id[0][0]
            session['username'] = username
            return redirect('/')
        
    return render_template('login_signup.html')

@app.route('/logout', methods=['POST', 'GET'])
def logout():
    session.pop('user_id')
    session.pop('username')
    return redirect('/')

@app.route('/user_info', methods=['POST', 'GET'])
def user_info():
    username = select_sql('SELECT username FROM users WHERE id = ?', (session['user_id'],))
    count = select_sql('SELECT sentence_count FROM users WHERE id = ?', (session['user_id'],))
    streak = select_sql('SELECT best_streak FROM users WHERE id = ?', (session['user_id'],))


    return render_template('user_info.html', username=username[0][0], count=count[0][0], streak=streak[0][0])


@app.route('/db_edits')
def db_edits():
    return render_template('db_edits.html')


@app.route("/add_sentence", methods=["POST"])
def add_sentence():
    data = request.json
    with open('data/sentences.json', 'r', encoding = "utf-8") as s:
        sentences = json.load(s)

    new_sentence = {
        "words": data["words"],
        "examples": data["examples"],
        "word_index": data["word_index"]
    }

    sentences[data["difficulty"]].append(new_sentence)

    with open("data/sentences.json", "w") as file:
        json.dump(sentences, file, indent=2)

    return jsonify({"message": "Teikums pievienots!"})


@app.route('/', methods=['POST', 'GET'])
def sakums():
    with open('data/sentences.json', 'r', encoding = "utf-8") as s:
        x = s.read()
        global sentences
        sentences = json.loads(x)

    if request.method == 'POST':
        account = request.form['account']
        return redirect(url_for(f"{account}"))

    return render_template('sakums.html')


def select_sql(cmd, vals=None):
    conn = sqlite3.connect('flask.db')
    c = conn.cursor()
    res = c.execute(cmd, vals).fetchall() if vals else c.execute(cmd).fetchall()
    conn.commit()
    conn.close()
    return res

if __name__ == '__main__':
    db_izveide()
    app.run(debug=True)