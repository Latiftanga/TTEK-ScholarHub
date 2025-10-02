from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponse
from django.db.models import Q
from .models import Teacher
from .forms import TeacherForm, BulkTeacherUploadForm
from .utils import BulkTeacherProcessor
import pandas as pd
from io import BytesIO

@login_required
def teacher_list(request):
    """List all teachers"""
    teachers = Teacher.objects.filter(is_active=True).select_related('user')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        teachers = teachers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(employee_id__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(specialization__icontains=search_query)
        )
    
    # Check if HTMX request
    if request.headers.get('HX-Request'):
        return render(request, 'teachers/teacher_list_content.html', {
            'teachers': teachers,
            'search_query': search_query
        })
    
    return render(request, 'teachers/teacher_list.html', {
        'teachers': teachers,
        'search_query': search_query
    })


@login_required
def teacher_create(request):
    """Create a new teacher"""
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES)
        if form.is_valid():
            teacher = form.save()
            messages.success(
                request, 
                f"Teacher {teacher.get_full_name()} created successfully!"
            )
            
            # If HTMX request, return the new row
            if request.headers.get('HX-Request'):
                return render(request, 'teachers/teacher_row.html', {
                    'teacher': teacher
                })
            
            return redirect('teachers:detail', pk=teacher.pk)
        else:
            if request.headers.get('HX-Request'):
                return render(request, 'teachers/teacher_form.html', {
                    'form': form,
                    'title': 'Create Teacher'
                })
    else:
        form = TeacherForm()
    
    return render(request, 'teachers/teacher_form.html', {
        'form': form,
        'title': 'Create Teacher'
    })


@login_required
def teacher_detail(request, pk):
    """View teacher details"""
    teacher = get_object_or_404(Teacher, pk=pk)
    
    if request.headers.get('HX-Request'):
        return render(request, 'teachers/teacher_detail_content.html', {
            'teacher': teacher
        })
    
    return render(request, 'teachers/teacher_detail.html', {
        'teacher': teacher
    })


@login_required
def teacher_edit(request, pk):
    """Edit teacher"""
    teacher = get_object_or_404(Teacher, pk=pk)
    
    if request.method == 'POST':
        form = TeacherForm(request.POST, request.FILES, instance=teacher)
        if form.is_valid():
            teacher = form.save()
            messages.success(request, f"Teacher {teacher.get_full_name()} updated successfully!")
            
            if request.headers.get('HX-Request'):
                return redirect('teachers:detail', pk=teacher.pk)
            
            return redirect('teachers:detail', pk=teacher.pk)
    else:
        form = TeacherForm(instance=teacher)
    
    return render(request, 'teachers/teacher_form.html', {
        'form': form,
        'teacher': teacher,
        'title': 'Edit Teacher'
    })


@login_required
def teacher_delete(request, pk):
    """Delete (deactivate) teacher"""
    teacher = get_object_or_404(Teacher, pk=pk)
    
    if request.method == 'POST':
        teacher.is_active = False
        teacher.save()
        messages.success(request, f"Teacher {teacher.get_full_name()} deactivated successfully!")
        
        if request.headers.get('HX-Request'):
            return HttpResponse(status=200)
        
        return redirect('teachers:list')
    
    return render(request, 'teachers/teacher_confirm_delete.html', {
        'teacher': teacher
    })


@login_required
def teacher_bulk_upload(request):
    """Bulk upload teachers via Excel/CSV"""
    if request.method == 'POST':
        form = BulkTeacherUploadForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                processor = BulkTeacherProcessor(
                    file=form.cleaned_data['file'],
                    create_accounts=form.cleaned_data['create_user_accounts'],
                    send_emails=form.cleaned_data['send_credentials_email']
                )
                
                result = processor.process()
                
                messages.success(
                    request,
                    f"Successfully imported {result['success']} teachers!"
                )
                
                if result['errors']:
                    for error in result['errors']:
                        messages.warning(request, error)
                
                return redirect('teachers:list')
            
            except Exception as e:
                messages.error(request, f"Error processing file: {str(e)}")
    else:
        form = BulkTeacherUploadForm()
    
    return render(request, 'teachers/teacher_bulk_upload.html', {
        'form': form
    })


@login_required
def download_template(request):
    """Download sample Excel template"""
    df = BulkTeacherProcessor.get_sample_template()
    
    # Create Excel file in memory
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Teachers')
    
    output.seek(0)
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=teacher_template.xlsx'
    
    return response