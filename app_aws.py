from flask import Flask, render_template, request, redirect, url_for, session
import boto3
import os
from botocore.exceptions import ClientError

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'your_secret_key')  # Use environment variable in EC2

# AWS Configuration
AWS_REGION = 'us-east-1'
USERS_TABLE = 'fixitnow_user'
SERVICES_TABLE = 'fixitnow_service'
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN')  # Set this in your EC2 instance

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb', region_name=AWS_REGION)
sns_client = boto3.client('sns', region_name=AWS_REGION)

users_table = dynamodb.Table(USERS_TABLE)
services_table = dynamodb.Table(SERVICES_TABLE)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            # Check if user already exists
            response = users_table.get_item(Key={'username': username})
            if 'Item' in response:
                return "User already exists. Try logging in."

            # Store new user in DynamoDB
            users_table.put_item(Item={'username': username, 'password': password})

            # Optional: Send SNS notification
            if SNS_TOPIC_ARN:
                sns_client.publish(
                    TopicArn=SNS_TOPIC_ARN,
                    Message=f"New user registered: {username}",
                    Subject="New User Registration"
                )

            return redirect(url_for('login'))

        except ClientError as e:
            return f"Error accessing database: {e.response['Error']['Message']}"

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        try:
            response = users_table.get_item(Key={'username': username})
            user = response.get('Item')

            if user and user['password'] == password:
                session['username'] = username
                return redirect(url_for('dashboard'))
            return "Invalid credentials. Try again."

        except ClientError as e:
            return f"Error accessing database: {e.response['Error']['Message']}"

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

# Additional Pages
@app.route('/profile')
def profile():
    return render_template('profile.html', username=session.get('username'))

@app.route('/hotel')
def hotel():
    return render_template('hotel.html', username=session.get('username'))

@app.route('/hoteldashboard')
def hoteldashboard():
    return render_template('hoteldashboard.html', username=session.get('username'))

@app.route('/busfilter')
def busfilter():
    return render_template('busfilter.html', username=session.get('username'))

@app.route('/busdashboard')
def busdashboard():
    return render_template('busdashboard.html', username=session.get('username'))

@app.route('/flightfilter')
def flightfilter():
    return render_template('flightfilter.html', username=session.get('username'))

@app.route('/flightdashboard')
def flightdashboard():
    return render_template('flightdashboard.html', username=session.get('username'))

@app.route('/trainfilter')
def trainfilter():
    return render_template('trainfilter.html', username=session.get('username'))

@app.route('/traindashboard')
def traindashboard():
    return render_template('traindashboard.html', username=session.get('username'))

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
