from flask import Flask, render_template, request, redirect, url_for, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace with a real secret key in production

# Fake user store (for demo purposes)
users = {}

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users:
            return "User already exists. Try logging in."
        users[username] = password
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in users and users[username] == password:
            session['username'] = username
            return redirect(url_for('dashboard'))
        return "Invalid credentials. Try again."
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' in session:
        return render_template('home.html', username=session['username'])
    return redirect(url_for('login'))

@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return redirect(url_for('login'))

# Add routing for the new booking pages
@app.route('/profile')
def profile():
    return render_template('profile.html', username=session.get('username'))

@app.route('/hotel')
def hotel():
    return render_template('hotel.html', username=session.get('username'))

# Hotel Dashboard Page
@app.route('/hoteldashboard')
def hoteldashboard():
    return render_template('hoteldashboard.html', username=session.get('username'))

@app.route('/busfilter')
def busfilter():
    return render_template('busfilter.html', username=session.get('username'))

# Bus Dashboard Page
@app.route('/busdashboard')
def busdashboard():
    return render_template('busdashboard.html', username=session.get('username'))

@app.route('/flightfilter')
def flightfilter():
    return render_template('flightfilter.html', username=session.get('username'))

# Flight Dashboard Page
@app.route('/flightdashboard')
def flightdashboard():
    return render_template('flightdashboard.html', username=session.get('username'))

@app.route('/trainfilter')
def trainfilter():
    return render_template('trainfilter.html', username=session.get('username'))

# Train Dashboard Page
@app.route('/traindashboard')
def traindashboard():
    return render_template('traindashboard.html', username=session.get('username'))

if __name__ == '__main__':
    app.run(debug=True)
