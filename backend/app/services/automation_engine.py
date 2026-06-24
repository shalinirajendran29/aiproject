import os
import re
from playwright.sync_api import sync_playwright
from typing import Dict, Any, List
from ..config import settings

def levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
        
    return previous_row[-1]

JS_RESOLVER_DEFINITION = r"""
window.resolveInputLabel = (elem) => {
    if (!elem) return '';
    function clean(txt) {
        return txt ? txt.replace(/[\u200b\u200c\n]/g, '').replace(/\*$/, '').trim() : '';
    }
    let id = elem.id;
    if (id) {
        let label = document.querySelector(`label[for="${id}"]`);
        if (label && clean(label.innerText)) return clean(label.innerText);
    }
    let current = elem;
    for (let i = 0; i < 5; i++) {
        let parent = current.parentElement;
        if (!parent) break;
        
        let sibling = current.previousElementSibling;
        while (sibling) {
            let sibText = clean(sibling.innerText);
            if (sibText && sibText.length < 50 && /[a-zA-Z]/.test(sibText)) {
                return sibText;
            }
            sibling = sibling.previousElementSibling;
        }
        
        let parentSib = parent.previousElementSibling;
        if (parentSib) {
            let sibText = clean(parentSib.innerText);
            if (sibText && sibText.length < 50 && /[a-zA-Z]/.test(sibText)) {
                return sibText;
            }
        }
        
        let pText = clean(parent.innerText);
        if (pText && pText.length < 50 && /[a-zA-Z]/.test(pText)) {
            return pText;
        }
        current = parent;
    }
    return '';
};
"""


class PlaywrightAutomationEngine:
    def __init__(self):
        self.headless = settings.PLAYWRIGHT_HEADLESS

    def inspect_page_forms(self, url: str) -> List[Dict[str, Any]]:
        """
        Crawls a page and returns lists of inputs and interactive fields.
        Supports loading saved session state.
        """
        auth_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "auth.json")
        form_fields = []
        with sync_playwright() as p:
            has_auth = os.path.exists(auth_path)
            browser = p.chromium.launch(headless=True) # Always headless for crawling
            
            if has_auth:
                print(f"Loading saved session cookies for crawl from {auth_path}")
                context = browser.new_context(storage_state=auth_path)
            else:
                context = browser.new_context()
                
            page = context.new_page()
            try:
                page.goto(url, wait_until="load", timeout=20000)
            except Exception as e:
                print(f"Navigation warning: {e}. Trying to parse load state.")
                
            # Wait for inputs to render
            try:
                page.wait_for_selector("input", timeout=5000)
            except Exception:
                pass
                
            # Inject resolveInputLabel function
            page.evaluate(JS_RESOLVER_DEFINITION)
            
            # Scan standard text inputs, textareas, checkboxes, selects
            elements = page.query_selector_all("input, textarea, select")
            
            for index, elem in enumerate(elements):
                try:
                    elem_type = elem.get_attribute("type") or "text"
                    elem_name = elem.get_attribute("name") or ""
                    elem_id = elem.get_attribute("id") or ""
                    elem_placeholder = elem.get_attribute("placeholder") or ""
                    
                    # Exclude hidden, submit, buttons, password
                    if elem_type in ("hidden", "submit", "button", "image", "radio", "password"):
                        continue
                        
                    # Skip disabled elements
                    is_disabled = elem.is_disabled() or elem.evaluate("el => el.disabled") or elem.evaluate("el => el.classList.contains('Mui-disabled')")
                    if is_disabled:
                        continue
                        
                    # Resolve label using custom JS function
                    label_text = page.evaluate("window.resolveInputLabel", elem)
                    label_text = label_text.strip()
                    
                    # Clean/Fallback label text if empty
                    if not label_text:
                        label_text = page.evaluate(
                            "(elem) => {"
                            "  let parent = elem.parentElement;"
                            "  if (!parent) return '';"
                            "  return parent.innerText.replace(elem.innerText, '').trim().split('\\n')[0];"
                            "}",
                            elem
                        )
                        label_text = label_text.replace('\u200b', '').replace('\u200c', '').strip().rstrip(":")
                    
                    # Skip Customer Code completely
                    if label_text.lower() in ("customer code", "customercode"):
                        continue
                        
                    # Skip Rate selector
                    if label_text.lower() in ("gold & silver rate", "rate"):
                        continue
                    
                    # Generate dynamic label selector or fallback CSS Selector
                    selector = ""
                    if label_text:
                        selector = f"label:{label_text}"
                    elif elem_id:
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
                        "label": label_text or elem_name or elem_id,
                        "selector": selector
                    })
                except Exception:
                    pass
                
            browser.close()
        return form_fields

    def _verify_submission_success(self, page, original_url) -> tuple[bool, str]:
        # Helper to verify if the form submit succeeded.
        # Returns (success_boolean, error_message)
        try:
            # Check for HTML5 invalid fields
            invalid_fields = page.query_selector_all("input:invalid, select:invalid, textarea:invalid")
            if len(invalid_fields) > 0:
                return False, f"Form submission failed: {len(invalid_fields)} required fields are missing or invalid in the target browser."
            
            # Check if URL hasn't changed and required fields are still empty
            curr_url = page.url
            if curr_url == original_url:
                required_empty = page.evaluate("""() => {
                    let inputs = document.querySelectorAll("input[required], select[required], textarea[required]");
                    let emptyCount = 0;
                    for (let elem of inputs) {
                        if (!elem.value || !elem.value.trim()) {
                            emptyCount++;
                        }
                    }
                    return emptyCount;
                }""")
                if required_empty > 0:
                    return False, f"Form submission failed: {required_empty} required fields are empty on the page."
                    
            return True, ""
        except Exception as ex:
            return True, ""

    def fill_form(
        self, 
        url: str, 
        extracted_data: Dict[str, Any], 
        mapping_engine: Any, 
        db: Any, 
        screenshot_path: str
    ) -> Dict[str, Any]:
        """
        Navigates to url, logs in if needed, scans form fields, maps them dynamically, 
        fills values using Playwright, and takes a verification screenshot.
        """
        result = {"success": True, "filled": [], "errors": [], "mappings": {}}
        
        # Store the login session state in the project root directory
        auth_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "auth.json")
        
        with sync_playwright() as p:
            # Check if we have a saved session state
            has_auth = os.path.exists(auth_path)
            
            # Start by launching browser (try headless if we have auth, else headed)
            run_headless = self.headless if has_auth else False
            browser = p.chromium.launch(headless=run_headless)
            
            if has_auth:
                print(f"Loading saved session cookies from {auth_path}...")
                context = browser.new_context(storage_state=auth_path)
            else:
                print("No active login session found (auth.json missing). Launching browser to capture session...")
                context = browser.new_context()
                
            page = context.new_page()
            
            try:
                page.goto(url, wait_until="load", timeout=30000)
            except Exception as e:
                print(f"Initial page load warning: {e}")
                
            # Verify if we are logged in (i.e. some form input fields are visible)
            # Since we haven't scanned yet, we look for any standard input/textarea on the page
            is_logged_in = False
            if has_auth:
                try:
                    # Wait up to 4 seconds for any input to appear
                    page.wait_for_selector("input:not([type='hidden']), textarea, select", timeout=4000)
                    
                    # Check if it's the login page by inspecting if password input exists but no other inputs exist
                    inputs_count = len(page.query_selector_all("input:not([type='hidden']), textarea, select"))
                    has_password = page.query_selector("input[type='password']") is not None
                    if has_password and inputs_count <= 3:
                        print("Redirected to login page. Session cookies are invalid/expired.")
                        is_logged_in = False
                    else:
                        is_logged_in = True
                except Exception:
                    is_logged_in = False
            
            # Relaunch headed if redirected to login page or no session exists
            if not is_logged_in:
                if run_headless:
                    print("Relaunching browser visibly to allow manual login...")
                    page.close()
                    context.close()
                    browser.close()
                    
                    browser = p.chromium.launch(headless=False)
                    context = browser.new_context()
                    page = context.new_page()
                    try:
                        page.goto(url, wait_until="load", timeout=30000)
                    except Exception as e:
                        print(f"Page load warning on relaunch: {e}")
                
                print("--------------------------------------------------------------------------------")
                print("ACTION REQUIRED: If this site requires authentication, please log in now.")
                print("The system is waiting for the target form fields to load...")
                print("--------------------------------------------------------------------------------")
                
                # Wait up to 60 seconds for the user to login and the form to load
                print("Waiting for login to complete and form to load...")
                logged_in = False
                for _ in range(60):
                    has_password = page.query_selector("input[type='password']") is not None
                    inputs = page.query_selector_all("input:not([type='hidden']), textarea, select")
                    if not has_password and len(inputs) > 2:  # Stricter check (> 2) to ensure the form loaded
                        logged_in = True
                        break
                    page.wait_for_timeout(1000)
                
                if not logged_in:
                    print("Timeout waiting for form inputs. Saving current session cookies...")
                
                # Save session cookies
                context.storage_state(path=auth_path)
                print(f"Successfully saved authenticated session state to: {auth_path}")

            # --- Now we are logged in. Let's Crawl the Form Fields ---
            # Wait for the form inputs to render dynamically
            print("Waiting for form inputs to render...")
            for _ in range(15):
                inputs = page.query_selector_all("input:not([type='hidden']), textarea, select")
                if len(inputs) > 2:
                    break
                page.wait_for_timeout(500)

            # Inject resolveInputLabel function
            page.evaluate(JS_RESOLVER_DEFINITION)
            
            print("Scanning page inputs...")
            elements = page.query_selector_all("input, textarea, select")
            form_fields = []
            
            for index, elem in enumerate(elements):
                try:
                    elem_type = elem.get_attribute("type") or "text"
                    elem_name = elem.get_attribute("name") or ""
                    elem_id = elem.get_attribute("id") or ""
                    elem_placeholder = elem.get_attribute("placeholder") or ""
                    
                    if elem_type in ("hidden", "submit", "button", "image", "radio", "password"):
                        continue
                        
                    # Skip disabled elements
                    is_disabled = elem.is_disabled() or elem.evaluate("el => el.disabled") or elem.evaluate("el => el.classList.contains('Mui-disabled')")
                    if is_disabled:
                        continue
                        
                    # Resolve label using custom JS function
                    label_text = page.evaluate("window.resolveInputLabel", elem)
                    label_text = label_text.strip()
                    
                    # Clean/Fallback label text if empty
                    if not label_text:
                        label_text = page.evaluate(
                            "(elem) => {"
                            "  let parent = elem.parentElement;"
                            "  if (!parent) return '';"
                            "  return parent.innerText.replace(elem.innerText, '').trim().split('\\n')[0];"
                            "}",
                            elem
                        )
                        label_text = label_text.replace('\u200b', '').replace('\u200c', '').strip().rstrip(":")
                    
                    # Skip Customer Code completely
                    if label_text.lower() in ("customer code", "customercode"):
                        continue
                        
                    # Skip Rate selector
                    if label_text.lower() in ("gold & silver rate", "rate"):
                        continue

                    # Generate dynamic label selector or fallback CSS Selector
                    selector = ""
                    if label_text:
                        selector = f"label:{label_text}"
                    elif elem_id:
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
                        "label": label_text or elem_name or elem_id,
                        "selector": selector
                    })
                except Exception:
                    pass

            if not form_fields:
                result["success"] = False
                result["errors"].append("No input fields found on target website after login.")
                browser.close()
                return result

            # --- Map the Fields ---
            print("Mapping document fields to web inputs...")
            mapped_selectors = mapping_engine.map_fields(extracted_data, form_fields, db)
            result["mappings"] = mapped_selectors

            if not mapped_selectors:
                result["success"] = False
                result["errors"].append("No matching fields could be semantically aligned.")
                browser.close()
                return result

            # --- Fill the Fields ---
            print("Filling form fields...")
            
            # Sort selectors to handle cascading dropdowns (Country -> State -> District -> others)
            def get_fill_priority(sel):
                sel_lower = sel.lower()
                if "country" in sel_lower:
                    return 1
                if "state" in sel_lower:
                    return 2
                if "district" in sel_lower or "city" in sel_lower:
                    return 3
                return 4
                
            sorted_selectors = sorted(mapped_selectors.items(), key=lambda x: get_fill_priority(x[0]))
            
            for selector, value in sorted_selectors:
                if not value:
                    continue
                
                # Clean mobile numbers: remove +91/91 country code and spaces
                selector_lower = selector.lower()
                if any(kw in selector_lower for kw in ["mobile", "phone", "contact", "tel"]):
                    if isinstance(value, str):
                        cleaned_val = value.strip()
                        if cleaned_val.startswith("+91"):
                            cleaned_val = cleaned_val[3:].strip()
                        elif cleaned_val.startswith("91") and len(cleaned_val) > 10:
                            cleaned_val = cleaned_val[2:].strip()
                        # Keep only digits
                        cleaned_val = "".join(c for c in cleaned_val if c.isdigit())
                        value = cleaned_val
                try:
                    elem = None
                    if selector.startswith("label:"):
                        label_name = selector.split(":", 1)[1]
                        elem_handle = page.evaluate_handle(
                            """(labelName) => {
                                let inputs = document.querySelectorAll("input, textarea, select");
                                for (let elem of inputs) {
                                    if (window.resolveInputLabel(elem).toLowerCase() === labelName.toLowerCase()) {
                                        return elem;
                                    }
                                }
                                return null;
                            }""",
                            label_name
                        )
                        if elem_handle and elem_handle.as_element():
                            elem = elem_handle.as_element()
                    else:
                        elem = page.wait_for_selector(selector, timeout=5000)
                        
                    if elem:
                        tag_name = elem.evaluate("e => e.tagName.toLowerCase()")
                        elem_type = elem.get_attribute("type") or ""
                        class_attr = elem.get_attribute("class") or ""
                        role_attr = elem.get_attribute("role") or ""
                        
                        if tag_name == "select":
                            elem.select_option(value=value)
                        elif elem_type == "checkbox":
                            if value.lower() in ("true", "yes", "checked", "1"):
                                elem.check()
                        elif role_attr == "combobox" or "MuiAutocomplete-input" in class_attr:
                            # Material UI Autocomplete selection
                            print(f"Handling MUI Autocomplete for selector '{selector}' with value '{value}'")
                            elem.click()
                            page.wait_for_timeout(300)
                            
                            # Case-insensitive, space-insensitive, and fuzzy option matching
                            try:
                                page.wait_for_selector("li[role='option'], .MuiAutocomplete-option", timeout=2000)
                                option_locator = page.locator("li[role='option'], .MuiAutocomplete-option")
                                count = option_locator.count()
                                matched = False
                                
                                val_norm = re.sub(r'[^a-z0-9]', '', value.lower())
                                
                                # 1. Try exact normalized match
                                for idx in range(count):
                                    opt = option_locator.nth(idx)
                                    opt_text = opt.inner_text().strip()
                                    opt_norm = re.sub(r'[^a-z0-9]', '', opt_text.lower())
                                    if opt_norm == val_norm:
                                        opt.click()
                                        print(f"Found exact normalized match for '{value}': '{opt_text}'")
                                        matched = True
                                        break
                                        
                                # 2. Try substring match
                                if not matched:
                                    for idx in range(count):
                                        opt = option_locator.nth(idx)
                                        opt_text = opt.inner_text().strip()
                                        opt_norm = re.sub(r'[^a-z0-9]', '', opt_text.lower())
                                        if val_norm in opt_norm or opt_norm in val_norm:
                                            opt.click()
                                            print(f"Found substring match for '{value}': '{opt_text}'")
                                            matched = True
                                            break
                                            
                                # 3. Try fuzzy Levenshtein match (threshold >= 65%)
                                if not matched:
                                    best_opt = None
                                    best_sim = 0.0
                                    best_text = ""
                                    for idx in range(count):
                                        opt = option_locator.nth(idx)
                                        opt_text = opt.inner_text().strip()
                                        opt_norm = re.sub(r'[^a-z0-9]', '', opt_text.lower())
                                        
                                        dist = levenshtein_distance(val_norm, opt_norm)
                                        max_len = max(len(val_norm), len(opt_norm))
                                        sim = 1.0 - (dist / max_len) if max_len > 0 else 0.0
                                        
                                        if sim > best_sim:
                                            best_sim = sim
                                            best_opt = opt
                                            best_text = opt_text
                                            
                                    if best_sim >= 0.65:
                                        best_opt.click()
                                        print(f"Found fuzzy match for '{value}': '{best_text}' (similarity: {best_sim:.2f})")
                                        matched = True
                                        
                                if not matched:
                                    # Fallback: type the value to filter
                                    print(f"No match in open list. Typing value '{value}' to filter...")
                                    elem.fill(value)
                                    page.wait_for_timeout(500)
                                    
                                    page.wait_for_selector("li[role='option'], .MuiAutocomplete-option", timeout=1500)
                                    option_locator = page.locator("li[role='option'], .MuiAutocomplete-option")
                                    count = option_locator.count()
                                    if count > 0:
                                        for idx in range(count):
                                            opt = option_locator.nth(idx)
                                            opt_text = opt.inner_text().strip()
                                            opt_norm = re.sub(r'[^a-z0-9]', '', opt_text.lower())
                                            
                                            dist = levenshtein_distance(val_norm, opt_norm)
                                            max_len = max(len(val_norm), len(opt_norm))
                                            sim = 1.0 - (dist / max_len) if max_len > 0 else 0.0
                                            
                                            if opt_norm == val_norm or val_norm in opt_norm or opt_norm in val_norm or sim >= 0.65:
                                                opt.click()
                                                print(f"Clicked filtered option matching '{value}': '{opt_text}'")
                                                matched = True
                                                break
                                        if not matched:
                                            option_locator.first.click()
                                            print(f"Clicked first filtered option for '{value}'")
                                    else:
                                        page.keyboard.press("Enter")
                            except Exception as autocomplete_err:
                                print(f"Autocomplete click option error: {autocomplete_err}. Fallback: typing value and enter.")
                                elem.fill(value)
                                page.wait_for_timeout(300)
                                page.keyboard.press("Enter")
                                
                            # If we filled country or state, wait for cascading sub-options to load
                            selector_lower = selector.lower()
                            if "country" in selector_lower or "state" in selector_lower:
                                print("Waiting for dynamic sub-options to load...")
                                page.wait_for_timeout(1000)
                        else:
                            elem.click()
                            elem.fill("")
                            page.keyboard.type(value, delay=50)
                            
                        result["filled"].append(selector)
                except Exception as ex:
                    err_msg = f"Failed to fill selector '{selector}': {str(ex)}"
                    print(err_msg)
                    result["errors"].append(err_msg)
            
            # --- Auto-click Submit Button ---
            submit_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "#submit_btn",
                "#submit",
                ".btn-submit",
                "button:has-text('Submit')",
                "button:has-text('Confirm')",
                "button:has-text('Save')",
                "button:has-text('Create')" # Added 'Create' for ERP form
            ]
            
            submit_clicked = False
            for sub_sel in submit_selectors:
                try:
                    elem = page.locator(sub_sel).first
                    if elem and elem.is_visible():
                        elem.click()
                        submit_clicked = True
                        print(f"Auto-clicked submit button using selector: {sub_sel}")
                        break
                except Exception:
                    pass
            
            if submit_clicked:
                try:
                    page.wait_for_load_state("networkidle", timeout=5000)
                except Exception:
                    pass
                page.wait_for_timeout(4000)
                
                # Verify submission success
                success_status, err_msg = self._verify_submission_success(page, url)
                if not success_status:
                    result["success"] = False
                    result["errors"].append(err_msg)
            else:
                page.wait_for_timeout(1000)

            # Save screenshot
            os.makedirs(os.path.dirname(screenshot_path), exist_ok=True)
            page.screenshot(path=screenshot_path)
            browser.close()
            
        if len(result["errors"]) > 0:
            result["success"] = False
            
        return result

    def fill_form_bulk(
        self, 
        url: str, 
        records: List[Dict[str, Any]], 
        mapping_engine: Any, 
        db: Any, 
        screenshot_dir: str
    ) -> Dict[str, Any]:
        """
        Loops through all records, navigating to the form URL for each record,
        filling the fields, submitting the form, and repeating.
        """
        result = {"success": True, "results": [], "errors": []}
        auth_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "auth.json")
        
        with sync_playwright() as p:
            has_auth = os.path.exists(auth_path)
            run_headless = self.headless if has_auth else False
            browser = p.chromium.launch(headless=run_headless)
            
            if has_auth:
                print(f"Loading saved session cookies from {auth_path}...")
                context = browser.new_context(storage_state=auth_path)
            else:
                context = browser.new_context()
                
            page = context.new_page()
            
            # --- Check Login (Similar to single fill) ---
            try:
                page.goto(url, wait_until="load", timeout=30000)
            except Exception as e:
                print(f"Initial page load warning: {e}")
                
            is_logged_in = False
            if has_auth:
                try:
                    page.wait_for_selector("input:not([type='hidden']), textarea, select", timeout=4000)
                    inputs_count = len(page.query_selector_all("input:not([type='hidden']), textarea, select"))
                    has_password = page.query_selector("input[type='password']") is not None
                    if has_password and inputs_count <= 3:
                        is_logged_in = False
                    else:
                        is_logged_in = True
                except Exception:
                    is_logged_in = False
            
            if not is_logged_in:
                if run_headless:
                    page.close()
                    context.close()
                    browser.close()
                    browser = p.chromium.launch(headless=False)
                    context = browser.new_context()
                    page = context.new_page()
                    try:
                        page.goto(url, wait_until="load", timeout=30000)
                    except Exception as e:
                        print(f"Page load warning on relaunch: {e}")
                
                print("Waiting for login to complete and form to load...")
                logged_in = False
                for _ in range(60):
                    has_password = page.query_selector("input[type='password']") is not None
                    inputs = page.query_selector_all("input:not([type='hidden']), textarea, select")
                    if not has_password and len(inputs) > 2:
                        logged_in = True
                        break
                    page.wait_for_timeout(1000)
                
                context.storage_state(path=auth_path)
                print(f"Saved authenticated session state.")

            # --- Now we loop through the records ---
            for record_idx, record in enumerate(records):
                print(f"Bulk Autofill: Processing record {record_idx + 1}/{len(records)} ({record.get('full_name', 'Unnamed')})")
                
                # Navigate to the form URL for this record
                try:
                    page.goto(url, wait_until="load", timeout=30000)
                    # Wait for form inputs to render
                    page.wait_for_selector("input:not([type='hidden']), textarea, select", timeout=10000)
                    
                    # Ensure more than 2 inputs have rendered dynamically (since the form loads fields asynchronously)
                    for _ in range(20):
                        inputs = page.query_selector_all("input:not([type='hidden']), textarea, select")
                        if len(inputs) > 2:
                            break
                        page.wait_for_timeout(300)
                except Exception as e:
                    err_msg = f"Failed to navigate to form for record {record_idx + 1}: {str(e)}"
                    result["results"].append({"record_index": record_idx, "success": False, "errors": [err_msg]})
                    result["errors"].append(err_msg)
                    continue

                # Inject resolveInputLabel function
                page.evaluate(JS_RESOLVER_DEFINITION)
                
                # Scan inputs
                elements = page.query_selector_all("input, textarea, select")
                form_fields = []
                for index, elem in enumerate(elements):
                    try:
                        elem_type = elem.get_attribute("type") or "text"
                        elem_name = elem.get_attribute("name") or ""
                        elem_id = elem.get_attribute("id") or ""
                        elem_placeholder = elem.get_attribute("placeholder") or ""
                        
                        if elem_type in ("hidden", "submit", "button", "image", "radio", "password"):
                            continue
                            
                        # Skip disabled
                        is_disabled = elem.is_disabled() or elem.evaluate("el => el.disabled") or elem.evaluate("el => el.classList.contains('Mui-disabled')")
                        if is_disabled:
                            continue
                            
                        label_text = page.evaluate("window.resolveInputLabel", elem).strip()
                        if not label_text:
                            label_text = page.evaluate(
                                "(elem) => { let parent = elem.parentElement; if (!parent) return ''; return parent.innerText.replace(elem.innerText, '').trim().split('\\n')[0]; }",
                                elem
                            ).replace('\u200b', '').replace('\u200c', '').strip().rstrip(":")
                        
                        if label_text.lower() in ("customer code", "customercode", "gold & silver rate", "rate"):
                            continue
                            
                        selector = ""
                        if label_text:
                            selector = f"label:{label_text}"
                        elif elem_id:
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
                            "label": label_text or elem_name or elem_id,
                            "selector": selector
                        })
                    except Exception:
                        pass

                # Map fields
                mapped_selectors = mapping_engine.map_fields(record, form_fields, db)
                if not mapped_selectors:
                    err_msg = f"No matching fields aligned for record {record_idx + 1}."
                    result["results"].append({"record_index": record_idx, "success": False, "errors": [err_msg]})
                    result["errors"].append(err_msg)
                    continue

                # Fill fields
                # Sort selectors to handle cascading dropdowns (Country -> State -> District -> others)
                def get_fill_priority(sel):
                    sel_lower = sel.lower()
                    if "country" in sel_lower: return 1
                    if "state" in sel_lower: return 2
                    if "district" in sel_lower or "city" in sel_lower: return 3
                    return 4
                    
                sorted_selectors = sorted(mapped_selectors.items(), key=lambda x: get_fill_priority(x[0]))
                
                record_errors = []
                filled_selectors = []
                
                for selector, value in sorted_selectors:
                    if not value:
                        continue
                    
                    # Clean mobile numbers
                    selector_lower = selector.lower()
                    if any(kw in selector_lower for kw in ["mobile", "phone", "contact", "tel"]):
                        if isinstance(value, str):
                            cleaned_val = value.strip()
                            if cleaned_val.startswith("+91"):
                                cleaned_val = cleaned_val[3:].strip()
                            elif cleaned_val.startswith("91") and len(cleaned_val) > 10:
                                cleaned_val = cleaned_val[2:].strip()
                            cleaned_val = "".join(c for c in cleaned_val if c.isdigit())
                            value = cleaned_val
                    
                    try:
                        elem = None
                        if selector.startswith("label:"):
                            label_name = selector.split(":", 1)[1]
                            elem_handle = page.evaluate_handle(
                                """(labelName) => {
                                    let inputs = document.querySelectorAll("input, textarea, select");
                                    for (let elem of inputs) {
                                        if (window.resolveInputLabel(elem).toLowerCase() === labelName.toLowerCase()) {
                                            return elem;
                                        }
                                    }
                                    return null;
                                }""",
                                label_name
                            )
                            if elem_handle and elem_handle.as_element():
                                elem = elem_handle.as_element()
                        else:
                            elem = page.wait_for_selector(selector, timeout=5000)
                            
                        if elem:
                            tag_name = elem.evaluate("e => e.tagName.toLowerCase()")
                            elem_type = elem.get_attribute("type") or ""
                            class_attr = elem.get_attribute("class") or ""
                            role_attr = elem.get_attribute("role") or ""
                            
                            if tag_name == "select":
                                elem.select_option(value=value)
                            elif elem_type == "checkbox":
                                if value.lower() in ("true", "yes", "checked", "1"):
                                    elem.check()
                            elif role_attr == "combobox" or "MuiAutocomplete-input" in class_attr:
                                elem.click()
                                page.wait_for_timeout(300)
                                
                                page.wait_for_selector("li[role='option'], .MuiAutocomplete-option", timeout=2000)
                                option_locator = page.locator("li[role='option'], .MuiAutocomplete-option")
                                count = option_locator.count()
                                matched = False
                                val_norm = re.sub(r'[^a-z0-9]', '', value.lower())
                                
                                # Exact match
                                for idx in range(count):
                                    opt = option_locator.nth(idx)
                                    opt_text = opt.inner_text().strip()
                                    opt_norm = re.sub(r'[^a-z0-9]', '', opt_text.lower())
                                    if opt_norm == val_norm:
                                        opt.click()
                                        matched = True
                                        break
                                        
                                # Substring match
                                if not matched:
                                    for idx in range(count):
                                        opt = option_locator.nth(idx)
                                        opt_text = opt.inner_text().strip()
                                        opt_norm = re.sub(r'[^a-z0-9]', '', opt_text.lower())
                                        if val_norm in opt_norm or opt_norm in val_norm:
                                            opt.click()
                                            matched = True
                                            break
                                            
                                # Fuzzy Levenshtein match
                                if not matched:
                                    best_opt = None
                                    best_sim = 0.0
                                    best_text = ""
                                    for idx in range(count):
                                        opt = option_locator.nth(idx)
                                        opt_text = opt.inner_text().strip()
                                        opt_norm = re.sub(r'[^a-z0-9]', '', opt_text.lower())
                                        dist = levenshtein_distance(val_norm, opt_norm)
                                        max_len = max(len(val_norm), len(opt_norm))
                                        sim = 1.0 - (dist / max_len) if max_len > 0 else 0.0
                                        if sim > best_sim:
                                            best_sim = sim
                                            best_opt = opt
                                            best_text = opt_text
                                            
                                    if best_sim >= 0.65:
                                        best_opt.click()
                                        matched = True
                                        
                                if not matched:
                                    elem.fill(value)
                                    page.wait_for_timeout(500)
                                    page.wait_for_selector("li[role='option'], .MuiAutocomplete-option", timeout=1500)
                                    option_locator = page.locator("li[role='option'], .MuiAutocomplete-option")
                                    count = option_locator.count()
                                    if count > 0:
                                        for idx in range(count):
                                            opt = option_locator.nth(idx)
                                            opt_text = opt.inner_text().strip()
                                            opt_norm = re.sub(r'[^a-z0-9]', '', opt_text.lower())
                                            dist = levenshtein_distance(val_norm, opt_norm)
                                            max_len = max(len(val_norm), len(opt_norm))
                                            sim = 1.0 - (dist / max_len) if max_len > 0 else 0.0
                                            if opt_norm == val_norm or val_norm in opt_norm or opt_norm in val_norm or sim >= 0.65:
                                                opt.click()
                                                matched = True
                                                break
                                        if not matched:
                                            option_locator.first.click()
                                    else:
                                        page.keyboard.press("Enter")
                                
                                # Wait for dynamic sub-options
                                if "country" in selector_lower or "state" in selector_lower:
                                    page.wait_for_timeout(1000)
                            else:
                                elem.click()
                                elem.fill("")
                                page.keyboard.type(value, delay=50)
                                
                            filled_selectors.append(selector)
                    except Exception as ex:
                        record_errors.append(f"Failed to fill selector '{selector}': {str(ex)}")

                # --- Auto-click Create/Submit Button ---
                submit_selectors = [
                    "button[type='submit']",
                    "input[type='submit']",
                    "#submit_btn",
                    "#submit",
                    ".btn-submit",
                    "button:has-text('Submit')",
                    "button:has-text('Confirm')",
                    "button:has-text('Save')",
                    "button:has-text('Create')"
                ]
                submit_clicked = False
                for sub_sel in submit_selectors:
                    try:
                        elem = page.locator(sub_sel).first
                        if elem and elem.is_visible():
                            elem.click()
                            submit_clicked = True
                            print(f"Auto-clicked submit/create button for record {record_idx + 1}.")
                            break
                    except Exception:
                        pass
                
                if submit_clicked:
                    try:
                        page.wait_for_load_state("networkidle", timeout=5000)
                    except Exception:
                        pass
                    page.wait_for_timeout(4000)
                    
                    # Verify submission success
                    success_status, err_msg = self._verify_submission_success(page, url)
                    if not success_status:
                        record_errors.append(err_msg)
                else:
                    page.wait_for_timeout(1000)

                # Capture verification screenshot of each record submission
                rec_screenshot_filename = f"screenshot_bulk_{record_idx}.png"
                rec_screenshot_path = os.path.join(screenshot_dir, rec_screenshot_filename)
                try:
                    page.screenshot(path=rec_screenshot_path)
                except Exception:
                    pass

                result["results"].append({
                    "record_index": record_idx,
                    "success": len(record_errors) == 0,
                    "filled_fields": filled_selectors,
                    "errors": record_errors
                })
                
            browser.close()
            
        return result
