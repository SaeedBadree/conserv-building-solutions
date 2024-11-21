import requests
from flask import Flask, request, jsonify, redirect

app = Flask(__name__)

GOOGLE_MAPS_API_KEY = "AIzaSyAL_nbXfK7r9gRcY2D8VXJ2GQEJmrEvTbw"

# Address verification route
@app.route('/verify-address', methods=['GET'])
def verify_address():
    address = request.args.get('address')
    if not address:
        return jsonify({"valid": False, "error": "Address is required"}), 400

    # Call Google Maps API for geocoding
    response = requests.get(
        "https://maps.googleapis.com/maps/api/geocode/json",
        params={"address": address, "key": GOOGLE_MAPS_API_KEY}
    )
    data = response.json()

    # Check if the response contains results
    if response.status_code == 200 and data['results']:
        # Verify if the address is in Trinidad and Tobago
        for component in data['results'][0]['address_components']:
            if "country" in component['types'] and component['short_name'] == "TT":
                return jsonify({"valid": True})
        return jsonify({"valid": False, "error": "Address is not in Trinidad and Tobago"}), 400
    else:
        return jsonify({"valid": False, "error": "Invalid address"}), 400

@app.route('/pay', methods=['POST'])
def pay():
    order_id = request.form['order_id']
    amount = request.form['amount']

    payment_data = {
        "order_id": order_id,
        "amount": amount,
        "currency": "TTD",
        "redirect_url": "https://your-frontend-url/payment-success",
        "callback_url": "https://your-backend-url/payment-callback"
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer YOUR_WIPAY_SANDBOX_API_KEY"
    }

    response = requests.post(
        "https://sandbox-api.wipayfinancial.com/v1/payments",
        json=payment_data,
        headers=headers
    )

    if response.status_code == 200:
        payment_url = response.json().get("payment_url")
        return redirect(payment_url)
    else:
        return jsonify({"error": "Payment failed", "details": response.json()}), 400

if __name__ == "__main__":
    app.run(debug=True)
