from ..extensions import db
from datetime import datetime

def get_current_time():
    """يرجع الوقت الحالي بصيغة 12 ساعة مع AM/PM"""
    return datetime.now().strftime("%I:%M %p")

def generate_problem_id():
    """
    يولّد رقم عطل فريد بصيغة: سنة + تسلسل
    مثال: 2025001, 2025002, 2026001
    """
    year = datetime.now().year           # السنة الحالية
    prefix = year * 1000                 # 2025 × 1000 = 2025000

    # أكبر رقم موجود في نفس السنة
    from ..models import Problem
    max_id = db.session.query(db.func.max(Problem.ProblemID)).filter(
        Problem.ProblemID >= prefix,
        Problem.ProblemID < prefix + 1000
    ).scalar()

    if max_id is None:
        return prefix + 1   # أول عطل في هذه السنة → 2025001
    else:
        return max_id + 1   # التالي بعد آخر رقم

def init_db():
    """ينشئ الجداول الأساسية إذا لم تكن موجودة"""
    db.create_all()

def add_missing_columns():
    """إضافة أعمدة مفقودة في الجداول إذا لم تكن موجودة"""
    # في SQLAlchemy، الأعمدة تُعرف في الـ models، و db.create_all() ينشئها
    # هذه الدالة للتوافق مع الكود القديم
    pass