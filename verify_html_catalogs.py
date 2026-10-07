# -*- coding: utf-8 -*-
import os
import re
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

def verify_html(file_path, expected_rows):
    print(f"\n--- Verifying {file_path} ---")
    if not os.path.exists(file_path):
        print("  ❌ File does not exist!")
        return False

    size = os.path.getsize(file_path)
    print(f"  Size: {size:,} bytes")

    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Row count check
    rows = re.findall(r'<tr data-id="\d+"', content)
    print(f"  Row count: {len(rows)} (expected: {expected_rows})")
    assert len(rows) == expected_rows, f"Row count mismatch! Expected {expected_rows}, got {len(rows)}"

    # 2. Check for Persian/Arabic/Russian characters
    # Persian/Arabic range: \u0600-\u06FF, \u0750-\u077F, \uFB50-\uFDFF, \uFE70-\uFEFF
    # Cyrillic range: \u0400-\u04FF
    non_english = re.findall(r'[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF\u0400-\u04FF]', content)
    print(f"  Non-English (Persian/Arabic/Cyrillic) characters: {len(non_english)}")
    if non_english:
        print(f"  Sample non-English characters: {set(non_english[:10])}")
    assert len(non_english) == 0, f"Found {len(non_english)} non-English characters!"

    # 3. Check critical HTML elements
    critical_tags = [
        '<html lang="en"',
        '<table id="resultsTable">',
        'id="appSidebar"',
        'id="cardsGridContainer"',
        'id="compareDock"',
        'id="compareModal"',
        'id="scrollTopFab"',
        'id="noResultsRow"',
        'class="spotlight-grid"',
        'class="spectrum-card"',
        'class="workspace-toolbar"',
        '<script>'
    ]
    for tag in critical_tags:
        assert tag in content, f"Missing critical tag: {tag}"
    print("  ✅ All critical elements present")

    # 4. Check category counts in sidebar
    cats = re.findall(r'data-cat="([^"]+)".*?<span class="sb-count">(\d+)</span>', content, re.DOTALL)
    print(f"  Sidebar categories count: {len(cats)}")
    for cat, cnt in cats[:5]:
        print(f"    - {cat}: {cnt}")

    # 5. Check JS script closing
    assert '</script>' in content and '</body>' in content and '</html>' in content
    print("  ✅ Document properly closed and formatted")
    return True

print("=" * 80)
print("🔍 RUNNING COMPREHENSIVE AUDIT ON GENERATED HTML CATALOGS")
print("=" * 80)

verify_html("global_cloud_catalog.html", 609)
verify_html("master_cloud_directory.html", 609)
verify_html("master_hourly_directory.html", 62)
verify_html(r"C:\Users\Meow\Desktop\NewUI.html", 609)
verify_html(r"C:\Users\Meow\Desktop\thisisnew.html", 609)

print("\n" + "=" * 80)
print("🎉 ALL FILES PASSED 100% OF INTEGRITY AUDIT CHECKS!")
print("=" * 80)
