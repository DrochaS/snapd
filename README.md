# The Tkay Challenge Website

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.x-green.svg)](https://flask.palletsprojects.com/)
[![GitHub Actions](https://img.shields.io/badge/GitHub%20Actions-Pylint%20CI-success.svg)](https://github.com/DrochaS/snapd/actions)

A Flask-based web application for handling member registration, payment processing, and admin monitoring for **The Tkay Challenge** program.

## Getting Started
This project is designed to help you understand how the registration and payment flow works from start to finish. The main app logic lives in [app.py](app.py), and the required packages are listed in [requirements.txt](requirements.txt).

## Overview
This project allows users to:
- register for the program,
- submit their personal details,
- complete payment through IntaSend,
- track the payment status, and
- view success confirmation pages.

It also includes an admin area for managing and reviewing members.

## Features
- Responsive registration flow
- Phone number normalization and validation
- IntaSend payment integration
- Payment status checking and redirect handling
- Admin login and dashboard
- Google Sheets integration for storing member records
- Security headers for protecting the site from browser inspection tools

## Tech Stack
- Python 3
- Flask
- IntaSend API
- Google Sheets API (`gspread`)
- `python-dotenv`

## Project Structure
- [app.py](app.py) — main Flask application, routes, and business logic
- [requirements.txt](requirements.txt) — Python dependencies
- [.pylintrc](.pylintrc) — lint configuration
- [.github/workflows/pylint.yml](.github/workflows/pylint.yml) — CI lint workflow

## How the App Works
1. The app loads environment variables from the `.env` file.
2. It initializes the payment service using IntaSend credentials.
3. It attempts to connect to Google Sheets for storing registration data.
4. Users complete the registration form.
5. The app creates a payment request and redirects the user to the payment flow.
6. The user checks the payment status and reaches the success page.
7. Admin users can log in and review the registered members.

## Environment Variables

| Variable | Required | Description |
|---|---:|---|
| `INTASEND_PUBLISHABLE_KEY` | Yes | Public key used to initialize the payment gateway |
| `INTASEND_SECRET_TOKEN` | Yes | Secret token used for payment requests |
| `INTASEND_TEST_MODE` | Yes | Enables or disables test mode |
| `PROGRAM_FEE` | Yes | Registration fee amount |
| `PROGRAM_NAME` | Yes | Display name for the program |
| `PROGRAM_LINK` | Yes | WhatsApp or registration link |
| `FLASK_SECRET_KEY` | Yes | Secret key for Flask sessions |
| `GOOGLE_SHEET_NAME` | Optional | Name of the Google Sheet used to store records |
| `ADMIN_USERNAME` | Optional | Admin login username |
| `ADMIN_PASSWORD` | Optional | Admin login password |

## Routes

| Route | Method | Purpose |
|---|---|---|
| `/` | GET | Home/landing page |
| `/register` | POST | Submit registration data |
| `/payment-processing/<invoice_id>` | GET | Display payment processing page |
| `/check-status/<invoice_id>` | GET | Check the payment status |
| `/success` | GET | Show payment success confirmation |
| `/admin` | GET/POST | Admin login page |
| `/admin/dashboard` | GET | Admin dashboard |
| `/admin/logout` | GET | Logout endpoint |

## How to Run This Project

### 1) Open PowerShell in the project folder
```powershell
cd C:\Users\DROCHA\Desktop\gym-website
```

### 2) Create and activate a virtual environment
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3) Install dependencies
```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

### 4) Create the `.env` file
Add the environment variables listed above.

### 5) Start the application
```powershell
python app.py
```

### 6) Open the app in your browser
Visit:
```text
http://127.0.0.1:5000
```

## Code Notes
- `normalize_phone()` converts phone numbers to the required Kenyan format.
- `setup_google_sheets()` connects to Google Sheets if credentials are available.
- `save_member_to_sheets()` stores member data after registration.
- The `after_request` hook adds security response headers.

## Screenshots
Below is a clean placeholder layout you can replace with real screenshots later.

### 1. Home Page
[![Home Page](https://via.placeholder.com/1200x700?text=Home+Page)](https://via.placeholder.com/1200x700?text=Home+Page)

### 2. Registration Form
[![Registration Form](https://via.placeholder.com/1200x700?text=Registration+Form)](https://via.placeholder.com/1200x700?text=Registration+Form)

### 3. Payment Processing Page
[![Payment Processing](https://via.placeholder.com/1200x700?text=Payment+Processing)](https://via.placeholder.com/1200x700?text=Payment+Processing)

### 4. Admin Dashboard
[![Admin Dashboard](https://via.placeholder.com/1200x700?text=Admin+Dashboard)](https://via.placeholder.com/1200x700?text=Admin+Dashboard)

## Future Improvements
- Improve payment error handling
- Split the application into multiple modules for maintainability
- Add automated tests
- Expand admin reporting features
