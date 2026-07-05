"""
generate_sitemap.py
--------------------
يقوم هذا السكريبت بإعادة توليد ملف sitemap.xml بحيث يحتوي على:
  1. الصفحة الرئيسية للموقع.
  2. رابط منفصل (app-page.html?app=slug) لكل تطبيق موجود في Firestore.

الاستخدام:
    1. حمّل ملف اعتماد حساب الخدمة (Service Account) من Firebase Console:
       Project Settings → Service Accounts → Generate new private key
       وضعه بجانب هذا السكريبت باسم serviceAccountKey.json
    2. ثبّت المكتبة المطلوبة:
       pip install firebase-admin
    3. شغّل السكريبت:
       python generate_sitemap.py
    4. ارفع ملف sitemap.xml الناتج إلى مستودع GitHub Pages (مجلد web/).

يفضّل ربط هذا السكريبت ببوت التليجرام الخاص بك أو بـ GitHub Action
بحيث يعمل تلقائيًا كل مرة يُنشر أو يُحذف تطبيق، أو على جدول زمني (مثلاً كل 6 ساعات).
"""

import json
from datetime import datetime, timezone

import firebase_admin
from firebase_admin import credentials, firestore

SITE_BASE_URL = "https://volttechcode.github.io/web/"
SERVICE_ACCOUNT_PATH = "serviceAccountKey.json"
OUTPUT_PATH = "sitemap.xml"


def slugify(app_data: dict, doc_id: str) -> str:
    """يحدد نفس منطق تحديد الـ slug المستخدم في app-page.html"""
    if app_data.get("seoSlug"):
        return app_data["seoSlug"]
    package_id = app_data.get("packageId") or doc_id
    return package_id.replace(".", "-")


def xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def main():
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)
    db = firestore.client()

    apps_ref = db.collection("apps").stream()

    urls = [
        {
            "loc": SITE_BASE_URL,
            "changefreq": "daily",
            "priority": "1.0",
            "lastmod": None,
        }
    ]

    count = 0
    for doc in apps_ref:
        data = doc.to_dict() or {}
        slug = slugify(data, doc.id)
        loc = f"{SITE_BASE_URL}app-page.html?app={slug}"

        lastmod = None
        updated_at = data.get("updatedAt") or data.get("createdAt")
        if updated_at is not None and hasattr(updated_at, "isoformat"):
            lastmod = updated_at.astimezone(timezone.utc).strftime("%Y-%m-%d")

        urls.append(
            {
                "loc": loc,
                "changefreq": "weekly",
                "priority": "0.8",
                "lastmod": lastmod,
            }
        )
        count += 1

    lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for u in urls:
        lines.append("  <url>")
        lines.append(f"    <loc>{xml_escape(u['loc'])}</loc>")
        if u["lastmod"]:
            lines.append(f"    <lastmod>{u['lastmod']}</lastmod>")
        lines.append(f"    <changefreq>{u['changefreq']}</changefreq>")
        lines.append(f"    <priority>{u['priority']}</priority>")
        lines.append("  </url>")
    lines.append("</urlset>")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"تم توليد {OUTPUT_PATH} بنجاح — يحتوي على {count} تطبيق + الصفحة الرئيسية.")


if __name__ == "__main__":
    main()
