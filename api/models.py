from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class GymClass(models.Model):
    name = models.CharField(max_length=255)
    trainer = models.CharField(max_length=255)
    schedule = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} - {self.schedule}"

class ClassRegistration(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Chờ phê duyệt'),
        ('APPROVED', 'Đã duyệt'),
        ('REJECTED', 'Từ chối'),
    ]

    member_name = models.CharField(max_length=255, verbose_name="Tên hội viên")
    phone = models.CharField(max_length=20, verbose_name="Số điện thoại")
    class_name = models.CharField(max_length=255, verbose_name="Tên lớp học")
    trainer = models.CharField(max_length=255, blank=True, null=True, verbose_name="Huấn luyện viên")
    schedule = models.CharField(max_length=255, blank=True, null=True, verbose_name="Lịch học")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING', verbose_name="Trạng thái")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Ngày đăng ký")

    def __str__(self):
        return f"{self.member_name} - {self.class_name} ({self.get_status_display()})"

# 1. Bảng quản lý Gói tập (Tên mới: GymPackage)
class GymPackage(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_months = models.IntegerField(default=1)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} - {self.price} VNĐ"

class Trainer(models.Model):
    name = models.CharField(max_length=255)
    specialty = models.CharField(max_length=255)
    experience_years = models.IntegerField(default=1)
    phone = models.CharField(max_length=20)
    bio = models.TextField(blank=True, null=True)
    avatar_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.specialty}"

class CheckInLog(models.Model):
    member_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20)
    check_in_time = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return f"{self.member_name} - {self.check_in_time.strftime('%Y-%m-%d %H:%M')}"

class ContactMessage(models.Model):
    full_name = models.CharField(max_length=100)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.email}"

# 2. Bảng lưu thông tin hội viên đã đăng ký gói tập (Giữ nguyên tên MemberPackage)
class MemberPackage(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    package_name = models.CharField(max_length=100, default="Gói Chuẩn")
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.package_name}"