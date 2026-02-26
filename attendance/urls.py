from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Admin
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('departments/', views.manage_departments, name='manage_departments'),
    path('departments/delete/<int:pk>/', views.delete_department, name='delete_department'),
    path('students/', views.manage_students, name='manage_students'),
    path('students/delete/<int:pk>/', views.delete_student, name='delete_student'),
    path('teachers/', views.manage_teachers, name='manage_teachers'),
    path('teachers/delete/<int:pk>/', views.delete_teacher, name='delete_teacher'),
    path('subjects/', views.manage_subjects, name='manage_subjects'),
    path('subjects/delete/<int:pk>/', views.delete_subject, name='delete_subject'),

    # Teacher
    path('teacher/dashboard/', views.teacher_dashboard, name='teacher_dashboard'),
    path('teacher/mark-attendance/', views.mark_attendance, name='mark_attendance'),
    path('teacher/report/', views.teacher_attendance_report, name='teacher_report'),

    # Student
    path('student/dashboard/', views.student_dashboard, name='student_dashboard'),
    path('student/attendance/<int:subject_id>/', views.student_attendance_detail, name='student_detail'),
]
