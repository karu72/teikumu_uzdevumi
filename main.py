from flask import Flask, redirect, request, session, render_template, url_for, jsonify
import json
import random
import sqlite3

app = Flask(__name__)
app.secret_key = '1111'

def db_izveide():
    select_sql('''CREATE TABLE IF NOT EXISTS users (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               username TEXT UNIQUE NOT NULL,
               password TEXT NOT NULL,
               sentence_count INTEGER DEFAULT 0,
               best_streak INTEGER DEFAULT 0)''')

    select_sql('INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)', ("Admin", "qwerty"))

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

            print(session[f"used_sentences_{level}"], ", LENGTH: ", len(session[f"used_sentences_{level}"]))

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

    if user_input.lower() == correct_word.lower():
        if 'user_id' in session:
            select_sql('UPDATE users SET sentence_count = sentence_count + 1 WHERE id = ?', (session['user_id'],))
        return jsonify({'result': 'correct'})
    else:
        return jsonify({'result': 'incorrect'})


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        select_sql('INSERT OR IGNORE INTO users (username, password) VALUES (?, ?)', (username, password))
        return redirect('/')
    return render_template('login_signup.html')

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = select_sql('SELECT id, username FROM users WHERE username = ? AND password = ?', (username, password))

        if user:
            session['user_id'] = user[0][0]
            session['username'] = user[0][1]

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

    return render_template('user_info.html', username=username[0][0], count=count[0][0])


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

    return jsonify({"message": "Sentence added successfully!"})


@app.route('/', methods=['POST', 'GET'])
def sakums():
    #session.clear()
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