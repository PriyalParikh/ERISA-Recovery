from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Claim, Note

from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect


@login_required
def claim_list(request):
    print("Claim list view accessed")
    claims = Claim.objects.select_related('detail').order_by("-id")
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        claims = claims.filter(
            Q(id__icontains=search_query) |
            Q(patient_name__icontains=search_query) |
            Q(insurer_name__icontains=search_query)
        )
    
    # Status filter
    status_filter = request.GET.get('status', '')
    if status_filter:

        claims = claims.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(claims, 15)  
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get the first claim for initial detail view
    selected_claim = None
    if page_obj.object_list:
        selected_claim = page_obj.object_list[0]
    
    context = {
        'page_obj': page_obj,
        'selected_claim': selected_claim,
    }
    
    # If this is an HTMX request for just the table, return only the table body
    if request.headers.get('HX-Request'):
        return render(request, 'claims/partial_claims_table.html', context)
    
    return render(request, "claims/claim_list.html", context)


@login_required
def claim_detail(request, pk):
    claim = get_object_or_404(Claim.objects.select_related('detail').prefetch_related('notes__author'), pk=pk)
    return render(request, "claims/claim_detail.html", {"claim": claim})


@login_required
def claim_detail_partial(request, pk):
    claim = get_object_or_404(Claim.objects.select_related('detail').prefetch_related('notes__author'), pk=pk)
    return render(request, "claims/partial_claim_detail.html", {"claim": claim})


@login_required
def toggle_flag(request, pk):
    claim = get_object_or_404(Claim, pk=pk)
    claim.flagged = not claim.flagged
    claim.save()
    html = render_to_string("claims/partial_claim_row.html", {"claim": claim})
    return HttpResponse(html)


@login_required
def add_note(request, pk):
    claim = get_object_or_404(Claim.objects.prefetch_related('notes__author'), pk=pk)
    text = request.POST.get("text", "").strip()
    if text:
        Note.objects.create(claim=claim, author=request.user if request.user.is_authenticated else None, text=text)
    html = render_to_string("claims/partial_notes.html", {"claim": claim})
    return HttpResponse(html)


# Admin dashboard view (admin only)
from django.db.models import Avg, F, ExpressionWrapper, DecimalField
from .forms import ClaimsUploadForm
import json, csv, tempfile
from pathlib import Path
@login_required
@user_passes_test(lambda u: u.is_superuser)
def admin_dashboard(request):
    total_flagged = Claim.objects.filter(flagged=True).count()
    underpayment_expr = ExpressionWrapper(F('billed_amount') - F('paid_amount'), output_field=DecimalField())
    avg_underpayment = Claim.objects.annotate(underpayment=underpayment_expr).aggregate(avg=Avg('underpayment'))['avg'] or 0
    total_claims = Claim.objects.count()
    context = {
        'total_flagged': total_flagged,
        'avg_underpayment': avg_underpayment,
        'total_claims': total_claims,
    }
    return render(request, "claims/admin_dashboard.html", context)


# Admin-only: Upload claims and details via UI
@login_required
@user_passes_test(lambda u: u.is_superuser)
def upload_claims(request):
    msg = None
    if request.method == "POST":
        form = ClaimsUploadForm(request.POST, request.FILES)
        if form.is_valid():
            claims_file = request.FILES["claims_file"]
            details_file = request.FILES["details_file"]
            mode = form.cleaned_data["mode"]

            claims_data_string = claims_file.read().decode('utf-8')
            details_data_string = details_file.read().decode('utf-8')

            # The data we read from the file starts as just one long piece of text. 
            # This line is our translator; it parses that text and turns it into a clean Python list 
            # of dictionaries, which is a format we can easily loop through.
            claims_data = json.loads(claims_data_string)
            details_data = json.loads(details_data_string)
            
            # Now, claims_data is a Python list of dictionaries.
            # You can now loop through it and process it.
            print(claims_data[0]) # This will print the first claim dictionary correctly.

            # If the user selected the 'overwrite' option on the upload form, we'll prepare the database
            # by first deleting all existing records. This ensures a completely fresh start with the new data.

            if mode == "overwrite":
                print("Deleting existing claims and details...")
                from claims.models import Claim, ClaimDetail
                ClaimDetail.objects.all().delete()
                Claim.objects.all().delete()
                msg = "All existing claims and details deleted (overwrite mode)."

            # Helper to load JSON or CSV
            def load_data(file_path):
                if str(file_path).endswith(".json"):
                    with open(file_path, "r") as f:
                        return json.load(f)
                else:
                    with open(file_path, newline="", encoding="utf-8") as f:
                        reader = csv.DictReader(f)
                        return list(reader)

            for entry in claims_data:
                Claim.objects.update_or_create(
                    id=entry.get("id"),
                    defaults={
                        "patient_name": entry.get("patient_name"),
                        "billed_amount": entry.get("billed_amount"),
                        "paid_amount": entry.get("paid_amount"),
                        "status": entry.get("status"),
                        "insurer_name": entry.get("insurer_name"),
                        "discharge_date": entry.get("discharge_date"),
                    },
                )

            for entry in details_data:
                try:
                    claim = Claim.objects.get(id=entry["claim_id"])
                except Claim.DoesNotExist:
                    continue
                ClaimDetail.objects.update_or_create(
                    claim=claim,
                    defaults={
                        "denial_reason": entry["denial_reason"],
                        "cpt_codes": entry["cpt_codes"],
                    },
                )
            msg = (msg or "") + " Data import complete."
    else:
        form = ClaimsUploadForm()
    return render(request, "claims/upload_claims.html", {"form": form, "msg": msg})

# User registration
def register(request):
    if request.user.is_authenticated:
        return redirect('claim_list')
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('claim_list')
    else:
        form = UserCreationForm()
    return render(request, 'claims/register.html', {'form': form})

# User login
def user_login(request):
    if request.user.is_authenticated:
        return redirect('claim_list')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('claim_list')
    else:
        form = AuthenticationForm()
    return render(request, 'claims/login.html', {'form': form})

# User logout
@login_required
def user_logout(request):
    logout(request)
    return redirect('login')
