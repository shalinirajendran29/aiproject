import os
from playwright.sync_api import sync_playwright
from typing import Dict, Any, List
from ..config import settings

class PlaywrightAutomationEngine:
    def __init__(self):
        self.headless = settings.PLAYWRIGHT_HEADLESS

    def inspect_page_forms(self, url: str) -> List[Dict[str, Any]]:
        """
        Crawls a page and returns lists of inputs and interactive fields.
        """
        form_fields = []
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True) # Always headless for crawling
            page = browser.new_page()
            try:
                page.goto(url, wait_until="networkidle", timeout=20000)
            except Exception as e:
                print(f"Navigation warning: {e}. Trying to parse load state.")
                
            # Scan standard text inputs, textareas, checkboxes, selects
            elements = page.query_selector_all("input, textarea, select")
            
            for index, elem in enumerate(elements):
                elem_type = elem.get_attribute("type") or "text"
                elem_name = elem.get_attribute("name") or ""
                elem_id = elem.get_attribute("id") or ""
                elem_placeholder = elem.get_attribute("placeholder") or ""
                
                # Exclude hidden, submit, buttons
                if elem_type in ("hidden", "submit", "button", "image", "radio"):
                    continue
                    
                # Try to extract a label
                label_text = ""
                if elem_id:
                    label_elem = page.query_selector(f"label[for='{elem_id}']")
                    if label_elem:
                        label_text = label_elem.inner_text().strip()
                
                # If no direct label, check parent container text
                if not label_text:
                    # Execute script to get text of closest text node
                    label_text = page.evaluate(
                        "(elem) => {"
                        "  let parent = elem.parentElement;"
                        "  if (!parent) return '';"
                        "  return parent.innerText.replace(elem.innerText, '').trim().split('\\n')[0];"
                        "}",
                        elem
                    )
                
                # Clean label text
                label_text = label_text.strip().rstrip(":")
                
                # Generate unique CSS Selector
                selector = ""
                if elem_id:
                    selector = f"#{elem_id}"
                elif elem_name:
                    selector = f"input[name='{elem_name}'], textarea[name='{elem_name}'], select[name='{elem_name}']"
                else:
                    tag = elem.evaluate("(e) => e.tagName.toLowerCase()")
                    selector = f"{tag}:nth-of-type({index + 1})"

                form_fields.append({
                    "id": elem_id,
                    "name": elem_name,
                    "type": elem_type,
                    "placeholder": elem_placeholder,
                    "label": label_text,
                    "selector": selector
                })
                
            browser.close()
        return form_fields

    def fill_form(self, url: str, selector_values: Dict[str, str], screenshot_path: str) -> Dict[str, Any]:
        """
        Navigates to url, fills values using Playwright, and takes a verification screenshot.
        """
        result = {"success": True, "filled": [], "errors": []}
        
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=self.headless)
            page = browser.new_page()
            try:
                page.goto(url, wait_until="networkidle", timeout=30000)
            except Exception as e:
                print(f"Initial navigation slow: {e}")
                
            for selector, value in selector_values.items():
                if not value:
                    continue
                try:
                    # Verify element exists
                    elem = page.wait_for_selector(selector, timeout=3000)
                    if elem:
                        tag_name = elem.evaluate("e => e.tagName.toLowerCase()")
                        elem_type = elem.get_attribute("type") or ""
                        
                        if tag_name == "select":
                            # Handle dropdown elements
                            elem.select_option(value=value)
                        elif elem_type == "checkbox":
                            if value.lower() in ("true", "yes", "checked", "1"):
                                elem.check()
                        else:
                            # Standard text input, slow typing to mimic human
                            elem.click()
                            elem.fill("")  # Clear field first
                            page.keyboard.type(value, delay=50) # 50ms delay
                            
                        result["filled"].append(selector)
                except Exception as ex:
                    err_msg = f"Failed to fill selector '{selector}': {str(ex)}"
                    print(err_msg)
                    result["errors"].append(err_msg)
            
            # Auto-detect and click the submit button to store data on target website
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "#submit_btn",
                "#submit",
                ".btn-submit",
                "button:has-text('Submit')",
                "button:has-text('Confirm')",
                "button:has-text('Save')"
            ]
            
            submit_clicked = False
            for sub_sel in submit_selectors:
                try:
                    # Try to locate and click it
                    elem = page.locator(sub_sel).first
                    if elem and elem.is_visible():
                        elem.click()
                        submit_clicked = True
                        print(f"Auto-clicked submit button using selector: {sub_sel}")
                        break
                except Exception as click_err:
                    pass
            
            if submit_clicked:
                # Wait for any network requests/navigation to complete after submit
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    page.wait_for_timeout(2000)  # Safe buffer timeout
            else:
                # If no submit button is found, wait briefly
                page.wait_for_timeout(1000)

            # Ensure upload folder for screenshots exists
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            
            # Take screenshot of the post-submission success/stored page
            page.screenshot(path=screenshot_path)
            browser.close()
            
        if len(result["errors"]) > 0 and len(result["filled"]) == 0:
            result["success"] = False
            
        return result
