from flask import Blueprint, render_template, request, redirect, url_for
from ..models import Project, MainDevice, SubDevice, Employee, db

database_bp = Blueprint('database', __name__)

@database_bp.route('/edit_database')
def edit_database():
    """صفحة إدارة قاعدة البيانات"""
    tenant_id = 1  # TODO: Get from session/user
    projects = Project.query.filter_by(TenantID=tenant_id).all()
    main_devices = db.session.query(
        MainDevice.MainDeviceID,
        MainDevice.DeviceName,
        Project.ProjectName
    ).join(Project, MainDevice.ProjectID == Project.ProjectID) \
     .filter(MainDevice.TenantID == tenant_id).all()

    sub_devices = db.session.query(
        SubDevice.SubDeviceID,
        SubDevice.SubDeviceName,
        MainDevice.DeviceName.label('MainDeviceName'),
        Project.ProjectName
    ).join(MainDevice, SubDevice.MainDeviceID == MainDevice.MainDeviceID) \
     .join(Project, MainDevice.ProjectID == Project.ProjectID) \
     .filter(SubDevice.TenantID == tenant_id).all()

    employees = Employee.query.filter_by(TenantID=tenant_id).all()

    return render_template('edit_database.html',
                         projects=projects,
                         main_devices=main_devices,
                         sub_devices=sub_devices,
                         employees=employees)

# Projects CRUD
@database_bp.route('/add_project', methods=['POST'])
def add_project():
    tenant_id = 1  # TODO: Get from session/user
    name = request.form.get('project_name')
    if name:
        new_project = Project(TenantID=tenant_id, ProjectName=name)
        db.session.add(new_project)
        db.session.commit()
    return redirect(url_for('database.edit_database') + '#projects-tab')

@database_bp.route('/delete_project/<int:project_id>')
def delete_project(project_id):
    project = Project.query.get_or_404(project_id)
    project.IsActive = False
    db.session.commit()
    return redirect(url_for('database.edit_database') + '#projects-tab')

# Main Devices CRUD
@database_bp.route('/add_main_device', methods=['POST'])
def add_main_device():
    tenant_id = 1  # TODO: Get from session/user
    name = request.form.get('device_name')
    location = request.form.get('location')
    device_type = request.form.get('device_type')
    project_id = request.form.get('project_id')

    if name and project_id:
        new_device = MainDevice(
            TenantID=tenant_id,
            DeviceName=name,
            Location=location,
            DeviceType=device_type,
            ProjectID=project_id
        )
        db.session.add(new_device)
        db.session.commit()
    return redirect(url_for('database.edit_database') + '#maindevices-tab')

@database_bp.route('/delete_main_device/<int:device_id>')
def delete_main_device(device_id):
    device = MainDevice.query.get_or_404(device_id)
    device.IsActive = False
    db.session.commit()
    return redirect(url_for('database.edit_database') + '#maindevices-tab')

# Sub Devices CRUD
@database_bp.route('/add_sub_device', methods=['POST'])
def add_sub_device():
    tenant_id = 1  # TODO: Get from session/user
    name = request.form.get('sub_device_name')
    sub_type = request.form.get('sub_device_type')
    main_device_id = request.form.get('main_device_id')

    if name and main_device_id:
        new_sub_device = SubDevice(
            TenantID=tenant_id,
            SubDeviceName=name,
            SubDeviceType=sub_type,
            MainDeviceID=main_device_id
        )
        db.session.add(new_sub_device)
        db.session.commit()
    return redirect(url_for('database.edit_database') + '#subdevices-tab')

@database_bp.route('/delete_sub_device/<int:sub_device_id>')
def delete_sub_device(sub_device_id):
    sub_device = SubDevice.query.get_or_404(sub_device_id)
    sub_device.IsActive = False
    db.session.commit()
    return redirect(url_for('database.edit_database') + '#subdevices-tab')

# Employees CRUD
@database_bp.route('/add_employee', methods=['POST'])
def add_employee():
    tenant_id = 1  # TODO: Get from session/user
    code = request.form.get('employee_code')
    name = request.form.get('full_name')

    if name:
        new_employee = Employee(TenantID=tenant_id, EmployeeCode=code, FullName=name)
        db.session.add(new_employee)
        db.session.commit()
    return redirect(url_for('database.edit_database') + '#employees-tab')

@database_bp.route('/delete_employee/<int:employee_id>')
def delete_employee(employee_id):
    employee = Employee.query.get_or_404(employee_id)
    employee.IsActive = False
    db.session.commit()
    return redirect(url_for('database.edit_database') + '#employees-tab')