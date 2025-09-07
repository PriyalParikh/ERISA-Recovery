# ERISA Recovery App

## Setup Instructions

1. **Install dependencies:**
   - Run `pip install -r requirements.txt` in your project root.

   -Create and activate a virtual environment:
   -python -m venv .venv
   -source .venv/bin/activate


2. **Apply migrations:**
   - Change directory to the Django project folder:
     cd erisa_recovery
   - Run:
     python manage.py makemigrations
     python manage.py migrate
     python manage.py load_claims --claims data/claims.json --details data/details.json

3. **Create a superuser (admin):**
   - In the `erisa_recovery` directory, run:
     python manage.py createsuperuser
   - Follow the prompts to set username and password.

4. **Run the development server:**
   - In the `erisa_recovery` directory, run:
     python manage.py runserver

5. **Access the app:**
   - Open your browser and go to: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

## User Login & Roles

- **Register a new user:** Click "Register" in the top navigation.
- **Login:** Click "Login" in the top navigation and enter your credentials.
- **Normal users** can view the dashboard and add notes to claims.
- **Admin users (superusers)** can also access the "Admin Dashboard" link for statistics.

## Admin Dashboard
- Only visible to admin users after login.
- Shows total claims, flagged claims, and average underpayment.


