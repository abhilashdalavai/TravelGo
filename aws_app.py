from flask import Flask, render_template, request, redirect, session
import uuid
import boto3
import os
from decimal import Decimal
from boto3.dynamodb.conditions import Key
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'devkey')

# AWS Setup
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
sns = boto3.client('sns', region_name='us-east-1')

# SNS Topic ARN from environment
# SNS Topic ARN from environment or fallback to default
SNS_TOPIC_ARN = os.getenv('SNS_TOPIC_ARN', 'arn:aws:sns:us-east-1:842676002305:TravelGo')

# Tables
users_table = dynamodb.Table('travel-Users')
bookings_table = dynamodb.Table('Bookings')

# Static Data (buses, trains, flights, hotels) — same as before...
transport_data = {
    'bus': [
        {'id': 'B001', 'name': 'Sharma Travels', 'source': 'Delhi', 'destination': 'Jaipur', 'departure': '08:00', 'arrival': '14:00', 'price': 800, 'seats': 40},
        {'id': 'B002', 'name': 'Patel Tours', 'source': 'Mumbai', 'destination': 'Goa', 'departure': '20:00', 'arrival': '08:00', 'price': 1200, 'seats': 35},
        {'id': 'B003', 'name': 'Royal Express', 'source': 'Bangalore', 'destination': 'Chennai', 'departure': '06:00', 'arrival': '12:00', 'price': 600, 'seats': 45}
    ],
    'train': [
        {'id': 'T001', 'name': 'Rajdhani Express', 'source': 'Delhi', 'destination': 'Mumbai', 'departure': '16:00', 'arrival': '08:00', 'price': 1500, 'seats': 300},
        {'id': 'T002', 'name': 'Shatabdi Express', 'source': 'Chennai', 'destination': 'Bangalore', 'departure': '06:00', 'arrival': '11:00', 'price': 800, 'seats': 250},
        {'id': 'T003', 'name': 'Duronto Express', 'source': 'Kolkata', 'destination': 'Delhi', 'departure': '22:00', 'arrival': '12:00', 'price': 1800, 'seats': 350}
    ],
    'flight': [
        {'id': 'F001', 'name': 'Air India', 'source': 'Delhi', 'destination': 'Bangalore', 'departure': '07:00', 'arrival': '09:30', 'price': 4500, 'seats': 180},
        {'id': 'F002', 'name': 'IndiGo', 'source': 'Mumbai', 'destination': 'Delhi', 'departure': '12:00', 'arrival': '14:00', 'price': 3500, 'seats': 160},
        {'id': 'F003', 'name': 'SpiceJet', 'source': 'Kolkata', 'destination': 'Chennai', 'departure': '15:00', 'arrival': '17:30', 'price': 4000, 'seats': 170}
    ]
}

hotel_data = [
    {'id': 'H001', 'name': 'Taj Mahal Palace', 'location': 'Mumbai', 'price': 12000, 'rooms': 50, 'rating': 4.8},
    {'id': 'H002', 'name': 'The Oberoi', 'location': 'Delhi', 'price': 10000, 'rooms': 40, 'rating': 4.7},
    {'id': 'H003', 'name': 'ITC Grand Chola', 'location': 'Chennai', 'price': 9000, 'rooms': 60, 'rating': 4.6},
    {'id': 'H004', 'name': 'The Lalit', 'location': 'Bangalore', 'price': 8000, 'rooms': 45, 'rating': 4.5},
    {'id': 'H005', 'name': 'Radisson Blu', 'location': 'Goa', 'price': 7500, 'rooms': 55, 'rating': 4.4}
]

@app.route('/')
def home():
    return render_template('index.html', logged_in='user' in session)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        try:
            response = users_table.get_item(Key={'email': email})
            if 'Item' in response:
                return render_template('register.html', message="User already exists.")
            hashed_pw = generate_password_hash(request.form['password'])
            users_table.put_item(Item={
                'email': email,
                'name': request.form['name'],
                'password': hashed_pw,
                'logins': Decimal(0)
            })
            return redirect('/login')
        except Exception as e:
            print("DynamoDB error in register:", e)
            return render_template('register.html', message="Error occurred. Please try again.")
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        try:
            response = users_table.get_item(Key={'email': email})
            user = response.get('Item')
            if user and check_password_hash(user['password'], password):
                session['user'] = email
                users_table.update_item(
                    Key={'email': email},
                    UpdateExpression="SET logins = if_not_exists(logins, :start) + :inc",
                    ExpressionAttributeValues={':inc': Decimal(1), ':start': Decimal(0)}
                )
                return '''
                    <script>
                        localStorage.setItem("loggedIn", "true");
                        window.location.href = "/dashboard";
                    </script>
                '''
            return render_template('login.html', message="Invalid credentials.")
        except Exception as e:
            print("DynamoDB error in login:", e)
            return render_template('login.html', message="Error occurred. Please try again.")
    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect('/login')
    email = session['user']
    try:
        user_resp = users_table.get_item(Key={'email': email})
        user = user_resp.get('Item')
        response = bookings_table.query(
            KeyConditionExpression=Key('email').eq(email)
        )
        bookings = response.get('Items', [])
        return render_template('dashboard.html', name=user['name'], bookings=bookings)
    except Exception as e:
        print("DynamoDB error in dashboard:", e)
        return redirect('/login')

@app.route('/bus', methods=['GET', 'POST'])
def bus():
    if request.method == 'POST':
        s, d, dt = request.form['source'], request.form['destination'], request.form['date']
        buses = [b for b in transport_data['bus'] if b['source'] == s and b['destination'] == d]
        return render_template('bus.html', buses=buses, source=s, destination=d, date=dt)
    return render_template('bus.html', buses=None)

@app.route('/train', methods=['GET', 'POST'])
def train():
    if request.method == 'POST':
        s, d, dt = request.form['source'], request.form['destination'], request.form['date']
        trains = [t for t in transport_data['train'] if t['source'] == s and t['destination'] == d]
        return render_template('train.html', trains=trains, source=s, destination=d, date=dt)
    return render_template('train.html', trains=None)

@app.route('/flight', methods=['GET', 'POST'])
def flight():
    if request.method == 'POST':
        s, d, dt = request.form['source'], request.form['destination'], request.form['date']
        flights = [f for f in transport_data['flight'] if f['source'] == s and f['destination'] == d]
        return render_template('flight.html', flights=flights, source=s, destination=d, date=dt)
    return render_template('flight.html', flights=None)

@app.route('/hotels', methods=['GET', 'POST'])
def hotels():
    if request.method == 'POST':
        city = request.form['city']
        hotels = [h for h in hotel_data if h['location'] == city]
        return render_template('hotels.html', hotels=hotels, city=city)
    return render_template('hotels.html', hotels=None)

@app.route('/select_seats')
def select_seats():
    return render_template("select_seats.html")

@app.route('/book', methods=['POST'])
def book():
    if 'user' not in session:
        return redirect('/login')
    session['pending_booking'] = {
        "booking_id": str(uuid.uuid4())[:8],
        "type": request.form['type'],
        "source": request.form['source'],
        "destination": request.form['destination'],
        "date": request.form['date'],
        "seat": request.form.get('seat', 'N/A'),
        "details": request.form['details'],
        "price": Decimal(request.form['price']),
        "user_email": session['user'],
        "email": session['user']
    }
    return render_template("payment.html", booking=session['pending_booking'])

@app.route('/payment', methods=['POST'])
def payment():
    if 'user' not in session or 'pending_booking' not in session:
        return redirect('/login')
    booking = session.pop('pending_booking')
    booking['payment_method'] = request.form['method']
    booking['payment_reference'] = request.form['reference']
    try:
        bookings_table.put_item(Item=booking)
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=f"✅ Booking Confirmed!\n{booking['details']} on {booking['date']} for ₹{booking['price']}",
            Subject="TravelGo Booking Confirmation"
        )
    except Exception as e:
        print("Booking or SNS error:", e)
    return redirect('/dashboard')

@app.route('/remove_booking', methods=['POST'])
def remove_booking():
    if 'user' not in session:
        return redirect('/login')
    email = session['user']
    booking_id = request.form.get('booking_id')
    try:
        bookings_table.delete_item(
            Key={'email': email, 'booking_id': booking_id}
        )
        sns.publish(
            TopicArn=SNS_TOPIC_ARN,
            Message=f"❌ Booking Canceled\nBooking ID: {booking_id}",
            Subject="TravelGo Cancellation"
        )
    except Exception as e:
        print("Delete booking or SNS error:", e)
    return redirect('/dashboard')

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
