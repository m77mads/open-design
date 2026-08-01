#!/usr/bin/env python3
"""مزامنة حقائق البراند من brand/catalog.json إلى كل الملفات اللي تستهلكها.

    python3 brand/sync.py           # يكتب التحديثات
    python3 brand/sync.py --check   # يفحص فقط، ويخرج بـ 1 لو فيه انحراف

المصدر الوحيد هو catalog.json. أي سعر أو اسم أو وصف يُعدّل هناك، ثم يُشغّل
هذا السكريبت — لا تعدّل الكتل المولّدة يدوياً لأن أول مزامنة تمسحها.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

TOOLKIT = Path(__file__).resolve().parent.parent
REPO = TOOLKIT.parent
CATALOG_PATH = TOOLKIT / "brand" / "catalog.json"
TEMPLATE_DIR = REPO / "design-templates" / "mtm-watch-product-page"

# علامات الكتل المولّدة. علامات البرومبت نصية عربية لأنها تُنسخ مع البرومبت
# نفسه إلى Claude.ai — تعليق HTML كان راح يظهر كضجيج داخل النص.
BRAND_BEGIN = "=== سياق البراند — مُولَّد من brand/catalog.json (لا تعدّله يدوياً) ==="
BRAND_END = "=== نهاية سياق البراند ==="

HTML_BEGIN = "<!-- BEGIN:MTM-CATALOG -->"
HTML_END = "<!-- END:MTM-CATALOG -->"

MD_PRICES_BEGIN = "<!-- BEGIN:PRICES -->"
MD_PRICES_END = "<!-- END:PRICES -->"

MD_FACTS_BEGIN = "<!-- BEGIN:FACTS -->"
MD_FACTS_END = "<!-- END:FACTS -->"

PROMPT_FILES = [
    "01_viral_hooks.md",
    "02_content_calendar.md",
    "03_account_analysis.md",
    "04_stepbystep_guide.md",
    "05_engagement_system.md",
    "06_idea_to_carousel.md",
    "07_sales_funnel.md",
]


def load_catalog() -> dict:
    if not CATALOG_PATH.is_file():
        sys.exit(f"ملف الكتالوج غير موجود: {CATALOG_PATH}")
    try:
        return json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as err:
        sys.exit(f"catalog.json غير صالح: {err}")


# ---------------------------------------------------------------------------
# استبدال الكتل
# ---------------------------------------------------------------------------
def replace_block(text: str, begin: str, end: str, body: str, where: str) -> str:
    """يستبدل ما بين العلامتين، مع الإبقاء على العلامتين نفسيهما."""
    start = text.find(begin)
    stop = text.find(end)
    if start == -1 or stop == -1:
        sys.exit(f"ما لقيت علامتَي الكتلة في {where}:\n  {begin}\n  {end}")
    if stop < start:
        sys.exit(f"ترتيب العلامات معكوس في {where}")
    return text[: start + len(begin)] + "\n" + body.strip("\n") + "\n" + text[stop:]


# ---------------------------------------------------------------------------
# مولّدات المحتوى
# ---------------------------------------------------------------------------
def price_table(catalog: dict, indent: str = "") -> str:
    """جدول الأسعار: صف لكل دولة، عمود لكل خط منتج."""
    lines = [
        f"{indent}| الدولة | بوابة الوطن | اليوم الوطني |",
        f"{indent}|---|---|---|",
    ]
    for country in catalog["countries"]:
        key = country["key"]
        bawaba = catalog["products"]["bawaba"]["countries"][key]["price"]
        national = catalog["products"]["national"]["countries"][key]["price"]
        lines.append(f"{indent}| {country['name']} | {bawaba} | {national} |")
    return "\n".join(lines)


def motif_table(catalog: dict, indent: str = "") -> str:
    """جدول الإصدارات ومعالمها — أساس التمايز وقصص المحتوى."""
    lines = [
        f"{indent}| الإصدار | المَعلم/الرمز المنقوش |",
        f"{indent}|---|---|",
    ]
    for pkey, product in catalog["products"].items():
        for country in catalog["countries"]:
            edition = product["countries"][country["key"]]
            lines.append(f"{indent}| {edition['name']} | {edition['motif']} |")
    return "\n".join(lines)


def brand_context(catalog: dict) -> str:
    """كتلة السياق اللي تُحقن في كل برومبت."""
    brand = catalog["brand"]
    bawaba = catalog["products"]["bawaba"]
    national = catalog["products"]["national"]
    countries = "، ".join(c["name"] for c in catalog["countries"])

    parts = [
        f"- البراند: {brand['name']} ({brand['tagline']}) — ساعات فاخرة بنقوش تراثية خليجية، مطلية بالذهب النقي عيار 24.",
        "- خطان للمنتج:",
        f"  · {bawaba['baseTitle']} ({bawaba['collection']}) — نقش لمَعلم تاريخي خاص بكل دولة.",
        f"  · {national['baseTitle']} ({national['collection']}) — إصدار احتفالي لكل دولة.",
        f"- 12 إصدار = خطان × 6 دول: {countries}.",
        "- الأسعار:",
        price_table(catalog, indent="  "),
        "- المَعلم المنقوش على كل إصدار (استخدمه بالاسم، ولا تنسب معلماً لإصدار غير إصداره):",
        motif_table(catalog, indent="  "),
        "- المواصفات:",
    ]
    parts += [f"  · {spec}" for spec in catalog["specs"]]

    policies = catalog["policies"]
    parts += [
        "- السياسات:",
        f"  · {policies['warranty']}",
        f"  · {policies['returns']}",
        f"  · {policies['shipping']}",
        f"  · {policies['vat']}",
        f"  · {policies['packaging']}",
        f"- الجمهور: {brand['audience']}.",
        f"- إنستغرام: {brand['instagram']}. الطلب: {brand['order_channel']}.",
        f"- النبرة: {brand['positioning']}.",
        "  ممنوع: \"اشتري الآن\"، علامات تعجب متتالية، إيموجي مزدحم، لغة تحفيزية صارخة.",
        "- اللهجة: عربي مبسّط مع لمسة خليجية طبيعية، بدون تكلّف.",
        f"- أساس الندرة: {catalog['scarcity_basis']}",
        "- قنوات جمع العملاء المحتملين — هذه فقط، ولا يجوز اقتراح غيرها:",
    ]
    parts += [f"  · {channel}" for channel in catalog["lead_channels"]["approved"]]
    parts += [
        f"- ممنوع تماماً: {catalog['lead_channels']['banned']}",
        f"- قاعدة الإغلاق: {catalog['closing_rule']}",
        "",
        "معلومات ممنوع ذكرها أو الاستنتاج منها — غير مؤكدة بعد:",
    ]
    parts += [f"  · {item}" for item in catalog["needs_confirmation"]]
    parts.append(
        "  لا تخترع بديلاً عن أي معلومة أعلاه، ولا تذكرها بصيغة تقريبية. تجاهلها تماماً."
    )
    return "\n".join(parts)


def facts_table(catalog: dict) -> str:
    """جدول الحقائق المختصر داخل playbook."""
    policies = catalog["policies"]
    lines = [
        "| الحقيقة | القيمة |",
        "|---|---|",
        f"| خطوط المنتج | {catalog['products']['bawaba']['baseTitle']} · {catalog['products']['national']['baseTitle']} |",
        f"| عدد الإصدارات | 12 (خطان × 6 دول) |",
        f"| نطاق السوق | {'، '.join(c['name'] for c in catalog['countries'])} |",
        f"| الضمان | {policies['warranty']} |",
        f"| الإرجاع | {policies['returns']} |",
        f"| التوصيل | {policies['shipping']} |",
        f"| قناة الطلب | واتساب `{catalog['brand']['whatsapp']}` |",
    ]
    return "\n".join(lines)


def html_catalog_block(catalog: dict) -> str:
    """كتلة JSON المضمّنة في الصفحة — مضمّنة لا مجلوبة، عشان تشتغل من file://."""
    payload = json.dumps(catalog, ensure_ascii=False, indent=2)
    return (
        '  <script type="application/json" id="mtm-catalog">\n'
        f"{payload}\n"
        "  </script>"
    )


# ---------------------------------------------------------------------------
# الأهداف
# ---------------------------------------------------------------------------
def build_targets(catalog: dict) -> list[tuple[Path, str]]:
    """يرجّع قائمة (المسار، المحتوى المتوقع بعد المزامنة)."""
    targets: list[tuple[Path, str]] = []
    context = brand_context(catalog)

    for name in PROMPT_FILES:
        path = TOOLKIT / "prompts" / name
        if not path.is_file():
            sys.exit(f"ملف برومبت مفقود: {path}")
        text = path.read_text(encoding="utf-8")
        targets.append(
            (path, replace_block(text, BRAND_BEGIN, BRAND_END, context, path.name))
        )

    html_path = TEMPLATE_DIR / "example.html"
    if html_path.is_file():
        text = html_path.read_text(encoding="utf-8")
        targets.append(
            (
                html_path,
                replace_block(
                    text, HTML_BEGIN, HTML_END, html_catalog_block(catalog), html_path.name
                ),
            )
        )

    skill_path = TEMPLATE_DIR / "SKILL.md"
    if skill_path.is_file():
        text = skill_path.read_text(encoding="utf-8")
        targets.append(
            (
                skill_path,
                replace_block(
                    text, MD_PRICES_BEGIN, MD_PRICES_END, price_table(catalog), skill_path.name
                ),
            )
        )

    playbook_path = TOOLKIT / "docs" / "playbook.md"
    if playbook_path.is_file():
        text = playbook_path.read_text(encoding="utf-8")
        targets.append(
            (
                playbook_path,
                replace_block(
                    text, MD_FACTS_BEGIN, MD_FACTS_END, facts_table(catalog), playbook_path.name
                ),
            )
        )

    return targets


def default_markup_drift(catalog: dict) -> list[str]:
    """القيم الابتدائية في markup الصفحة يستبدلها renderPage عند التحميل،
    لكنها تظهر قبل تنفيذ الـJS — فنتأكد أنها تطابق الافتراضي في الكتالوج."""
    html_path = TEMPLATE_DIR / "example.html"
    if not html_path.is_file():
        return []

    defaults = catalog["defaults"]
    edition = catalog["products"][defaults["product"]]["countries"][defaults["country"]]
    text = html_path.read_text(encoding="utf-8")

    problems = []
    for label, value in (("السعر", edition["price"]), ("الوصف", edition["desc"])):
        if value not in text:
            problems.append(
                f"{html_path.name}: {label} الابتدائي في الـmarkup ما يطابق الكتالوج "
                f"(المتوقع: {value[:40]}…)"
            )
    return problems


# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="مزامنة حقائق البراند من catalog.json إلى كل الملفات المستهلِكة."
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="يفحص فقط بدون كتابة، ويخرج بـ 1 لو فيه انحراف",
    )
    args = parser.parse_args()

    catalog = load_catalog()
    targets = build_targets(catalog)

    stale = [
        path for path, expected in targets
        if path.read_text(encoding="utf-8") != expected
    ]
    drift = default_markup_drift(catalog)

    if args.check:
        if not stale and not drift:
            print(f"المزامنة سليمة — {len(targets)} ملف مطابق للكتالوج.")
            return
        print("انحراف عن الكتالوج:", file=sys.stderr)
        for path in stale:
            print(f"  - {path.relative_to(REPO)}", file=sys.stderr)
        for problem in drift:
            print(f"  - {problem}", file=sys.stderr)
        print("\nشغّل: python3 brand/sync.py", file=sys.stderr)
        sys.exit(1)

    for path, expected in targets:
        if path.read_text(encoding="utf-8") != expected:
            path.write_text(expected, encoding="utf-8")

    if stale:
        print(f"تم تحديث {len(stale)} ملف:")
        for path in stale:
            print(f"  - {path.relative_to(REPO)}")
    else:
        print("كل الملفات محدّثة أصلاً.")

    for problem in drift:
        print(f"تنبيه: {problem}", file=sys.stderr)


if __name__ == "__main__":
    main()
