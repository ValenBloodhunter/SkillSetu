from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import requests
from bs4 import BeautifulSoup

from playwright.sync_api import (
    Page,
    TimeoutError as PlaywrightTimeoutError,
    sync_playwright,
)


# ============================================================
# CONFIG
# ============================================================

MYSCHEME_HOME_URL = "https://www.myscheme.gov.in/"
MYSCHEME_SEARCH_URL = "https://search.myscheme.gov.in/"

REQUEST_TIMEOUT = 30_000
QUESTION_TIMEOUT = 5_000
MAX_QUESTION_STEPS = 20

# These are the profile fields that SkillSetu may provide to
# myScheme. Do not invent values for fields that are missing.
QUESTION_FIELDS = {
    "gender",
    "age",
    "marital_status",
    "state",
    "residence",
    "caste",
    "disability",
    "minority",
    "is_student",
    "is_bpl",
    "annual_family_income",
    "annual_parent_income",
}


# ============================================================
# BASIC HELPERS
# ============================================================

def _clean_text(value: Any) -> str:
    """Normalize whitespace and convert a value to text."""

    if value is None:
        return ""

    text = str(value)

    return " ".join(text.split()).strip()


def _now_iso() -> str:
    """Return the current UTC timestamp."""

    return datetime.now(timezone.utc).isoformat()


def _normalise_key(value: Any) -> str:
    """Normalize text for case-insensitive comparisons."""

    return _clean_text(value).lower()


def _get_profile_value(
    profile: dict[str, Any],
    *keys: str,
) -> Any:
    """
    Return the first available profile value.

    This allows the profile to use aliases such as:
    state/location.
    """

    for key in keys:
        if key in profile:
            value = profile[key]

            if value is not None and _clean_text(value) != "":
                return value

    return None


# ============================================================
# PROFILE NORMALIZATION
# ============================================================

def _normalise_profile(
    profile: dict[str, Any],
) -> dict[str, Any]:
    """
    Normalize SkillSetu profile fields without inventing data.
    """

    normalized = dict(profile or {})

    # Location/state aliases
    if "state" not in normalized and "location" in normalized:
        normalized["state"] = normalized["location"]

    if "location" not in normalized and "state" in normalized:
        normalized["location"] = normalized["state"]

    # Student aliases
    if "is_student" not in normalized:
        if "student" in normalized:
            normalized["is_student"] = normalized["student"]

    # BPL aliases
    if "is_bpl" not in normalized:
        if "bpl" in normalized:
            normalized["is_bpl"] = normalized["bpl"]

    # Disability aliases
    if "disability" not in normalized:
        if "has_disability" in normalized:
            normalized["disability"] = normalized["has_disability"]

    # Minority aliases
    if "minority" not in normalized:
        if "is_minority" in normalized:
            normalized["minority"] = normalized["is_minority"]

    return normalized


# ============================================================
# PROFILE → MYSCHEME ANSWER
# ============================================================

def _profile_answer(
    profile: dict[str, Any],
    field_name: str,
) -> Any:
    """
    Get the answer for a myScheme questionnaire field.

    Returns None when SkillSetu does not have enough information.
    """

    profile = _normalise_profile(profile)

    aliases: dict[str, tuple[str, ...]] = {
        "gender": (
            "gender",
        ),
        "age": (
            "age",
        ),
        "marital_status": (
            "marital_status",
            "marital",
        ),
        "state": (
            "state",
            "location",
        ),
        "residence": (
            "residence",
            "residence_type",
        ),
        "caste": (
            "caste",
            "category",
        ),
        "disability": (
            "disability",
            "has_disability",
        ),
        "minority": (
            "minority",
            "is_minority",
        ),
        "is_student": (
            "is_student",
            "student",
        ),
        "is_bpl": (
            "is_bpl",
            "bpl",
        ),
        "annual_family_income": (
            "annual_family_income",
            "family_income",
            "annual_income",
        ),
        "annual_parent_income": (
            "annual_parent_income",
            "parent_income",
        ),
    }

    keys = aliases.get(field_name, (field_name,))

    return _get_profile_value(profile, *keys)


# ============================================================
# VISIBLE QUESTION DETECTION
# ============================================================

def _visible_question(
    page: Page,
) -> tuple[str | None, str]:
    """
    Find the next unanswered visible myScheme question.

    myScheme keeps previously answered controls visible.

    Therefore:
    - answered radio groups are skipped
    - already-selected dropdowns are skipped
    - already-filled inputs are skipped

    This prevents the questionnaire from repeatedly selecting
    the gender question.
    """

    # --------------------------------------------------------
    # 1. RADIO QUESTIONS
    # --------------------------------------------------------

    radios = page.locator(
        'input[type="radio"]:visible'
    )

    seen_radio_names: set[str] = set()

    for i in range(radios.count()):
        radio = radios.nth(i)

        try:
            name = radio.get_attribute("name")

            if not name:
                continue

            if name not in QUESTION_FIELDS:
                continue

            # Only inspect each radio group once.
            if name in seen_radio_names:
                continue

            seen_radio_names.add(name)

            # ------------------------------------------------
            # CRITICAL FIX:
            # Skip radio groups that already have an answer.
            # ------------------------------------------------

            checked = page.locator(
                f'input[type="radio"][name="{name}"]'
                ':visible:checked'
            )

            if checked.count() > 0:
                continue

            question_text = ""

            try:
                parent = radio.locator("xpath=..")
                question_text = _clean_text(
                    parent.inner_text()
                )
            except Exception:
                pass

            return name, question_text

        except Exception:
            continue

    # --------------------------------------------------------
    # 2. SELECT / DROPDOWN QUESTIONS
    # --------------------------------------------------------

    selects = page.locator(
        "select:visible"
    )

    for i in range(selects.count()):
        element = selects.nth(i)

        try:
            name = element.get_attribute("name")

            if not name:
                continue

            if name not in QUESTION_FIELDS:
                continue

            selected_value = _clean_text(
                element.input_value()
            )

            # Skip already answered dropdowns.
            if selected_value and selected_value.lower() not in {
                "",
                "0",
                "--",
                "select",
                "please select",
            }:
                continue

            question_text = ""

            try:
                parent = element.locator("xpath=..")
                question_text = _clean_text(
                    parent.inner_text()
                )
            except Exception:
                pass

            return name, question_text

        except Exception:
            continue

    # --------------------------------------------------------
    # 3. NUMBER INPUTS
    # --------------------------------------------------------

    numbers = page.locator(
        'input[type="number"]:visible'
    )

    for i in range(numbers.count()):
        element = numbers.nth(i)

        try:
            name = element.get_attribute("name")

            if not name:
                continue

            if name not in QUESTION_FIELDS:
                continue

            value = _clean_text(
                element.input_value()
            )

            if value:
                continue

            question_text = ""

            try:
                parent = element.locator("xpath=..")
                question_text = _clean_text(
                    parent.inner_text()
                )
            except Exception:
                pass

            return name, question_text

        except Exception:
            continue

    # --------------------------------------------------------
    # 4. TEXT INPUTS
    # --------------------------------------------------------

    text_inputs = page.locator(
        'input[type="text"]:visible'
    )

    for i in range(text_inputs.count()):
        element = text_inputs.nth(i)

        try:
            name = element.get_attribute("name")

            if not name:
                continue

            if name not in QUESTION_FIELDS:
                continue

            value = _clean_text(
                element.input_value()
            )

            if value:
                continue

            question_text = ""

            try:
                parent = element.locator("xpath=..")
                question_text = _clean_text(
                    parent.inner_text()
                )
            except Exception:
                pass

            return name, question_text

        except Exception:
            continue

    return None, ""


# ============================================================
# RADIO SELECTION
# ============================================================

def _click_radio_by_value(
    page: Page,
    field_name: str,
    value: str,
) -> bool:
    """
    Select a radio option by its value or associated label.
    """

    target = _normalise_key(value)

    radios = page.locator(
        f'input[type="radio"][name="{field_name}"]:visible'
    )

    for i in range(radios.count()):
        radio = radios.nth(i)

        try:
            radio_value = radio.get_attribute("value") or ""

            if _normalise_key(radio_value) == target:
                radio.check()
                return True

            # Try associated label.
            radio_id = radio.get_attribute("id")

            if radio_id:
                labels = page.locator(
                    f'label[for="{radio_id}"]:visible'
                )

                if labels.count():
                    label_text = _clean_text(
                        labels.first.inner_text()
                    )

                    if _normalise_key(label_text) == target:
                        radio.check()
                        return True

        except Exception:
            continue

    # Fallback: inspect labels near the radio.
    labels = page.locator(
        f'input[type="radio"][name="{field_name}"]:visible'
    )

    for i in range(labels.count()):
        radio = labels.nth(i)

        try:
            parent_text = _clean_text(
                radio.locator("xpath=..").inner_text()
            )

            if target == _normalise_key(parent_text):
                radio.check()
                return True

        except Exception:
            continue

    return False


# ============================================================
# SELECT / DROPDOWN
# ============================================================

def _select_value(
    page: Page,
    field_name: str,
    answer: Any,
) -> bool:
    """
    Select a dropdown value using:
    1. exact value
    2. exact label
    3. case-insensitive label/value
    4. numeric matching
    """

    select = page.locator(
        f'select[name="{field_name}"]:visible'
    )

    if select.count() == 0:
        return False

    select = select.first

    answer_text = _clean_text(answer)

    # --------------------------------------------------------
    # Exact value
    # --------------------------------------------------------

    try:
        select.select_option(value=answer_text)
        return True
    except Exception:
        pass

    # --------------------------------------------------------
    # Exact label
    # --------------------------------------------------------

    try:
        select.select_option(label=answer_text)
        return True
    except Exception:
        pass

    # --------------------------------------------------------
    # Inspect options
    # --------------------------------------------------------

    options = select.locator("option")

    target = _normalise_key(answer_text)

    for i in range(options.count()):
        option = options.nth(i)

        try:
            option_value = _clean_text(
                option.get_attribute("value")
            )

            option_label = _clean_text(
                option.inner_text()
            )

            if (
                _normalise_key(option_value) == target
                or _normalise_key(option_label) == target
            ):
                select.select_option(
                    value=option_value
                )
                return True

            # Numeric comparison.
            try:
                if float(option_value) == float(answer):
                    select.select_option(
                        value=option_value
                    )
                    return True
            except Exception:
                pass

        except Exception:
            continue

    return False


# ============================================================
# FILL INPUT
# ============================================================

def _fill_input(
    page: Page,
    field_name: str,
    answer: Any,
) -> bool:
    """
    Fill a visible text/number input.
    """

    selectors = [
        f'input[name="{field_name}"][type="number"]:visible',
        f'input[name="{field_name}"][type="text"]:visible',
        f'input[name="{field_name}"]:visible',
    ]

    for selector in selectors:
        inputs = page.locator(selector)

        if inputs.count() == 0:
            continue

        try:
            inputs.first.fill(
                _clean_text(answer)
            )
            return True
        except Exception:
            continue

    return False


# ============================================================
# ANSWER CURRENT QUESTION
# ============================================================

def _answer_current_question(
    page: Page,
    profile: dict[str, Any],
) -> bool:
    """
    Answer the currently visible myScheme question.
    """

    field_name, _ = _visible_question(page)

    if not field_name:
        return False

    answer = _profile_answer(
        profile,
        field_name,
    )

    if answer is None:
        raise ValueError(
            f"myScheme requires profile field "
            f"'{field_name}', but SkillSetu does not "
            "have it."
        )

    # --------------------------------------------------------
    # RADIO
    # --------------------------------------------------------

    radio = page.locator(
        f'input[type="radio"][name="{field_name}"]:visible'
    )

    if radio.count():
        answer_string = _clean_text(answer)

        candidates = [
            answer_string
        ]

        lowered = answer_string.lower()

        if lowered in {"yes", "true"}:
            candidates.extend([
                "Yes",
                "true",
            ])

        elif lowered in {"no", "false"}:
            candidates.extend([
                "No",
                "false",
            ])

        for candidate in candidates:
            if _click_radio_by_value(
                page,
                field_name,
                candidate,
            ):
                return True

        raise ValueError(
            f"Could not select '{answer_string}' "
            f"for myScheme field '{field_name}'."
        )

    # --------------------------------------------------------
    # SELECT
    # --------------------------------------------------------

    select = page.locator(
        f'select[name="{field_name}"]:visible'
    )

    if select.count():
        if _select_value(
            page,
            field_name,
            answer,
        ):
            return True

        raise ValueError(
            f"Could not select '{answer}' "
            f"for myScheme field '{field_name}'."
        )

    # --------------------------------------------------------
    # TEXT / NUMBER
    # --------------------------------------------------------

    if _fill_input(
        page,
        field_name,
        answer,
    ):
        return True

    raise ValueError(
        f"Could not answer visible myScheme "
        f"field '{field_name}'."
    )


# ============================================================
# NEXT / SUBMIT
# ============================================================

def _click_next(page: Page) -> bool:
    """
    Click Next or Submit.
    """

    selectors = [
        'button:has-text("Next"):visible',
        'button:has-text("Submit"):visible',
        'input[type="submit"]:visible',
    ]

    for selector in selectors:
        buttons = page.locator(selector)

        if buttons.count() == 0:
            continue

        for i in range(buttons.count()):
            button = buttons.nth(i)

            try:
                if button.is_enabled():
                    button.click()
                    return True
            except Exception:
                continue

    return False


# ============================================================
# WAIT AFTER NAVIGATION
# ============================================================

def _wait_after_navigation(page: Page) -> None:
    """
    Give the client-rendered myScheme page time to update.
    """

    try:
        page.wait_for_load_state(
            "domcontentloaded",
            timeout=QUESTION_TIMEOUT,
        )
    except Exception:
        pass

    page.wait_for_timeout(800)


# ============================================================
# EXTRACT SCHEME CARDS
# ============================================================

def _extract_scheme_cards(
    page: Page,
) -> list[dict[str, str]]:
    """
    Extract real scheme links from the myScheme results page.

    No fake schemes are generated.
    """

    cards: list[dict[str, str]] = []

    links = page.locator(
        'a[href*="/schemes/"]'
    )

    seen_urls: set[str] = set()

    for i in range(links.count()):
        link = links.nth(i)

        try:
            href = link.get_attribute("href")

            if not href:
                continue

            if href.startswith("/"):
                url = (
                    "https://www.myscheme.gov.in"
                    + href
                )
            else:
                url = href

            if "/schemes/" not in url:
                continue

            if url in seen_urls:
                continue

            seen_urls.add(url)

            title = _clean_text(
                link.inner_text()
            )

            # Some cards have the title in a parent.
            if not title:
                try:
                    title = _clean_text(
                        link.locator(
                            "xpath=.."
                        ).inner_text()
                    )
                except Exception:
                    pass

            if not title:
                title = "Government scheme"

            cards.append({
                "scheme_name": title,
                "url": url,
            })

        except Exception:
            continue

    return cards


# ============================================================
# PARSE INDIVIDUAL SCHEME
# ============================================================

def _parse_scheme_page(
    page: Page,
    url: str,
    state: str,
) -> dict[str, Any] | None:
    """
    Parse an official myScheme scheme page.

    Information is taken from the live page only.
    """

    try:
        title = _clean_text(
            page.locator("h1").first.inner_text()
        )
    except Exception:
        title = ""

    if not title:
        try:
            title = _clean_text(
                page.title()
            )
        except Exception:
            title = ""

    body_text = ""

    try:
        body_text = _clean_text(
            page.locator("body").inner_text()
        )
    except Exception:
        pass

    if not title and not body_text:
        return None

    # --------------------------------------------------------
    # Basic section extraction
    # --------------------------------------------------------

    description = body_text

    # Keep documents reasonably sized.
    if len(description) > 12_000:
        description = description[:12_000]

    return {
        "scheme_name": title or "Government scheme",
        "description": description,
        "eligibility_signals": [],
        "benefits": [],
        "application_info": "",
        "url": url,
        "source": "myScheme",
        "state": state,
        "category": "",
        "fetched_at": _now_iso(),
    }


# ============================================================
# QUESTIONNAIRE
# ============================================================

def _run_myscheme_questionnaire(
    page: Page,
    profile: dict[str, Any],
) -> list[dict[str, str]]:
    """
    Drive the live myScheme questionnaire until results appear.

    The questionnaire is dynamic. Do not rely on fixed screen
    numbers because later questions depend on earlier answers.
    """

    profile = _normalise_profile(profile)

    print(
        "[myScheme] Opening questionnaire..."
    )

    page.goto(
        MYSCHEME_SEARCH_URL,
        wait_until="domcontentloaded",
        timeout=REQUEST_TIMEOUT,
    )

    page.wait_for_timeout(1500)

    print(
        f"[myScheme] Home URL: {page.url}"
    )

    # --------------------------------------------------------
    # Find "Find Schemes For You"
    # --------------------------------------------------------

    find_button = page.get_by_text(
        "Find Schemes For You",
        exact=True,
    )

    if find_button.count() == 0:
        # Fallback for slight text differences.
        find_button = page.get_by_text(
            "Find Schemes For You"
        )

    if find_button.count() == 0:
        raise RuntimeError(
            "Could not find myScheme "
            "'Find Schemes For You' button."
        )

    find_button.first.click()

    page.wait_for_timeout(1000)

    print(
        f"[myScheme] Questionnaire URL: {page.url}"
    )

    # --------------------------------------------------------
    # Dynamic questionnaire loop
    # --------------------------------------------------------

    for step in range(1, MAX_QUESTION_STEPS + 1):

        page.wait_for_timeout(500)

        # Results page reached.
        if "/search/user-journey" in page.url:
            print(
                "[myScheme] Results page reached."
            )

            cards = _extract_scheme_cards(page)

            print(
                f"[myScheme] Found {len(cards)} scheme links."
            )

            return cards

        field_name, question_text = (
            _visible_question(page)
        )

        print(
            f"[myScheme] Step {step}: "
            f"url={page.url} | "
            f"field={field_name} | "
            f"question={question_text[:120]}"
        )

        if not field_name:
            raise RuntimeError(
                "myScheme reached an unknown "
                f"questionnaire state: {page.url}"
            )

        # Answer current question.
        _answer_current_question(
            page,
            profile,
        )

        # Click Next/Submit.
        if not _click_next(page):
            raise RuntimeError(
                "Could not find Next/Submit after "
                f"answering '{field_name}'."
            )

        _wait_after_navigation(page)

    raise RuntimeError(
        "myScheme questionnaire exceeded the "
        f"safety limit of {MAX_QUESTION_STEPS} steps."
    )


# ============================================================
# PUBLIC API
# ============================================================

def fetch_schemes(
    profile: dict[str, Any],
) -> list[dict[str, Any]]:
    """
    Fetch live government schemes from official myScheme.

    Returns normalized scheme documents.

    No fake schemes are generated.

    If the live source cannot be queried, an empty list
    is returned.
    """

    profile = _normalise_profile(profile)

    print("[myScheme] fetch_schemes() started.")

    try:
        with sync_playwright() as playwright:

            print("[myScheme] Launching Chromium...")

            browser = playwright.chromium.launch(
                headless=True
            )

            try:
                page = browser.new_page(
                    viewport={
                        "width": 1440,
                        "height": 1000,
                    }
                )

                cards = _run_myscheme_questionnaire(
                    page,
                    profile,
                )

                print(
                    f"[myScheme] Questionnaire returned "
                    f"{len(cards)} cards."
                )

                if not cards:
                    print(
                        "[myScheme] No scheme cards found."
                    )
                    return []

                state = _clean_text(
                    _get_profile_value(
                        profile,
                        "state",
                        "location",
                    )
                    or ""
                )

                schemes: list[
                    dict[str, Any]
                ] = []

                # Limit detailed page retrieval for
                # hackathon/demo performance.
                for index, card in enumerate(
                    cards[:30],
                    start=1,
                ):

                    url = card.get("url", "")

                    if not url:
                        continue

                    print(
                        f"[myScheme] Fetching scheme "
                        f"{index}/{min(len(cards), 30)}: "
                        f"{url}"
                    )

                    try:
                        page.goto(
                            url,
                            wait_until="domcontentloaded",
                            timeout=REQUEST_TIMEOUT,
                        )

                        page.wait_for_timeout(800)

                        scheme = _parse_scheme_page(
                            page,
                            url,
                            state,
                        )

                        if scheme:
                            schemes.append(
                                scheme
                            )

                    except PlaywrightTimeoutError as exc:
                        print(
                            "[myScheme] Timeout: "
                            f"{url} | {exc}"
                        )
                        continue

                    except Exception as exc:
                        print(
                            "[myScheme] Could not parse "
                            f"{url}: {exc}"
                        )
                        continue

                print(
                    f"[myScheme] Returning "
                    f"{len(schemes)} schemes."
                )

                return schemes

            finally:
                browser.close()

    except Exception as exc:
        print(
            "[myScheme] ERROR in fetch_schemes(): "
            f"{type(exc).__name__}: {exc}"
        )

        return []


# ============================================================
# LOCAL TEST
# ============================================================

if __name__ == "__main__":

    test_profile = {
        "persona": "student",
        "name": "Test Student",
        "state": "Andhra Pradesh",
        "location": "Andhra Pradesh",
        "gender": "Male",
        "age": 18,
        "residence": "Rural",
        "caste": "SC",
        "disability": "No",
        "minority": "No",
        "is_student": "Yes",
        "is_bpl": "No",
    }

    print("=" * 60)
    print("SkillSetu myScheme live test")
    print("=" * 60)

    results = fetch_schemes(
        test_profile
    )

    print()
    print(
        f"RESULT COUNT: {len(results)}"
    )

    for i, scheme in enumerate(
        results[:5],
        start=1,
    ):
        print()
        print(
            f"{i}. "
            f"{scheme.get('scheme_name', '')}"
        )
        print(
            f"   URL: "
            f"{scheme.get('url', '')}"
        )
        print(
            f"   Source: "
            f"{scheme.get('source', '')}"
        )
        print(
            f"   State: "
            f"{scheme.get('state', '')}"
        )