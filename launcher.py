# ================================================
# launcher.py - مشغّل تطبيق Fault Registration System (نسخة مصححة)
# ================================================

import sys
import os
import time
import threading
import webbrowser

# ---- تحديد المسارات ----
if getattr(sys, 'frozen', False):
    # شغّال كـ exe
    BASE_DIR = os.path.dirname(sys.executable)
    INTERNAL = sys._MEIPASS
else:
    # شغّال كـ Python عادي
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    INTERNAL = BASE_DIR

# ---- إضافة المسار لـ sys.path عشان يلاقي flask و app.py ----
if INTERNAL not in sys.path:
    sys.path.insert(0, INTERNAL)
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# ---- تعيين مسار قاعدة البيانات ----
os.environ['FRS_BASE_DIR'] = BASE_DIR

def open_browser():
    """ينتظر 3 ثواني ثم يفتح المتصفح"""
    time.sleep(3)
    webbrowser.open('http://127.0.0.1:5000')

try:
    print("=" * 50)
    print("  Fault Registration System v2.1")
    print("  General Fault Management System")
    print("  Developed by: Ahmed Ragab")
    print("=" * 50)
    print(f"📁 App Dir : {BASE_DIR}")
    print(f"🗄️  DB Path : {os.path.join(BASE_DIR, 'fault_registration.db')}")
    print(f"✅ DB Found: {os.path.exists(os.path.join(BASE_DIR, 'fault_registration.db'))}")
    print("=" * 50)

    # استيراد app بعد تحديد المسارات
    from app import create_app

    app = create_app()

    # فتح المتصفح في background
    t = threading.Thread(target=open_browser)
    t.daemon = True
    t.start()

    print("🚀 Server running on http://127.0.0.1:5000")
    print("⛔ Press Ctrl+C to stop")
    print("=" * 50)

    app.run(
        host='127.0.0.1',
        port=5000,
        debug=False,
        use_reloader=False
    )

except Exception as e:
    print(f"\n❌ Error: {e}")
    import traceback
    traceback.print_exc()
    print("\nPress Enter to close...")
    input()