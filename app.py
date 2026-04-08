# ================================================
# app.py - الملف الرئيسي لتطبيق Fault Registration System
# نظام تسجيل الأعطال العام
# Developer: Ahmed Ragab | Version: 2.1
# ================================================

from flask import Flask, render_template, request, redirect, url_for, jsonify
import sqlite3      # للتعامل مع قاعدة البيانات
import os           # للتعامل مع مسارات الملفات
from datetime import datetime  # للتاريخ والوقت التلقائي
from io import BytesIO
from flask import make_response
from io import BytesIO
from flask import make_response

# ------------------------------------------------
# إعداد التطبيق
# ------------------------------------------------
app = Flask(__name__)  # إنشاء تطبيق Flask

# المسار بيتغير لما التطبيق يشتغل كـ exe
if os.environ.get('FRS_BASE_DIR'):
    BASE_DIR = os.environ.get('FRS_BASE_DIR')
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(BASE_DIR, 'fault_registration.db')


# ================================================
# دالة مساعدة: الاتصال بقاعدة البيانات
# ================================================
def get_db():
    """تفتح اتصال بقاعدة البيانات وترجعه"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row   # النتائج كـ dict بدل tuple (أسهل في الاستخدام)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ================================================
# دالة مساعدة: إنشاء قاعدة البيانات إذا لم تكن موجودة
# ================================================
def init_db():
    """ينشئ الجداول الأساسية إذا لم تكن موجودة"""
    conn = get_db()
    cursor = conn.cursor()

    # جدول المشاريع
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            ProjectID INTEGER PRIMARY KEY AUTOINCREMENT,
            ProjectName TEXT NOT NULL,
            IsActive INTEGER DEFAULT 1
        )
    ''')

    # جدول الأجهزة الرئيسية
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS MainDevices (
            MainDeviceID INTEGER PRIMARY KEY AUTOINCREMENT,
            DeviceName TEXT NOT NULL,
            Location TEXT,
            DeviceType TEXT,
            ProjectID INTEGER,
            IsActive INTEGER DEFAULT 1,
            FOREIGN KEY (ProjectID) REFERENCES projects(ProjectID)
        )
    ''')

    # جدول الأجهزة الثانوية
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS SubDevices (
            SubDeviceID INTEGER PRIMARY KEY AUTOINCREMENT,
            SubDeviceName TEXT NOT NULL,
            SubDeviceType TEXT,
            MainDeviceID INTEGER,
            IsActive INTEGER DEFAULT 1,
            FOREIGN KEY (MainDeviceID) REFERENCES MainDevices(MainDeviceID)
        )
    ''')

    # جدول الموظفين
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS Employees (
            EmployeeID INTEGER PRIMARY KEY AUTOINCREMENT,
            EmployeeCode TEXT,
            FullName TEXT NOT NULL,
            IsActive INTEGER DEFAULT 1
        )
    ''')

    # جدول الأعطال
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS problems (
            ProblemID INTEGER PRIMARY KEY,
            ProjectID INTEGER,
            MainDeviceID INTEGER,
            SubDeviceID INTEGER,
            ProblemDescription TEXT,
            ReportedDate TEXT,
            ReportedTime TEXT,
            Status TEXT DEFAULT 'مفتوح',
            AssignedTo INTEGER,
            Location TEXT,
            DeviceType TEXT,
            ClosedDate TEXT,
            ClosedTime TEXT,
            Solution TEXT,
            MTTR REAL,
            FOREIGN KEY (ProjectID) REFERENCES projects(ProjectID),
            FOREIGN KEY (MainDeviceID) REFERENCES MainDevices(MainDeviceID),
            FOREIGN KEY (SubDeviceID) REFERENCES SubDevices(SubDeviceID),
            FOREIGN KEY (AssignedTo) REFERENCES Employees(EmployeeID)
        )
    ''')

    # جدول سجل الأحداث للأجهزة
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS DeviceTimeline (
            TimelineID INTEGER PRIMARY KEY AUTOINCREMENT,
            DeviceID INTEGER,
            EventDate TEXT,
            EventTime TEXT,
            EventType TEXT,
            Description TEXT,
            FOREIGN KEY (DeviceID) REFERENCES MainDevices(MainDeviceID)
        )
    ''')

    conn.commit()
    conn.close()


# إنشاء قاعدة البيانات إذا لم تكن موجودة
init_db()


# ================================================
# دالة مساعدة: توليد ProblemID يبدأ من 2025001
# ================================================
def generate_problem_id(conn):
    """
    يولّد رقم عطل فريد بصيغة: سنة + تسلسل
    مثال: 2025001, 2025002, 2026001
    """
    year = datetime.now().year           # السنة الحالية
    prefix = year * 1000                 # 2025 × 1000 = 2025000

    # أكبر رقم موجود في نفس السنة
    cursor = conn.execute(
        "SELECT MAX(ProblemID) FROM problems WHERE ProblemID >= ? AND ProblemID < ?",
        (prefix, prefix + 1000)
    )
    max_id = cursor.fetchone()[0]

    if max_id is None:
        return prefix + 1   # أول عطل في هذه السنة → 2025001
    else:
        return max_id + 1   # التالي بعد آخر رقم


# ================================================
# الوقت الحالي بصيغة HH:MM AM/PM
# ================================================
def get_current_time():
    """يرجع الوقت الحالي بصيغة 12 ساعة مع AM/PM"""
    return datetime.now().strftime("%I:%M %p")


# ================================================
# ROUTE 1: الصفحة الرئيسية
# ================================================
@app.route('/')
def index():
    """الصفحة الرئيسية - تعرض آخر 5 أعطال"""
    conn = get_db()

    # جلب آخر 5 أعطال مع أسماء المشروع والجهاز والموظف
    problems = conn.execute('''
        SELECT
            p.ProblemID,
            p.MainDeviceID,
            pr.ProjectName,
            md.DeviceName,
            p.ProblemDescription,
            p.ReportedDate,
            p.ReportedTime,
            p.Status,
            e.FullName AS AssignedToName
        FROM problems p
        LEFT JOIN projects    pr ON p.ProjectID    = pr.ProjectID
        LEFT JOIN MainDevices md ON p.MainDeviceID = md.MainDeviceID
        LEFT JOIN Employees   e  ON p.AssignedTo   = e.EmployeeID
        ORDER BY p.ProblemID DESC
        LIMIT 5
    ''').fetchall()

    conn.close()
    return render_template('index.html', problems=problems)


# ================================================
# ROUTE 2: إضافة عطل جديد (GET = عرض النموذج)
# ================================================
@app.route('/add_problem', methods=['GET'])
def add_problem():
    """عرض صفحة إضافة عطل جديد"""
    conn = get_db()

    # جلب المشاريع النشطة فقط للقائمة المنسدلة
    projects = conn.execute(
        "SELECT ProjectID, ProjectName FROM projects WHERE IsActive = 1"
    ).fetchall()

    # جلب الموظفين النشطين للقائمة المنسدلة
    employees = conn.execute(
        "SELECT EmployeeID, EmployeeCode, FullName FROM Employees WHERE IsActive = 1"
    ).fetchall()

    conn.close()
    return render_template('add_problem.html', projects=projects, employees=employees)


# ================================================
# ROUTE 3: حفظ العطل الجديد (POST = استقبال البيانات)
# ================================================
@app.route('/add_problem', methods=['POST'])
def save_problem():
    """استقبال بيانات العطل الجديد وحفظها في قاعدة البيانات"""
    conn = get_db()

    # قراءة البيانات من النموذج
    project_id    = request.form.get('project_id')
    main_device_id = request.form.get('main_device_id')
    sub_device_id  = request.form.get('sub_device_id') or None  # اختياري
    description    = request.form.get('problem_description')
    status         = request.form.get('status', 'مفتوح')
    assigned_to    = request.form.get('assigned_to') or None

    # جلب Location و Type تلقائياً من الجهاز المختار
    device = conn.execute(
        "SELECT Location, DeviceType FROM MainDevices WHERE MainDeviceID = ?",
        (main_device_id,)
    ).fetchone()

    location    = device['Location']  if device else ''
    device_type = device['DeviceType'] if device else ''

    # التاريخ والوقت التلقائيان
    reported_date = datetime.now().strftime("%Y-%m-%d")
    reported_time = get_current_time()

    # توليد رقم العطل
    problem_id = generate_problem_id(conn)

    # حفظ العطل في قاعدة البيانات
    conn.execute('''
        INSERT INTO problems (
            ProblemID, ProjectID, MainDeviceID, SubDeviceID,
            Location, Type, ProblemDescription,
            ReportedDate, ReportedTime, Status, AssignedTo, UpdateNo
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0)
    ''', (
        problem_id, project_id, main_device_id, sub_device_id,
        location, device_type, description,
        reported_date, reported_time, status, assigned_to
    ))

    # إضافة حدث تلقائي في DeviceTimeline
    conn.execute('''
        INSERT INTO DeviceTimeline (
            DeviceID, DeviceType, EventType, EventDate, EventTime,
            Description, PerformedBy, RelatedProblemID
        ) VALUES (?, 'Main', 'خروج من الخدمة', ?, ?, ?, ?, ?)
    ''', (
        main_device_id, reported_date, reported_time,
        f"تسجيل عطل جديد: {description[:50]}",
        assigned_to, problem_id
    ))

    conn.commit()
    conn.close()

    # بعد الحفظ، ارجع للصفحة الرئيسية
    return redirect(url_for('index'))


# ================================================
# ROUTE 4: عرض الأعطال والبحث
# ================================================
@app.route('/view_problems', methods=['GET', 'POST'])
def view_problems():
    """صفحة البحث وعرض الأعطال"""
    conn   = get_db()
    problems = []
    search   = ''
    from_date = ''
    to_date   = ''

    if request.method == 'POST':
        # قراءة معايير البحث
        search    = request.form.get('search', '').strip()
        from_date = request.form.get('from_date', '')
        to_date   = request.form.get('to_date', '')

        # بناء جملة SQL ديناميكياً حسب المعايير المدخلة
        query = '''
            SELECT
                p.ProblemID,
                pr.ProjectName,
                p.MainDeviceID,
                md.DeviceName,
                p.SubDeviceID,
                sd.SubDeviceName,
                p.Location,
                p.Type,
                p.ProblemDescription,
                p.ReportedDate,
                p.ReportedTime,
                p.Status,
                p.Solution,
                e.FullName AS AssignedToName,
                p.UpdateNo,
                p.RepairDurationHours
            FROM problems p
            LEFT JOIN projects    pr ON p.ProjectID    = pr.ProjectID
            LEFT JOIN MainDevices md ON p.MainDeviceID = md.MainDeviceID
            LEFT JOIN SubDevices  sd ON p.SubDeviceID  = sd.SubDeviceID
            LEFT JOIN Employees   e  ON p.AssignedTo   = e.EmployeeID
            WHERE 1=1
        '''
        params = []

        # فلتر البحث النصي
        if search:
            query += ''' AND (
                CAST(p.ProblemID AS TEXT) LIKE ? OR
                md.DeviceName             LIKE ? OR
                pr.ProjectName            LIKE ? OR
                p.ProblemDescription      LIKE ?
            )'''
            like = f'%{search}%'
            params.extend([like, like, like, like])

        # فلتر التاريخ
        if from_date:
            query += " AND p.ReportedDate >= ?"
            params.append(from_date)
        if to_date:
            query += " AND p.ReportedDate <= ?"
            params.append(to_date)

        query += " ORDER BY p.ProblemID DESC"
        problems = conn.execute(query, params).fetchall()

    conn.close()
    return render_template('view_problems.html',
                           problems=problems,
                           search=search,
                           from_date=from_date,
                           to_date=to_date)


# ================================================
# ROUTE 5: تعديل عطل (GET = عرض البيانات)
# ================================================
@app.route('/edit_problem/<int:problem_id>', methods=['GET'])
def edit_problem(problem_id):
    """عرض صفحة تعديل عطل محدد"""
    conn = get_db()

    # جلب بيانات العطل كاملة
    problem = conn.execute('''
        SELECT
            p.*,
            pr.ProjectName,
            md.DeviceName,
            sd.SubDeviceName,
            e.FullName AS AssignedToName
        FROM problems p
        LEFT JOIN projects    pr ON p.ProjectID    = pr.ProjectID
        LEFT JOIN MainDevices md ON p.MainDeviceID = md.MainDeviceID
        LEFT JOIN SubDevices  sd ON p.SubDeviceID  = sd.SubDeviceID
        LEFT JOIN Employees   e  ON p.AssignedTo   = e.EmployeeID
        WHERE p.ProblemID = ?
    ''', (problem_id,)).fetchone()

    # جلب الموظفين للقائمة المنسدلة
    employees = conn.execute(
        "SELECT EmployeeID, EmployeeCode, FullName FROM Employees WHERE IsActive = 1"
    ).fetchall()

    conn.close()
    return render_template('edit_problem.html', problem=problem, employees=employees)


# ================================================
# ROUTE 6: حفظ تعديل العطل (POST)
# ================================================
@app.route('/edit_problem/<int:problem_id>', methods=['POST'])
def update_problem(problem_id):
    """حفظ التعديلات على العطل"""
    conn = get_db()

    # القيم الجديدة من النموذج
    description = request.form.get('problem_description')
    solution    = request.form.get('solution')
    comment     = request.form.get('comment')
    new_status  = request.form.get('status')
    assigned_to = request.form.get('assigned_to') or None

    # الحالة القديمة (لمعرفة إذا تغيرت)
    old = conn.execute(
        "SELECT Status, ResolutionStartDate FROM problems WHERE ProblemID = ?",
        (problem_id,)
    ).fetchone()

    now_date = datetime.now().strftime("%Y-%m-%d")
    now_time = get_current_time()

    # منطق تسجيل وقت الإصلاح تلقائياً
    resolution_start_date = old['ResolutionStartDate']
    resolution_start_time = None
    resolution_end_date   = None
    resolution_end_time   = None
    repair_hours          = None

    # إذا تغيرت الحالة إلى "قيد الإصلاح" → سجّل وقت البدء (اختياري)
    if new_status == 'قيد الإصلاح' and old['Status'] != 'قيد الإصلاح':
        resolution_start_date = now_date
        resolution_start_time = now_time

    # إذا تغيرت الحالة إلى "مغلق" → سجّل وقت الانتهاء واحسب المدة من وقت فتح العطل
    if new_status == 'مغلق' and old['Status'] != 'مغلق':
        resolution_end_date = now_date
        resolution_end_time = now_time

        # حساب مدة الإصلاح بالساعات من وقت فتح العطل
        reported = conn.execute(
            "SELECT ReportedDate, ReportedTime FROM problems WHERE ProblemID = ?",
            (problem_id,)
        ).fetchone()
        try:
            fmt = "%Y-%m-%d %I:%M %p"
            start_dt = datetime.strptime(
                f"{reported['ReportedDate']} {reported['ReportedTime']}", fmt
            )
            end_dt   = datetime.strptime(f"{now_date} {now_time}", fmt)
            repair_hours = round((end_dt - start_dt).total_seconds() / 3600, 2)
        except:
            repair_hours = None  # إذا حصل خطأ في الحساب

    # تحديث بيانات العطل
    conn.execute('''
        UPDATE problems SET
            ProblemDescription   = ?,
            Solution             = ?,
            Comment              = ?,
            Status               = ?,
            AssignedTo           = ?,
            UpdateDate           = ?,
            UpdateTime           = ?,
            UpdateNo             = UpdateNo + 1,
            ResolutionStartDate  = COALESCE(ResolutionStartDate, ?),
            ResolutionStartTime  = COALESCE(ResolutionStartTime, ?),
            ResolutionEndDate    = COALESCE(?, ResolutionEndDate),
            ResolutionEndTime    = COALESCE(?, ResolutionEndTime),
            RepairDurationHours  = COALESCE(?, RepairDurationHours)
        WHERE ProblemID = ?
    ''', (
        description, solution, comment, new_status, assigned_to,
        now_date, now_time,
        resolution_start_date, resolution_start_time,
        resolution_end_date, resolution_end_time,
        repair_hours,
        problem_id
    ))

    conn.commit()
    conn.close()

    return redirect(url_for('view_problems'))


# ================================================
# ROUTE 7: APIs ديناميكية للقوائم المترابطة
# ================================================

# جلب الأجهزة الرئيسية حسب المشروع
@app.route('/api/main_devices/<int:project_id>')
def api_main_devices(project_id):
    """يرجع الأجهزة الرئيسية التابعة لمشروع معين (JSON)"""
    conn    = get_db()
    devices = conn.execute(
        "SELECT MainDeviceID, DeviceName, Location, DeviceType FROM MainDevices WHERE ProjectID = ? AND IsActive = 1",
        (project_id,)
    ).fetchall()
    conn.close()
    # تحويل النتائج إلى قائمة من القواميس
    return jsonify([dict(d) for d in devices])


# جلب الأجهزة الثانوية حسب الجهاز الرئيسي
@app.route('/api/sub_devices/<int:main_device_id>')
def api_sub_devices(main_device_id):
    """يرجع الأجهزة الثانوية التابعة لجهاز رئيسي معين (JSON)"""
    conn    = get_db()
    devices = conn.execute(
        "SELECT SubDeviceID, SubDeviceName, SubDeviceType FROM SubDevices WHERE MainDeviceID = ? AND IsActive = 1",
        (main_device_id,)
    ).fetchall()
    conn.close()
    return jsonify([dict(d) for d in devices])


# ================================================
# ROUTE 8: إدارة قاعدة البيانات
# ================================================
@app.route('/edit_database')
def edit_database():
    """صفحة إدارة البيانات الأساسية"""
    conn = get_db()

    projects  = conn.execute("SELECT * FROM projects ORDER BY ProjectID").fetchall()

    devices = conn.execute('''
        SELECT md.*, pr.ProjectName
        FROM MainDevices md
        LEFT JOIN projects pr ON md.ProjectID = pr.ProjectID
        ORDER BY md.ProjectID, md.DeviceName
    ''').fetchall()

    employees = conn.execute("SELECT * FROM Employees ORDER BY FullName").fetchall()

    # جلب الأجهزة الثانوية مع اسم الجهاز الرئيسي والمشروع
    sub_devices = conn.execute('''
        SELECT
            sd.*,
            md.DeviceName  AS MainDeviceName,
            pr.ProjectName AS ProjectName
        FROM SubDevices sd
        LEFT JOIN MainDevices md ON sd.MainDeviceID = md.MainDeviceID
        LEFT JOIN projects    pr ON sd.ProjectID    = pr.ProjectID
        WHERE sd.IsActive = 1
        ORDER BY pr.ProjectName, md.DeviceName, sd.SubDeviceName
    ''').fetchall()

    conn.close()
    return render_template('edit_database.html',
                           projects=projects,
                           devices=devices,
                           employees=employees,
                           sub_devices=sub_devices)


# ================================================
# ROUTE 9: إضافة موظف جديد
# ================================================
@app.route('/add_employee', methods=['POST'])
def add_employee():
    conn = get_db()
    conn.execute('''
        INSERT INTO Employees (EmployeeCode, FullName, JobTitle, Department, Phone, Email, HireDate, IsActive)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1)
    ''', (
        request.form.get('employee_code'),
        request.form.get('full_name'),
        request.form.get('job_title'),
        request.form.get('department'),
        request.form.get('phone'),
        request.form.get('email'),
        request.form.get('hire_date'),
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('edit_database'))


# ================================================
# ROUTE 10: إضافة جهاز رئيسي جديد
# ================================================
@app.route('/add_main_device', methods=['POST'])
def add_main_device():
    conn = get_db()
    conn.execute('''
        INSERT INTO MainDevices (ProjectID, DeviceName, DeviceType, Location,
                                  IPAddress, SerialNumber, Manufacturer, Model,
                                  OSVersion, InstallDate, Status, IsActive)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'نشط', 1)
    ''', (
        request.form.get('project_id'),
        request.form.get('device_name'),
        request.form.get('device_type'),
        request.form.get('location'),
        request.form.get('ip_address'),
        request.form.get('serial_number'),
        request.form.get('manufacturer'),
        request.form.get('model'),
        request.form.get('os_version'),
        request.form.get('install_date'),
    ))
    conn.commit()
    conn.close()
    return redirect(url_for('edit_database'))
# ================================================
# ROUTE: صفحة التقارير
# ================================================
@app.route('/reports', methods=['GET', 'POST'])
def reports():
    """صفحة التقارير - تعرض إحصائيات وتقارير الأعطال"""
    conn = get_db()

    # جلب المشاريع والموظفين لقوائم الفلترة
    projects  = conn.execute("SELECT * FROM projects  WHERE IsActive = 1").fetchall()
    employees = conn.execute("SELECT * FROM Employees WHERE IsActive = 1").fetchall()

    # ---- القيم الافتراضية ----
    from_date   = request.form.get('from_date', '')
    to_date     = request.form.get('to_date',   '')
    project_id  = request.form.get('project_id', '')
    report_type = request.form.get('report_type', 'summary')

    # ---- بناء فلتر التاريخ والمشروع ----
    where  = "WHERE 1=1"
    params = []

    if from_date:
        where += " AND p.ReportedDate >= ?"
        params.append(from_date)
    if to_date:
        where += " AND p.ReportedDate <= ?"
        params.append(to_date)
    if project_id:
        where += " AND p.ProjectID = ?"
        params.append(project_id)

    # ================================================
    # KPI 1: إجمالي الأعطال
    # ================================================
    total = conn.execute(
        f"SELECT COUNT(*) FROM problems p {where}", params
    ).fetchone()[0]

    # ================================================
    # KPI 2: الأعطال حسب الحالة
    # ================================================
    by_status = conn.execute(f'''
        SELECT Status, COUNT(*) as count
        FROM problems p {where}
        GROUP BY Status
    ''', params).fetchall()

    # تحويل النتيجة لـ dict سهل الاستخدام في HTML
    status_dict = {row['Status']: row['count'] for row in by_status}
    open_count     = status_dict.get('مفتوح', 0)
    progress_count = status_dict.get('قيد الإصلاح', 0)
    closed_count   = status_dict.get('مغلق', 0)

    # ================================================
    # KPI 3: متوسط وقت الإصلاح (MTTR)
    # ================================================
    mttr_row = conn.execute(f'''
        SELECT AVG(RepairDurationHours) as mttr
        FROM problems p {where}
        AND RepairDurationHours IS NOT NULL
    ''', params).fetchone()
    mttr = round(mttr_row['mttr'], 2) if mttr_row['mttr'] else 0

    # ================================================
    # KPI 4: الأعطال حسب المشروع
    # ================================================
    by_project = conn.execute(f'''
        SELECT pr.ProjectName, COUNT(*) as count,
               AVG(p.RepairDurationHours) as avg_repair
        FROM problems p
        LEFT JOIN projects pr ON p.ProjectID = pr.ProjectID
        {where}
        GROUP BY p.ProjectID
        ORDER BY count DESC
    ''', params).fetchall()

    # ================================================
    # KPI 5: أكثر الأجهزة تعطلاً
    # ================================================
    top_devices = conn.execute(f'''
        SELECT md.DeviceName, pr.ProjectName,
               COUNT(*) as fault_count,
               AVG(p.RepairDurationHours) as avg_repair
        FROM problems p
        LEFT JOIN MainDevices md ON p.MainDeviceID = md.MainDeviceID
        LEFT JOIN projects    pr ON p.ProjectID    = pr.ProjectID
        {where}
        GROUP BY p.MainDeviceID
        ORDER BY fault_count DESC
        LIMIT 10
    ''', params).fetchall()

    # ================================================
    # KPI 6: أداء الموظفين
    # ================================================
    by_employee = conn.execute(f'''
        SELECT e.FullName, e.EmployeeCode,
               COUNT(*) as total,
               SUM(CASE WHEN p.Status = 'مغلق' THEN 1 ELSE 0 END) as closed,
               AVG(p.RepairDurationHours) as avg_repair
        FROM problems p
        LEFT JOIN Employees e ON p.AssignedTo = e.EmployeeID
        {where}
        AND p.AssignedTo IS NOT NULL
        GROUP BY p.AssignedTo
        ORDER BY total DESC
    ''', params).fetchall()

    # ================================================
    # KPI 7: الأعطال المتكررة (نفس الجهاز أكثر من مرة)
    # ================================================
    recurring = conn.execute(f'''
        SELECT md.DeviceName, pr.ProjectName,
               COUNT(*) as fault_count,
               MAX(p.ReportedDate) as last_fault
        FROM problems p
        LEFT JOIN MainDevices md ON p.MainDeviceID = md.MainDeviceID
        LEFT JOIN projects    pr ON p.ProjectID    = pr.ProjectID
        {where}
        GROUP BY p.MainDeviceID
        HAVING fault_count > 1
        ORDER BY fault_count DESC
    ''', params).fetchall()

    # ================================================
    # تفاصيل كل الأعطال في الفترة
    # ================================================
    all_problems = conn.execute(f'''
        SELECT p.ProblemID, pr.ProjectName, md.DeviceName,
               p.SubDeviceID, sd.SubDeviceName,
               p.ProblemDescription, p.ReportedDate, p.ReportedTime,
               p.Status, p.Solution, e.FullName as AssignedToName,
               p.RepairDurationHours
        FROM problems p
        LEFT JOIN projects    pr ON p.ProjectID    = pr.ProjectID
        LEFT JOIN MainDevices md ON p.MainDeviceID = md.MainDeviceID
        LEFT JOIN SubDevices  sd ON p.SubDeviceID  = sd.SubDeviceID
        LEFT JOIN Employees   e  ON p.AssignedTo   = e.EmployeeID
        {where}
        ORDER BY p.ProblemID DESC
    ''', params).fetchall()

    conn.close()

    return render_template('reports.html',
        projects=projects, employees=employees,
        from_date=from_date, to_date=to_date,
        project_id=project_id, report_type=report_type,
        total=total,
        open_count=open_count, progress_count=progress_count, closed_count=closed_count,
        mttr=mttr,
        by_project=by_project, top_devices=top_devices,
        by_employee=by_employee, recurring=recurring,
        all_problems=all_problems
    )
# ================================================
# ROUTE: بطاقة الجهاز الثانوي والتايم لاين
# ================================================
@app.route('/sub_device_card/<int:sub_device_id>')
def sub_device_card(sub_device_id):
    """بطاقة الجهاز الثانوي - تعرض كل تاريخ الجهاز الثانوي والتايم لاين"""
    conn = get_db()

    # جلب بيانات الجهاز الثانوي
    sub_device = conn.execute('''
        SELECT sd.*, md.DeviceName AS MainDeviceName, pr.ProjectName
        FROM SubDevices sd
        LEFT JOIN MainDevices md ON sd.MainDeviceID = md.MainDeviceID
        LEFT JOIN projects    pr ON sd.ProjectID    = pr.ProjectID
        WHERE sd.SubDeviceID = ?
    ''', (sub_device_id,)).fetchone()

    if not sub_device:
        return "الجهاز الثانوي غير موجود", 404

    # ---- إحصائيات الجهاز الثانوي ----

    # إجمالي الأعطال المرتبطة بهذا الجهاز الثانوي
    total_faults = conn.execute(
        "SELECT COUNT(*) FROM problems WHERE SubDeviceID = ?",
        (sub_device_id,)
    ).fetchone()[0]

    # الأعطال المفتوحة
    open_faults = conn.execute(
        "SELECT COUNT(*) FROM problems WHERE SubDeviceID = ? AND Status = 'مفتوح'",
        (sub_device_id,)
    ).fetchone()[0]

    # متوسط وقت الإصلاح لهذا الجهاز الثانوي
    mttr_row = conn.execute('''
        SELECT AVG(RepairDurationHours)
        FROM problems
        WHERE SubDeviceID = ? AND RepairDurationHours IS NOT NULL
    ''', (sub_device_id,)).fetchone()
    mttr = round(mttr_row[0], 2) if mttr_row[0] else 0

    # آخر عطل مسجل
    last_fault = conn.execute('''
        SELECT p.*, e.FullName as AssignedToName
        FROM problems p
        LEFT JOIN Employees e ON p.AssignedTo = e.EmployeeID
        WHERE p.SubDeviceID = ?
        ORDER BY p.ProblemID DESC
        LIMIT 1
    ''', (sub_device_id,)).fetchone()

    # سجل كل الأعطال
    all_faults = conn.execute('''
        SELECT p.*, e.FullName as AssignedToName
        FROM problems p
        LEFT JOIN Employees e ON p.AssignedTo = e.EmployeeID
        WHERE p.SubDeviceID = ?
        ORDER BY p.ProblemID DESC
    ''', (sub_device_id,)).fetchall()

    # ---- التايم لاين (إذا كان هناك جدول منفصل للأجهزة الثانوية، لكن حالياً نستخدم DeviceTimeline للرئيسية فقط) ----
    # للأجهزة الثانوية، قد نحتاج إلى إضافة DeviceType = 'Sub'
    timeline = conn.execute('''
        SELECT dt.*, e.FullName as PerformedByName
        FROM DeviceTimeline dt
        LEFT JOIN Employees e ON dt.PerformedBy = e.EmployeeID
        WHERE dt.DeviceID = ? AND dt.DeviceType = 'Sub'
        ORDER BY dt.EventDate DESC, dt.EventTime DESC
    ''', (sub_device_id,)).fetchall()

    # جلب الموظفين لنموذج إضافة حدث
    employees = conn.execute(
        "SELECT EmployeeID, EmployeeCode, FullName FROM Employees WHERE IsActive = 1"
    ).fetchall()

    conn.close()

    return render_template('sub_device_card.html',
        sub_device=sub_device,
        total_faults=total_faults,
        open_faults=open_faults,
        mttr=mttr,
        last_fault=last_fault,
        all_faults=all_faults,
        timeline=timeline,
        employees=employees
    )


# ================================================
# ROUTE: بطاقة الجهاز والتايم لاين
# ================================================
@app.route('/device_card/<int:device_id>')
def device_card(device_id):
    """بطاقة الجهاز - تعرض كل تاريخ الجهاز والتايم لاين"""
    conn = get_db()

    # جلب بيانات الجهاز الرئيسي
    device = conn.execute('''
        SELECT md.*, pr.ProjectName
        FROM MainDevices md
        LEFT JOIN projects pr ON md.ProjectID = pr.ProjectID
        WHERE md.MainDeviceID = ?
    ''', (device_id,)).fetchone()

    if not device:
        return "الجهاز غير موجود", 404

    # جلب الأجهزة الثانوية التابعة له
    sub_devices = conn.execute('''
        SELECT * FROM SubDevices
        WHERE MainDeviceID = ? AND IsActive = 1
    ''', (device_id,)).fetchall()

    # ---- إحصائيات الجهاز ----

    # إجمالي الأعطال
    total_faults = conn.execute(
        "SELECT COUNT(*) FROM problems WHERE MainDeviceID = ?",
        (device_id,)
    ).fetchone()[0]

    # الأعطال المفتوحة
    open_faults = conn.execute(
        "SELECT COUNT(*) FROM problems WHERE MainDeviceID = ? AND Status = 'مفتوح'",
        (device_id,)
    ).fetchone()[0]

    # متوسط وقت الإصلاح لهذا الجهاز
    mttr_row = conn.execute('''
        SELECT AVG(RepairDurationHours)
        FROM problems
        WHERE MainDeviceID = ? AND RepairDurationHours IS NOT NULL
    ''', (device_id,)).fetchone()
    mttr = round(mttr_row[0], 2) if mttr_row[0] else 0

    # آخر عطل مسجل
    last_fault = conn.execute('''
        SELECT p.*, e.FullName as AssignedToName
        FROM problems p
        LEFT JOIN Employees e ON p.AssignedTo = e.EmployeeID
        WHERE p.MainDeviceID = ?
        ORDER BY p.ProblemID DESC
        LIMIT 1
    ''', (device_id,)).fetchone()

    # سجل كل الأعطال
    all_faults = conn.execute('''
        SELECT p.*, e.FullName as AssignedToName
        FROM problems p
        LEFT JOIN Employees e ON p.AssignedTo = e.EmployeeID
        WHERE p.MainDeviceID = ?
        ORDER BY p.ProblemID DESC
    ''', (device_id,)).fetchall()

    # ---- التايم لاين ----
    timeline = conn.execute('''
        SELECT dt.*, e.FullName as PerformedByName
        FROM DeviceTimeline dt
        LEFT JOIN Employees e ON dt.PerformedBy = e.EmployeeID
        WHERE dt.DeviceID = ? AND dt.DeviceType = 'Main'
        ORDER BY dt.EventDate DESC, dt.EventTime DESC
    ''', (device_id,)).fetchall()

    # جلب الموظفين لنموذج إضافة حدث
    employees = conn.execute(
        "SELECT EmployeeID, EmployeeCode, FullName FROM Employees WHERE IsActive = 1"
    ).fetchall()

    conn.close()

    return render_template('device_card.html',
        device=device,
        sub_devices=sub_devices,
        total_faults=total_faults,
        open_faults=open_faults,
        mttr=mttr,
        last_fault=last_fault,
        all_faults=all_faults,
        timeline=timeline,
        employees=employees
    )


# ================================================
# ROUTE: إضافة حدث للتايم لاين
# ================================================
@app.route('/add_timeline_event', methods=['POST'])
def add_timeline_event():
    """إضافة حدث جديد في تايم لاين الجهاز"""
    conn = get_db()

    device_id   = request.form.get('device_id')
    device_type = request.form.get('device_type', 'Main')
    event_type  = request.form.get('event_type')
    description = request.form.get('description')
    performed_by = request.form.get('performed_by') or None
    notes       = request.form.get('notes')

    now_date = datetime.now().strftime("%Y-%m-%d")
    now_time = get_current_time()

    conn.execute('''
        INSERT INTO DeviceTimeline
            (DeviceID, DeviceType, EventType, EventDate, EventTime, Description, PerformedBy, Notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (device_id, device_type, event_type, now_date, now_time, description, performed_by, notes))

    # إذا كان الحدث صيانة → حدّث LastMaintenDate في جدول MainDevices
    if event_type in ['صيانة دورية', 'تغيير جزء', 'تحديث برمجي']:
        conn.execute(
            "UPDATE MainDevices SET LastMaintenDate = ? WHERE MainDeviceID = ?",
            (now_date, device_id)
        )

    conn.commit()
    conn.close()

    return redirect(url_for('device_card', device_id=device_id))

# ================================================
# ROUTE: إضافة جهاز ثانوي جديد
# ================================================
@app.route('/add_sub_device', methods=['POST'])
def add_sub_device():
    """إضافة جهاز ثانوي جديد مرتبط بجهاز رئيسي"""
    conn = get_db()

    main_device_id = request.form.get('main_device_id')

    # جلب ProjectID تلقائياً من الجهاز الرئيسي
    device = conn.execute(
        "SELECT ProjectID FROM MainDevices WHERE MainDeviceID = ?",
        (main_device_id,)
    ).fetchone()

    project_id = device['ProjectID'] if device else None

    conn.execute('''
        INSERT INTO SubDevices (
            MainDeviceID, ProjectID, SubDeviceName, SubDeviceType,
            SerialNumber, AssetTag, Manufacturer, Model,
            ConnectedPort, InstallDate, Status, IsActive
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'نشط', 1)
    ''', (
        main_device_id,
        project_id,
        request.form.get('sub_device_name'),
        request.form.get('sub_device_type'),
        request.form.get('serial_number'),
        request.form.get('asset_tag'),
        request.form.get('manufacturer'),
        request.form.get('model'),
        request.form.get('connected_port'),
        request.form.get('install_date'),
    ))

    conn.commit()
    conn.close()
    return redirect(url_for('edit_database') + '#subdevices-tab')


# ================================================
# ROUTE: تعطيل جهاز ثانوي (حذف ناعم)
# ================================================
@app.route('/deactivate_sub_device/<int:sub_device_id>', methods=['POST'])
def deactivate_sub_device(sub_device_id):
    """تعطيل جهاز ثانوي بدل حذفه للحفاظ على السجلات"""
    conn = get_db()
    conn.execute(
        "UPDATE SubDevices SET IsActive = 0 WHERE SubDeviceID = ?",
        (sub_device_id,)
    )
    conn.commit()
    conn.close()
    return redirect(url_for('edit_database') + '#subdevices-tab')

# ================================================
# ROUTE: تصدير PDF بدون مكتبات خارجية
# ================================================
@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    """تصدير التقرير كـ HTML قابل للطباعة كـ PDF من المتصفح"""
    conn = get_db()

    from_date  = request.form.get('from_date', '')
    to_date    = request.form.get('to_date',   '')
    project_id = request.form.get('project_id', '')

    where  = "WHERE 1=1"
    params = []
    if from_date:
        where += " AND p.ReportedDate >= ?"
        params.append(from_date)
    if to_date:
        where += " AND p.ReportedDate <= ?"
        params.append(to_date)
    if project_id:
        where += " AND p.ProjectID = ?"
        params.append(project_id)

    problems = conn.execute(f'''
        SELECT
            p.ProblemID, pr.ProjectName, md.DeviceName,
            p.ProblemDescription, p.ReportedDate, p.ReportedTime,
            p.Status, e.FullName as AssignedToName,
            p.RepairDurationHours, p.Solution
        FROM problems p
        LEFT JOIN projects    pr ON p.ProjectID    = pr.ProjectID
        LEFT JOIN MainDevices md ON p.MainDeviceID = md.MainDeviceID
        LEFT JOIN Employees   e  ON p.AssignedTo   = e.EmployeeID
        {where}
        ORDER BY p.ProblemID DESC
    ''', params).fetchall()

    total          = len(problems)
    open_count     = sum(1 for p in problems if p['Status'] == 'مفتوح')
    progress_count = sum(1 for p in problems if p['Status'] == 'قيد الإصلاح')
    closed_count   = sum(1 for p in problems if p['Status'] == 'مغلق')
    repair_times   = [p['RepairDurationHours'] for p in problems if p['RepairDurationHours']]
    mttr           = round(sum(repair_times) / len(repair_times), 2) if repair_times else 0

    conn.close()

    now_str    = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    period_str = f"{from_date or 'All'} → {to_date or 'All'}"

    # ---- بناء HTML للطباعة ----
    rows_html = ''
    for p in problems:
        desc     = str(p['ProblemDescription'] or '')[:60]
        status   = str(p['Status'] or '')
        duration = f"{p['RepairDurationHours']} hrs" if p['RepairDurationHours'] else '-'

        if status == 'مفتوح':
            status_style = 'background:#e74c3c;color:white'
        elif status == 'قيد الإصلاح':
            status_style = 'background:#f39c12;color:white'
        else:
            status_style = 'background:#27ae60;color:white'

        rows_html += f'''
        <tr>
            <td style="text-align:center">{p['ProblemID']}</td>
            <td style="text-align:center">{p['ProjectName'] or '-'}</td>
            <td style="text-align:center">{p['DeviceName'] or '-'}</td>
            <td>{desc}</td>
            <td style="text-align:center">{p['ReportedDate'] or '-'}</td>
            <td style="text-align:center;{status_style};padding:3px 8px;border-radius:4px">{status}</td>
            <td style="text-align:center">{p['AssignedToName'] or '-'}</td>
            <td>{p['Solution'] or '-'}</td>
            <td style="text-align:center">{duration}</td>
        </tr>'''

    html = f'''<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
    <meta charset="UTF-8">
    <title>Fault Registration System Report - {now_str}</title>
    <style>
        * {{ margin:0; padding:0; box-sizing:border-box; }}
        body {{ font-family: Arial, sans-serif; font-size: 11px; color: #2c3e50; }}

        .header {{
            background: linear-gradient(135deg, #1a3a5c, #2e86c1);
            color: white;
            text-align: center;
            padding: 15px;
        }}
        .header h1 {{ font-size: 20px; margin-bottom: 4px; }}
        .header p  {{ font-size: 11px; opacity: 0.9; }}

        .info-bar {{
            background: #eef2f7;
            padding: 8px 15px;
            display: flex;
            justify-content: space-between;
            border-bottom: 2px solid #2e86c1;
            font-size: 10px;
        }}

        .kpi-row {{
            display: flex;
            gap: 10px;
            padding: 10px 15px;
            background: white;
        }}
        .kpi-box {{
            flex: 1;
            text-align: center;
            padding: 10px;
            border-radius: 8px;
            color: white;
        }}
        .kpi-box .num {{ font-size: 24px; font-weight: bold; }}
        .kpi-box .lbl {{ font-size: 10px; margin-top: 2px; }}
        .kpi-total    {{ background: #2e86c1; }}
        .kpi-open     {{ background: #e74c3c; }}
        .kpi-progress {{ background: #f39c12; }}
        .kpi-closed   {{ background: #27ae60; }}
        .kpi-mttr     {{ background: #9b59b6; }}

        .section-title {{
            background: #1a3a5c;
            color: white;
            padding: 6px 15px;
            font-size: 12px;
            font-weight: bold;
            margin: 0 0 0 0;
        }}

        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 9.5px;
        }}
        thead th {{
            background: #1a3a5c;
            color: white;
            padding: 6px 5px;
            text-align: center;
            border: 1px solid #dee2e6;
        }}
        tbody tr:nth-child(even) {{ background: #f8f9fa; }}
        tbody tr:nth-child(odd)  {{ background: white; }}
        tbody td {{
            padding: 5px;
            border: 1px solid #dee2e6;
            vertical-align: middle;
        }}

        .footer {{
            background: #1a3a5c;
            color: white;
            text-align: center;
            padding: 8px;
            font-size: 9px;
            margin-top: 10px;
        }}

        @media print {{
            body {{ -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
            @page {{ size: A4 portrait; margin: 10mm; }}
        }}
    </style>
</head>
<body>

    <!-- هيدر -->
    <div class="header">
        <h1>Fault Registration System</h1>
        <p>Aswan International Airport &nbsp;|&nbsp; v2.0 &nbsp;|&nbsp; Developed by: Ahmed Ragab</p>
    </div>

    <!-- معلومات التقرير -->
    <div class="info-bar">
        <span><strong>Report Date:</strong> {now_str}</span>
        <span><strong>Period:</strong> {period_str}</span>
        <span><strong>Total Records:</strong> {total}</span>
    </div>

    <!-- KPI Cards -->
    <div class="kpi-row">
        <div class="kpi-box kpi-total">
            <div class="num">{total}</div>
            <div class="lbl">Total Faults</div>
        </div>
        <div class="kpi-box kpi-open">
            <div class="num">{open_count}</div>
            <div class="lbl">Open</div>
        </div>
        <div class="kpi-box kpi-progress">
            <div class="num">{progress_count}</div>
            <div class="lbl">In Progress</div>
        </div>
        <div class="kpi-box kpi-closed">
            <div class="num">{closed_count}</div>
            <div class="lbl">Closed</div>
        </div>
        <div class="kpi-box kpi-mttr">
            <div class="num">{mttr}</div>
            <div class="lbl">MTTR (hrs)</div>
        </div>
    </div>

    <!-- جدول الأعطال -->
    <div class="section-title">Fault Details</div>
    <table>
        <thead>
            <tr>
                <th style="width:6%">ID</th>
                <th style="width:8%">Project</th>
                <th style="width:8%">Device</th>
                <th style="width:20%">Description</th>
                <th style="width:9%">Date</th>
                <th style="width:8%">Status</th>
                <th style="width:10%">Assigned To</th>
                <th style="width:15%">Solution</th>
                <th style="width:7%">Duration</th>
            </tr>
        </thead>
        <tbody>
            {rows_html}
        </tbody>
    </table>

    <!-- فوتر -->
    <div class="footer">
        Fault Registration System &nbsp;|&nbsp; v2.0 &nbsp;|&nbsp;
        Aswan International Airport &nbsp;|&nbsp; Generated: {now_str}
    </div>

    <!-- طباعة تلقائية عند فتح الصفحة -->
    <script>
        window.onload = function() {{
            window.print();
        }};
    </script>

</body>
</html>'''

    return html

# ================================================
# تشغيل التطبيق
# ================================================
if __name__ == '__main__':
    app.run(debug=True)   # debug=True يعرض الأخطاء بالتفصيل أثناء التطوير