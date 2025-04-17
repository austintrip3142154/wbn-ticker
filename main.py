from flask import Flask, render_template, request, redirect, session
import json, os

app = Flask(__name__)
app.secret_key = "wbnsecret"

DATA_DIR = 'data'
TICKER_FILE = os.path.join('data', 'ticker.json')
GAMES_FILE = os.path.join(DATA_DIR, 'games.json')
HEADLINES_FILE = os.path.join(DATA_DIR, 'headlines.json')
TEAMS_FILE = 'teams.json'
ADMIN_PIN = "1234"

def load_teams():
    with open(TEAMS_FILE, 'r') as f:
        return json.load(f)

def update_ticker_json(headlines, games):
    ticker_data = []
    for h in headlines:
        if isinstance(h, dict) and h.get("TICKER", ""):
            ticker_data.append({
                "NAME": h.get("NAME", ""),
                "TEAM NAME1": "",
                "TEAM LOGO1": "",
                "TEAM COLOR1": "#000000",
                "SCORE1": "",
                "TEAM NAME2": "",
                "TEAM LOGO2": "",
                "TEAM COLOR2": "#000000",
                "SCORE2": "",
                "QTR": "",
                "TICKER": h.get("TICKER", "")
            })
    for g in games:
        if isinstance(g, dict) and g.get("TEAM NAME1", ""):
            ticker_data.append(g)
    with open(TICKER_FILE, 'w') as f:
        json.dump(ticker_data, f, indent=2)

@app.route('/')
def index():
    return '''
    <h1>✅ WBN Ticker Portal</h1>
    <ul>
        <li><a href="/submit-score">Submit Score</a></li>
        <li><a href="/submit-headline">Submit Headline</a></li>
        <li><a href="/edit-scores">Edit Scores</a></li>
        <li><a href="/edit-headlines">Edit Headlines</a></li>
        <li><a href="/dashboard">View Dashboard</a></li>
        <li><a href="/admin">Admin Login</a> | <a href="/logout">Logout</a></li>
        <li><a href="/reset-scores">Reset Scores</a></li>
        <li><a href="/reset-headlines">Reset Headlines</a></li>
        <li><a href="/reset-all">Reset All</a></li>
    </ul>
    '''

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        pin = request.form.get('pin')
        if pin == ADMIN_PIN:
            session['admin'] = True
            return redirect('/')
    return render_template('admin.html')

@app.route('/logout')
def logout():
    session.pop('admin', None)
    return redirect('/')

@app.route('/submit-score', methods=['GET', 'POST'])
def submit_score():
    teams = load_teams()
    if request.method == 'POST':
        region = request.form['region']
        visitor = request.form['visitor_team']
        home = request.form['home_team']
        v_score = request.form['visitor_score']
        h_score = request.form['home_score']
        qtr = request.form['quarter']

        game_entry = {
            "NAME": region,
            "TEAM NAME1": visitor,
            "TEAM LOGO1": teams.get(visitor, {}).get("logo", ""),
            "TEAM COLOR1": teams.get(visitor, {}).get("color", "#000000"),
            "SCORE1": v_score,
            "TEAM NAME2": home,
            "TEAM LOGO2": teams.get(home, {}).get("logo", ""),
            "TEAM COLOR2": teams.get(home, {}).get("color", "#000000"),
            "SCORE2": h_score,
            "QTR": qtr,
            "TICKER": ""
        }

        if os.path.exists(GAMES_FILE):
            with open(GAMES_FILE) as f:
                games = json.load(f)
        else:
            games = []

        games.insert(0, game_entry)
        with open(GAMES_FILE, 'w') as f:
            json.dump(games, f, indent=2)

        if os.path.exists(HEADLINES_FILE):
            with open(HEADLINES_FILE) as f:
                headlines = json.load(f)
        else:
            headlines = []

        update_ticker_json(headlines, games)
        return redirect('/')

    return render_template('score_form.html', teams=teams)

@app.route('/submit-headline', methods=['GET', 'POST'])
def submit_headline():
    if request.method == 'POST':
        title = request.form['title']
        text = request.form['text']

        # Load or create headlines.json
        if os.path.exists(HEADLINES_FILE):
            with open(HEADLINES_FILE) as f:
                headlines = json.load(f)
        else:
            headlines = []

        # Add new headline
        headlines.insert(0, {"NAME": title, "TICKER": text})

        # Save headlines
        with open(HEADLINES_FILE, 'w') as f:
            json.dump(headlines, f, indent=2)

        # Load current scores
        if os.path.exists(GAMES_FILE):
            with open(GAMES_FILE) as f:
                games = json.load(f)
        else:
            games = []

        # ✅ Always update ticker.json after submitting headline
        update_ticker_json(headlines, games)

        return redirect('/')
    return render_template('headline_form.html')


@app.route('/edit-scores', methods=['GET', 'POST'])
def edit_scores():
    if not session.get('admin'): return redirect('/admin')
    teams = load_teams()
    if os.path.exists(GAMES_FILE):
        with open(GAMES_FILE) as f:
            games = json.load(f)
    else:
        games = []
    if request.method == 'POST':
        if 'delete' in request.form:
            index = int(request.form['delete'])
            del games[index]
        else:
            index = int(request.form['game_index'])
            games[index]['SCORE1'] = request.form['visitor_score']
            games[index]['SCORE2'] = request.form['home_score']
            games[index]['QTR'] = request.form['quarter']
        with open(GAMES_FILE, 'w') as f:
            json.dump(games, f, indent=2)
        if os.path.exists(HEADLINES_FILE):
            with open(HEADLINES_FILE) as f:
                headlines = json.load(f)
        else:
            headlines = []
        update_ticker_json(headlines, games)
        return redirect('/edit-scores')
    return render_template('edit_scores.html', games=games, teams=teams)

@app.route('/edit-headlines', methods=['GET', 'POST'])
def edit_headlines():
    if not session.get('admin'): return redirect('/admin')
    if os.path.exists(HEADLINES_FILE):
        with open(HEADLINES_FILE) as f:
            headlines = json.load(f)
    else:
        headlines = []
    if request.method == 'POST':
        if 'delete' in request.form:
            index = int(request.form['delete'])
            del headlines[index]
        else:
            index = int(request.form['headline_index'])
            headlines[index]['NAME'] = request.form['title']
            headlines[index]['TICKER'] = request.form['text']
        with open(HEADLINES_FILE, 'w') as f:
            json.dump(headlines, f, indent=2)
        if os.path.exists(GAMES_FILE):
            with open(GAMES_FILE) as f:
                games = json.load(f)
        else:
            games = []
        update_ticker_json(headlines, games)
        return redirect('/edit-headlines')
    return render_template('edit_headlines.html', headlines=headlines)

@app.route('/dashboard')
def dashboard():
    with open(HEADLINES_FILE) as f:
        headlines = json.load(f)
    with open(GAMES_FILE) as f:
        games = json.load(f)
    return render_template('dashboard.html', headlines=headlines, games=games)

@app.route('/reset-scores')
def reset_scores():
    if not session.get('admin'): return redirect('/admin')
    with open(GAMES_FILE, 'w') as f:
        json.dump([], f)

    if os.path.exists(HEADLINES_FILE):
        with open(HEADLINES_FILE) as f:
            headlines = json.load(f)
    else:
        headlines = []

    update_ticker_json(headlines, [])
    return redirect('/')


@app.route('/reset-headlines')
def reset_headlines():
    if not session.get('admin'): return redirect('/admin')
    with open(HEADLINES_FILE, 'w') as f:
        json.dump([], f)

    if os.path.exists(GAMES_FILE):
        with open(GAMES_FILE) as f:
            games = json.load(f)
    else:
        games = []

    update_ticker_json([], games)
    return redirect('/')


@app.route('/reset-all')
def reset_all():
    if not session.get('admin'): return redirect('/admin')

    with open(HEADLINES_FILE, 'w') as f:
        json.dump([], f)
    with open(GAMES_FILE, 'w') as f:
        json.dump([], f)

    update_ticker_json([], [])
    return redirect('/')

@app.route('/ticker.json')
def serve_ticker():
    if os.path.exists(TICKER_FILE):
        with open(TICKER_FILE) as f:
            return f.read(), 200, {'Content-Type': 'application/json'}
    else:
        return '{}', 200, {'Content-Type': 'application/json'}

if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)
    app.run(host='0.0.0.0', port=8080, debug=True)