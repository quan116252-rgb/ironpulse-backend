from django.contrib import admin
from .models import ContactMessage, MemberPackage, CheckInLog, Trainer, GymPackage

from .models import ClassRegistration

@admin.register(ClassRegistration)
class ClassRegistrationAdmin(admin.ModelAdmin):
    list_display = ('id', 'member_name', 'phone', 'class_name', 'schedule', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('member_name', 'phone', 'class_name')
    list_editable = ('status',)

# Đăng ký Gói tập (GymPackage) vào Django Admin
@admin.register(GymPackage)
class GymPackageAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'price', 'duration_months')
    search_fields = ('name',)

# Đăng ký Trainer vào trang quản trị Django Admin
@admin.register(Trainer)
class TrainerAdmin(admin.ModelAdmin):
    list_display = ('id', 'name', 'specialty', 'experience_years', 'phone')
    search_fields = ('name', 'specialty', 'phone')

# Đăng ký CheckInLog để hiển thị trên trang Django Admin
@admin.register(CheckInLog)
class CheckInLogAdmin(admin.ModelAdmin):
    list_display = ('id', 'member_name', 'phone', 'check_in_time')
    search_fields = ('member_name', 'phone')

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'created_at')
    search_fields = ('full_name', 'email')

@admin.register(MemberPackage)
class MemberPackageAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'package_name', 'start_date', 'end_date')
    search_fields = ('full_name', 'email', 'phone')