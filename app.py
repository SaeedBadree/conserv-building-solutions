from flask import Flask, render_template, request, redirect, url_for, jsonify, flash
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, UserMixin, login_user, logout_user, current_user, login_required
import requests

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SECRET_KEY'] = 'supersecretkey'  # Replace with a strong secret key
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# API Keys
WIPAY_API_KEY = "YOUR_WIPAY_API_KEY"  # Replace with your WiPay API key
GOOGLE_MAPS_API_KEY = "AIzaSyAL_nbXfK7r9gRcY2D8VXJ2GQEJmrEvTbw"  # Replace with your Google Maps API key

# Models
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_name = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Float, nullable=False)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Routes
@app.route('/')
def index():
    return render_template('index.html')  # Ensure the home page renders correctly

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    print("Rendering signup.html")
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = bcrypt.generate_password_hash(request.form['password']).decode('utf-8')
        
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        
        flash('Account created successfully!', 'success')
        return redirect(url_for('login'))
    return render_template('signup.html')




@app.route('/verify-address', methods=['GET', 'POST'])
def verify_address():
    if request.method == 'POST':
        address = request.form['address']

        # Log the received address for debugging
        print(f"Address received: {address}")

        # Call Google Maps API
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": address, "key": GOOGLE_MAPS_API_KEY}
        )
        data = response.json()
        print("Google Maps API Response:", data)  # Log the API response

        # If the address is valid
        if response.status_code == 200 and data['results']:
            location = data['results'][0]['geometry']['location']
            formatted_address = data['results'][0]['formatted_address']
            return render_template(
                'verify_address.html',
                address=formatted_address,
                lat=location['lat'],
                lng=location['lng']
            )

        # If the address is invalid
        flash("Invalid address. Please try again.", "danger")
        return redirect(url_for('verify_address'))

    # Render the verification form for a GET request
    return render_template('verify_address.html')



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Login failed. Check your email and password.', 'danger')
    return render_template('login.html')

@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

@app.route('/payment', methods=['GET', 'POST'])
@login_required
def payment():
    if request.method == 'POST':
        product_name = request.form['product_name']
        amount = request.form['amount']
        order = Order(user_id=current_user.id, product_name=product_name, amount=amount)
        db.session.add(order)
        db.session.commit()

        # WiPay API request
        payment_data = {
            "order_id": str(order.id),
            "amount": amount,
            "currency": "TTD",
            "redirect_url": url_for('payment_success', _external=True),
            "callback_url": url_for('payment_callback', _external=True),
        }
        headers = {"Authorization": f"Bearer {WIPAY_API_KEY}"}
        response = requests.post("https://sandbox-api.wipayfinancial.com/v1/payments", json=payment_data, headers=headers)

        if response.status_code == 200:
            payment_url = response.json().get('payment_url')
            return redirect(payment_url)
        else:
            flash('Payment initiation failed.', 'danger')

    return render_template('payment.html')

@app.route('/payment-callback', methods=['POST'])
def payment_callback():
    data = request.json
    print("Payment callback received:", data)
    return jsonify({"status": "success"}), 200

@app.route('/payment-success')
def payment_success():
    flash('Payment successful!', 'success')
    return render_template('success.html')



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
