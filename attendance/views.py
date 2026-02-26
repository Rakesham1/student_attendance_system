from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count, Q
from django.utils import timezone
import datetime

from .models import CustomUser, Department, Subject, Student, AttendanceSession, AttendanceRecord
from .forms import (
    LoginForm, DepartmentForm, SubjectForm,
    StudentForm, TeacherForm, MarkAttendanceForm
)


# ─────────────────────────────────────────────
#  AUTH VIEWS
# ─────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    form = LoginForm(request, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        return redirect('dashboard')
    return render(request, 'attendance/login.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    user = request.user
    if user.role == 'ADMIN':
        return redirect('admin_dashboard')
    elif user.role == 'TEACHER':
        return redirect('teacher_dashboard')
    elif user.role == 'STUDENT':
        return redirect('student_dashboard')
    return redirect('login')


# ─────────────────────────────────────────────
#  ADMIN VIEWS
# ─────────────────────────────────────────────

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'ADMIN':
            messages.error(request, 'Access denied.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@admin_required
def admin_dashboard(request):
    total_students = Student.objects.count()
    total_teachers = CustomUser.objects.filter(role='TEACHER').count()
    total_subjects = Subject.objects.count()
    total_departments = Department.objects.count()
    recent_sessions = AttendanceSession.objects.select_related('subject', 'teacher').order_by('-date')[:5]
    context = {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_subjects': total_subjects,
        'total_departments': total_departments,
        'recent_sessions': recent_sessions,
    }
    return render(request, 'attendance/admin_dashboard.html', context)


# --- Department ---
@login_required
@admin_required
def manage_departments(request):
    departments = Department.objects.annotate(student_count=Count('students'), subject_count=Count('subjects'))
    form = DepartmentForm()
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Department added successfully.')
            return redirect('manage_departments')
    return render(request, 'attendance/manage_departments.html', {'departments': departments, 'form': form})


@login_required
@admin_required
def delete_department(request, pk):
    dept = get_object_or_404(Department, pk=pk)
    dept.delete()
    messages.success(request, 'Department deleted.')
    return redirect('manage_departments')


# --- Students ---
@login_required
@admin_required
def manage_students(request):
    students = Student.objects.select_related('user', 'department').all()
    form = StudentForm()
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            # Create user first
            user = CustomUser.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                role='STUDENT',
            )
            Student.objects.create(
                user=user,
                roll_number=form.cleaned_data['roll_number'],
                department=form.cleaned_data['department'],
                semester=form.cleaned_data['semester'],
                joining_year=form.cleaned_data['joining_year'],
            )
            messages.success(request, 'Student added successfully.')
            return redirect('manage_students')
        else:
            messages.error(request, 'Please fix the errors below.')
    return render(request, 'attendance/manage_students.html', {'students': students, 'form': form})


@login_required
@admin_required
def delete_student(request, pk):
    student = get_object_or_404(Student, pk=pk)
    student.user.delete()
    messages.success(request, 'Student deleted.')
    return redirect('manage_students')


# --- Teachers ---
@login_required
@admin_required
def manage_teachers(request):
    teachers = CustomUser.objects.filter(role='TEACHER')
    form = TeacherForm()
    if request.method == 'POST':
        form = TeacherForm(request.POST)
        if form.is_valid():
            CustomUser.objects.create_user(
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password'],
                first_name=form.cleaned_data['first_name'],
                last_name=form.cleaned_data['last_name'],
                email=form.cleaned_data['email'],
                phone=form.cleaned_data.get('phone', ''),
                role='TEACHER',
            )
            messages.success(request, 'Teacher added successfully.')
            return redirect('manage_teachers')
    return render(request, 'attendance/manage_teachers.html', {'teachers': teachers, 'form': form})


@login_required
@admin_required
def delete_teacher(request, pk):
    teacher = get_object_or_404(CustomUser, pk=pk, role='TEACHER')
    teacher.delete()
    messages.success(request, 'Teacher deleted.')
    return redirect('manage_teachers')


# --- Subjects ---
@login_required
@admin_required
def manage_subjects(request):
    subjects = Subject.objects.select_related('department', 'teacher')
    form = SubjectForm()
    if request.method == 'POST':
        form = SubjectForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subject added successfully.')
            return redirect('manage_subjects')
    return render(request, 'attendance/manage_subjects.html', {'subjects': subjects, 'form': form})


@login_required
@admin_required
def delete_subject(request, pk):
    subject = get_object_or_404(Subject, pk=pk)
    subject.delete()
    messages.success(request, 'Subject deleted.')
    return redirect('manage_subjects')


# ─────────────────────────────────────────────
#  TEACHER VIEWS
# ─────────────────────────────────────────────

def teacher_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'TEACHER':
            messages.error(request, 'Access denied.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@teacher_required
def teacher_dashboard(request):
    subjects = Subject.objects.filter(teacher=request.user).select_related('department')
    recent_sessions = AttendanceSession.objects.filter(
        teacher=request.user
    ).select_related('subject').order_by('-date')[:5]
    context = {
        'subjects': subjects,
        'recent_sessions': recent_sessions,
        'today': timezone.localdate(),
    }
    return render(request, 'attendance/teacher_dashboard.html', context)


@login_required
@teacher_required
def mark_attendance(request):
    form = MarkAttendanceForm(teacher=request.user)
    students = []
    selected_subject = None
    selected_date = None
    already_marked = False

    if request.method == 'GET' and request.GET.get('subject') and request.GET.get('date'):
        subject_id = request.GET.get('subject')
        date_str = request.GET.get('date')
        try:
            selected_subject = Subject.objects.get(pk=subject_id, teacher=request.user)
            selected_date = datetime.date.fromisoformat(date_str)
            form = MarkAttendanceForm(
                initial={'subject': selected_subject, 'date': selected_date},
                teacher=request.user
            )
            # Get students in this department & semester
            students = Student.objects.filter(
                department=selected_subject.department,
                semester=selected_subject.semester
            ).select_related('user')

            # Check if already marked
            already_marked = AttendanceSession.objects.filter(
                subject=selected_subject, date=selected_date
            ).exists()
        except (Subject.DoesNotExist, ValueError):
            messages.error(request, 'Invalid subject or date.')

    if request.method == 'POST':
        subject_id = request.POST.get('subject_id')
        date_str = request.POST.get('date')
        try:
            selected_subject = Subject.objects.get(pk=subject_id, teacher=request.user)
            selected_date = datetime.date.fromisoformat(date_str)
        except (Subject.DoesNotExist, ValueError):
            messages.error(request, 'Invalid data submitted.')
            return redirect('mark_attendance')

        # Create session (or get existing)
        session, created = AttendanceSession.objects.get_or_create(
            subject=selected_subject,
            date=selected_date,
            defaults={'teacher': request.user}
        )

        student_ids = request.POST.getlist('student_ids')
        present_ids = request.POST.getlist('present_students')

        for sid in student_ids:
            student = get_object_or_404(Student, pk=sid)
            status = 'PRESENT' if sid in present_ids else 'ABSENT'
            AttendanceRecord.objects.update_or_create(
                session=session,
                student=student,
                defaults={'status': status}
            )

        messages.success(request, f'Attendance marked for {selected_subject.name} on {selected_date}.')
        return redirect('teacher_dashboard')

    return render(request, 'attendance/mark_attendance.html', {
        'form': form,
        'students': students,
        'selected_subject': selected_subject,
        'selected_date': selected_date,
        'already_marked': already_marked,
    })


@login_required
@teacher_required
def teacher_attendance_report(request):
    subjects = Subject.objects.filter(teacher=request.user)
    selected_subject = None
    sessions = []
    if request.GET.get('subject'):
        try:
            selected_subject = subjects.get(pk=request.GET['subject'])
            sessions = AttendanceSession.objects.filter(
                subject=selected_subject
            ).prefetch_related('records__student__user').order_by('-date')
        except Subject.DoesNotExist:
            pass
    return render(request, 'attendance/teacher_report.html', {
        'subjects': subjects,
        'selected_subject': selected_subject,
        'sessions': sessions,
    })


# ─────────────────────────────────────────────
#  STUDENT VIEWS
# ─────────────────────────────────────────────

def student_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'STUDENT':
            messages.error(request, 'Access denied.')
            return redirect('login')
        return view_func(request, *args, **kwargs)
    return wrapper


@login_required
@student_required
def student_dashboard(request):
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        messages.error(request, 'Student profile not found.')
        return redirect('login')

    subjects = Subject.objects.filter(
        department=student.department,
        semester=student.semester
    )

    subject_data = []
    overall_present = 0
    overall_total = 0

    for subject in subjects:
        records = AttendanceRecord.objects.filter(
            student=student, session__subject=subject
        )
        total = records.count()
        present = records.filter(status='PRESENT').count()
        percentage = round((present / total) * 100, 1) if total > 0 else 0
        overall_present += present
        overall_total += total
        subject_data.append({
            'subject': subject,
            'total': total,
            'present': present,
            'absent': total - present,
            'percentage': percentage,
        })

    overall_percentage = round((overall_present / overall_total) * 100, 1) if overall_total > 0 else 0

    return render(request, 'attendance/student_dashboard.html', {
        'student': student,
        'subject_data': subject_data,
        'overall_present': overall_present,
        'overall_absent': overall_total - overall_present,
        'overall_total': overall_total,
        'overall_percentage': overall_percentage,
    })


@login_required
@student_required
def student_attendance_detail(request, subject_id):
    try:
        student = request.user.student_profile
    except Student.DoesNotExist:
        return redirect('login')

    subject = get_object_or_404(Subject, pk=subject_id)
    records = AttendanceRecord.objects.filter(
        student=student, session__subject=subject
    ).select_related('session').order_by('-session__date')

    total = records.count()
    present = records.filter(status='PRESENT').count()
    percentage = round((present / total) * 100, 1) if total > 0 else 0

    return render(request, 'attendance/student_detail.html', {
        'subject': subject,
        'records': records,
        'total': total,
        'present': present,
        'absent': total - present,
        'percentage': percentage,
    })
