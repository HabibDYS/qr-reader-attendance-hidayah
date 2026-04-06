# Copyright (c) 2026 SMK Hidayah. All rights reserved.
# This file is part of QR Reader Attendance System

from flask import Blueprint, render_template, flash, redirect, url_for, current_app, request, send_file, jsonify
from flask_login import login_required, current_user
from app.models import User, Attendance
from app.utils.qr_generator import generate_qr_code
from app.utils.attendance import calculate_attendance_stats
from datetime import datetime, timedelta
import os
import logging
import pandas as pd
import io

# Configure logging
logger = logging.getLogger(__name__)

student_bp = Blueprint('student', __name__)

@student_bp.route('/my-qr')
@login_required
def my_qr():
    if current_user.role != 'student':
        flash('Access denied. Students only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Create qrcodes directory if it doesn't exist
        qr_dir = os.path.join(current_app.static_folder, 'qrcodes')
        os.makedirs(qr_dir, exist_ok=True)
        
        # Check if user already has a QR code
        existing_qr = None
        for file in os.listdir(qr_dir):
            if file.startswith(f'qr_{current_user.username}_'):
                existing_qr = file
                break
        
        if existing_qr:
            qr_code_path = f'qrcodes/{existing_qr}'
            logger.info(f"Using existing QR code: {qr_code_path}")
            return render_template('student_qr.html', qr_code_path=qr_code_path)
        
        # Generate new QR code if none exists
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        qr_filename = f'qr_{current_user.username}_{timestamp}.png'
        qr_path = os.path.join(qr_dir, qr_filename)
        
        # Generate QR code
        logger.info(f"Generating QR code for user {current_user.username}")
        generate_qr_code(current_user.username, qr_path, student_name=current_user.name)
        qr_code_path = f'qrcodes/{qr_filename}'
        
        # Verify the file was created
        if not os.path.exists(qr_path):
            raise FileNotFoundError("QR code file was not created")
        
        logger.info(f"QR code generated successfully at {qr_path}")
        flash('QR code generated successfully!', 'success')
        return render_template('student_qr.html', qr_code_path=qr_code_path)
        
    except Exception as e:
        logger.error(f"Error generating QR code: {str(e)}")
        flash('Error generating QR code. Please try again.', 'danger')
        return render_template('student_qr.html', qr_code_path=None)

@student_bp.route('/download-qr/<filename>')
@login_required
def download_qr(filename):
    if current_user.role != 'student':
        flash('Access denied. Students only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Ensure the filename only contains safe characters
        if '..' in filename or filename.startswith('/'):
            raise ValueError("Invalid filename")
            
        qr_path = os.path.join(current_app.static_folder, 'qrcodes', filename)
        
        # Verify file exists and is within the qrcodes directory
        if not os.path.exists(qr_path):
            logger.error(f"QR code file not found: {qr_path}")
            flash('QR code file not found.', 'danger')
            return redirect(url_for('student.my_qr'))
            
        # Send the file
        return send_file(
            qr_path,
            as_attachment=True,
            download_name=f"qr_code_{current_user.username}.png",
            mimetype='image/png'
        )
            
    except Exception as e:
        logger.error(f"Error downloading QR code: {str(e)}")
        flash('Error downloading QR code.', 'danger')
        return redirect(url_for('student.my_qr'))

@student_bp.route('/my-attendance')
@login_required
def my_attendance():
    if current_user.role != 'student':
        flash('Access denied. Students only.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get date filter from query parameters
    date_filter = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
    try:
        filter_date = datetime.strptime(date_filter, '%Y-%m-%d')
    except ValueError:
        filter_date = datetime.now()
    
    # Get attendance records for the student
    attendance_records = Attendance.query.filter_by(
        user_id=current_user.id
    ).filter(
        Attendance.date >= filter_date,
        Attendance.date < filter_date + timedelta(days=1)
    ).order_by(Attendance.date.desc()).all()
    
    return render_template('student_attendance.html', 
                         attendance_records=attendance_records,
                         selected_date=date_filter)

@student_bp.route('/dashboard')
@login_required
def student_dashboard():
    if current_user.role != 'student':
        flash('Access denied. Students only.', 'danger')
        return redirect(url_for('main.index'))
    
    # Get date range for statistics
    end_date = datetime.now().date()
    start_date = end_date - timedelta(days=30)
    
    # Get attendance records
    attendance_records = Attendance.query.filter(
        Attendance.user_id == current_user.id,
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).order_by(Attendance.date.desc()).all()
    
    # Calculate statistics using the enhanced utility function
    stats = calculate_attendance_stats(
        current_user.id,
        start_date=start_date,
        end_date=end_date
    )
    
    # Get today's attendance status
    today_attendance = Attendance.query.filter_by(
        user_id=current_user.id,
        date=datetime.now().date()
    ).first()
    
    return render_template('student_dashboard.html',
                         attendance_records=attendance_records,
                         stats=stats,
                         today_attendance=today_attendance)

@student_bp.route('/export-attendance')
@login_required
def export_attendance():
    """Export student attendance records as CSV"""
    if current_user.role != 'student':
        flash('Access denied. Students only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Get all attendance records for the student
        attendance_records = Attendance.query.filter_by(
            user_id=current_user.id
        ).order_by(Attendance.date.desc()).all()
        
        # Create DataFrame
        data = []
        for record in attendance_records:
            data.append({
                'Tanggal': record.date.strftime('%Y-%m-%d'),
                'Nama Siswa': current_user.name,
                'Username': current_user.username,
                'Check-In': record.check_in.strftime('%H:%M:%S') if record.check_in else 'N/A',
                'Check-Out': record.check_out.strftime('%H:%M:%S') if record.check_out else 'N/A',
                'Status': record.status
            })
        
        df = pd.DataFrame(data)
        
        # Create CSV in memory
        output = io.StringIO()
        df.to_csv(output, index=False, encoding='utf-8-sig')
        output.seek(0)
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8-sig')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'attendance_{current_user.username}_{datetime.now().strftime("%Y%m%d")}.csv'
        )
    except Exception as e:
        logger.error(f"Error exporting attendance: {str(e)}")
        flash('Error exporting attendance. Please try again.', 'danger')
        return redirect(url_for('student.student_dashboard'))

@student_bp.route('/share-attendance')
@login_required
def share_attendance():
    """Generate shareable link for attendance report"""
    if current_user.role != 'student':
        flash('Access denied. Students only.', 'danger')
        return redirect(url_for('main.index'))
    
    try:
        # Get attendance summary
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=30)
        
        attendance_records = Attendance.query.filter(
            Attendance.user_id == current_user.id,
            Attendance.date >= start_date,
            Attendance.date <= end_date
        ).all()
        
        # Calculate stats
        total_days = len(attendance_records)
        present_days = len([a for a in attendance_records if a.status == 'present'])
        late_days = len([a for a in attendance_records if a.status == 'late'])
        absent_days = len([a for a in attendance_records if a.status == 'absent'])
        
        attendance_rate = (present_days / total_days * 100) if total_days > 0 else 0
        
        # Create shareable message
        share_message = f"""
Laporan Kehadiran Siswa
====================
Nama: {current_user.name}
Username: {current_user.username}
Email: {current_user.email}

Periode: {start_date} - {end_date}

📊 Statistik:
- Total Hari: {total_days}
- Hadir: {present_days} hari
- Terlambat: {late_days} hari
- Absen: {absent_days} hari
- Tingkat Kehadiran: {attendance_rate:.1f}%

Dibuat: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        # Return as JSON for easy sharing
        return jsonify({
            'success': True,
            'message': share_message,
            'data': {
                'nama': current_user.name,
                'username': current_user.username,
                'total': total_days,
                'hadir': present_days,
                'terlambat': late_days,
                'absen': absent_days,
                'tingkat_kehadiran': f"{attendance_rate:.1f}%"
            }
        })
    except Exception as e:
        logger.error(f"Error generating share data: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error generating share data'
        }), 500 