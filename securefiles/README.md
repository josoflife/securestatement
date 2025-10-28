# Secure Bank Statements Django Project

## Features
- User registration and login
- Dashboard with statement generation and download
- Select custom date range for statements
- Expiring download links (10 minutes)
- Modern red/white UI theme
- Production-ready Docker setup

## Quick Start (Local)
1. Install Python 3.11+
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run migrations:
   ```bash
   python manage.py migrate
   ```
4. Start the server:
   ```bash
   python manage.py runserver 8000
   ```
5. Access:
   - Register: http://127.0.0.1:8000/
   - Login: http://127.0.0.1:8000/login/
   - Dashboard: http://127.0.0.1:8000/dashboard/

## Docker Usage
1. Build the image:
   ```bash
   docker build -t securefiles .
   ```
2. Run the container:
   ```bash
   docker run -d -p **80:8000** securefiles --name securefiles_app securefiles
   ```
3. Access the app at http://127.0.0.1:8000/

## Testing
Run all tests:
```bash
python manage.py test statements
```

## Statement Generation
- On the dashboard, select a start and end date to generate a statement for that period.
- Download link is valid for 10 minutes.

## Production Notes
- Uses Gunicorn for WSGI serving in Docker
- Static/media files are stored in `/app/media` in the container
- Set `DEBUG=False` and configure allowed hosts for production

---
For any issues or improvements, open a pull request or issue!
