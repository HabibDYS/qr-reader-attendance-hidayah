# Copyright (c) 2026 SMK Hidayah. All rights reserved.
# This file is part of QR Reader Attendance System

from flask import Blueprint, render_template, jsonify, request, redirect, url_for, send_file, flash, current_app
from flask_login import login_required, current_user
from app.models.user import User
from app.models.attendance import Attendance
from app import db
from datetime import datetime, timedelta
import pandas as pd
import io
import os
import logging
import qrcode

# Set up logging
logger = logging.getLogger(__name__)

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    """Decorator to ensure the user is an admin."""
    @login_required
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You must be an admin to access this page.', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@bp.route('/admin-portal')
@admin_required
def admin_portal():
    """Admin portal dashboard."""
    # Get today's attendance count
    today = datetime.now().date()
    today_attendance = Attendance.query.filter_by(date=today).count()
    
    # Get total students
    total_students = User.query.filter_by(role='student').count()
    
    # Get attendance statistics
    start_date = today - timedelta(days=30)
    attendance_stats = Attendance.query.filter(
        Attendance.date >= start_date,
        Attendance.date <= today
    ).count()
    
    # Get recent attendance records
    recent_attendance = Attendance.query.order_by(Attendance.date.desc(), Attendance.check_in.desc()).limit(5).all()
    
    stats = {
        'today_attendance': today_attendance,
        'total_students': total_students,
        'monthly_attendance': attendance_stats
    }
    
    return render_template('admin/portal.html', stats=stats, recent_attendance=recent_attendance)

@bp.route('/scan')
@admin_required
def scan_attendance():
    """QR code scanning page for attendance."""
    return render_template('admin/scan.html')

@bp.route('/view-attendance')
@admin_required
def view_attendance():
    """View attendance records for a specific date."""
    try:
        date_str = request.args.get('date')
        if date_str:
            try:
                selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                flash('Invalid date format', 'danger')
                selected_date = datetime.now().date()
        else:
            selected_date = datetime.now().date()

        attendance_records = Attendance.query.filter_by(date=selected_date).all()
        return render_template('admin/view_attendance.html', 
                             attendance_records=attendance_records,
                             selected_date=selected_date)
    except Exception as e:
        logger.error(f"Error viewing attendance: {str(e)}")
        flash('An error occurred while viewing attendance', 'danger')
        return redirect(url_for('admin.admin_portal'))

@bp.route('/student-list')
@admin_required
def student_list():
    """View list of all students with search functionality."""
    search_query = request.args.get('search', '').strip()
    
    if search_query:
        students = User.query.filter(
            User.role == 'student',
            db.or_(
                User.name.ilike(f'%{search_query}%'),
                User.username.ilike(f'%{search_query}%'),
                User.email.ilike(f'%{search_query}%')
            )
        ).all()
    else:
        students = User.query.filter_by(role='student').all()
    
    return render_template('admin/students.html', students=students)

@bp.route('/generate-report', methods=['GET', 'POST'])
@admin_required
def generate_report():
    """Generate attendance report for a date range."""
    if request.method == 'POST':
        try:
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d').date()
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d').date()
            
            if start_date > end_date:
                flash('Start date must be before end date', 'danger')
                return redirect(url_for('admin.generate_report'))

            attendance_records = Attendance.query.filter(
                Attendance.date.between(start_date, end_date)
            ).all()

            return render_template('admin/report.html',
                                 attendance_records=attendance_records,
                                 start_date=start_date,
                                 end_date=end_date)
        except ValueError:
            flash('Invalid date format', 'danger')
            return redirect(url_for('admin.generate_report'))
        except Exception as e:
            logger.error(f"Error generating report: {str(e)}")
            flash('An error occurred while generating the report', 'danger')
            return redirect(url_for('admin.generate_report'))

    return render_template('admin/generate_report.html')

@bp.route('/export_attendance')
@admin_required
def export_attendance():
    # Get date range
    start_date = request.args.get('start_date', 
                                 (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
    
    # Query attendance records
    attendances = Attendance.query.filter(
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).order_by(Attendance.date.desc()).all()
    
    # Create DataFrame
    data = []
    for record in attendances:
        data.append({
            'Date': record.date.strftime('%Y-%m-%d'),
            'Student Name': record.user.name,
            'Check In': record.check_in.strftime('%H:%M:%S') if record.check_in else 'N/A',
            'Check Out': record.check_out.strftime('%H:%M:%S') if record.check_out else 'N/A',
            'Status': record.status
        })
    
    df = pd.DataFrame(data)
    
    # Create Excel file in memory
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Attendance', index=False)
    
    output.seek(0)
    
    return send_file(
        output,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=f'attendance_report_{start_date}_to_{end_date}.xlsx'
    )

@bp.route('/register-student', methods=['GET', 'POST'])
@admin_required
def register_student():
    """Register a new student from admin panel."""
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            
            # Validate input
            if not all([name, username, email, password]):
                flash('All fields are required', 'danger')
                return redirect(url_for('admin.register_student'))
            
            # Check if username or email already exists
            if User.query.filter_by(username=username).first():
                flash('Username already exists', 'danger')
                return redirect(url_for('admin.register_student'))
                
            if User.query.filter_by(email=email).first():
                flash('Email already registered', 'danger')
                return redirect(url_for('admin.register_student'))
            
            # Create new student user
            user = User(
                name=name,
                username=username,
                email=email,
                role='student'
            )
            user.set_password(password)
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=5)
            qr.add_data(username)
            qr.make(fit=True)
            qr_image = qr.make_image(fill_color="black", back_color="white")
            
            # Save QR code
            qr_filename = f'qr_{username}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.png'
            qr_path = os.path.join('app', 'static', 'qrcodes', qr_filename)
            os.makedirs(os.path.dirname(qr_path), exist_ok=True)
            qr_image.save(qr_path)
            
            user.qr_code = qr_filename
            db.session.add(user)
            db.session.commit()
            
            flash(f'Student {name} ({username}) registered successfully!', 'success')
            return redirect(url_for('admin.register_student'))
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error registering student: {str(e)}")
            flash('An error occurred while registering the student', 'danger')
            return redirect(url_for('admin.register_student'))
    
    return render_template('admin/register_student.html')

@bp.route('/mark-attendance', methods=['POST'])
@admin_required
def mark_attendance():
    """API endpoint to mark attendance for a student."""
    try:
        data = request.get_json()
        if not data or 'username' not in data or 'action' not in data:
            return jsonify({'success': False, 'message': 'Invalid request data'}), 400

        username = data['username']
        action = data['action']

        if action not in ['check-in']:
            return jsonify({'success': False, 'message': 'Invalid action'}), 400

        user = User.query.filter_by(username=username).first()
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404

        if user.role != 'student':
            return jsonify({'success': False, 'message': 'Only students can be marked for attendance'}), 400

        today = datetime.now().date()
        attendance = Attendance.query.filter_by(
            user_id=user.id,
            date=today
        ).first()

        if not attendance:
            attendance = Attendance(user_id=user.id, date=today)
            db.session.add(attendance)

        current_time = datetime.now()
        
        if action == 'check-in':
            if attendance.check_in:
                return jsonify({'success': False, 'message': 'Already checked in today'}), 400
            attendance.check_in = current_time
            message = f'Check-in recorded for {user.name}'

        attendance.update_status()
        db.session.commit()

        return jsonify({
            'success': True,
            'message': message,
            'attendance': attendance.to_dict()
        })

    except Exception as e:
        logger.error(f"Error marking attendance: {str(e)}")
        db.session.rollback()
        return jsonify({'success': False, 'message': 'An error occurred while marking attendance'}), 500

@bp.route('/student/<int:student_id>')
@admin_required
def view_student(student_id):
    """View detailed information about a specific student."""
    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        flash('User is not a student', 'danger')
        return redirect(url_for('admin.student_list'))
    
    # Get attendance statistics
    today = datetime.now().date()
    month_start = today.replace(day=1)
    
    attendance_records = Attendance.query.filter_by(user_id=student_id).order_by(Attendance.date.desc()).limit(10).all()
    
    total_attendance = Attendance.query.filter_by(user_id=student_id, status='present').count()
    total_late = Attendance.query.filter_by(user_id=student_id, status='late').count()
    total_absent = Attendance.query.filter_by(user_id=student_id, status='absent').count()
    
    month_attendance = Attendance.query.filter(
        Attendance.user_id == student_id,
        Attendance.date >= month_start,
        Attendance.date <= today
    ).count()
    
    stats = {
        'total_present': total_attendance,
        'total_late': total_late,
        'total_absent': total_absent,
        'month_attendance': month_attendance
    }
    
    return render_template('admin/view_student.html', 
                         student=student, 
                         attendance_records=attendance_records,
                         stats=stats)

@bp.route('/student/<int:student_id>/edit', methods=['GET', 'POST'])
@admin_required
def edit_student(student_id):
    """Edit student information."""
    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        flash('User is not a student', 'danger')
        return redirect(url_for('admin.student_list'))
    
    if request.method == 'POST':
        try:
            name = request.form.get('name')
            email = request.form.get('email')
            
            if not name or not email:
                flash('Name and email are required', 'danger')
                return redirect(url_for('admin.edit_student', student_id=student_id))
            
            # Check if email is already used by another user
            existing_email = User.query.filter(User.email == email, User.id != student_id).first()
            if existing_email:
                flash('Email is already taken', 'danger')
                return redirect(url_for('admin.edit_student', student_id=student_id))
            
            student.name = name
            student.email = email
            
            db.session.commit()
            flash('Student information updated successfully', 'success')
            return redirect(url_for('admin.view_student', student_id=student_id))
        except Exception as e:
            logger.error(f"Error updating student: {str(e)}")
            db.session.rollback()
            flash('An error occurred while updating student information', 'danger')
            return redirect(url_for('admin.edit_student', student_id=student_id))
    
    return render_template('admin/edit_student.html', student=student)

@bp.route('/student/<int:student_id>/delete', methods=['POST'])
@admin_required
def delete_student(student_id):
    """Delete a student and all their records."""
    student = User.query.get_or_404(student_id)
    if student.role != 'student':
        flash('User is not a student', 'danger')
        return redirect(url_for('admin.student_list'))
    
    try:
        student_name = student.name
        db.session.delete(student)
        db.session.commit()
        flash(f'Student {student_name} has been deleted successfully', 'success')
    except Exception as e:
        logger.error(f"Error deleting student: {str(e)}")
        db.session.rollback()
        flash('An error occurred while deleting the student', 'danger')
    
    return redirect(url_for('admin.student_list')) 