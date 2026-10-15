from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework import viewsets, status
from datetime import date, timedelta
from django.db.models import Count
from django.utils import timezone

from .models import (
    ContactMessage, 
    MemberPackage, 
    CheckInLog, 
    GymPackage, 
    Trainer, 
    ClassRegistration,
    GymClass
)
from .serializers import (
    ContactMessageSerializer, 
    GymPackageSerializer, 
    TrainerSerializer,
    GymClassSerializer
)


@api_view(['PUT', 'PATCH'])
def update_member_profile(request):
    data = request.data
    real_id = data.get('realId')
    old_email = data.get('oldEmail') or data.get('email')
    old_phone = data.get('oldPhone') or data.get('phone')
    password = data.get('password')

    # 1. Yêu cầu bắt buộc nhập mật khẩu
    if not password:
        return Response({"error": "Vui lòng nhập mật khẩu tài khoản để xác nhận thay đổi!"}, status=status.HTTP_400_BAD_REQUEST)

    # 2. Tìm tài khoản User tương ứng trong hệ thống Auth
    user_obj = None
    if old_email:
        user_obj = User.objects.filter(email=old_email).first() or User.objects.filter(username=old_email).first()
    
    if not user_obj and request.user.is_authenticated:
        user_obj = request.user

    # 3. Kiểm tra tính đúng đắn của mật khẩu
    if user_obj:
        if not user_obj.check_password(password):
            return Response({"error": "Mật khẩu xác nhận không chính xác!"}, status=status.HTTP_400_BAD_REQUEST)
    else:
        # Trường hợp không tìm thấy tài khoản User khớp email, thử authenticate trực tiếp
        auth_user = authenticate(username=old_email, password=password)
        if not auth_user:
            return Response({"error": "Mật khẩu xác nhận không chính xác!"}, status=status.HTTP_400_BAD_REQUEST)
        user_obj = auth_user

    # 4. Tìm bản ghi hội viên trong bảng MemberPackage
    member = None
    if real_id:
        member = MemberPackage.objects.filter(id=real_id).first()
    if not member and old_email:
        member = MemberPackage.objects.filter(email=old_email).first()
    if not member and old_phone:
        member = MemberPackage.objects.filter(phone=old_phone).first()

    if not member:
        return Response({"error": "Không tìm thấy thông tin hội viên trong CSDL!"}, status=status.HTTP_404_NOT_FOUND)

    # Lấy thông tin mới từ request
    new_full_name = data.get('fullName')
    new_phone = data.get('phone')
    new_email = data.get('email')

    # 5. Cập nhật bảng MemberPackage
    if new_full_name:
        member.full_name = new_full_name
    if new_phone:
        member.phone = new_phone
    if new_email:
        member.email = new_email

    try:
        member.save()

        # 6. Cập nhật đồng bộ sang bảng User (Authentication)
        if user_obj:
            if new_email:
                user_obj.email = new_email
                user_obj.username = new_email
            if new_full_name:
                user_obj.first_name = new_full_name
            user_obj.save()

        print(f"✅ ĐÃ CẬP NHẬT DATABASE THÀNH CÔNG CHO ID {member.id}: {member.full_name}, {member.phone}, {member.email}")
        return Response({
            "message": "Cập nhật thông tin thành công!",
            "data": {
                "realId": member.id,
                "fullName": member.full_name,
                "phone": member.phone,
                "email": member.email
            }
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({"error": f"Lỗi lưu Database: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)


# ViewSet Quản lý Lớp học (CRUD đầy đủ cho Admin)
class GymClassViewSet(viewsets.ModelViewSet):
    queryset = GymClass.objects.all().order_by('-id')
    serializer_class = GymClassSerializer

@api_view(['GET', 'POST'])
def class_registrations_api(request):
    if request.method == 'GET':
        phone = request.query_params.get('phone')
        if phone:
            regs = ClassRegistration.objects.filter(phone=phone)
        else:
            regs = ClassRegistration.objects.all().order_by('-created_at')
        
        data = [{
            'id': r.id,
            'memberName': r.member_name,
            'phone': r.phone,
            'className': r.class_name,
            'trainer': r.trainer,
            'schedule': r.schedule,
            'status': r.status,
            'createdAt': r.created_at.strftime('%Y-%m-%d %H:%M')
        } for r in regs]
        return Response(data)

    elif request.method == 'POST':
        data = request.data
        reg = ClassRegistration.objects.create(
            member_name=data.get('memberName', 'Hội viên'),
            phone=data.get('phone', ''),
            class_name=data.get('className'),
            trainer=data.get('trainer', ''),
            schedule=data.get('schedule', ''),
            status='PENDING'
        )
        return Response({'message': 'Đã gửi yêu cầu đăng ký!', 'id': reg.id}, status=status.HTTP_201_CREATED)

@api_view(['PATCH'])
def update_registration_status(request, pk):
    try:
        reg = ClassRegistration.objects.get(pk=pk)
        new_status = request.data.get('status')
        if new_status in ['APPROVED', 'REJECTED', 'PENDING']:
            reg.status = new_status
            reg.save()
            return Response({'message': f'Đã cập nhật trạng thái thành {new_status}'})
        return Response({'error': 'Trạng thái không hợp lệ!'}, status=status.HTTP_400_BAD_REQUEST)
    except ClassRegistration.DoesNotExist:
        return Response({'error': 'Không tìm thấy yêu cầu!'}, status=status.HTTP_404_NOT_FOUND)

class GymPackageViewSet(viewsets.ModelViewSet):
    queryset = GymPackage.objects.all()
    serializer_class = GymPackageSerializer

class TrainerViewSet(viewsets.ModelViewSet):
    queryset = Trainer.objects.all().order_by('-created_at')
    serializer_class = TrainerSerializer


@api_view(['GET'])
def expiring_soon_statistics(request):
    try:
        today = date.today()
        seven_days_later = today + timedelta(days=7)
        count = MemberPackage.objects.filter(
            end_date__gte=today,
            end_date__lte=seven_days_later
        ).count()
        return Response({"expiring_count": count})
    except Exception as e:
        return Response({"expiring_count": 0})

@api_view(['GET'])
def weekly_visits_statistics(request):
    try:
        today = timezone.localdate()
        start_of_week = today - timedelta(days=today.weekday())
        days_map = ["T2", "T3", "T4", "T5", "T6", "T7", "CN"]
        visits_data = []

        for i in range(7):
            current_day = start_of_week + timedelta(days=i)
            count = CheckInLog.objects.filter(check_in_time__date=current_day).count()
            visits_data.append({
                "day": days_map[i],
                "visits": count
            })
        return Response(visits_data)
    except Exception as e:
        default_weekly = [
            {"day": "T2", "visits": 120}, {"day": "T3", "visits": 98},
            {"day": "T4", "visits": 135}, {"day": "T5", "visits": 110},
            {"day": "T6", "visits": 142}, {"day": "T7", "visits": 160}, {"day": "CN", "visits": 90}
        ]
        return Response(default_weekly)

@api_view(['POST'])
def check_in_member(request):
    try:
        phone = request.data.get('phone')
        full_name = request.data.get('full_name', 'Hội viên')
        CheckInLog.objects.create(member_name=full_name, phone=phone)
        return Response({"message": "Check-in thành công!", "member": full_name})
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def today_visits_statistics(request):
    try:
        today = timezone.localdate()
        count = CheckInLog.objects.filter(check_in_time__date=today).count()
        return Response({"today_visits": count})
    except Exception as e:
        return Response({"today_visits": 0})

@api_view(['GET'])
def revenue_statistics(request):
    try:
        package_stats = MemberPackage.objects.values('package_name').annotate(
            total_count=Count('id')
        )
        monthly_revenue_list = []
        total_revenue = 0

        for item in package_stats:
            pkg_name = item['package_name'] or ""
            count = item['total_count']
            unit_price = 1200000 if "VIP" in pkg_name else 500000  
            revenue_by_pkg = count * unit_price
            total_revenue += revenue_by_pkg
            monthly_revenue_list.append({
                "packageName": pkg_name,
                "revenue": revenue_by_pkg,
                "total_count": count
            })

        return Response({
            "total_revenue": total_revenue,
            "monthly_revenue": monthly_revenue_list,
        })
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET', 'POST', 'DELETE'])
def manage_members(request, member_id=None):
    if request.method == 'GET':
        try:
            members = MemberPackage.objects.all().order_by('-created_at')
            data = [{
                "id": f"M00{m.id}",
                "realId": m.id,
                "fullName": getattr(m, 'full_name', '') or 'Chưa cập nhật',
                "email": getattr(m, 'email', '') or '',
                "phone": getattr(m, 'phone', '') or 'Chưa cập nhật',
                "packageName": getattr(m, 'package_name', 'Gói Chuẩn'),
                "startDate": str(m.start_date) if m.start_date else str(date.today()),
                "endDate": str(m.end_date) if m.end_date else str(date.today()),
                "status": "Active" if (m.end_date and m.end_date >= date.today()) else "Expired"
            } for m in members]
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    elif request.method == 'POST':
        data = request.data
        try:
            member = MemberPackage.objects.create(
                full_name=data.get('fullName'),
                email=data.get('email'),
                phone=data.get('phone'),
                package_name=data.get('packageName', 'Gói Chuẩn'),
                start_date=data.get('startDate'),
                end_date=data.get('endDate')
            )
            return Response({"message": "Thêm hội viên thành công!", "id": member.id}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    elif request.method == 'DELETE':
        if not member_id:
            return Response({"error": "Thiếu ID hội viên!"}, status=status.HTTP_400_BAD_REQUEST)
        try:
            member = MemberPackage.objects.get(id=member_id)
            member.delete()
            return Response({"message": "Xóa hội viên thành công!"}, status=status.HTTP_200_OK)
        except MemberPackage.DoesNotExist:
            return Response({"error": "Không tìm thấy hội viên!"}, status=status.HTTP_404_NOT_FOUND)

@api_view(['POST'])
def register_user(request):
    username = request.data.get('username') or request.data.get('email')
    email = request.data.get('email')
    password = request.data.get('password')
    full_name = request.data.get('fullName', '')

    if not username or not password:
        return Response({"error": "Vui lòng nhập đầy đủ thông tin!"}, status=status.HTTP_400_BAD_REQUEST)

    if User.objects.filter(username=username).exists() or User.objects.filter(email=email).exists():
        return Response({"error": "Tên đăng nhập hoặc email này đã tồn tại!"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.create_user(username=username, email=email, password=password, first_name=full_name)
        return Response({"message": "Đăng ký thành công!", "role": "Member"}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
def login_user(request):
    login_input = request.data.get('username') or request.data.get('email')
    password = request.data.get('password')

    if not login_input or not password:
        return Response({"error": "Vui lòng nhập đầy đủ email và mật khẩu!"}, status=status.HTTP_400_BAD_REQUEST)

    user_obj = User.objects.filter(username=login_input).first() or User.objects.filter(email=login_input).first()

    if user_obj:
        user = authenticate(username=user_obj.username, password=password)
        if user is not None:
            role = "Admin" if user.is_superuser else "Member"
            return Response({
                "message": "Đăng nhập thành công!",
                "username": user.username,
                "email": user.email,
                "fullName": f"{user.first_name} {user.last_name}".strip(),
                "role": role
            }, status=status.HTTP_200_OK)

    return Response({"error": "Sai tên đăng nhập/email hoặc mật khẩu!"}, status=status.HTTP_400_BAD_REQUEST)

class ContactMessageViewSet(viewsets.ModelViewSet):
    queryset = ContactMessage.objects.all().order_by('-created_at')
    serializer_class = ContactMessageSerializer

@api_view(['POST'])
def register_package_api(request):
    data = request.data
    phone = data.get('phone')
    email = data.get('email')
    pkg_name = data.get('packageName')
    duration_months = int(data.get('durationMonths', 1))
    
    if not phone and not email:
        return Response({"error": "Thiếu thông tin nhận diện hội viên!"}, status=status.HTTP_400_BAD_REQUEST)

    existing_package = None
    if phone:
        existing_package = MemberPackage.objects.filter(phone=phone).order_by('-end_date').first()
    elif email:
        existing_package = MemberPackage.objects.filter(email=email).order_by('-end_date').first()

    if existing_package and existing_package.end_date and existing_package.end_date >= date.today():
        return Response(
            {"error": f"⚠️ Bạn đang sử dụng gói '{existing_package.package_name}' đến hết ngày {existing_package.end_date}. Không thể đăng ký gói mới!"},
            status=status.HTTP_400_BAD_REQUEST
        )

    start_date = date.today()
    end_date = start_date + timedelta(days=duration_months * 30)

    try:
        new_package = MemberPackage.objects.create(
            full_name=data.get('fullName', getattr(existing_package, 'full_name', 'Hội viên')),
            email=email or getattr(existing_package, 'email', ''),
            phone=phone or getattr(existing_package, 'phone', ''),
            package_name=pkg_name,
            start_date=start_date,
            end_date=end_date
        )
        return Response({"message": "Đăng ký gói thành công!", "id": new_package.id}, status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
def check_in_status_api(request):
    phone = request.GET.get('phone', '')
    return Response({
        "phone": phone,
        "hasCheckedIn": False,
        "message": "Chưa check-in hôm nay"
    }, status=status.HTTP_200_OK)