from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ContactMessageViewSet, 
    GymPackageViewSet,
    TrainerViewSet,
    GymClassViewSet, 
    register_user, 
    login_user, 
    revenue_statistics, 
    check_in_member, 
    today_visits_statistics, 
    weekly_visits_statistics,
    expiring_soon_statistics,
    register_package_api,
    check_in_status_api,
    update_member_profile
)
from . import views

router = DefaultRouter()
router.register(r'contacts', ContactMessageViewSet)
router.register(r'trainers', TrainerViewSet)
router.register(r'packages', GymPackageViewSet)
router.register(r'classes', GymClassViewSet)

urlpatterns = [
    path('', include(router.urls)),
    path('register/', register_user, name='register'),
    path('login/', login_user, name='login'),
    path('members/', views.manage_members, name='manage_members_list'),
    path('members/<int:member_id>/', views.manage_members, name='manage_member_delete'),
    path('revenue/', revenue_statistics, name='revenue-statistics'),
    path('checkin/', check_in_member, name='check-in-member'),
    path('members/update-profile/', update_member_profile, name='update_member_profile'),
    
    # Endpoint trả về trạng thái điểm danh cho MemberDashboard.jsx
    path('checkin/status/', check_in_status_api, name='check_in_status_api'),

    path('visits/today/', today_visits_statistics, name='today-visits'),
    path('visits/weekly/', weekly_visits_statistics, name='weekly-visits'),
    path('members/expiring-soon/', expiring_soon_statistics, name='expiring-soon'),

    # API Đăng ký gói tập (Có cơ chế chặn đăng ký đè)
    path('register-package/', register_package_api, name='register_package_api'),
    
    # API Đăng ký lớp tập
    path('class-registrations/', views.class_registrations_api, name='class_registrations_api'),
    path('class-registrations/<int:pk>/status/', views.update_registration_status, name='update_registration_status'),
]