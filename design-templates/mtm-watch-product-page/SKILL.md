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

| الدولة      | بوابة الوطن | اليوم الوطني |
|-------------|------------|--------------|
| الكويت      | ١٨٠ د.ك    | ١٩٥ د.ك      |
| السعودية    | ٢,٢٠٠ ر.س  | ٢,٣٨٠ ر.س    |
| الإمارات    | ٢,١٥٠ د.إ  | ٢,٣٣٠ د.إ    |
| قطر         | ٢,١٣٠ ر.ق  | ٢,٣١٠ ر.ق    |
| البحرين     | ٢٢٠ د.ب    | ٢٤٠ د.ب      |
| عُمان       | ٢٢٥ ر.ع    | ٢٤٥ ر.ع      |

## الاستخدام

افتح `example.html` مباشرة في المتصفح — الصفحة تعمل بالكامل بدون خادم.
لإضافة صور المنتجات الحقيقية: استبدل `data-country` و`data-product` placeholders
بمسارات الصور الفعلية في قاموس `catalogData` داخل `<script>`.
