from flask import Blueprint, render_template, request, redirect, url_for
from ..models import MainDevice, SubDevice, Problem, DeviceTimeline, Project, db
from ..services import get_current_time
from datetime import datetime

devices_bp = Blueprint('devices', __name__)

@devices_bp.route('/device_card/<int:device_id>')
def device_card(device_id):
    """بطاقة الجهاز الرئيسي - تعرض كل تاريخ الجهاز والتايم لاين"""
    device = MainDevice.query.get_or_404(device_id)

    # ---- إحصائيات الجهاز ----
    total_faults = Problem.query.filter_by(MainDeviceID=device_id).count()
    open_faults = Problem.query.filter_by(MainDeviceID=device_id, Status='مفتوح').count()
    closed_faults = Problem.query.filter_by(MainDeviceID=device_id, Status='مغلق').count()

    # متوسط وقت الإصلاح
    avg_mttr = db.session.query(db.func.avg(Problem.MTTR)).filter(
        Problem.MainDeviceID == device_id,
        Problem.Status == 'مغلق',
        Problem.MTTR.isnot(None)
    ).scalar() or 0

    # ---- التايم لاين ----
    timeline = DeviceTimeline.query.filter_by(DeviceID=device_id).order_by(
        DeviceTimeline.EventDate.desc(),
        DeviceTimeline.EventTime.desc()
    ).all()

    # ---- الأعطال المرتبطة ----
    problems = Problem.query.filter_by(MainDeviceID=device_id).order_by(Problem.ProblemID.desc()).all()

    # ---- الأجهزة الثانوية ----
    sub_devices = SubDevice.query.filter_by(MainDeviceID=device_id, IsActive=True).all()

    return render_template('device_card.html',
                         device=device,
                         total_faults=total_faults,
                         open_faults=open_faults,
                         closed_faults=closed_faults,
                         avg_mttr=round(avg_mttr, 2),
                         timeline=timeline,
                         problems=problems,
                         sub_devices=sub_devices)

@devices_bp.route('/sub_device_card/<int:sub_device_id>')
def sub_device_card(sub_device_id):
    """بطاقة الجهاز الثانوي - تعرض كل تاريخ الجهاز الثانوي والتايم لاين"""
    sub_device = SubDevice.query.get_or_404(sub_device_id)

    # ---- إحصائيات الجهاز الثانوي ----
    total_faults = Problem.query.filter_by(SubDeviceID=sub_device_id).count()
    open_faults = Problem.query.filter_by(SubDeviceID=sub_device_id, Status='مفتوح').count()
    closed_faults = Problem.query.filter_by(SubDeviceID=sub_device_id, Status='مغلق').count()

    # متوسط وقت الإصلاح
    avg_mttr = db.session.query(db.func.avg(Problem.MTTR)).filter(
        Problem.SubDeviceID == sub_device_id,
        Problem.Status == 'مغلق',
        Problem.MTTR.isnot(None)
    ).scalar() or 0

    # ---- الأعطال المرتبطة ----
    problems = Problem.query.filter_by(SubDeviceID=sub_device_id).order_by(Problem.ProblemID.desc()).all()

    return render_template('sub_device_card.html',
                         sub_device=sub_device,
                         total_faults=total_faults,
                         open_faults=open_faults,
                         closed_faults=closed_faults,
                         avg_mttr=round(avg_mttr, 2),
                         problems=problems)

@devices_bp.route('/add_timeline_event/<int:device_id>', methods=['POST'])
def add_timeline_event(device_id):
    """إضافة حدث جديد في التايم لاين"""
    event_type = request.form.get('event_type')
    description = request.form.get('description')

    new_event = DeviceTimeline(
        DeviceID=device_id,
        EventDate=datetime.now().strftime('%Y-%m-%d'),
        EventTime=get_current_time(),
        EventType=event_type,
        Description=description
    )

    db.session.add(new_event)
    db.session.commit()

    return redirect(url_for('devices.device_card', device_id=device_id))