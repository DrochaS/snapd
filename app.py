"""
🏋️ THE TKAY CHALLENGE WEBSITE WITH INTASEND - COMPLETE FIXED VERSION
All imports included - No undefined variables!
"""

# ============================================
# ALL REQUIRED IMPORTS - EVERYTHING IS HERE!
# ============================================
import os
import logging
import uuid
import functools
import traceback
import sys
import re
from datetime import datetime
from flask import Flask, request, redirect, session, url_for
from intasend import APIService
from dotenv import load_dotenv
import gspread
from oauth2client.service_account import ServiceAccountCredentials

# Load environment variables with ABSOLUTE PATH
ENV_PATH = '/home/drocha/gym-website/.env'
load_dotenv(ENV_PATH)
print(f"Loading .env from: {ENV_PATH}", file=sys.stderr)
print(f"File exists: {os.path.exists(ENV_PATH)}", file=sys.stderr)
print(f"INTASEND_PUBLISHABLE_KEY exists: {bool(os.getenv('INTASEND_PUBLISHABLE_KEY'))}", file=sys.stderr)
print(f"INTASEND_SECRET_TOKEN exists: {bool(os.getenv('INTASEND_SECRET_TOKEN'))}", file=sys.stderr)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')
logger = logging.getLogger(__name__)

# Create Flask app
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', os.urandom(24))


def normalize_phone(phone_value):
    """Normalize phone inputs to the required 254 format."""
    if phone_value is None:
        return ''

    cleaned = phone_value.strip()
    cleaned = cleaned.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')
    cleaned = cleaned.replace('+', '')

    if cleaned.startswith('254') and len(cleaned) == 12 and cleaned.isdigit():
        return cleaned
    if cleaned.startswith('0') and len(cleaned) == 10 and cleaned.isdigit():
        return '254' + cleaned[1:]
    if cleaned.isdigit() and len(cleaned) == 12:
        return cleaned if cleaned.startswith('254') else ''
    return cleaned if cleaned.isdigit() and cleaned.startswith('254') else ''


# ============================================
# INTASEND CONFIGURATION
# ============================================
PUBLISHABLE_KEY = os.getenv('INTASEND_PUBLISHABLE_KEY')
SECRET_TOKEN = os.getenv('INTASEND_SECRET_TOKEN')
TEST_MODE = os.getenv('INTASEND_TEST_MODE', 'False').lower() == 'true'

# Initialize IntaSend
try:
    INTASEND_SERVICE = APIService(
        token=SECRET_TOKEN,
        publishable_key=PUBLISHABLE_KEY,
        test=TEST_MODE
    )
    logger.info("✅ IntaSend initialized")
except Exception as e:  # pylint: disable=broad-exception-caught
    logger.error("❌ IntaSend failed: %s", e)
    INTASEND_SERVICE = None

# Program details - Read from .env
PROGRAM_FEE = int(os.getenv('PROGRAM_FEE', '1500'))
PROGRAM_NAME = os.getenv('PROGRAM_NAME', 'The Tkay Challenge')
PROGRAM_LINK = os.getenv('PROGRAM_LINK', 'https://chat.whatsapp.com/CsNACCVEIyOHgglAxmW9XN')
CURRENCY = os.getenv('CURRENCY', 'KES')

# Admin credentials
ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'gym123')

# ============================================
# GOOGLE SHEETS SETUP - FIXED WITH ABSOLUTE PATH
# ============================================
def setup_google_sheets():
    """Connect to Google Sheets using absolute path"""
    try:
        scope = [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive"
        ]

        # Use ABSOLUTE path to the file
        credentials_path = '/home/drocha/gym-website/gym-credentials.json'

        if not os.path.exists(credentials_path):
            logger.warning("⚠️  gym-credentials.json not found at %s", credentials_path)
            logger.warning("Current directory: %s", os.getcwd())
            logger.warning("Google Sheets will be disabled")
            return None

        creds = ServiceAccountCredentials.from_json_keyfile_name(
            credentials_path, scope
        )
        client = gspread.authorize(creds)

        sheet_name = os.getenv('GOOGLE_SHEET_NAME', 'Tkay Challenge Members')
        sheet = client.open(sheet_name).sheet1

        # Check if headers exist
        headers = sheet.row_values(1)
        expected_headers = [
            'Timestamp', 'Name', 'Age', 'Height (cm)', 'Weight (kg)',
            'Email', 'Phone', 'Amount (KES)', 'Registration ID',
            'Invoice ID', 'Status', 'Program'
        ]

        if not headers or headers[0] != 'Timestamp':
            sheet.clear()
            sheet.append_row(expected_headers)
            logger.info("✅ Added headers to Google Sheet")

        logger.info("✅ Connected to Google Sheet: %s", sheet_name)
        return sheet

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("❌ Google Sheets error: %s", e)
        return None

google_sheet = setup_google_sheets()

def save_member_to_sheets(member_data, invoice_id, status):
    """Save member details to Google Sheets"""
    try:
        if not google_sheet:
            return False

        row = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            member_data.get('name', ''),
            member_data.get('age', ''),
            member_data.get('height', ''),
            member_data.get('weight', ''),
            member_data.get('email', ''),
            member_data.get('phone', ''),
            member_data.get('amount', PROGRAM_FEE),
            member_data.get('registration_id', ''),
            invoice_id,
            status,
            PROGRAM_NAME
        ]

        google_sheet.append_row(row)
        logger.info("✅ Member saved: %s", member_data.get('email'))
        return True

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("❌ Sheets save error: %s", e)
        return False

# ============================================
# MIDDLEWARE: Disable F12 and Right-Click
# ============================================
@app.after_request
def add_security_headers(response):
    """Add headers to disable F12 and right-click"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    return response

def inject_disable_f12():
    """JavaScript to disable F12, right-click, and dev tools"""
    return '''
    <script>
        // Disable right-click
        document.addEventListener('contextmenu', function(e) {
            e.preventDefault();
            return false;
        });

        // Disable F12, Ctrl+Shift+I, Ctrl+Shift+J, Ctrl+U
        document.addEventListener('keydown', function(e) {
            // F12
            if (e.key === 'F12' || e.keyCode === 123) {
                e.preventDefault();
                return false;
            }

            // Ctrl+Shift+I (Windows)
            if (e.ctrlKey && e.shiftKey && e.key === 'I') {
                e.preventDefault();
                return false;
            }

            // Ctrl+Shift+J (Windows)
            if (e.ctrlKey && e.shiftKey && e.key === 'J') {
                e.preventDefault();
                return false;
            }

            // Ctrl+U (View Source)
            if (e.ctrlKey && e.key === 'u') {
                e.preventDefault();
                return false;
            }

            // Ctrl+Shift+C (Inspect)
            if (e.ctrlKey && e.shiftKey && e.key === 'C') {
                e.preventDefault();
                return false;
            }
        });

        // Detect DevTools opening (optional, not 100% reliable)
        setInterval(function() {
            if (window.outerHeight - window.innerHeight > 200 ||
                window.outerWidth - window.innerWidth > 200) {
                // DevTools might be open - optional action
                console.clear();
            }
        }, 1000);
    </script>
    '''

# ============================================
# ADMIN LOGIN DECORATOR
# ============================================
def admin_required(f):
    """Decorator to require admin login."""
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# ============================================
# ROUTES
# ============================================
@app.route('/')
def index():
    """Homepage with registration form - Mobile & Desktop Responsive"""
    disable_f12 = inject_disable_f12()

    return f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=yes">
        <title>Join {PROGRAM_NAME}</title>
        {disable_f12}
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            }}

            body {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 15px;
            }}

            .container {{
                width: 100%;
                max-width: 500px;
                background: white;
                border-radius: 24px;
                padding: 30px 20px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                animation: slideUp 0.5s ease;
            }}

            @keyframes slideUp {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}

            /* Desktop styles (max-width > 768px) */
            @media (min-width: 769px) {{
                .container {{
                    padding: 40px;
                }}

                h1 {{
                    font-size: 32px !important;
                }}

                .price-tag {{
                    padding: 25px !important;
                }}

                .price {{
                    font-size: 48px !important;
                }}
            }}

            /* Mobile styles (max-width 768px) */
            @media (max-width: 768px) {{
                .container {{
                    padding: 20px 15px;
                    border-radius: 20px;
                }}

                h1 {{
                    font-size: 24px !important;
                }}

                .price-tag {{
                    padding: 15px !important;
                }}

                .price {{
                    font-size: 36px !important;
                }}

                input {{
                    padding: 12px !important;
                    font-size: 16px !important;
                }}

                button {{
                    padding: 16px !important;
                    font-size: 18px !important;
                }}

                .info-box {{
                    padding: 15px !important;
                }}
            }}

            h1 {{
                color: #333;
                text-align: center;
                margin-bottom: 10px;
                font-size: 28px;
                font-weight: 700;
            }}

            .price-tag {{
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: white;
                text-align: center;
                padding: 20px;
                border-radius: 16px;
                margin: 20px 0;
                box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
            }}

            .price {{
                font-size: 42px;
                font-weight: 800;
                display: block;
                line-height: 1.2;
            }}

            .currency {{
                font-size: 18px;
                opacity: 0.9;
                display: block;
                margin-bottom: 5px;
            }}

            .form-group {{
                margin-bottom: 20px;
            }}

            label {{
                display: block;
                margin-bottom: 8px;
                font-weight: 600;
                color: #555;
                font-size: 14px;
            }}

            input {{
                width: 100%;
                padding: 14px 16px;
                border: 2px solid #e0e0e0;
                border-radius: 12px;
                font-size: 15px;
                transition: all 0.3s;
                background: #f8f9fa;
            }}

            input:focus {{
                border-color: #4CAF50;
                outline: none;
                background: white;
                box-shadow: 0 0 0 4px rgba(76, 175, 80, 0.1);
            }}

            button {{
                width: 100%;
                padding: 16px;
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: white;
                border: none;
                border-radius: 12px;
                font-size: 18px;
                font-weight: 700;
                cursor: pointer;
                transition: all 0.3s;
                margin-top: 20px;
                box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
            }}

            button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
            }}

            button:active {{
                transform: translateY(0);
            }}

            .info-box {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 16px;
                margin-top: 30px;
                font-size: 14px;
                border: 1px solid #e0e0e0;
            }}

            .info-box p {{
                margin: 8px 0;
                display: flex;
                align-items: center;
                gap: 10px;
                color: #555;
            }}

            .phone-hint {{
                color: #666;
                font-size: 12px;
                margin-top: 5px;
                padding-left: 5px;
            }}

            .admin-link {{
                text-align: center;
                margin-top: 20px;
                font-size: 12px;
            }}

            .admin-link a {{
                color: #999;
                text-decoration: none;
            }}

            .admin-link a:hover {{
                color: #4CAF50;
            }}

            /* Loading animation */
            .loading {{
                display: none;
                text-align: center;
                margin-top: 10px;
            }}

            .loading.active {{
                display: block;
            }}

            .spinner {{
                border: 3px solid #f3f3f3;
                border-top: 3px solid #4CAF50;
                border-radius: 50%;
                width: 24px;
                height: 24px;
                animation: spin 1s linear infinite;
                margin: 10px auto;
            }}

            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏋️ {PROGRAM_NAME}</h1>

            <div class="price-tag">
                <span class="currency">{CURRENCY}</span>
                <span class="price" id="programFee">{PROGRAM_FEE:,}</span>
            </div>

            <form action="/register" method="POST" id="registrationForm" onsubmit="return validateForm()">
                <div class="form-group">
                    <label>📝 Full Name</label>
                    <input type="text" name="name" required placeholder="John Doe">
                </div>

                <div class="form-group">
                    <label>🎂 Age</label>
                    <input type="number" name="age" required min="18" max="100" placeholder="25">
                </div>

                <div class="form-group">
                    <label>📏 Height (cm)</label>
                    <input type="number" name="height" required min="100" max="250" step="0.1" placeholder="175">
                </div>

                <div class="form-group">
                    <label>⚖️ Weight (kg)</label>
                    <input type="number" name="weight" required min="30" max="200" step="0.1" placeholder="70">
                </div>

                <div class="form-group">
                    <label>📧 Email</label>
                    <input type="email" name="email" required placeholder="john@example.com">
                </div>

                <div class="form-group">
                    <label>📱 M-Pesa Number</label>
                    <input type="text" name="phone" required
                           inputmode="numeric"
                           autocomplete="tel"
                           placeholder="254712345678"
                           pattern="254[0-9]{{9}}"
                           title="Use format: 2547XXXXXXXX"
                           id="phone">
                    <div class="phone-hint">Use only the 254 format (example: 254712345678)</div>
                </div>

                <button type="submit" id="payButton">
                    Pay {CURRENCY} <span id="buttonAmount">{PROGRAM_FEE:,}</span> via M-Pesa
                </button>

                <div class="loading" id="loading">
                    <div class="spinner"></div>
                    <p>Processing... Please check your phone</p>
                </div>
            </form>

            <div class="info-box">
                <p>✅ <strong>Secure Payment</strong> via IntaSend</p>
                <p>📱 <strong>M-Pesa STK Push</strong> sent to your phone</p>
                <p>⚡ <strong>Instant Access</strong> after payment</p>
                <p>🔒 <strong>256-bit SSL</strong> encrypted</p>
            </div>

            <div class="admin-link">
                <a href="/admin">⚙️ Admin Area</a>
            </div>
        </div>

        <script>
            // Form validation
            function normalizePhone(rawPhone) {{
                const digitsOnly = rawPhone.replace(/\\D/g, '');

                if (digitsOnly.startsWith('254') && digitsOnly.length === 12) {{
                    return digitsOnly;
                }}

                if (digitsOnly.startsWith('0') && digitsOnly.length === 10) {{
                    return '254' + digitsOnly.slice(1);
                }}

                return digitsOnly;
            }}

            function validateForm() {{
                const rawPhone = document.getElementById('phone').value;
                const phone = normalizePhone(rawPhone);
                const payButton = document.getElementById('payButton');
                const loading = document.getElementById('loading');

                if (!/^254\\d{{9}}$/.test(phone)) {{
                    alert('❌ Use format: 2547XXXXXXXX');
                    return false;
                }}

                document.getElementById('phone').value = phone;

                // Show loading
                payButton.style.display = 'none';
                loading.classList.add('active');

                return true;
            }}

            // Disable text selection
            document.onselectstart = function() {{ return false; }};

            // Disable copy
            document.oncopy = function() {{ return false; }};

            // Check if mobile
            function isMobile() {{
                return window.innerWidth <= 768;
            }}

            // Adjust for mobile
            if (isMobile()) {{
                document.body.style.padding = '10px';
            }}

            // Prevent zoom on input focus (mobile)
            document.querySelectorAll('input').forEach(input => {{
                input.addEventListener('focus', function() {{
                    if (isMobile()) {{
                        setTimeout(() => {{
                            window.scrollTo(0, 0);
                        }}, 300);
                    }}
                }});
            }});
        </script>
    </body>
    </html>
    '''

@app.route('/register', methods=['POST'])
def register():
    """Handle registration and initiate IntaSend STK Push"""

    try:
        registration_id = str(uuid.uuid4())[:8].upper()

        raw_phone = request.form.get('phone', '')
        normalized_phone = normalize_phone(raw_phone)

        member = {
            'name': request.form['name'].strip(),
            'age': int(request.form['age']),
            'height': float(request.form['height']),
            'weight': float(request.form['weight']),
            'email': request.form['email'].strip().lower(),
            'phone': normalized_phone,
            'amount': PROGRAM_FEE,
            'registration_id': registration_id,
            'timestamp': datetime.now().isoformat()
        }

        # Validate phone
        if not re.fullmatch(r'254\d{9}', member['phone']):
            return "Invalid phone number. Use format: 2547XXXXXXXX"

        # Save to session
        session['member'] = member
        session['registration_id'] = registration_id

        if not INTASEND_SERVICE:
            logger.error("Payment service unavailable")
            return "Payment service unavailable. Please try again later."

        logger.info("Initiating payment for %s", member['phone'])

        # IntaSend STK Push
        response = INTASEND_SERVICE.collect.mpesa_stk_push(
            phone_number=member['phone'],
            email=member['email'],
            amount=member['amount'],
            narrative=f"{PROGRAM_NAME} - {member['name']}"
        )

        logger.info("IntaSend response: %s", response)

        # Extract invoice ID from response
        invoice_id = None
        if response and isinstance(response, dict):
            if response.get('invoice'):
                invoice_id = response['invoice'].get('invoice_id')
            elif response.get('id'):
                invoice_id = response.get('id')
            elif response.get('invoice_id'):
                invoice_id = response.get('invoice_id')

        if invoice_id:
            session['invoice_id'] = invoice_id
            logger.info("✅ Invoice ID: %s", invoice_id)

            # Save to Google Sheets - PENDING
            save_member_to_sheets(member, invoice_id, 'PENDING')

            # Redirect to processing page with invoice_id in URL
            return redirect(url_for('payment_processing', invoice_id=invoice_id))

        logger.error("Could not extract invoice_id from response: %s", response)
        return "Payment initiated but couldn't get invoice ID. Check IntaSend dashboard."

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Registration error: %s", str(e))
        traceback.print_exc()
        return f"Error: {str(e)}"

@app.route('/payment-processing/<invoice_id>')
def payment_processing(invoice_id):
    """Show payment processing page with auto-refresh"""
    disable_f12 = inject_disable_f12()
    member = session.get('member', {})

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Processing Payment</title>
        <meta http-equiv="refresh" content="5;/check-status/{invoice_id}">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {disable_f12}
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }}

            .container {{
                max-width: 450px;
                width: 100%;
                background: white;
                border-radius: 24px;
                padding: 30px;
                text-align: center;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                animation: pulse 2s infinite;
            }}

            @keyframes pulse {{
                0% {{ transform: scale(1); }}
                50% {{ transform: scale(1.02); }}
                100% {{ transform: scale(1); }}
            }}

            .spinner {{
                border: 5px solid #f3f3f3;
                border-top: 5px solid #4CAF50;
                border-radius: 50%;
                width: 60px;
                height: 60px;
                animation: spin 1s linear infinite;
                margin: 20px auto;
            }}

            @keyframes spin {{
                0% {{ transform: rotate(0deg); }}
                100% {{ transform: rotate(360deg); }}
            }}

            h2 {{
                color: #333;
                margin-bottom: 20px;
            }}

            .details {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 16px;
                margin: 20px 0;
                text-align: left;
            }}

            .detail-row {{
                display: flex;
                justify-content: space-between;
                margin: 10px 0;
                padding: 8px 0;
                border-bottom: 1px solid #e0e0e0;
            }}

            .detail-row:last-child {{
                border-bottom: none;
            }}

            .steps {{
                background: #e8f5e9;
                padding: 20px;
                border-radius: 16px;
                margin: 20px 0;
                text-align: left;
            }}

            .steps h3 {{
                color: #2e7d32;
                margin-bottom: 10px;
            }}

            .steps ol {{
                padding-left: 20px;
            }}

            .steps li {{
                margin: 8px 0;
                color: #1e5e24;
            }}

            .manual-check {{
                margin-top: 20px;
                padding: 15px;
                background: #fff3cd;
                border-radius: 10px;
            }}

            .manual-check button {{
                background: #ffc107;
                color: #333;
                border: none;
                padding: 10px 20px;
                border-radius: 5px;
                font-weight: bold;
                cursor: pointer;
                margin-top: 10px;
            }}

            .manual-check button:hover {{
                background: #e0a800;
            }}

            @media (max-width: 768px) {{
                .container {{
                    padding: 20px;
                }}

                .detail-row {{
                    flex-direction: column;
                    gap: 5px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="spinner"></div>

            <h2>⏳ Processing Your Payment</h2>
            <p style="color: #4CAF50; font-weight: bold;">Please check your phone for M-Pesa prompt</p>

            <div class="details">
                <div class="detail-row">
                    <strong>Name:</strong>
                    <span>{member.get('name', '')}</span>
                </div>
                <div class="detail-row">
                    <strong>Phone:</strong>
                    <span>{member.get('phone', '')}</span>
                </div>
                <div class="detail-row">
                    <strong>Amount:</strong>
                    <span>KES {member.get('amount', '')}</span>
                </div>
                <div class="detail-row">
                    <strong>Reference:</strong>
                    <span>{session.get('registration_id', '')}</span>
                </div>
                <div class="detail-row">
                    <strong>Invoice:</strong>
                    <span>{invoice_id}</span>
                </div>
            </div>

            <div class="steps">
                <h3>📱 Next Steps:</h3>
                <ol>
                    <li>Check your phone for M-Pesa STK Push prompt</li>
                    <li>Enter your M-Pesa PIN</li>
                    <li>Wait for confirmation message</li>
                    <li>You'll be redirected automatically</li>
                </ol>
            </div>

            <p style="color: #666; margin-top: 20px;">This page refreshes every 5 seconds to check payment status...</p>

            <div class="manual-check">
                <p><strong>Already paid but still stuck?</strong></p>
                <button onclick="window.location.href='/check-status/{invoice_id}'">
                    ✅ I've Already Paid - Check Now
                </button>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/check-status/<invoice_id>')
def check_status(invoice_id):
    """Check payment status via IntaSend"""

    if not invoice_id:
        logger.error("No invoice_id provided")
        return redirect('/')

    try:
        logger.info("Checking status for invoice: %s", invoice_id)

        # Get payment status from IntaSend
        status = INTASEND_SERVICE.collect.status(invoice_id=invoice_id)
        logger.info("Status check response: %s", status)

        # Check different possible status fields
        payment_state = None
        if isinstance(status, dict):
            payment_state = status.get('state') or status.get('status') or status.get('invoice', {}).get('state')

        logger.info("Payment state: %s", payment_state)

        # If payment is complete
        if payment_state in ('COMPLETE', 'completed', 'success'):
            member = session.get('member', {})

            # Update Google Sheets
            save_member_to_sheets(member, invoice_id, 'COMPLETE')

            # Clear session data
            session.pop('member', None)
            session.pop('invoice_id', None)
            session.pop('registration_id', None)

            logger.info("✅ Payment complete for invoice %s", invoice_id)
            return redirect(url_for('success'))

        # If payment failed
        if payment_state in ('FAILED', 'failed'):
            logger.warning("❌ Payment failed for invoice %s", invoice_id)
            return '''
            <div style="text-align: center; padding: 50px; font-family: Arial;">
                <h2 style="color: #f44336;">Payment Failed</h2>
                <p>Your payment was not successful. Please try again.</p>
                <a href="/" style="color: #4CAF50;">Back to Home</a>
            </div>
            '''

        # Still pending - redirect back to processing page
        logger.info("⏳ Payment still pending for invoice %s", invoice_id)
        return redirect(url_for('payment_processing', invoice_id=invoice_id))

    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Status check error: %s", e)
        traceback.print_exc()
        # If there's an error, redirect back to processing page
        return redirect(url_for('payment_processing', invoice_id=invoice_id))

@app.route('/success')
def success():
    """Success page with program link"""
    disable_f12 = inject_disable_f12()

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Welcome to {PROGRAM_NAME}!</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <meta http-equiv="refresh" content="5;url={PROGRAM_LINK}">
        {disable_f12}
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }}

            .container {{
                max-width: 500px;
                width: 100%;
                background: white;
                border-radius: 24px;
                padding: 40px;
                text-align: center;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
                animation: slideUp 0.5s ease;
            }}

            @keyframes slideUp {{
                from {{ opacity: 0; transform: translateY(20px); }}
                to {{ opacity: 1; transform: translateY(0); }}
            }}

            .success-icon {{
                font-size: 80px;
                margin-bottom: 20px;
            }}

            h1 {{
                color: #4CAF50;
                margin-bottom: 15px;
                font-size: 2.5em;
            }}

            .welcome-message {{
                font-size: 20px;
                color: #333;
                margin-bottom: 20px;
                line-height: 1.6;
            }}

            .program-button {{
                display: inline-block;
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%);
                color: white;
                text-decoration: none;
                padding: 16px 32px;
                border-radius: 50px;
                font-size: 18px;
                font-weight: bold;
                margin: 20px 0;
                box-shadow: 0 4px 15px rgba(76, 175, 80, 0.3);
                transition: all 0.3s;
                word-break: break-all;
            }}

            .program-button:hover {{
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(76, 175, 80, 0.4);
            }}

            .info {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 16px;
                margin-top: 20px;
                text-align: left;
            }}

            .info h3 {{
                color: #333;
                margin-bottom: 10px;
            }}

            .info ul {{
                padding-left: 20px;
                margin: 10px 0;
            }}

            .info li {{
                margin: 8px 0;
                color: #555;
            }}

            .countdown {{
                margin-top: 20px;
                padding: 10px;
                background: #e3f2fd;
                border-radius: 10px;
                color: #1976d2;
            }}

            .manual-redirect {{
                margin-top: 15px;
            }}

            .manual-redirect a {{
                color: #4CAF50;
                text-decoration: none;
                font-weight: bold;
            }}

            @media (max-width: 768px) {{
                .container {{
                    padding: 30px 20px;
                }}

                h1 {{
                    font-size: 28px;
                }}

                .program-button {{
                    font-size: 16px;
                    padding: 14px 25px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✅</div>

            <h1>Payment Successful!</h1>

            <div class="welcome-message">
                🎉 Welcome to {PROGRAM_NAME}! 🎉
            </div>

            <p style="font-size: 18px; margin-bottom: 20px;">
                Your payment has been processed successfully.
            </p>

            <a href="{PROGRAM_LINK}" target="_blank" class="program-button">
                👥 Join WhatsApp Group Now
            </a>

            <div class="info">
                <h3>📋 What's Next:</h3>
                <ul>
                    <li>✅ Click the button above to join our private WhatsApp group</li>
                    <li>📱 Save the group to your chats for easy access</li>
                    <li>👋 Introduce yourself to the community</li>
                    <li>📅 Check pinned messages for today's challenge</li>
                    <li>💪 Start your Tkay Challenge journey!</li>
                </ul>
            </div>

            <div class="countdown">
                ⏰ You'll be automatically redirected to WhatsApp in 5 seconds...
            </div>

            <div class="manual-redirect">
                <p>Not working? <a href="{PROGRAM_LINK}" target="_blank">Click here to join now</a></p>
            </div>

            <p style="color: #666; margin-top: 20px;">
                📧 Check your email for payment receipt and program details
            </p>
        </div>
    </body>
    </html>
    '''

@app.route('/admin', methods=['GET', 'POST'])
def admin_login():
    """Admin login page"""
    disable_f12 = inject_disable_f12()
    error = ''

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('admin_dashboard'))

        error = 'Invalid credentials'

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Login</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {disable_f12}
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }}

            .container {{
                max-width: 400px;
                width: 100%;
                background: white;
                border-radius: 20px;
                padding: 30px;
                box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            }}

            h2 {{
                color: #333;
                margin-bottom: 20px;
                text-align: center;
            }}

            .form-group {{
                margin-bottom: 20px;
            }}

            label {{
                display: block;
                margin-bottom: 5px;
                font-weight: 600;
                color: #555;
            }}

            input {{
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 16px;
            }}

            input:focus {{
                border-color: #4CAF50;
                outline: none;
            }}

            button {{
                width: 100%;
                padding: 12px;
                background: #4CAF50;
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
            }}

            button:hover {{
                background: #45a049;
            }}

            .error {{
                color: #f44336;
                text-align: center;
                margin-bottom: 15px;
            }}

            .back-link {{
                text-align: center;
                margin-top: 20px;
            }}

            .back-link a {{
                color: #666;
                text-decoration: none;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>🔐 Admin Login</h2>

            {f'<div class="error">{error}</div>' if error else ''}

            <form method="POST">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" name="username" required>
                </div>

                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" required>
                </div>

                <button type="submit">Login</button>
            </form>

            <div class="back-link">
                <a href="/">← Back to Home</a>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    """Admin dashboard to view logs"""
    disable_f12 = inject_disable_f12()

    # Get current fee
    current_fee = PROGRAM_FEE

    # Get recent members from Google Sheets
    members = []
    if google_sheet:
        try:
            records = google_sheet.get_all_records()
            members = records[-20:] if len(records) > 20 else records
            members.reverse()  # Newest first
        except Exception:  # pylint: disable=broad-exception-caught
            members = []

    members_html = (''.join([f'''
                        <tr>
                            <td>{m.get('Timestamp', '')}</td>
                            <td>{m.get('Name', '')}</td>
                            <td>{m.get('Email', '')}</td>
                            <td>{m.get('Phone', '')}</td>
                            <td>KES {m.get('Amount (KES)', '')}</td>
                            <td class="status-{m.get('Status', '').lower()}">{m.get('Status', '')}</td>
                        </tr>
                        ''' for m in members]) if members else '<tr><td colspan="6" style="text-align: center;">No members yet</td></tr>')

    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Admin Dashboard</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        {disable_f12}
        <style>
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}

            body {{
                background: #f5f5f5;
                min-height: 100vh;
                padding: 20px;
            }}

            .container {{
                max-width: 1200px;
                margin: 0 auto;
            }}

            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
                flex-wrap: wrap;
            }}

            .header h1 {{
                font-size: 24px;
            }}

            .logout {{
                background: rgba(255,255,255,0.2);
                color: white;
                text-decoration: none;
                padding: 8px 16px;
                border-radius: 5px;
            }}

            .price-card {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}

            .price-card h2 {{
                color: #333;
                margin-bottom: 15px;
            }}

            .current-price {{
                font-size: 36px;
                font-weight: bold;
                color: #4CAF50;
                margin: 20px 0;
                padding: 20px;
                background: #e8f5e9;
                border-radius: 10px;
                text-align: center;
            }}

            .note {{
                color: #666;
                font-style: italic;
                margin: 10px 0;
                padding: 10px;
                background: #fff3cd;
                border-left: 4px solid #ffc107;
            }}

            .members-section {{
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow-x: auto;
            }}

            .members-section h2 {{
                color: #333;
                margin-bottom: 20px;
            }}

            table {{
                width: 100%;
                border-collapse: collapse;
                min-width: 800px;
            }}

            th {{
                background: #4CAF50;
                color: white;
                padding: 12px;
                text-align: left;
            }}

            td {{
                padding: 10px;
                border-bottom: 1px solid #ddd;
            }}

            tr:hover {{
                background: #f5f5f5;
            }}

            .status-complete {{
                color: #4CAF50;
                font-weight: bold;
            }}

            .status-pending {{
                color: #ff9800;
                font-weight: bold;
            }}

            .status-failed {{
                color: #f44336;
                font-weight: bold;
            }}

            @media (max-width: 768px) {{
                .header {{
                    flex-direction: column;
                    gap: 10px;
                    text-align: center;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>⚙️ Admin Dashboard - {PROGRAM_NAME}</h1>
                <div>
                    <a href="/admin/logout" class="logout">🚪 Logout</a>
                </div>
            </div>

            <div class="price-card">
                <h2>💰 Current Program Fee</h2>
                <div class="current-price">
                    KES {current_fee:,}
                </div>
                <div class="note">
                    <strong>📝 Note:</strong> To change the price, edit the .env file and restart the app.<br>
                    <code>PROGRAM_FEE={current_fee}</code> in your .env file
                </div>
            </div>

            <div class="members-section">
                <h2>📋 Recent Members ({len(members)} shown)</h2>

                <table>
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Name</th>
                            <th>Email</th>
                            <th>Phone</th>
                            <th>Amount</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {members_html}
                    </tbody>
                </table>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/admin/logout')
def admin_logout():
    """Logout admin"""
    session.pop('admin_logged_in', None)
    return redirect(url_for('admin_login'))

# ============================================
# RUN THE APPLICATION
# ============================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print(f"🏋️  {PROGRAM_NAME} WEBSITE")
    print("="*60)
    print("📍 URL: http://127.0.0.1:5000")
    print(f"💰 Program Fee: KES {PROGRAM_FEE}")
    print(f"📱 Mode: {'TEST' if TEST_MODE else 'LIVE - REAL MONEY!'}")
    print(f"🔑 IntaSend: {'Connected' if INTASEND_SERVICE else 'NOT CONNECTED'}")
    print(f"📊 Google Sheets: {'✅ Connected' if google_sheet else '❌ Not Connected'}")
    print(f"📱 WhatsApp Group: {PROGRAM_LINK}")
    print("="*60 + "\n")

    app.run(debug=True, host='0.0.0.0', port=5000)
