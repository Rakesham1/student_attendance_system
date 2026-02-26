from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Department, Subject, Student, AttendanceSession, AttendanceRecord


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'role', 'is_active')
    list_filter = ('role', 'is_active')
    fieldsets = UserAdmin.fieldsets + (
        ('Role Info', {'fields': ('role', 'phone')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Info', {'fields': ('role', 'phone', 'first_name', 'last_name', 'email')}),
    )


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'created_at')
    search_fields = ('name', 'code')


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'department', 'teacher', 'semester')
    list_filter = ('department', 'semester')
    search_fields = ('name', 'code')


@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('roll_number', 'get_name', 'department', 'semester', 'joining_year')
    list_filter = ('department', 'semester')
    search_fields = ('roll_number', 'user__first_name', 'user__last_name')

    def get_name(self, obj):
        return obj.user.get_full_name()
    get_name.short_description = 'Name'


@admin.register(AttendanceSession)
class AttendanceSessionAdmin(admin.ModelAdmin):
    list_display = ('subject', 'date', 'teacher', 'created_at')
    list_filter = ('subject', 'date')


@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('get_student', 'get_subject', 'get_date', 'status')
    list_filter = ('status', 'session__subject')

    def get_student(self, obj):
        return obj.student.roll_number
    get_student.short_description = 'Roll No'

    def get_subject(self, obj):
        return obj.session.subject.name
    get_subject.short_description = 'Subject'

    def get_date(self, obj):
        return obj.session.date
    get_date.short_description = 'Date'
