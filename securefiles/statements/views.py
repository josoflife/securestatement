from django.shortcuts import render
from django.contrib.auth import authenticate, login as auth_login, logout as auth_logout
from django.contrib import messages

# Create your views here.
from django.shortcuts import render, redirect
from .forms import RegisterForm
from .models import Transaction
import random
from datetime import date, timedelta

def register(request):
    if request.method == "POST":
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Generate 10 random transactions
            for i in range(10):
                Transaction.objects.create(
                    user=user,
                    date=date.today() - timedelta(days=random.randint(0, 30)),
                    amount=round(random.uniform(10, 500), 2),
                    description=random.choice(['Groceries', 'Utilities', 'Shopping', 'Dining'])
                )
            return redirect("login")
    else:
        form = RegisterForm()
    return render(request, "statements/register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect("dashboard")
        else:
            messages.error(request, "Invalid username or password.")
    return render(request, "statements/login.html")

from django.http import HttpResponse, FileResponse, Http404
from fpdf import FPDF
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from .models import Transaction, Statement
from django.utils import timezone
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
import os
from django.conf import settings
from datetime import timedelta
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage

@login_required
def generate_statement(request):
    if request.method != 'POST':
        return redirect('dashboard')

    # Get date range from form
    start_date = request.POST.get('start_date')
    end_date = request.POST.get('end_date')
    try:
        start_date_obj = date.fromisoformat(start_date)
        end_date_obj = date.fromisoformat(end_date)
    except Exception:
        messages.error(request, "Invalid date format.")
        return redirect('dashboard')
    if start_date_obj > end_date_obj:
        messages.error(request, "Start date must be before end date.")
        return redirect('dashboard')

    transactions = Transaction.objects.filter(user=request.user, date__range=(start_date_obj, end_date_obj))
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    # Add header
    pdf.set_font("Arial", 'B', size=16)
    pdf.cell(200, 10, txt="Bank Statement", ln=True, align='C')
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt=f"Account Holder: {request.user.username}", ln=True)
    pdf.cell(200, 10, txt=f"Date Generated: {date.today()}", ln=True)
    pdf.cell(200, 10, txt=f"Period: {start_date} to {end_date}", ln=True)
    pdf.ln(10)  # Add some space
    
    # Add column headers
    pdf.set_font("Arial", 'B', size=12)
    pdf.cell(50, 10, txt="Date", border=1)
    pdf.cell(70, 10, txt="Description", border=1)
    pdf.cell(70, 10, txt="Amount (R)", border=1, ln=True)
    pdf.set_font("Arial", size=12)
    
    # Add transactions
    total = 0
    for txn in transactions:
        pdf.cell(50, 10, txt=str(txn.date))
        pdf.cell(70, 10, txt=str(txn.description))
        pdf.cell(70, 10, txt=f"R {txn.amount:.2f}", ln=True)
        total += float(txn.amount)
    
    # Add total
    pdf.ln(10)
    pdf.set_font("Arial", 'B', size=12)
    pdf.cell(120, 10, txt="Total:")
    pdf.cell(70, 10, txt=f"R {total:.2f}", ln=True)
    
    # (Pie chart generation moved to after statements_dir is prepared)
    
    # Prepare statements directory (used for both PDF and chart)
    filename = f"{request.user.username}_statement_{start_date}_to_{end_date}.pdf"
    statements_dir = os.path.join(settings.MEDIA_ROOT, "statements")
    os.makedirs(statements_dir, exist_ok=True)

    # Pie chart code (uses statements_dir)
    category_totals = {}
    for txn in transactions:
        category = txn.description or 'Other'
        category_totals[category] = category_totals.get(category, 0) + float(txn.amount)

    if category_totals:
        labels = list(category_totals.keys())
        sizes = list(category_totals.values())
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(figsize=(4, 4), dpi=100)
        ax.pie(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
        ax.axis('equal')
        chart_filename = f"{request.user.username}_spending_pie_{start_date}_to_{end_date}.png"
        chart_path = os.path.join(statements_dir, chart_filename)
        plt.tight_layout()
        fig.savefig(chart_path, bbox_inches='tight')
        plt.close(fig)
        pdf.ln(5)
        try:
            pdf.image(chart_path, x=60, w=90)
        except Exception:
            pass

    # Save the file
    pdf_path = os.path.join(statements_dir, filename)
    pdf.output(pdf_path)

    # Generate secure token and create Statement record
    s = URLSafeTimedSerializer(settings.SECRET_KEY)
    token = s.dumps(request.user.username)
    expiry = timezone.now() + timedelta(minutes=10)

    statement = Statement.objects.create(
        user=request.user,
        pdf=os.path.join('statements', filename),  # Store relative path
        token=token,
        token_expiry=expiry
    )

    link = f"/statements/download/{token}/"
    messages.success(request, f"Statement generated for {start_date} to {end_date}! Download link (valid 10 min): {link}")
    return redirect('dashboard')


@login_required
def dashboard(request):
    statements_list = Statement.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'statements/dashboard.html', {'statements': statements_list})


def logout_view(request):
    auth_logout(request)
    return redirect('login')


def download_statement(request, token):
    s = URLSafeTimedSerializer(settings.SECRET_KEY)
    try:
        username = s.loads(token, max_age=600)  # Token expires after 10 minutes
        statement = Statement.objects.get(token=token)
        
        if statement.token_expiry < timezone.now():
            return HttpResponse("Token expired", status=403)
            
        if not statement.pdf:
            raise Http404("Statement file not found")
            
        file_path = os.path.join(settings.MEDIA_ROOT, str(statement.pdf))
        if not os.path.exists(file_path):
            raise Http404("Statement file not found")
            
        return FileResponse(
            open(file_path, 'rb'),
            as_attachment=True,
            filename=os.path.basename(file_path)
        )
    except SignatureExpired:
        return HttpResponse("Token expired", status=403)
    except BadSignature:
        return HttpResponse("Invalid token", status=403)
    except Statement.DoesNotExist:
        raise Http404("Statement not found")
    except Exception as e:
        return HttpResponse(f"Error downloading statement: {str(e)}", status=500)