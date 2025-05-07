"""
Paysafe Python SDK Demo Website

A simple Flask application that demonstrates how to use the Paysafe Python SDK.
"""

import os
import logging
from datetime import datetime, timedelta

from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
from dotenv import load_dotenv

import paysafe
from paysafe.models.payment import Payment, CardPaymentMethod
from paysafe.models.customer import Customer, CustomerBillingDetails

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.DEBUG)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "paysafesdk-demo-secret-key")

# Initialize Paysafe client
PAYSAFE_API_KEY = os.environ.get("PAYSAFE_API_KEY")
PAYSAFE_CREDENTIALS_FILE = os.environ.get("PAYSAFE_CREDENTIALS_FILE")
paysafe_client = None

# Try to initialize the client with different credential sources
if PAYSAFE_API_KEY:
    logging.info("Initializing Paysafe client with API key from environment variable")
    paysafe_client = paysafe.Client(
        api_key=PAYSAFE_API_KEY,
        environment="sandbox"  # Use 'production' for live environment
    )
elif PAYSAFE_CREDENTIALS_FILE:
    logging.info(f"Initializing Paysafe client with credentials file: {PAYSAFE_CREDENTIALS_FILE}")
    try:
        paysafe_client = paysafe.Client(
            credentials_file=PAYSAFE_CREDENTIALS_FILE,
            environment="sandbox"
        )
    except Exception as e:
        logging.error(f"Error loading credentials file: {str(e)}")
else:
    logging.warning("No API key or credentials file provided. "
                 "Set either PAYSAFE_API_KEY or PAYSAFE_CREDENTIALS_FILE environment variable.")


@app.route('/')
def index():
    """Homepage."""
    credentials_available = bool(paysafe_client)
    credentials_source = None
    
    if PAYSAFE_API_KEY:
        credentials_source = "API_KEY"
    elif PAYSAFE_CREDENTIALS_FILE:
        credentials_source = "CREDENTIALS_FILE"
    
    return render_template('index.html', 
                          credentials_available=credentials_available,
                          credentials_source=credentials_source)


@app.route('/payments')
def payments():
    """List payments."""
    if not paysafe_client:
        flash("Paysafe credentials not available. Please set either PAYSAFE_API_KEY or PAYSAFE_CREDENTIALS_FILE environment variable.", "error")
        return redirect(url_for('index'))
    
    try:
        # Get payments from the last 30 days
        thirty_days_ago = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        today = datetime.now().strftime("%Y-%m-%d")
        
        payment_list = paysafe.Payment.list(
            client=paysafe_client,
            created_from=thirty_days_ago,
            created_to=today,
            limit=10
        )
        
        return render_template('payments.html', payments=payment_list)
    except Exception as e:
        flash(f"Error fetching payments: {str(e)}", "error")
        return redirect(url_for('index'))


@app.route('/payment/create', methods=['GET', 'POST'])
def create_payment():
    """Create a new payment."""
    if not paysafe_client:
        flash("Paysafe credentials not available. Please set either PAYSAFE_API_KEY or PAYSAFE_CREDENTIALS_FILE environment variable.", "error")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # Create payment with provided form data
            payment = paysafe.Payment.create(
                client=paysafe_client,
                payment_method="card",
                amount=int(float(request.form['amount']) * 100),  # Convert to cents
                currency_code=request.form['currency_code'],
                card={
                    "card_number": request.form['card_number'],
                    "expiry_month": int(request.form['expiry_month']),
                    "expiry_year": int(request.form['expiry_year']),
                    "cvv": request.form['cvv']
                },
                merchant_reference_number=f"demo-{datetime.now().strftime('%Y%m%d%H%M%S')}",
                description=request.form['description']
            )
            
            flash(f"Payment created successfully! ID: {payment.id}", "success")
            return redirect(url_for('payment_detail', payment_id=payment.id))
        except Exception as e:
            flash(f"Error creating payment: {str(e)}", "error")
    
    return render_template('create_payment.html')


@app.route('/payment/<payment_id>')
def payment_detail(payment_id):
    """Show payment details."""
    if not paysafe_client:
        flash("Paysafe credentials not available. Please set either PAYSAFE_API_KEY or PAYSAFE_CREDENTIALS_FILE environment variable.", "error")
        return redirect(url_for('index'))
    
    try:
        payment = paysafe.Payment.retrieve(
            client=paysafe_client,
            payment_id=payment_id
        )
        
        return render_template('payment_detail.html', payment=payment)
    except Exception as e:
        flash(f"Error fetching payment: {str(e)}", "error")
        return redirect(url_for('payments'))


@app.route('/customers')
def customers():
    """List customers."""
    if not paysafe_client:
        flash("Paysafe API key not set. Please set the PAYSAFE_API_KEY environment variable.", "error")
        return redirect(url_for('index'))
    
    try:
        customer_list = paysafe.Customer.list(
            client=paysafe_client,
            limit=10
        )
        
        return render_template('customers.html', customers=customer_list)
    except Exception as e:
        flash(f"Error fetching customers: {str(e)}", "error")
        return redirect(url_for('index'))


@app.route('/customer/create', methods=['GET', 'POST'])
def create_customer():
    """Create a new customer."""
    if not paysafe_client:
        flash("Paysafe API key not set. Please set the PAYSAFE_API_KEY environment variable.", "error")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            # Create customer with provided form data
            customer = paysafe.Customer.create(
                client=paysafe_client,
                email=request.form['email'],
                first_name=request.form['first_name'],
                last_name=request.form['last_name'],
                phone=request.form.get('phone'),
                billing_details={
                    "street": request.form.get('street'),
                    "city": request.form.get('city'),
                    "state": request.form.get('state'),
                    "country": request.form.get('country'),
                    "zip": request.form.get('zip')
                }
            )
            
            flash(f"Customer created successfully! ID: {customer.id}", "success")
            return redirect(url_for('customer_detail', customer_id=customer.id))
        except Exception as e:
            flash(f"Error creating customer: {str(e)}", "error")
    
    return render_template('create_customer.html')


@app.route('/customer/<customer_id>')
def customer_detail(customer_id):
    """Show customer details."""
    if not paysafe_client:
        flash("Paysafe API key not set. Please set the PAYSAFE_API_KEY environment variable.", "error")
        return redirect(url_for('index'))
    
    try:
        customer = paysafe.Customer.retrieve(
            client=paysafe_client,
            customer_id=customer_id
        )
        
        return render_template('customer_detail.html', customer=customer)
    except Exception as e:
        flash(f"Error fetching customer: {str(e)}", "error")
        return redirect(url_for('customers'))


@app.route('/api/payment_status/<payment_id>')
def api_payment_status(payment_id):
    """API endpoint to check payment status."""
    if not paysafe_client:
        return jsonify({"error": "API key not configured"}), 500
    
    try:
        payment = paysafe.Payment.retrieve(
            client=paysafe_client,
            payment_id=payment_id
        )
        
        return jsonify({
            "payment_id": payment.id,
            "status": payment.status,
            "amount": payment.amount,
            "currency": payment.currency_code
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 400


if __name__ == '__main__':
    # Check if API key is configured
    if not PAYSAFE_API_KEY:
        logging.warning("PAYSAFE_API_KEY environment variable not set. "
                     "The demo will run but API functions will not work.")
    
    # Start the development server
    app.run(host='0.0.0.0', port=5000, debug=True)