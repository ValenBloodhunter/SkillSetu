"""
Live myScheme integration for SkillSetu.

Important:
- Schemes are NOT hardcoded.
- Questionnaire answers come from the user's profile.
- Only official myScheme URLs are accepted.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright


MYSCHEME_SEARCH_URL = (
    "https://search.myscheme.gov.in/"
)

MYSCHEME_BASE_URL = (
    "https://www.myscheme.gov.in/"
)

SOURCE_NAME = "myScheme"


OFFICIAL_HOSTS = {
    "myscheme.gov.in",
    "www.myscheme.gov.in",
    "search.myscheme.gov.in",
}


QUESTION_FIELDS = {
    "gender",
    "age",
    "maritalStatus",
    "state",
    "residence",
    "caste",
    "disability",
    "minority",
    "isStudent",
    "employmentStatus",
    "isBpl",
    "isEconomicDistress",
    "annualFamilyIncome",
    "annualParentIncome",
}


def _clean(value: Any) -> str:
    if value is None:
        return ""

    return " ".join(
        str(value).split()
    ).strip()


def _normal(value: Any) -> str:
    return _clean(value).lower()


def _now():
    return datetime.now(
        timezone.utc
    ).isoformat()


def _profile_value(
    profile,
    *keys,
):
    for key in keys:
        if key not in profile:
            continue

        value = profile[key]

        if value is not None and value != "":
            return value

    return None


def _normalise_profile(profile):
    profile = dict(
        profile or {}
    )

    aliases = {
        "sex": "gender",
        "marital": "marital_status",
        "maritalStatus": "marital_status",
        "residence_type": "residence",
        "area": "residence",
        "employmentStatus": (
            "employment_status"
        ),
        "isEconomicDistress": (
            "is_economic_distress"
        ),
        "annualFamilyIncome": (
            "annual_family_income"
        ),
        "family_income": (
            "annual_family_income"
        ),
        "annualParentIncome": (
            "annual_parent_income"
        ),
        "parent_income": (
            "annual_parent_income"
        ),
    }

    for old, new in aliases.items():
        if (
            new not in profile
            and old in profile
        ):
            profile[new] = profile[old]

    profile.setdefault(
        "gender",
        "Male",
    )

    profile.setdefault(
        "age",
        18,
    )

    profile.setdefault(
        "state",
        "Andhra Pradesh",
    )

    profile.setdefault(
        "residence",
        "Rural",
    )

    profile.setdefault(
        "caste",
        "General",
    )

    profile.setdefault(
        "disability",
        "No",
    )

    profile.setdefault(
        "minority",
        "No",
    )

    profile.setdefault(
        "is_student",
        False,
    )

    profile.setdefault(
        "employment_status",
        "Unemployed",
    )

    profile.setdefault(
        "marital_status",
        "Never Married",
    )

    profile.setdefault(
        "is_bpl",
        False,
    )

    profile.setdefault(
        "is_economic_distress",
        False,
    )

    profile.setdefault(
        "annual_family_income",
        0,
    )

    profile.setdefault(
        "annual_parent_income",
        0,
    )

    return profile


def _answer_for(
    profile,
    field_name,
):
    mapping = {
        "gender": (
            "gender",
        ),

        "age": (
            "age",
        ),

        "maritalStatus": (
            "marital_status",
            "maritalStatus",
        ),

        "state": (
            "state",
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
        ),

        "minority": (
            "minority",
        ),

        "isStudent": (
            "is_student",
            "isStudent",
        ),

        "employmentStatus": (
            "employment_status",
            "employmentStatus",
        ),

        "isBpl": (
            "is_bpl",
            "isBpl",
        ),

        "isEconomicDistress": (
            "is_economic_distress",
            "isEconomicDistress",
        ),

        "annualFamilyIncome": (
            "annual_family_income",
            "annualFamilyIncome",
        ),

        "annualParentIncome": (
            "annual_parent_income",
            "annualParentIncome",
        ),
    }

    return _profile_value(
        profile,
        *mapping.get(
            field_name,
            (),
        ),
    )


def _candidate_answers(answer):
    if isinstance(
        answer,
        bool,
    ):
        return (
            ["Yes", "yes", "true"]
            if answer
            else ["No", "no", "false"]
        )

    raw = _clean(answer)

    values = [raw]

    aliases = {
        "general": [
            "General",
        ],

        "obc": [
            "OBC",
            "Other Backward Class (OBC)",
        ],

        "sc": [
            "SC",
            "Scheduled Caste (SC)",
        ],

        "st": [
            "ST",
            "Scheduled Tribe (ST)",
        ],

        "pvtg": [
            "PVTG",
            (
                "Particularly Vulnerable "
                "Tribal Group (PVTG)"
            ),
        ],

        "dnt": [
            "DNT",
            (
                "De-Notified, Nomadic, and "
                "Semi-Nomadic (DNT) communities"
            ),
        ],

        "self-employed/ entrepreneur": [
            "Self-Employed/ Entrepreneur",
            "Self-Employed/Entrepreneur",
        ],
    }

    values.extend(
        aliases.get(
            raw.lower(),
            [],
        )
    )

    return values


def _visible_radio_names(page):
    names = []

    radios = page.locator(
        'input[type="radio"]:visible'
    )

    for index in range(
        radios.count()
    ):
        try:
            name = radios.nth(
                index
            ).get_attribute(
                "name"
            )

            if (
                name
                and name not in names
            ):
                names.append(name)

        except Exception:
            continue

    return names


def _radio_checked(
    page,
    name,
):
    radios = page.locator(
        f'input[type="radio"]'
        f'[name="{name}"]'
    )

    for index in range(
        radios.count()
    ):
        try:
            if radios.nth(
                index
            ).is_checked():
                return True

        except Exception:
            continue

    return False


def _choose_radio(
    page,
    name,
    answer,
):
    candidates = {
        _normal(value)
        for value in _candidate_answers(
            answer
        )
    }

    radios = page.locator(
        f'input[type="radio"]'
        f'[name="{name}"]'
    )

    selected = None

    for index in range(
        radios.count()
    ):
        radio = radios.nth(index)

        value = _normal(
            radio.get_attribute(
                "value"
            )
        )

        if value in candidates:
            selected = radio
            break

        radio_id = (
            radio.get_attribute(
                "id"
            )
        )

        if radio_id:
            label = page.locator(
                f'label[for="{radio_id}"]'
            )

            if label.count():
                try:
                    label_text = _normal(
                        label.first.inner_text()
                    )

                    if label_text in candidates:
                        selected = radio
                        break

                except Exception:
                    pass

    if selected is None:
        print(
            f"No radio match: "
            f"{name}={answer!r}"
        )

        return False

    print(
        f"Selecting {name}: "
        f"{answer!r} -> "
        f"{selected.get_attribute('value')!r}"
    )

    # myScheme uses visually hidden radios.
    # Clicking the associated label is more reliable
    # than radio.check().

    radio_id = selected.get_attribute(
        "id"
    )

    if radio_id:
        label = page.locator(
            f'label[for="{radio_id}"]'
        )

        if label.count():
            try:
                label.first.click(
                    force=True,
                    timeout=5000,
                )

                page.wait_for_timeout(
                    300
                )

                if selected.is_checked():
                    return True

            except Exception:
                pass

    try:
        selected.click(
            force=True,
            timeout=5000,
        )

        page.wait_for_timeout(
            300
        )

        if selected.is_checked():
            return True

    except Exception:
        pass

    try:
        selected.evaluate(
            """
            element => {
                element.click();

                element.dispatchEvent(
                    new Event(
                        'input',
                        {bubbles: true}
                    )
                );

                element.dispatchEvent(
                    new Event(
                        'change',
                        {bubbles: true}
                    )
                );
            }
            """
        )

        page.wait_for_timeout(
            300
        )

        return selected.is_checked()

    except Exception:
        return False


def _option_texts(select):
    values = []

    options = select.locator(
        "option"
    )

    for index in range(
        options.count()
    ):
        try:
            text = _clean(
                options.nth(
                    index
                ).inner_text()
            )

            if text:
                values.append(text)

        except Exception:
            continue

    return values


def _looks_like_age_select(
    select,
):
    options = _option_texts(
        select
    )

    numeric = 0

    for value in options:
        if value.isdigit():
            numeric += 1

    return numeric >= 30


def _select_from_element(
    select,
    answer,
):
    desired = _clean(answer)

    try:
        select.select_option(
            label=desired
        )

        page_value = _clean(
            select.input_value()
        )

        if page_value:
            return True

    except Exception:
        pass

    try:
        select.select_option(
            value=desired
        )

        return True

    except Exception:
        pass

    options = select.locator(
        "option"
    )

    for index in range(
        options.count()
    ):
        option = options.nth(index)

        try:
            text = _normal(
                option.inner_text()
            )

            if text != _normal(
                desired
            ):
                continue

            value = option.get_attribute(
                "value"
            )

            if value is None:
                continue

            select.select_option(
                value=value
            )

            return True

        except Exception:
            continue

    return False


def _answer_named_select(
    page,
    field_name,
    answer,
):
    selects = page.locator(
        f'select[name="{field_name}"]'
        ":visible"
    )

    if not selects.count():
        return False

    return _select_from_element(
        selects.first,
        answer,
    )


def _answer_age(
    page,
    answer,
):
    named = page.locator(
        'select[name="age"]:visible'
    )

    if named.count():
        return _select_from_element(
            named.first,
            answer,
        )

    selects = page.locator(
        "select:visible"
    )

    for index in range(
        selects.count()
    ):
        select = selects.nth(index)

        if _looks_like_age_select(
            select
        ):
            return _select_from_element(
                select,
                answer,
            )

    return False


def _answer_state(
    page,
    answer,
):
    named = page.locator(
        'select[name="state"]:visible'
    )

    if named.count():
        return _select_from_element(
            named.first,
            answer,
        )

    wanted = _normal(answer)

    selects = page.locator(
        "select:visible"
    )

    for index in range(
        selects.count()
    ):
        select = selects.nth(index)

        options = {
            _normal(value)
            for value in _option_texts(
                select
            )
        }

        if wanted in options:
            return _select_from_element(
                select,
                answer,
            )

    return False


def _answer_marital(
    page,
    answer,
):
    if _answer_named_select(
        page,
        "maritalStatus",
        answer,
    ):
        return True

    marital_options = {
        "never married",
        "married",
        "divorced",
        "separated",
        "widowed",
        "unmarried",
    }

    selects = page.locator(
        "select:visible"
    )

    for index in range(
        selects.count()
    ):
        select = selects.nth(index)

        options = {
            _normal(value)
            for value in _option_texts(
                select
            )
        }

        if (
            options
            & marital_options
        ):
            return _select_from_element(
                select,
                answer,
            )

    return False


def _answer_input(
    page,
    field_name,
    answer,
):
    inputs = page.locator(
        f'input[name="{field_name}"]'
        ':not([type="radio"]):visible'
    )

    if not inputs.count():
        return False

    try:
        inputs.first.fill(
            str(answer)
        )

        page.wait_for_timeout(
            200
        )

        return True

    except Exception:
        return False


def _answer_field(
    page,
    profile,
    field_name,
):
    answer = _answer_for(
        profile,
        field_name,
    )

    if answer is None:
        raise RuntimeError(
            "No profile answer available "
            f"for myScheme field: {field_name}"
        )

    print(
        f"Answering {field_name}: "
        f"{answer!r}"
    )

    radio = page.locator(
        f'input[type="radio"]'
        f'[name="{field_name}"]:visible'
    )

    if radio.count():
        return _choose_radio(
            page,
            field_name,
            answer,
        )

    if field_name == "age":
        return _answer_age(
            page,
            answer,
        )

    if field_name == "state":
        return _answer_state(
            page,
            answer,
        )

    if field_name == "maritalStatus":
        return _answer_marital(
            page,
            answer,
        )

    if _answer_named_select(
        page,
        field_name,
        answer,
    ):
        return True

    if _answer_input(
        page,
        field_name,
        answer,
    ):
        return True

    return False


def _detect_select_fields(
    page,
    answered,
    profile,
):
    fields = []

    selects = page.locator(
        "select:visible"
    )

    for index in range(
        selects.count()
    ):
        select = selects.nth(index)

        name = select.get_attribute(
            "name"
        )

        if (
            name
            and name in QUESTION_FIELDS
            and name not in answered
        ):
            fields.append(name)

    if (
        "age" not in answered
        and "age" not in fields
    ):
        for index in range(
            selects.count()
        ):
            if _looks_like_age_select(
                selects.nth(index)
            ):
                fields.append("age")
                break

    if (
        "state" not in answered
        and "state" not in fields
    ):
        state = _answer_for(
            profile,
            "state",
        )

        if state:
            wanted = _normal(state)

            for index in range(
                selects.count()
            ):
                options = {
                    _normal(value)
                    for value in _option_texts(
                        selects.nth(index)
                    )
                }

                if wanted in options:
                    fields.append(
                        "state"
                    )
                    break

    if (
        "maritalStatus"
        not in answered
        and "maritalStatus"
        not in fields
    ):
        marital_options = {
            "never married",
            "married",
            "divorced",
            "separated",
            "widowed",
            "unmarried",
        }

        for index in range(
            selects.count()
        ):
            options = {
                _normal(value)
                for value in _option_texts(
                    selects.nth(index)
                )
            }

            if (
                options
                & marital_options
            ):
                fields.append(
                    "maritalStatus"
                )
                break

    return fields


def _detect_input_fields(
    page,
    answered,
):
    fields = []

    inputs = page.locator(
        (
            'input[type="number"]:visible, '
            'input[type="text"]:visible'
        )
    )

    for index in range(
        inputs.count()
    ):
        name = inputs.nth(
            index
        ).get_attribute(
            "name"
        )

        if (
            name
            and name in QUESTION_FIELDS
            and name not in answered
        ):
            fields.append(name)

    return fields


def _visible_supported_fields(
    page,
    answered,
    profile,
):
    fields = []

    # Radio groups
    for name in _visible_radio_names(
        page
    ):
        if (
            name in QUESTION_FIELDS
            and name not in answered
        ):
            fields.append(name)

    # Selects
    for name in _detect_select_fields(
        page,
        answered,
        profile,
    ):
        if name not in fields:
            fields.append(name)

    # Inputs
    for name in _detect_input_fields(
        page,
        answered,
    ):
        if name not in fields:
            fields.append(name)

    return fields


def _unknown_required_radios(
    page,
    answered,
):
    unknown = []

    for name in _visible_radio_names(
        page
    ):
        if (
            name not in QUESTION_FIELDS
            and name not in answered
        ):
            unknown.append(name)

    return unknown


def _debug_page(page):
    print()
    print("=" * 60)
    print("MYSCHEME DEBUG")
    print("=" * 60)

    print(
        "URL:",
        page.url,
    )

    try:
        body = _clean(
            page.locator(
                "body"
            ).inner_text()
        )

        print(
            "BODY:",
            body[:5000],
        )

    except Exception:
        pass

    radios = page.locator(
        'input[type="radio"]:visible'
    )

    print(
        "VISIBLE RADIOS:",
        radios.count(),
    )

    for index in range(
        radios.count()
    ):
        radio = radios.nth(index)

        print(
            index,
            "name=",
            radio.get_attribute(
                "name"
            ),
            "value=",
            radio.get_attribute(
                "value"
            ),
        )

    selects = page.locator(
        "select:visible"
    )

    print(
        "VISIBLE SELECTS:",
        selects.count(),
    )

    for index in range(
        selects.count()
    ):
        select = selects.nth(index)

        print(
            index,
            "name=",
            select.get_attribute(
                "name"
            ),
            "options=",
            _option_texts(
                select
            )[:25],
        )

    print("=" * 60)
    print()


def _click_continue(page):
    selectors = [
        'button:has-text("Next"):visible',
        'button:has-text("Submit"):visible',
        'button[type="submit"]:visible',
        'input[type="submit"]:visible',
    ]

    for selector in selectors:
        buttons = page.locator(
            selector
        )

        for index in range(
            buttons.count()
        ):
            button = buttons.nth(index)

            try:
                text = ""

                try:
                    text = _clean(
                        button.inner_text()
                    )

                except Exception:
                    pass

                print(
                    "Clicking:",
                    text or selector,
                )

                button.click(
                    force=True,
                    timeout=5000,
                )

                page.wait_for_timeout(
                    900
                )

                return True

            except Exception:
                continue

    return False


def _click_skip_to_results(
    page,
):
    skip = page.get_by_text(
        "Skip to Results",
        exact=True,
    )

    if not skip.count():
        return False

    try:
        print(
            "Using Skip to Results."
        )

        skip.first.click(
            force=True,
            timeout=5000,
        )

        page.wait_for_timeout(
            1200
        )

        return True

    except Exception:
        return False


def _official_scheme_url(url):
    if not url:
        return ""

    absolute = urljoin(
        MYSCHEME_BASE_URL,
        url,
    )

    parsed = urlparse(
        absolute
    )

    host = (
        parsed.netloc
        or ""
    ).lower()

    if (
        parsed.scheme != "https"
        or host not in OFFICIAL_HOSTS
    ):
        return ""

    if (
        "/schemes/"
        not in parsed.path.lower()
    ):
        return ""

    result = (
        f"https://{host}"
        f"{parsed.path}"
    )

    if parsed.query:
        result += (
            f"?{parsed.query}"
        )

    return result


def _extract_scheme_links(
    page,
):
    links = page.locator(
        'a[href*="/schemes/"]'
    )

    results = []
    seen = set()

    print(
        "Candidate scheme links:",
        links.count(),
    )

    for index in range(
        links.count()
    ):
        try:
            href = links.nth(
                index
            ).get_attribute(
                "href"
            )

            url = _official_scheme_url(
                href
            )

            if (
                not url
                or url in seen
            ):
                continue

            seen.add(url)

            results.append(url)

        except Exception:
            continue

    print(
        "Official scheme links:",
        len(results),
    )

    return results


def _parse_scheme_page(
    page,
    url,
    state,
):
    try:
        print(
            "Loading scheme:",
            url,
        )

        page.goto(
            url,
            wait_until="domcontentloaded",
            timeout=30000,
        )

        page.wait_for_timeout(
            800
        )

        soup = BeautifulSoup(
            page.content(),
            "html.parser",
        )

        for tag in soup(
            [
                "script",
                "style",
                "svg",
                "noscript",
            ]
        ):
            tag.decompose()

        text = _clean(
            soup.get_text(
                " "
            )
        )

        if not text:
            return None

        title = ""

        heading = soup.find("h1")

        if heading:
            title = _clean(
                heading.get_text(
                    " "
                )
            )

        if (
            not title
            and soup.title
        ):
            title = _clean(
                soup.title.get_text(
                    " "
                )
            )

        if not title:
            title = (
                "Government Scheme"
            )

        return {
            "scheme_name": title,
            "description": text,
            "eligibility_signals": "",
            "benefits": "",
            "application_info": "",
            "url": url,
            "source": SOURCE_NAME,
            "state": state,
            "category": "",
            "fetched_at": _now(),
        }

    except Exception as exc:
        print(
            "Scheme page failed:",
            repr(exc),
        )

        return None


def _is_results_page(page):
    url = page.url.lower()

    return (
        "/search/user-journey"
        in url
        or "/search?"
        in url
    )


def _run_questionnaire(
    page,
    profile,
):
    page.goto(
        MYSCHEME_SEARCH_URL,
        wait_until="domcontentloaded",
        timeout=30000,
    )

    page.wait_for_timeout(
        1200
    )

    start = page.get_by_text(
        "Find Schemes For You",
        exact=True,
    )

    if not start.count():
        start = page.get_by_text(
            "Find Schemes For You"
        )

    if not start.count():
        _debug_page(page)

        raise RuntimeError(
            "Could not start myScheme "
            "questionnaire."
        )

    start.first.click(
        force=True
    )

    page.wait_for_timeout(
        1000
    )

    answered = set()

    # Page transitions, not individual fields.
    for page_step in range(
        1,
        30,
    ):
        print()
        print(
            f"myScheme page {page_step}"
        )

        print(
            "URL:",
            page.url,
        )

        if _is_results_page(
            page
        ):
            page.wait_for_timeout(
                1500
            )

            return _extract_scheme_links(
                page
            )

        # ------------------------------------------
        # Critical improvement:
        # answer EVERY supported field currently
        # visible before clicking Next/Submit.
        # ------------------------------------------

        answered_on_page = False

        for inner_pass in range(
            1,
            15,
        ):
            fields = (
                _visible_supported_fields(
                    page,
                    answered,
                    profile,
                )
            )

            if not fields:
                break

            print(
                "Visible fields:",
                fields,
            )

            progress = False

            for field_name in fields:
                if field_name in answered:
                    continue

                success = _answer_field(
                    page,
                    profile,
                    field_name,
                )

                if not success:
                    _debug_page(page)

                    raise RuntimeError(
                        "Could not answer "
                        f"myScheme field "
                        f"{field_name!r}."
                    )

                answered.add(
                    field_name
                )

                progress = True
                answered_on_page = True

                page.wait_for_timeout(
                    350
                )

            if not progress:
                break

        # ------------------------------------------
        # Detect a new unknown radio field BEFORE
        # clicking Next/Submit.
        # ------------------------------------------

        unknown = (
            _unknown_required_radios(
                page,
                answered,
            )
        )

        if unknown:
            _debug_page(page)

            raise RuntimeError(
                "myScheme introduced an "
                "unsupported questionnaire "
                "field: "
                + ", ".join(unknown)
            )

        if _is_results_page(
            page
        ):
            return _extract_scheme_links(
                page
            )

        # ------------------------------------------
        # Continue.
        # ------------------------------------------

        if _click_continue(
            page
        ):
            continue

        # If there is no Next/Submit but myScheme
        # exposes Skip to Results, use that only
        # after all visible supported fields have
        # already been answered.

        if _click_skip_to_results(
            page
        ):
            continue

        _debug_page(page)

        if not answered_on_page:
            raise RuntimeError(
                "No questionnaire field or "
                "continue control could be "
                "processed."
            )

        raise RuntimeError(
            "Could not continue the "
            "myScheme questionnaire."
        )

    raise RuntimeError(
        "myScheme questionnaire exceeded "
        "the maximum number of pages."
    )


def fetch_schemes(
    profile: dict[str, Any],
):
    """
    Fetch live government scheme results
    from the official myScheme questionnaire.
    """

    profile = _normalise_profile(
        profile
    )

    print()
    print("=" * 60)
    print("SKILLSETU LIVE MYSCHEME")
    print("=" * 60)

    print(
        "Profile:",
        profile,
    )

    try:
        with sync_playwright() as p:
            browser = (
                p.chromium.launch(
                    headless=True
                )
            )

            try:
                page = browser.new_page(
                    viewport={
                        "width": 1440,
                        "height": 1000,
                    }
                )

                urls = _run_questionnaire(
                    page,
                    profile,
                )

                print(
                    "Questionnaire returned:",
                    len(urls),
                )

                if not urls:
                    return []

                state = _clean(
                    profile.get(
                        "state",
                        ""
                    )
                )

                schemes = []

                # Keep hackathon demo responsive.
                for index, url in enumerate(
                    urls[:12],
                    start=1,
                ):
                    print()
                    print(
                        f"Scheme {index}/"
                        f"{min(len(urls), 12)}"
                    )

                    scheme = (
                        _parse_scheme_page(
                            page,
                            url,
                            state,
                        )
                    )

                    if scheme:
                        schemes.append(
                            scheme
                        )

                print()
                print(
                    "Live schemes parsed:",
                    len(schemes),
                )

                return schemes

            finally:
                browser.close()

    except Exception as exc:
        print()
        print(
            "myScheme retrieval failed:"
        )

        print(
            repr(exc)
        )

        return []


if __name__ == "__main__":
    test_profile = {
        "name": "Ravi",
        "location": "Guntur",
        "state": "Andhra Pradesh",
        "gender": "Male",
        "age": 25,
        "residence": "Rural",
        "caste": "General",
        "disability": "No",
        "minority": "No",
        "is_student": False,
        "employment_status": "Unemployed",
        "marital_status": "Never Married",
        "is_bpl": True,
        "is_economic_distress": False,
        "annual_family_income": 0,
        "annual_parent_income": 0,
    }

    schemes = fetch_schemes(
        test_profile
    )

    print()
    print(
        "SCHEMES RETURNED:",
        len(schemes),
    )

    for scheme in schemes[:5]:
        print(
            "-",
            scheme.get(
                "scheme_name"
            ),
        )

        print(
            " ",
            scheme.get(
                "url"
            ),
        )