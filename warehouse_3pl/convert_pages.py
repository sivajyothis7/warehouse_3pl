import frappe


def execute():
    # Test md_to_html
    test_md = "# Hello\n\n1. Item 1\n2. Item 2\n\n- Bullet 1\n- Bullet 2"
    try:
        html = frappe.utils.md_to_html(test_md)
        print("md_to_html test SUCCESS:", repr(html[:100]))
    except Exception as e:
        print("md_to_html ERROR:", e)
        return

    pages = frappe.get_all(
        "Web Page",
        filters={"route": ["like", "3pl-guide%"]},
        fields=["name", "route", "content_type", "main_section_md"],
        order_by="route asc",
    )

    print(f"Found {len(pages)} pages")

    for page in pages:
        if not page.main_section_md:
            print(f"SKIP (no md): {page.route}")
            continue

        # Convert markdown to HTML
        html = frappe.utils.md_to_html(page.main_section_md)

        # Update the page
        doc = frappe.get_doc("Web Page", page.name)
        doc.content_type = "Rich Text"
        doc.main_section = html
        doc.main_section_md = ""
        doc.save(ignore_permissions=True)
        print(f"Updated: {page.route} (html_len={len(html)})")

    frappe.db.commit()
    print("DONE - committed all changes")


def verify():
    pages = frappe.get_all(
        "Web Page",
        filters={"route": ["like", "3pl-guide%"]},
        fields=["name", "route", "content_type", "main_section", "main_section_md"],
        order_by="route asc",
    )

    print(f"Verifying {len(pages)} pages:")
    for page in pages:
        html_len = len(page.main_section or "")
        md_len = len(page.main_section_md or "")
        print(f"  {page.route}: content_type={page.content_type}, html_len={html_len}, md_len={md_len}")
        if page.main_section:
            # Show first 200 chars of HTML
            print(f"    HTML preview: {page.main_section[:200]!r}")
