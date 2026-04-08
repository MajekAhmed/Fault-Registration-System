from ..extensions import db
from datetime import datetime

class Project(db.Model):
    __tablename__ = 'projects'

    ProjectID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ProjectName = db.Column(db.String(255), nullable=False)
    IsActive = db.Column(db.Boolean, default=True)

    # Relationships
    main_devices = db.relationship('MainDevice', backref='project', lazy=True)
    problems = db.relationship('Problem', backref='project', lazy=True)

class MainDevice(db.Model):
    __tablename__ = 'MainDevices'

    MainDeviceID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    DeviceName = db.Column(db.String(255), nullable=False)
    Location = db.Column(db.String(255))
    DeviceType = db.Column(db.String(255))
    ProjectID = db.Column(db.Integer, db.ForeignKey('projects.ProjectID'))
    IsActive = db.Column(db.Boolean, default=True)

    # Relationships
    sub_devices = db.relationship('SubDevice', backref='main_device', lazy=True)
    problems = db.relationship('Problem', backref='main_device', lazy=True)
    timeline = db.relationship('DeviceTimeline', backref='device', lazy=True)

class SubDevice(db.Model):
    __tablename__ = 'SubDevices'

    SubDeviceID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SubDeviceName = db.Column(db.String(255), nullable=False)
    SubDeviceType = db.Column(db.String(255))
    MainDeviceID = db.Column(db.Integer, db.ForeignKey('MainDevices.MainDeviceID'))
    IsActive = db.Column(db.Boolean, default=True)

    # Relationships
    problems = db.relationship('Problem', backref='sub_device', lazy=True)

class Employee(db.Model):
    __tablename__ = 'Employees'

    EmployeeID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    EmployeeCode = db.Column(db.String(255))
    FullName = db.Column(db.String(255), nullable=False)
    IsActive = db.Column(db.Boolean, default=True)

    # Relationships
    problems = db.relationship('Problem', backref='assigned_employee', lazy=True)

class Problem(db.Model):
    __tablename__ = 'problems'

    ProblemID = db.Column(db.Integer, primary_key=True)
    ProjectID = db.Column(db.Integer, db.ForeignKey('projects.ProjectID'))
    MainDeviceID = db.Column(db.Integer, db.ForeignKey('MainDevices.MainDeviceID'))
    SubDeviceID = db.Column(db.Integer, db.ForeignKey('SubDevices.SubDeviceID'), nullable=True)
    ProblemDescription = db.Column(db.Text)
    ReportedDate = db.Column(db.String(50))
    ReportedTime = db.Column(db.String(50))
    Status = db.Column(db.String(50), default='مفتوح')
    AssignedTo = db.Column(db.Integer, db.ForeignKey('Employees.EmployeeID'), nullable=True)
    Location = db.Column(db.String(255))
    DeviceType = db.Column(db.String(255))
    ClosedDate = db.Column(db.String(50))
    ClosedTime = db.Column(db.String(50))
    Solution = db.Column(db.Text)
    MTTR = db.Column(db.Float)
    UpdateNo = db.Column(db.Integer, default=0)
    RepairDurationHours = db.Column(db.Float)

class DeviceTimeline(db.Model):
    __tablename__ = 'DeviceTimeline'

    TimelineID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    DeviceID = db.Column(db.Integer, db.ForeignKey('MainDevices.MainDeviceID'))
    EventDate = db.Column(db.String(50))
    EventTime = db.Column(db.String(50))
    EventType = db.Column(db.String(255))
    Description = db.Column(db.Text)