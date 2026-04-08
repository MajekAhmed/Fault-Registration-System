// ================================================
// Script.js - ملف JavaScript لتطبيق Fault Registration System
// مطار أسوان الدولي - نظام تسجيل الأعطال
// Developer: Ahmed Ragab | Version: 2.0
// ================================================


// ================================================
// 1. تشغيل الكود بعد تحميل الصفحة كاملاً
// ================================================
document.addEventListener('DOMContentLoaded', function () {

    // تمييز زر التنقل النشط حسب الصفحة الحالية
    highlightActiveNav();

    // إضافة تأثير ظهور تدريجي للبطاقات
    addFadeInEffect();

    console.log('✅ Fault Registration System Script.js تم تحميله بنجاح');
});


// ================================================
// 2. تمييز زر التنقل النشط
// ================================================
function highlightActiveNav() {
    // الحصول على المسار الحالي للصفحة
    const currentPath = window.location.pathname;

    // جلب كل أزرار التنقل
    const navButtons = document.querySelectorAll('.btn-nav');

    navButtons.forEach(btn => {
        // مقارنة رابط الزر بالمسار الحالي
        if (btn.getAttribute('href') === currentPath) {
            btn.style.backgroundColor = 'rgba(255,255,255,0.25)';
            btn.style.color = 'white';
            btn.style.fontWeight = 'bold';
        }
    });
}


// ================================================
// 3. تأثير الظهور التدريجي للبطاقات
// ================================================
function addFadeInEffect() {
    // إضافة كلاس fade-in لكل البطاقات في الصفحة
    const cards = document.querySelectorAll('.card');
    cards.forEach((card, index) => {
        card.style.animationDelay = `${index * 0.1}s`;  // تأخير متدرج لكل بطاقة
        card.classList.add('fade-in');
    });
}


// ================================================
// 4. جلب الأجهزة الرئيسية عند اختيار المشروع
//    (تُستخدم في صفحة إضافة عطل)
// ================================================
function loadMainDevices(projectId) {
    // إذا لم يُختر مشروع، أفرغ القوائم
    if (!projectId) {
        resetSelect('main_device_id', '-- اختر الجهاز الرئيسي --');
        resetSelect('sub_device_id', '-- لا يوجد جهاز ثانوي --');
        clearDeviceInfo();
        return;
    }

    // إظهار مؤشر التحميل
    setSelectLoading('main_device_id', 'جاري التحميل...');

    // طلب الأجهزة من الـ API
    fetch(`/api/main_devices/${projectId}`)
        .then(response => response.json())
        .then(devices => {
            const select = document.getElementById('main_device_id');
            select.innerHTML = '<option value="">-- اختر الجهاز الرئيسي --</option>';

            if (devices.length === 0) {
                // لا توجد أجهزة لهذا المشروع
                select.innerHTML += '<option disabled>لا توجد أجهزة مسجلة لهذا المشروع</option>';
            } else {
                // إضافة الأجهزة للقائمة مع تخزين Location و Type كـ data attributes
                devices.forEach(device => {
                    const option = document.createElement('option');
                    option.value = device.MainDeviceID;
                    option.textContent = `${device.DeviceName} - ${device.Location || 'غير محدد'}`;
                    option.dataset.location = device.Location  || '';
                    option.dataset.type     = device.DeviceType || '';
                    select.appendChild(option);
                });
            }

            // إعادة تعيين الأجهزة الثانوية
            resetSelect('sub_device_id', '-- لا يوجد جهاز ثانوي --');
            clearDeviceInfo();
        })
        .catch(error => {
            // في حالة خطأ في الاتصال
            console.error('خطأ في تحميل الأجهزة:', error);
            resetSelect('main_device_id', '-- خطأ في التحميل --');
        });
}


// ================================================
// 5. جلب الأجهزة الثانوية عند اختيار الجهاز الرئيسي
// ================================================
function loadSubDevices(mainDeviceId) {
    if (!mainDeviceId) {
        resetSelect('sub_device_id', '-- لا يوجد جهاز ثانوي --');
        return;
    }

    setSelectLoading('sub_device_id', 'جاري التحميل...');

    fetch(`/api/sub_devices/${mainDeviceId}`)
        .then(response => response.json())
        .then(devices => {
            const select = document.getElementById('sub_device_id');
            select.innerHTML = '<option value="">-- لا يوجد جهاز ثانوي --</option>';

            devices.forEach(device => {
                const option = document.createElement('option');
                option.value = device.SubDeviceID;
                option.textContent = `${device.SubDeviceName} (${device.SubDeviceType || 'غير محدد'})`;
                select.appendChild(option);
            });
        })
        .catch(error => {
            console.error('خطأ في تحميل الأجهزة الثانوية:', error);
            resetSelect('sub_device_id', '-- خطأ في التحميل --');
        });
}


// ================================================
// 6. عرض معلومات الجهاز تلقائياً (Location و Type)
// ================================================
function loadDeviceInfo(selectElement) {
    const selectedOption = selectElement.options[selectElement.selectedIndex];

    const locationField = document.getElementById('location_display');
    const typeField     = document.getElementById('type_display');

    if (locationField) locationField.value = selectedOption.dataset.location || '';
    if (typeField)     typeField.value     = selectedOption.dataset.type     || '';
}


// ================================================
// 7. دوال مساعدة للقوائم المنسدلة
// ================================================

// إعادة تعيين قائمة منسدلة
function resetSelect(selectId, defaultText) {
    const select = document.getElementById(selectId);
    if (select) {
        select.innerHTML = `<option value="">${defaultText}</option>`;
    }
}

// إظهار مؤشر تحميل في القائمة
function setSelectLoading(selectId, loadingText) {
    const select = document.getElementById(selectId);
    if (select) {
        select.innerHTML = `<option value="">${loadingText}</option>`;
    }
}

// مسح حقول معلومات الجهاز
function clearDeviceInfo() {
    const locationField = document.getElementById('location_display');
    const typeField     = document.getElementById('type_display');
    if (locationField) locationField.value = '';
    if (typeField)     typeField.value     = '';
}


// ================================================
// 8. تأكيد قبل الإجراءات الحساسة
// ================================================
function confirmAction(message) {
    // يرجع true إذا وافق المستخدم، false إذا ألغى
    return confirm(message || 'هل أنت متأكد من هذا الإجراء؟');
}


// ================================================
// 9. تحديد تاريخ اليوم تلقائياً في حقول التاريخ
// ================================================
function setTodayDate(fieldId) {
    const field = document.getElementById(fieldId);
    if (field) {
        // تنسيق التاريخ بصيغة YYYY-MM-DD (المطلوبة لـ input type="date")
        const today = new Date().toISOString().split('T')[0];
        field.value = today;
    }
}


// ================================================
// 10. البحث الفوري في الجداول (بدون زر)
// ================================================
function liveSearch(inputId, tableId) {
    const input = document.getElementById(inputId);
    if (!input) return;

    input.addEventListener('keyup', function () {
        const searchText = this.value.toLowerCase();
        const table      = document.getElementById(tableId);
        if (!table) return;

        const rows = table.querySelectorAll('tbody tr');

        rows.forEach(row => {
            // البحث في كل خلايا الصف
            const rowText = row.textContent.toLowerCase();
            row.style.display = rowText.includes(searchText) ? '' : 'none';
        });
    });
}
// ================================================
// فلترة الأجهزة الرئيسية حسب المشروع
// في نموذج إضافة جهاز ثانوي
// ================================================
function filterMainDevices(projectId) {
    const select  = document.getElementById('sub_main_device_id');
    if (!select) return;

    const options = select.querySelectorAll('option');

    options.forEach(opt => {
        if (!opt.value) return;  // تجاهل الخيار الافتراضي الفاضي
        // إظهار الخيار فقط إذا كان تابعاً للمشروع المختار
        opt.style.display = (!projectId || opt.dataset.project === projectId)
            ? '' : 'none';
    });

    // إعادة تعيين الاختيار
    select.value = '';
}


// ================================================
// بحث سريع في جدول الأجهزة الثانوية
// ================================================
function filterSubDevicesTable(searchText) {
    const table = document.getElementById('subDevicesTable');
    if (!table) return;

    const rows = table.querySelectorAll('tbody tr');
    const text = searchText.toLowerCase();

    rows.forEach(row => {
        row.style.display = row.textContent.toLowerCase().includes(text)
            ? '' : 'none';
    });
}
// ================================================
// تصدير التقرير كـ PDF
// ================================================
function exportPDF() {
    // نسخ بيانات الفلتر الحالية وإرسالها لـ Route الـ PDF
    const form = document.getElementById('reportForm');
    if (!form) return;

    // إنشاء فورم مؤقت بنفس البيانات لكن بـ action مختلف
    const tempForm = document.createElement('form');
    tempForm.method = 'POST';
    tempForm.action = '/export_pdf';

    // نسخ كل حقول الفورم الأصلي
    const formData = new FormData(form);
    formData.forEach((value, key) => {
        const input = document.createElement('input');
        input.type  = 'hidden';
        input.name  = key;
        input.value = value;
        tempForm.appendChild(input);
    });

    // إرسال الفورم المؤقت
    document.body.appendChild(tempForm);
    tempForm.submit();
    document.body.removeChild(tempForm);
}