---
name: mtm-watch-product-page
description: |
  صفحة منتج فاخرة لبراند MTM للساعات — تصميم Minimalist Light Luxury
  مستوحى من Verbier Wear (أبيض/أسود/هادئ). تضم منتجين (بوابة الوطن / اليوم الوطني)
  مع 6 دول خليجية وأسعارها، ونظام طلب مباشر عبر واتساب.
  A luxury RTL Arabic watch product page for the MTM brand featuring
  two product lines across 6 GCC countries with direct WhatsApp ordering.
triggers:
  - "MTM"
  - "watch product page"
  - "luxury product page"
  - "صفحة منتج ساعة"
  - "بوابة الوطن"
  - "اليوم الوطني"
  - "WhatsApp ordering"
  - "طلب واتساب"
od:
  mode: prototype
  platform: desktop
  scenario: sales
  preview:
    type: html
    entry: example.html
  design_system:
    requires: false
  craft:
    requires: []
---

# MTM Watch Product Page

صفحة منتج راقية لبراند MTM للساعات الفاخرة.

## ما تتضمنه الصفحة

- **هيدر بسيط**: شعار MTM على خلفية بيضاء نقية
- **مبدّل المنتجات**: زر للتبديل بين ساعة بوابة الوطن وساعة اليوم الوطني
- **معرض الصور**: صورة رئيسية + صور مصغرة تفاعلية (placeholders جاهزة للاستبدال)
- **محدد الدولة**: شبكة 3×2 لـ 6 دول خليجية مع تحديث فوري للسعر والوصف
- **المواصفات الفنية**: قائمة نقطية بلمسة ذهبية دقيقة
- **زر الطلب**: أسود فاخر يفتح واتساب برسالة جاهزة تلقائياً
- **أكورديون**: مواصفات فنية إضافية وسياسة التوصيل

## الأسعار

<!-- BEGIN:PRICES -->
| الدولة | بوابة الوطن | اليوم الوطني |
|---|---|---|
| الكويت | ١٨٠ د.ك | ١٩٥ د.ك |
| السعودية | ٢,٢٠٠ ر.س | ٢,٣٨٠ ر.س |
| الإمارات | ٢,١٥٠ د.إ | ٢,٣٣٠ د.إ |
| قطر | ٢,١٣٠ ر.ق | ٢,٣١٠ ر.ق |
| البحرين | ٢٢٠ د.ب | ٢٤٠ د.ب |
| عُمان | ٢٢٥ ر.ع | ٢٤٥ ر.ع |
<!-- END:PRICES -->

## مصدر البيانات

أسماء الإصدارات وأسعارها وأوصافها **لا تُعدّل في هذا الملف ولا في `example.html`**.
مصدرها الوحيد هو `mtm-content-toolkit/brand/catalog.json`. بعد أي تعديل هناك:

```bash
cd mtm-content-toolkit && python3 brand/sync.py
```

يكتب الجدول أعلاه وكتلة `<script type="application/json" id="mtm-catalog">` داخل
الصفحة. و`python3 brand/sync.py --check` يكشف أي انحراف بينهما.

## الاستخدام

افتح `example.html` مباشرة في المتصفح — الصفحة تعمل بالكامل بدون خادم، لأن
الكتالوج مضمّن في الصفحة كـJSON ولا يُجلب عبر الشبكة.

لإضافة صور المنتجات الحقيقية: استبدل الـplaceholder في `.watch-placeholder`
بعنصر `<img>` واربط مساره بمفتاح الدولة والمنتج من `CATALOG`.
