#!/usr/bin/env python3
"""مولّد تقويم محتوى MTM.

يقرأ البرومبت من مجلد prompts/ ويرسله لـ Anthropic API، ثم يحفظ الناتج
كملف CSV جاهز للفتح في Excel أو Google Sheets.

    python3 calendar/generate_calendar.py                        # تقويم 30 يوم
    python3 calendar/generate_calendar.py --hooks-only           # 50 هوك
    python3 calendar/generate_calendar.py --model claude-fable-5 # موديل أقوى
    python3 calendar/generate_calendar.py --effort max           # تفكير أعمق

يحتاج متغير البيئة ANTHROPIC_API_KEY.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
from datetime import datetime
from pathlib import Path

try:
    import anthropic
except ModuleNotFoundError:
    sys.exit(
        "مكتبة anthropic غير مثبّتة.\n"
        "ثبّتها بـ:  pip install -r requirements.txt"
    )

# جذر المشروع = المجلد الأب لمجلد calendar/
ROOT = Path(__file__).resolve().parent.parent
PROMPTS_DIR = ROOT / "prompts"
OUTPUT_DIR = Path(__file__).resolve().parent / "output"

DEFAULT_MODEL = "claude-opus-5"
DEFAULT_EFFORT = "high"
MAX_TOKENS = 32000


# ---------------------------------------------------------------------------
# قدرات الموديلات — كل عائلة تقبل شكل طلب مختلف، والخطأ هنا يرجّع 400
# ---------------------------------------------------------------------------
# adaptive:   يقبل thinking={"type": "adaptive"}
# effort:     يقبل output_config.effort
# structured: يقبل output_config.format (JSON Schema مضمون)
CAPABILITIES = {
    # عائلة Fable: التفكير مُفعّل دائماً، وأي إعداد صريح لـ thinking يرجّع 400
    "claude-fable-5": {"adaptive": False, "effort": True, "structured": True},
    "claude-mythos-5": {"adaptive": False, "effort": True, "structured": True},
    # الجيل الحالي
    "claude-opus-5": {"adaptive": True, "effort": True, "structured": True},
    "claude-opus-4-8": {"adaptive": True, "effort": True, "structured": True},
    "claude-opus-4-7": {"adaptive": True, "effort": True, "structured": False},
    "claude-opus-4-6": {"adaptive": True, "effort": True, "structured": False},
    "claude-sonnet-5": {"adaptive": True, "effort": True, "structured": True},
    # جيل سابق: يقبل effort لكن بدون Structured Outputs
    "claude-sonnet-4-6": {"adaptive": True, "effort": True, "structured": False},
    # موديلات أقدم: effort يرجّع خطأ عليها
    "claude-haiku-4-5": {"adaptive": False, "effort": False, "structured": True},
    "claude-sonnet-4-5": {"adaptive": False, "effort": False, "structured": False},
}

# الافتراضي لأي موديل غير معروف: أبسط شكل طلب ممكن — يشتغل في كل مكان
CONSERVATIVE = {"adaptive": False, "effort": False, "structured": False}


def capabilities_of(model: str) -> dict[str, bool]:
    """يرجّع قدرات الموديل، أو الوضع المتحفّظ لو الاسم غير معروف."""
    return CAPABILITIES.get(model, CONSERVATIVE)


# ---------------------------------------------------------------------------
# مخططات الإخراج (JSON Schema)
# ---------------------------------------------------------------------------
CALENDAR_SCHEMA = {
    "type": "object",
    "properties": {
        "days": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "day": {"type": "integer"},
                    "stage": {
                        "type": "string",
                        "enum": ["Awareness", "Trust", "Desire", "Action"],
                    },
                    "type": {"type": "string"},
                    "idea": {"type": "string"},
                    "hook": {"type": "string"},
                    "best_time": {"type": "string"},
                    "cta": {"type": "string"},
                    "hashtags": {"type": "string"},
                },
                "required": [
                    "day", "stage", "type", "idea",
                    "hook", "best_time", "cta", "hashtags",
                ],
                "additionalProperties": False,
            },
        }
    },
    "required": ["days"],
    "additionalProperties": False,
}

HOOKS_SCHEMA = {
    "type": "object",
    "properties": {
        "hooks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "number": {"type": "integer"},
                    "category": {"type": "string"},
                    "hook": {"type": "string"},
                },
                "required": ["number", "category", "hook"],
                "additionalProperties": False,
            },
        }
    },
    "required": ["hooks"],
    "additionalProperties": False,
}

# إعدادات كل وضع: البرومبت المصدر، المخطط، مفتاح المصفوفة، وأعمدة CSV العربية
MODES = {
    "calendar": {
        "prompt_file": "02_content_calendar.md",
        "schema": CALENDAR_SCHEMA,
        "root_key": "days",
        "file_stem": "mtm_calendar",
        "expected_rows": 30,
        "columns": [
            ("day", "اليوم"),
            ("stage", "المرحلة"),
            ("type", "النوع"),
            ("idea", "الفكرة"),
            ("hook", "الهوك"),
            ("best_time", "أفضل وقت نشر"),
            ("cta", "CTA"),
            ("hashtags", "الهاشتاجات"),
        ],
    },
    "hooks": {
        "prompt_file": "01_viral_hooks.md",
        "schema": HOOKS_SCHEMA,
        "root_key": "hooks",
        "file_stem": "mtm_hooks",
        "expected_rows": 50,
        "columns": [
            ("number", "رقم"),
            ("category", "التصنيف"),
            ("hook", "الهوك"),
        ],
    },
}


# ---------------------------------------------------------------------------
# قراءة البرومبت من ملف الماركداون
# ---------------------------------------------------------------------------
PROMPT_BLOCK = re.compile(
    r"<!--\s*BEGIN:PROMPT\s*-->(.*?)<!--\s*END:PROMPT\s*-->",
    re.DOTALL,
)


def warn_if_stale() -> None:
    """تحذير (لا خطأ) لو البرومبتات منحرفة عن brand/catalog.json — يمنع توليد
    محتوى بأسعار أو حقائق قديمة بدون ما تنتبه."""
    sys.path.insert(0, str(ROOT / "brand"))
    try:
        import sync
    except Exception:
        return  # أداة المزامنة غير متاحة — ما نوقف التوليد بسببها

    try:
        catalog = json.loads((ROOT / "brand" / "catalog.json").read_text(encoding="utf-8"))
        stale = [
            path.name
            for path, expected in sync.build_targets(catalog)
            if path.read_text(encoding="utf-8") != expected
        ]
    except SystemExit:
        return  # sync يستخدم sys.exit عند خطأ في الكتالوج — نتجاهله هنا
    except Exception:
        return

    if stale:
        print(
            "تحذير: البرومبتات غير متزامنة مع brand/catalog.json "
            f"({', '.join(stale)}).\nشغّل: python3 brand/sync.py",
            file=sys.stderr,
        )


def read_prompt(filename: str) -> str:
    """يستخرج نص البرومبت المحصور بين BEGIN:PROMPT و END:PROMPT."""
    path = PROMPTS_DIR / filename
    if not path.is_file():
        sys.exit(f"ملف البرومبت غير موجود: {path}")

    match = PROMPT_BLOCK.search(path.read_text(encoding="utf-8"))
    if not match:
        sys.exit(
            f"ما لقيت علامتَي BEGIN:PROMPT / END:PROMPT في {path}.\n"
            "السكريبت يقرأ النص المحصور بينهما فقط."
        )

    # إزالة أسطر ``` المحيطة بالنص داخل الماركداون
    lines = [
        line for line in match.group(1).strip().splitlines()
        if not line.strip().startswith("```")
    ]
    return "\n".join(lines).strip()


# ---------------------------------------------------------------------------
# بناء الطلب حسب قدرات الموديل
# ---------------------------------------------------------------------------
JSON_FALLBACK_INSTRUCTION = """

---
مهم جداً بخصوص شكل الإخراج: أخرج JSON صالح فقط، بدون أي نص قبله أو بعده،
وبدون علامات ``` — كائن واحد بهذا الشكل:
{{"{root_key}": [ ... ]}}
كل عنصر في المصفوفة يحتوي المفاتيح التالية بالضبط (بالإنجليزية كما هي):
{keys}
"""


def build_request(prompt: str, mode: dict, model: str, effort: str) -> dict:
    """يجمّع معاملات الطلب، ويتخطّى المعاملات اللي ما يدعمها الموديل."""
    caps = capabilities_of(model)
    output_config: dict = {}

    # التفكير: Fable مُفعّل دائماً (لا نرسل شيئاً)، والموديلات القديمة لا تدعم adaptive
    params: dict = {
        "model": model,
        "max_tokens": MAX_TOKENS,
    }
    if caps["adaptive"]:
        params["thinking"] = {"type": "adaptive"}

    if caps["effort"]:
        output_config["effort"] = effort

    if caps["structured"]:
        # المخطط يضمن JSON صالح بالمفاتيح المطلوبة — بدون تحليل نص هش
        output_config["format"] = {
            "type": "json_schema",
            "schema": mode["schema"],
        }
    else:
        # الموديل ما يدعم Structured Outputs — نطلب JSON في البرومبت ونحلّله يدوياً
        keys = ", ".join(key for key, _ in mode["columns"])
        prompt += JSON_FALLBACK_INSTRUCTION.format(
            root_key=mode["root_key"], keys=keys
        )

    if output_config:
        params["output_config"] = output_config

    params["messages"] = [{"role": "user", "content": prompt}]
    return params


# ---------------------------------------------------------------------------
# نداء الـ API
# ---------------------------------------------------------------------------
def call_api(params: dict) -> str:
    """يرسل الطلب ويرجّع النص الكامل. الـ streaming يمنع انتهاء المهلة."""
    client = anthropic.Anthropic()

    try:
        with client.messages.stream(**params) as stream:
            message = stream.get_final_message()
    except anthropic.AuthenticationError:
        sys.exit("المفتاح مرفوض. تأكد أن ANTHROPIC_API_KEY صحيح وغير منتهي.")
    except anthropic.NotFoundError:
        sys.exit(
            f"الموديل '{params['model']}' غير موجود أو غير متاح لحسابك.\n"
            "تأكد من الاسم، أو جرّب --model claude-opus-5"
        )
    except anthropic.BadRequestError as err:
        sys.exit(
            f"الطلب مرفوض: {err}\n"
            "غالباً الموديل ما يدعم أحد المعاملات المرسلة. جرّب --model claude-opus-5"
        )
    except anthropic.RateLimitError:
        sys.exit("تجاوزت حد الاستخدام. انتظر شوي وأعد المحاولة.")
    except anthropic.APIStatusError as err:
        sys.exit(f"خطأ من الـ API ({err.status_code}): {err}")
    except anthropic.APIConnectionError:
        sys.exit("فشل الاتصال بالـ API. تأكد من الإنترنت وأعد المحاولة.")

    # مصنّفات الأمان قد ترجّع 200 بمحتوى فاضي — نفحص قبل قراءة المحتوى
    if message.stop_reason == "refusal":
        sys.exit(
            "الموديل رفض الطلب لأسباب تتعلق بسياسات المحتوى.\n"
            "راجع نص البرومبت، أو جرّب موديل ثاني بـ --model"
        )
    if message.stop_reason == "max_tokens":
        print(
            "تحذير: الرد انقطع لأنه وصل الحد الأقصى للمخرجات — النتيجة قد تكون ناقصة.",
            file=sys.stderr,
        )

    text = "".join(block.text for block in message.content if block.type == "text")
    if not text.strip():
        sys.exit("الرد رجع فاضي. أعد المحاولة أو جرّب موديل ثاني.")

    usage = message.usage
    print(
        f"تم التوليد — دخل: {usage.input_tokens} توكن، خرج: {usage.output_tokens} توكن",
        file=sys.stderr,
    )
    return text


def parse_rows(text: str, root_key: str) -> list[dict]:
    """يحوّل نص الرد إلى قائمة صفوف."""
    cleaned = text.strip()

    # في وضع الاحتياط قد يلفّ الموديل الـ JSON بعلامات ``` — نزيلها
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```[a-zA-Z]*\n", "", cleaned)
        cleaned = re.sub(r"\n```\s*$", "", cleaned)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as err:
        sys.exit(
            f"ما قدرت أحلّل رد الموديل كـ JSON: {err}\n"
            "جرّب موديل يدعم Structured Outputs مثل claude-opus-5"
        )

    rows = data.get(root_key) if isinstance(data, dict) else None
    if not isinstance(rows, list) or not rows:
        sys.exit(f"الرد ما فيه مصفوفة '{root_key}' صالحة.")
    return rows


# ---------------------------------------------------------------------------
# كتابة CSV
# ---------------------------------------------------------------------------
def write_csv(rows: list[dict], mode: dict) -> Path:
    """يكتب الصفوف بترميز utf-8-sig — الـ BOM ضروري عشان Excel يعرض العربي صح."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    path = OUTPUT_DIR / f"{mode['file_stem']}_{stamp}.csv"

    keys = [key for key, _ in mode["columns"]]
    headers = [header for _, header in mode["columns"]]

    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(headers)
        for row in rows:
            writer.writerow([row.get(key, "") for key in keys])

    return path


# ---------------------------------------------------------------------------
def main() -> None:
    parser = argparse.ArgumentParser(
        description="مولّد تقويم محتوى MTM — يحفظ الناتج كملف CSV.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--hooks-only",
        action="store_true",
        help="يولّد 50 هوك بدل خطة الـ30 يوم",
    )
    parser.add_argument(
        "--model",
        default=os.environ.get("MTM_MODEL", DEFAULT_MODEL),
        help=f"موديل الـ API (الافتراضي: {DEFAULT_MODEL}، أو متغير البيئة MTM_MODEL)",
    )
    parser.add_argument(
        "--effort",
        default=DEFAULT_EFFORT,
        choices=["low", "medium", "high", "xhigh", "max"],
        help=f"عمق التفكير (الافتراضي: {DEFAULT_EFFORT})",
    )
    args = parser.parse_args()

    # فحص المفتاح أولاً — رسالة واضحة أفضل من انهيار داخل المكتبة
    if not os.environ.get("ANTHROPIC_API_KEY"):
        sys.exit(
            "متغير البيئة ANTHROPIC_API_KEY غير موجود.\n\n"
            'شغّل:  export ANTHROPIC_API_KEY="sk-ant-..."\n'
            "ثم أعد تشغيل السكريبت. لا تكتب المفتاح داخل أي ملف في المشروع."
        )

    mode = MODES["hooks" if args.hooks_only else "calendar"]

    warn_if_stale()
    prompt = read_prompt(mode["prompt_file"])
    params = build_request(prompt, mode, args.model, args.effort)

    print(f"الموديل: {args.model} | جاري التوليد...", file=sys.stderr)
    rows = parse_rows(call_api(params), mode["root_key"])

    expected = mode["expected_rows"]
    if len(rows) != expected:
        print(
            f"تنبيه: توقعت {expected} صف والناتج {len(rows)}. راجع الملف.",
            file=sys.stderr,
        )

    path = write_csv(rows, mode)
    print(f"\nتم الحفظ: {path}  ({len(rows)} صف)")
    print("راجع المحتوى يدوياً قبل النشر — الناتج هيكل، مو محتوى نهائي.")


if __name__ == "__main__":
    main()
