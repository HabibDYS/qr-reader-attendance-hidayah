# Copyright (c) 2026 SMK Hidayah. All rights reserved.
# This file is part of QR Reader Attendance System

from flask import Blueprint, render_template, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app.models.attendance import Attendance
from app.models.user import User
from app import db
from datetime import datetime, timedelta
import cv2
from pyzbar.pyzbar import decode
import numpy as np
import base64

bp = Blueprint('attendance', __name__)

@bp.route('/scan')
@login_required
def scan():
    return render_template('attendance/scan.html')

@bp.route('/process_qr', methods=['POST'])
@login_required
def process_qr():
    try:
        # Get the image data from the request
        image_data = request.json['image'].split(',')[1]
        image_bytes = base64.b64decode(image_data)
        
        # Convert to numpy array
        nparr = np.frombuffer(image_bytes, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # Decode QR code
        qr_codes = decode(img)
        
        if not qr_codes:
            return jsonify({'success': False, 'message': 'No QR code detected'})
        
        qr_data = qr_codes[0].data.decode('utf-8')
        user = User.query.filter_by(username=qr_data).first()
        
        if not user:
            return jsonify({'success': False, 'message': 'Invalid QR code'})
        
        # Process attendance
        today = datetime.now().date()
        current_time = datetime.now()
        
        # Get or create attendance record for today with lock
        attendance = Attendance.query.filter_by(user_id=user.id, date=today).first()
        
        if not attendance:
            # First scan - record check-in
            attendance = Attendance(
                user_id=user.id,
                date=today,
                check_in=current_time,
                status='present' if current_time.hour < 7 else 'late'
            )
            db.session.add(attendance)
            try:
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                # Someone else might have created the record, try again
                attendance = Attendance.query.filter_by(user_id=user.id, date=today).first()
                if attendance and attendance.check_in and not attendance.check_out:
                    # The other request was a check-out, so proceed with check-out
                    attendance.check_out = current_time
                    attendance.update_status()
                    db.session.commit()
                    return jsonify({
                        'success': True,
                        'message': f'Check-out recorded for {user.name} at {current_time.strftime("%H:%M:%S")}',
                        'type': 'checkout'
                    })
                elif attendance and not attendance.check_in:
                    # Try to set check-in again
                    attendance.check_in = current_time
                    db.session.commit()
                    return jsonify({
                        'success': True,
                        'message': f'Check-in recorded for {user.name} at {current_time.strftime("%H:%M:%S")}',
                        'type': 'checkin'
                    })
            
            return jsonify({
                'success': True,
                'message': f'Check-in recorded for {user.name} at {current_time.strftime("%H:%M:%S")}',
                'type': 'checkin'
            })
        elif attendance.check_in and not attendance.check_out:
            # Second scan - record check-out
            attendance.check_out = current_time
            attendance.update_status()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': f'Check-out recorded for {user.name} at {current_time.strftime("%H:%M:%S")}',
                'type': 'checkout'
            })
        elif attendance.check_in and attendance.check_out:
            # Attendance already completed
            return jsonify({
                'success': False,
                'message': f'Attendance already completed for {user.name} today'
            })
        else:
            # Shouldn't happen, but handle it
            return jsonify({
                'success': False,
                'message': 'Error processing attendance record'
            })
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@bp.route('/attendance_report')
@login_required
def attendance_report():
    if current_user.role != 'admin':
        flash('Access denied')
        return redirect(url_for('main.dashboard'))
        
    start_date = request.args.get('start_date', 
                                 (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
    end_date = request.args.get('end_date', 
                               datetime.now().strftime('%Y-%m-%d'))
    
    attendances = Attendance.query.filter(
        Attendance.date >= start_date,
        Attendance.date <= end_date
    ).order_by(Attendance.date.desc()).all()
    
    return render_template('attendance/report.html',
                         attendances=attendances,
                         start_date=start_date,
                         end_date=end_date)

@bp.route('/my_qr')
@login_required
def my_qr():
    if current_user.role == 'admin':
        flash('Access denied', 'danger')
        return redirect(url_for('admin.admin_portal'))
    return render_template('attendance/my_qr.html') 