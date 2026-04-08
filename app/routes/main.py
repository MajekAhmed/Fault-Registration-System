from flask import Blueprint, render_template, request, redirect, url_for, jsonify
from ..models import Project, MainDevice, SubDevice, Employee, Problem, DeviceTimeline, db
from ..services import generate_problem_id, get_current_time
from datetime import datetime

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """الصفحة الرئيسية - تعرض آخر 5 أعطال"""
    tenant_id = 1  # TODO: Get from session/user
    problems = db.session.query(
        Problem.ProblemID,
        Problem.MainDeviceID,
        Project.ProjectName,
        MainDevice.DeviceName,
        Problem.ProblemDescription,
        Problem.ReportedDate,
        Problem.ReportedTime,
        Problem.Status,
        Employee.FullName.label('AssignedToName')
    ).join(Project, Problem.ProjectID == Project.ProjectID) \
     .join(MainDevice, Problem.MainDeviceID == MainDevice.MainDeviceID) \
     .outerjoin(Employee, Problem.AssignedTo == Employee.EmployeeID) \
     .filter(Problem.TenantID == tenant_id) \
     .order_by(Problem.ProblemID.desc()) \
     .limit(5).all()

    return render_template('index.html', problems=problems)

@main_bp.route('/add_problem', methods=['GET'])
def add_problem():
    """عرض صفحة إضافة عطل جديد"""
    tenant_id = 1  # TODO: Get from session/user
    projects = Project.query.filter_by(TenantID=tenant_id, IsActive=True).all()
    employees = Employee.query.filter_by(TenantID=tenant_id, IsActive=True).all()
    return render_template('add_problem.html', projects=projects, employees=employees)

@main_bp.route('/add_problem', methods=['POST'])
def save_problem():
    """استقبال بيانات العطل الجديد وحفظها في قاعدة البيانات"""
    tenant_id = 1  # TODO: Get from session/user
    project_id = request.form.get('project_id')
    main_device_id = request.form.get('main_device_id')
    sub_device_id = request.form.get('sub_device_id') or None
    description = request.form.get('problem_description')
    status = request.form.get('status', 'مفتوح')
    assigned_to = request.form.get('assigned_to') or None

    # جلب Location و Type تلقائياً من الجهاز المختار
    device = MainDevice.query.get(main_device_id)
    location = device.Location if device else ''
    device_type = device.DeviceType if device else ''

    # توليد ProblemID
    problem_id = generate_problem_id()

    # إنشاء العطل الجديد
    new_problem = Problem(
        ProblemID=problem_id,
        TenantID=tenant_id,
        ProjectID=project_id,
        MainDeviceID=main_device_id,
        SubDeviceID=sub_device_id,
        ProblemDescription=description,
        ReportedDate=datetime.now().strftime('%Y-%m-%d'),
        ReportedTime=get_current_time(),
        Status=status,
        AssignedTo=assigned_to,
        Location=location,
        DeviceType=device_type
    )

    db.session.add(new_problem)

    # إضافة حدث تلقائي في DeviceTimeline
    timeline_event = DeviceTimeline(
        TenantID=tenant_id,
        DeviceID=main_device_id,
        EventDate=datetime.now().strftime('%Y-%m-%d'),
        EventTime=get_current_time(),
        EventType='عطل جديد',
        Description=f'تم تسجيل عطل جديد: {description}'
    )
    db.session.add(timeline_event)

    db.session.commit()

    return redirect(url_for('main.index'))

@main_bp.route('/view_problems', methods=['GET'])
def view_problems():
    """عرض صفحة البحث عن الأعطال"""
    return render_template('view_problems.html')

@main_bp.route('/view_problems', methods=['POST'])
def search_problems():
    """البحث عن الأعطال حسب المعايير"""
    tenant_id = 1  # TODO: Get from session/user
    search = request.form.get('search', '').strip()
    from_date = request.form.get('from_date', '')
    to_date = request.form.get('to_date', '')

    query = db.session.query(
        Problem.ProblemID,
        Project.ProjectName,
        MainDevice.DeviceName,
        SubDevice.SubDeviceName,
        Problem.Location,
        Problem.DeviceType,
        Problem.ProblemDescription,
        Problem.ReportedDate,
        Problem.ReportedTime,
        Problem.Status,
        Problem.Solution,
        Employee.FullName.label('AssignedToName'),
        Problem.UpdateNo,
        Problem.RepairDurationHours
    ).join(Project, Problem.ProjectID == Project.ProjectID) \
     .join(MainDevice, Problem.MainDeviceID == MainDevice.MainDeviceID) \
     .outerjoin(SubDevice, Problem.SubDeviceID == SubDevice.SubDeviceID) \
     .outerjoin(Employee, Problem.AssignedTo == Employee.EmployeeID) \
     .filter(Problem.TenantID == tenant_id)

    # تطبيق الفلاتر
    if search:
        query = query.filter(
            db.or_(
                Problem.ProblemDescription.contains(search),
                MainDevice.DeviceName.contains(search),
                Project.ProjectName.contains(search)
            )
        )

    if from_date:
        query = query.filter(Problem.ReportedDate >= from_date)
    if to_date:
        query = query.filter(Problem.ReportedDate <= to_date)

    problems = query.order_by(Problem.ProblemID.desc()).all()

    return render_template('view_problems.html', problems=problems, search=search, from_date=from_date, to_date=to_date)

@main_bp.route('/edit_problem/<int:problem_id>', methods=['GET'])
def edit_problem(problem_id):
    """عرض صفحة تعديل العطل"""
    tenant_id = 1  # TODO: Get from session/user
    problem = Problem.query.filter_by(ProblemID=problem_id, TenantID=tenant_id).first_or_404()
    projects = Project.query.filter_by(TenantID=tenant_id, IsActive=True).all()
    employees = Employee.query.filter_by(TenantID=tenant_id, IsActive=True).all()
    return render_template('edit_problem.html', problem=problem, projects=projects, employees=employees)

@main_bp.route('/edit_problem/<int:problem_id>', methods=['POST'])
def update_problem(problem_id):
    """تحديث بيانات العطل"""
    tenant_id = 1  # TODO: Get from session/user
    problem = Problem.query.filter_by(ProblemID=problem_id, TenantID=tenant_id).first_or_404()

    problem.ProjectID = request.form.get('project_id')
    problem.MainDeviceID = request.form.get('main_device_id')
    problem.SubDeviceID = request.form.get('sub_device_id') or None
    problem.ProblemDescription = request.form.get('problem_description')
    problem.Status = request.form.get('status')
    problem.AssignedTo = request.form.get('assigned_to') or None
    problem.Solution = request.form.get('solution')

    if problem.Status == 'مغلق' and not problem.ClosedDate:
        problem.ClosedDate = datetime.now().strftime('%Y-%m-%d')
        problem.ClosedTime = get_current_time()
        # حساب MTTR إذا أمكن
        if problem.RepairDurationHours:
            problem.MTTR = problem.RepairDurationHours

    problem.UpdateNo += 1
    db.session.commit()

    return redirect(url_for('main.view_problems'))

@main_bp.route('/reports')
def reports():
    """صفحة التقارير"""
    return render_template('reports.html')

@main_bp.route('/api/sub_devices/<int:main_device_id>')
def get_sub_devices(main_device_id):
    """API لجلب الأجهزة الثانوية لجهاز رئيسي"""
    tenant_id = 1  # TODO: Get from session/user
    sub_devices = SubDevice.query.filter_by(MainDeviceID=main_device_id, TenantID=tenant_id, IsActive=True).all()
    return jsonify([{'id': sd.SubDeviceID, 'name': sd.SubDeviceName} for sd in sub_devices])

@main_bp.route('/api/device_info/<int:device_id>')
def get_device_info(device_id):
    """API لجلب معلومات الجهاز"""
    device = MainDevice.query.get(device_id)
    if device:
        return jsonify({
            'location': device.Location,
            'type': device.DeviceType
        })
    return jsonify({})