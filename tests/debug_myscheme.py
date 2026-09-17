from playwright.sync_api import sync_playwright


BASE_URL = "https://search.myscheme.gov.in/"


def print_basic_page(page, title):
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)

    print("\nURL:")
    print(page.url)

    print("\n--- BODY ---")
    print(page.locator("body").inner_text())


def print_inputs(page):
    print("\n--- INPUTS ---")

    inputs = page.locator("input")

    print(f"COUNT: {inputs.count()}")

    for i in range(inputs.count()):
        el = inputs.nth(i)

        print(
            f"[{i}] "
            f"type={el.get_attribute('type')} "
            f"name={el.get_attribute('name')} "
            f"value={el.get_attribute('value')} "
            f"id={el.get_attribute('id')} "
            f"placeholder={el.get_attribute('placeholder')} "
            f"aria={el.get_attribute('aria-label')}"
        )


def print_selects(page):
    print("\n--- SELECTS ---")

    selects = page.locator("select")

    print(f"COUNT: {selects.count()}")

    for i in range(selects.count()):
        el = selects.nth(i)

        print(
            f"[{i}] "
            f"name={el.get_attribute('name')} "
            f"id={el.get_attribute('id')}"
        )

        try:
            options = el.locator("option")

            for j in range(options.count()):
                option = options.nth(j)

                print(
                    f"    [{j}] "
                    f"text={option.inner_text().strip()} "
                    f"value={option.get_attribute('value')}"
                )
        except Exception:
            pass


def print_buttons(page):
    print("\n--- BUTTONS ---")

    buttons = page.locator("button")

    print(f"COUNT: {buttons.count()}")

    for i in range(buttons.count()):
        el = buttons.nth(i)

        try:
            text = el.inner_text().strip()
        except Exception:
            text = ""

        print(
            f"[{i}] "
            f"text='{text}' "
            f"type={el.get_attribute('type')} "
            f"aria={el.get_attribute('aria-label')}"
        )


def print_full_state(page, title):
    print_basic_page(page, title)
    print_inputs(page)
    print_selects(page)
    print_buttons(page)


def click_visible_text(page, text):
    """
    Click visible text instead of hidden sr-only radio inputs.
    """
    locator = page.get_by_text(text, exact=True)

    for i in range(locator.count()):
        element = locator.nth(i)

        try:
            if element.is_visible():
                element.click()
                return True
        except Exception:
            pass

    return False


def click_button(page, text=None, aria=None):
    """
    Safely click a visible button.
    """

    if aria:
        locator = page.get_by_role("button", name=aria)

        for i in range(locator.count()):
            element = locator.nth(i)

            try:
                if element.is_visible():
                    element.click()
                    return True
            except Exception:
                pass

    if text:
        locator = page.get_by_role("button", name=text)

        for i in range(locator.count()):
            element = locator.nth(i)

            try:
                if element.is_visible():
                    element.click()
                    return True
            except Exception:
                pass

    return False


def wait_for_page_update(page):
    page.wait_for_timeout(1800)


def inspect_income_fields(page):
    print("\n" + "=" * 70)
    print("INCOME FIELD INSPECTION")
    print("=" * 70)

    # Find text inputs currently on the page.
    inputs = page.locator('input[type="text"]')

    print(f"\nText inputs found: {inputs.count()}")

    for i in range(inputs.count()):

        el = inputs.nth(i)

        print("\n" + "-" * 70)
        print(f"TEXT INPUT [{i}]")
        print("-" * 70)

        print("\nAttributes:")
        print("type       =", el.get_attribute("type"))
        print("name       =", el.get_attribute("name"))
        print("id         =", el.get_attribute("id"))
        print("placeholder=", el.get_attribute("placeholder"))
        print("aria-label =", el.get_attribute("aria-label"))
        print("value      =", el.input_value())

        print("\nOUTER HTML:")
        try:
            print(
                el.evaluate(
                    "(e) => e.outerHTML"
                )
            )
        except Exception as e:
            print("ERROR:", e)

        print("\nPARENT HTML:")
        try:
            print(
                el.evaluate(
                    "(e) => e.parentElement.outerHTML"
                )
            )
        except Exception as e:
            print("ERROR:", e)

        print("\nGRANDPARENT HTML:")
        try:
            print(
                el.evaluate(
                    "(e) => e.parentElement.parentElement.outerHTML"
                )
            )
        except Exception as e:
            print("ERROR:", e)

        print("\nNEARBY TEXT:")
        try:
            text = el.evaluate(
                """
                (e) => {
                    let p = e.parentElement;

                    if (!p) {
                        return "";
                    }

                    return p.innerText;
                }
                """
            )

            print(text)

        except Exception as e:
            print("ERROR:", e)

        print("\nANCESTOR TEXT:")
        try:
            text = el.evaluate(
                """
                (e) => {
                    let p = e.parentElement;

                    for (let i = 0; i < 3 && p; i++) {
                        if (p.innerText && p.innerText.trim().length > 0) {
                            return p.innerText;
                        }

                        p = p.parentElement;
                    }

                    return "";
                }
                """
            )

            print(text)

        except Exception as e:
            print("ERROR:", e)


def main():

    with sync_playwright() as p:

        browser = p.chromium.launch(
            headless=False
        )

        page = browser.new_page(
            viewport={
                "width": 1440,
                "height": 1000
            }
        )

        # =========================================================
        # HOME
        # =========================================================

        print("Opening myScheme...")

        page.goto(
            BASE_URL,
            wait_until="domcontentloaded",
            timeout=60000
        )

        page.wait_for_timeout(3000)

        print("\nHOME:")
        print(page.url)

        # Find Schemes For You
        find_button = page.get_by_text(
            "Find Schemes For You",
            exact=True
        )

        clicked = False

        for i in range(find_button.count()):

            try:
                if find_button.nth(i).is_visible():
                    find_button.nth(i).click()
                    clicked = True
                    break
            except Exception:
                pass

        if not clicked:
            print("Could not find 'Find Schemes For You'.")
            browser.close()
            return

        page.wait_for_timeout(2000)

        # =========================================================
        # SCREEN 1
        # =========================================================

        print_full_state(
            page,
            "SCREEN 1 - GENDER + AGE"
        )

        print("\nMANUAL:")
        print("1. Select the gender you want.")
        print("2. Select the age you want.")
        print("3. Click Next.")

        input(
            "\nPress ENTER after Screen 2 appears..."
        )

        # =========================================================
        # SCREEN 2
        # =========================================================

        print_full_state(
            page,
            "SCREEN 2 - STATE + RESIDENCE"
        )

        print("\nMANUAL:")
        print("1. Select your state.")
        print("2. Select Urban or Rural.")
        print("3. Click Next.")

        input(
            "\nPress ENTER after the caste screen appears..."
        )

        # =========================================================
        # SCREEN 3
        # =========================================================

        print_full_state(
            page,
            "SCREEN 3 - CASTE"
        )

        print("\nMANUAL:")
        print("Select the required caste/category.")
        print("Then click Next.")

        input(
            "\nPress ENTER after the disability screen appears..."
        )

        # =========================================================
        # DYNAMIC SCREEN
        # =========================================================

        print_full_state(
            page,
            "DYNAMIC SCREEN"
        )

        print(
            """
MANUAL:

Continue answering the questions as appropriate.

If the disability question appears:
    answer it.

If a minority question appears:
    answer it.

Continue until:
    "Are you a student?"

appears.
"""
        )

        input(
            "\nPress ENTER when the student question is visible..."
        )

        # =========================================================
        # STUDENT
        # =========================================================

        print_full_state(
            page,
            "STUDENT QUESTION"
        )

        print(
            """
MANUAL:

Select YES for:

    Are you a student?

Then click Next.
"""
        )

        input(
            "\nPress ENTER when the BPL screen appears..."
        )

        # =========================================================
        # BPL SCREEN
        # =========================================================

        print_full_state(
            page,
            "BPL SCREEN"
        )

        print(
            """
AUTOMATIC STEP:

We will now select:

    BPL = No

This is necessary because the income fields are
conditionally displayed after the BPL answer.
"""
        )

        # Find the actual radio by name/value.
        bpl_no = page.locator(
            'input[type="radio"][name="isBpl"][value="No"]'
        )

        if bpl_no.count() == 0:

            print(
                "\nERROR: Could not find BPL = No radio."
            )

            print(
                "\nPress ENTER to close browser..."
            )

            input()
            browser.close()
            return

        try:

            # The radio itself may be hidden.
            # Clicking the associated label/text is safer.
            bpl_no_id = bpl_no.first.get_attribute("id")

            print(
                "\nBPL No radio ID:",
                bpl_no_id
            )

            clicked = False

            if bpl_no_id:

                label = page.locator(
                    f'label[for="{bpl_no_id}"]'
                )

                if label.count() > 0:

                    try:
                        label.first.click()
                        clicked = True
                    except Exception:
                        pass

            if not clicked:

                clicked = click_visible_text(
                    page,
                    "No"
                )

            if not clicked:

                print(
                    "\nWARNING: Could not click BPL No visually."
                )

                print(
                    "Trying radio.check(force=True)..."
                )

                bpl_no.first.check(
                    force=True
                )

        except Exception as e:

            print(
                "\nERROR selecting BPL No:"
            )

            print(e)

        page.wait_for_timeout(1000)

        # =========================================================
        # SUBMIT BPL
        # =========================================================

        print(
            "\nBPL selection completed."
        )

        print(
            "Clicking Submit..."
        )

        submit = page.get_by_role(
            "button",
            name="Next"
        )

        if submit.count() == 0:

            submit = page.locator(
                'button[type="submit"]'
            )

        clicked = False

        for i in range(submit.count()):

            try:

                if submit.nth(i).is_visible():

                    submit.nth(i).click()

                    clicked = True
                    break

            except Exception:
                pass

        if not clicked:

            print(
                "\nERROR: Could not click Submit/Next."
            )

            print(
                "\nPress ENTER to close browser..."
            )

            input()
            browser.close()
            return

        # Give React time to render the next screen.
        page.wait_for_timeout(2500)

        # =========================================================
        # AFTER BPL
        # =========================================================

        print_full_state(
            page,
            "SCREEN AFTER BPL = NO"
        )

        # =========================================================
        # INCOME FIELDS
        # =========================================================

        inspect_income_fields(page)

        # =========================================================
        # SCREENSHOT
        # =========================================================

        screenshot_path = (
            "tests/myscheme_income_after_bpl_no.png"
        )

        page.screenshot(
            path=screenshot_path,
            full_page=True
        )

        print("\n" + "=" * 70)
        print("SCREENSHOT")
        print("=" * 70)

        print(
            f"Saved: {screenshot_path}"
        )

        # =========================================================
        # PAUSE
        # =========================================================

        print("\n" + "=" * 70)
        print("DEBUGGING PAUSED")
        print("=" * 70)

        print(
            """
Do NOT enter any income values.

The important information is the HTML printed above.

Press ENTER to close the browser.
"""
        )

        input()

        browser.close()


if __name__ == "__main__":
    main()