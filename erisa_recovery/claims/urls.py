from django.urls import path
from . import views

urlpatterns = [
    path("", views.claim_list, name="claim_list"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("register/", views.register, name="register"),
    path("login/", views.user_login, name="login"),
    path("logout/", views.user_logout, name="logout"),
    path("upload-claims/", views.upload_claims, name="upload_claims"),
    path("claims/<int:pk>/", views.claim_detail, name="claim_detail"),
    path("claims/<int:pk>/partial/", views.claim_detail_partial, name="claim_detail_partial"),
    path("claims/<int:pk>/toggle_flag/", views.toggle_flag, name="toggle_flag"),
    path("claims/<int:pk>/add_note/", views.add_note, name="add_note"),
]
