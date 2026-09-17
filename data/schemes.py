from __future__ import annotations

from datetime import datetime, timezonef
from typing import Any
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


MYSCHEME_SEARCH_URL = "https://search.myscheme.gov.in/"
MYSCHEME_BASE_URL = "https://www.myscheme.gov.in/"
SOURCE_NAME = "myScheme"


# Official myScheme hosts only.
MYSCHEME_OFFICIAL_HOSTS = {
    "search.myscheme.gov.in",
    "www.myscheme.gov.in",
    "myscheme.gov.in",
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
    "isBpl",
    "annualFamilyIncome",
    "annualParentIncome",
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_text(value: str | None) -> str:
    if not value:
        return ""

    return " ".join(value.split()).strip()


def _normalise_text(value: Any) -> str:
    return _clean_text(str(value)).lower()


def _normalise_profile(
    profile: dict[str, Any],
) -> dict[str, Any]:

    result = dict(profile)

    aliases = {
        "sex": "gender",
        "marital": "marital_status",
        "maritalStatus": "marital_status",
        "residence_type": "residence",
        "area": "residence",
        "annual_family_income": "annual_family_income",
        "annual_parent_income": "annual_parent_income",
        "parent_income": "annual_parent_income",
    }

    for old_key, new_key in aliases.items():

        if (
            new_key not in result
            and old_key in result
        ):
            result[new_key] = result[old_key]

    location = str(
        result.get(
            "location",
            "",
        )
    ).strip()

    if (
        "state" not in result
        and location
    ):
        result["state"] = location

    return result


def _get_profile_value(
    profile: dict[str, Any],
    *keys: str,
) -> Any:

    for key in keys:

        value = profile.get(key)

        if (
            value is not None
            and value != ""
        ):
            return value

    return None


def _radio_value_aliases(
    answer: Any,
) -> list[str]:

    # ---------------------------------------------------------
    # myScheme uses "Yes"/"No" for boolean questions.
    # SkillSetu profiles use Python True/False.
    # ---------------------------------------------------------

    if isinstance(answer, bool):

        raw = "Yes" if answer else "No"

    else:

        raw = _clean_text(
            str(answer)
        )

    lowered = raw.lower()

    aliases = {
        "sc": [
            "Scheduled Caste (SC)",
            "Scheduled Caste",
            "SC",
        ],
        "st": [
            "Scheduled Tribe (ST)",
            "Scheduled Tribe",
            "ST",
        ],
        "obc": [
            "Other Backward Class (OBC)",
            "Other Backward Class",
            "OBC",
        ],
        "pvtg": [
            "Particularly Vulnerable Tribal Group (PVTG)",
            "Particularly Vulnerable Tribal Group",
            "PVTG",
        ],
        "dnt": [
            "De-Notified, Nomadic, and Semi-Nomadic (DNT) communities",
            "De-Notified, Nomadic, and Semi-Nomadic (DNT)",
            "DNT",
        ],
        "general": [
            "General",
        ],
        "male": [
            "Male",
        ],
        "female": [
            "Female",
        ],
        "transgender": [
            "Transgender",
        ],
        "urban": [
            "Urban",
        ],
        "rural": [
            "Rural",
        ],
        "yes": [
            "Yes",
        ],
        "no": [
            "No",
        ],
    }

    result = [
        raw
    ]

    if lowered in aliases:

        result.extend(
            aliases[lowered]
        )

    if isinstance(answer, bool):

        if answer:

            result.extend(
                [
                    "true",
                    "yes",
                    "Yes",
                ]
            )

        else:

            result.extend(
                [
                    "false",
                    "no",
                    "No",
                ]
            )

    unique: list[str] = []
    seen: set[str] = set()

    for item in result:

        key = _normalise_text(
            item
        )

        if key not in seen:

            seen.add(key)
            unique.append(item)

    return unique


def _find_matching_radio(
    page,
    name: str,
    answer: Any,
):
    radios = page.locator(
        f'input[type="radio"][name="{name}"]'
    )

    if radios.count() == 0:
        return None

    candidates = _radio_value_aliases(
        answer
    )

    candidate_normalised = {
        _normalise_text(value)
        for value in candidates
    }

    # ---------------------------------------------------------
    # Match actual radio value.
    # ---------------------------------------------------------

    for i in range(
        radios.count()
    ):

        radio = radios.nth(i)

        try:

            value = radio.get_attribute(
                "value"
            )

            if not value:
                continue

            if (
                _normalise_text(value)
                in candidate_normalised
            ):

                return radio

        except Exception:
            continue

    # ---------------------------------------------------------
    # Match associated label.
    # ---------------------------------------------------------

    for i in range(
        radios.count()
    ):

        radio = radios.nth(i)

        try:

            radio_id = radio.get_attribute(
                "id"
            )

            if not radio_id:
                continue

            label = page.locator(
                f'label[for="{radio_id}"]'
            )

            if label.count() == 0:
                continue

            label_text = _normalise_text(
                label.first.inner_text()
            )

            if (
                label_text
                in candidate_normalised
            ):

                return radio

            for candidate in candidates:

                candidate_norm = _normalise_text(
                    candidate
                )

                if (
                    candidate_norm
                    and len(candidate_norm) > 1
                    and candidate_norm in label_text
                ):

                    return radio

        except Exception:
            continue

    return None


def _select_radio(
    page,
    name: str,
    answer: Any,
) -> bool:

    radio = _find_matching_radio(
        page,
        name,
        answer,
    )

    if radio is None:

        print(
            f"No matching radio found for "
            f"{name}={answer!r}"
        )

        return False

    value = radio.get_attribute(
        "value"
    )

    radio_id = radio.get_attribute(
        "id"
    )

    print(
        f"Resolved radio: "
        f"profile='{answer}' "
        f"-> value='{value}' "
        f"id='{radio_id}'"
    )

    # ---------------------------------------------------------
    # Preferred method: associated label.
    # ---------------------------------------------------------

    if radio_id:

        label = page.locator(
            f'label[for="{radio_id}"]'
        )

        if label.count():

            try:

                print(
                    "Clicking associated label..."
                )

                label.first.click(
                    force=True,
                    timeout=5000,
                )

                page.wait_for_timeout(
                    300
                )

                if radio.is_checked():

                    print(
                        f"Verified radio selection: "
                        f"{value}"
                    )

                    return True

            except Exception as exc:

                print(
                    f"Label click failed: "
                    f"{exc}"
                )

    # ---------------------------------------------------------
    # Wrapping label fallback.
    # ---------------------------------------------------------

    try:

        parent_label = radio.locator(
            "xpath=ancestor::label[1]"
        )

        if parent_label.count():

            print(
                "Trying wrapping label..."
            )

            parent_label.first.click(
                force=True,
                timeout=5000,
            )

            page.wait_for_timeout(
                300
            )

            if radio.is_checked():

                print(
                    f"Verified radio selection: "
                    f"{value}"
                )

                return True

    except Exception as exc:

        print(
            f"Wrapping label failed: "
            f"{exc}"
        )

    # ---------------------------------------------------------
    # Parent fallback.
    # ---------------------------------------------------------

    try:

        parent = radio.locator(
            "xpath=.."
        )

        if parent.count():

            print(
                "Trying radio parent..."
            )

            parent.first.click(
                force=True,
                timeout=5000,
            )

            page.wait_for_timeout(
                300
            )

            if radio.is_checked():

                print(
                    f"Verified radio selection: "
                    f"{value}"
                )

                return True

    except Exception as exc:

        print(
            f"Radio parent failed: "
            f"{exc}"
        )

    # ---------------------------------------------------------
    # JavaScript fallback.
    # ---------------------------------------------------------

    try:

        print(
            "Trying JavaScript native click..."
        )

        radio.evaluate(
            """
            element => {
                element.click();

                element.dispatchEvent(
                    new Event("input", {
                        bubbles: true
                    })
                );

                element.dispatchEvent(
                    new Event("change", {
                        bubbles: true
                    })
                );
            }
            """
        )

        page.wait_for_timeout(
            500
        )

        if radio.is_checked():

            print(
                f"Verified radio selection "
                f"after JavaScript: {value}"
            )

            return True

    except Exception as exc:

        print(
            f"JavaScript radio click failed: "
            f"{exc}"
        )

    return False


def _select_option_texts(
    select,
) -> list[str]:

    values: list[str] = []

    try:

        options = select.locator(
            "option"
        )

        for i in range(
            options.count()
        ):

            text = _clean_text(
                options.nth(i).inner_text()
            )

            if text:
                values.append(text)

    except Exception:
        pass

    return values


def _is_age_select(
    select,
) -> bool:

    try:

        options = select.locator(
            "option"
        )

        count = options.count()

        if count < 50:
            return False

        first_text = _clean_text(
            options.nth(0).inner_text()
        )

        if first_text != "--":
            return False

        numeric_count = 0

        for i in range(
            min(count, 120)
        ):

            text = _clean_text(
                options.nth(i).inner_text()
            )

            if text.isdigit():
                numeric_count += 1

        return numeric_count >= 40

    except Exception:
        return False


def _infer_unnamed_select_field(
    page,
    profile: dict[str, Any],
    answered_fields: set[str],
) -> str | None:

    selects = page.locator(
        "select:visible"
    )

    for i in range(
        selects.count()
    ):

        select = selects.nth(i)

        try:

            name = select.get_attribute(
                "name"
            )

            if (
                name in QUESTION_FIELDS
                and name not in answered_fields
            ):

                return name

            options = _select_option_texts(
                select
            )

            if not options:
                continue

            normalized_options = {
                _normalise_text(option)
                for option in options
            }

            # -------------------------------------------------
            # Age.
            # -------------------------------------------------

            if _is_age_select(
                select
            ):

                if "age" not in answered_fields:

                    return "age"

                continue

            # -------------------------------------------------
            # Marital status.
            # -------------------------------------------------

            marital_options = {
                "married",
                "never married",
                "divorced",
                "separated",
                "widowed",
            }

            if marital_options.intersection(
                normalized_options
            ):

                if (
                    "maritalStatus"
                    not in answered_fields
                ):

                    return "maritalStatus"

                continue

            # -------------------------------------------------
            # State.
            # -------------------------------------------------

            state = str(
                _get_profile_value(
                    profile,
                    "state",
                    "location",
                )
                or ""
            ).strip()

            if (
                "state"
                not in answered_fields
                and _normalise_text(state)
                in normalized_options
            ):

                return "state"

            # -------------------------------------------------
            # Residence.
            # -------------------------------------------------

            residence = str(
                _get_profile_value(
                    profile,
                    "residence",
                    "residence_type",
                    "area",
                )
                or ""
            ).strip()

            if (
                "residence"
                not in answered_fields
                and _normalise_text(residence)
                in normalized_options
            ):

                return "residence"

        except Exception:
            continue

    return None


def _visible_question(
    page,
    answered_fields: set[str],
    profile: dict[str, Any],
) -> tuple[str | None, str]:

    # ---------------------------------------------------------
    # Explicit gender.
    # ---------------------------------------------------------

    if (
        profile.get("gender")
        not in (None, "")
        and "gender"
        not in answered_fields
    ):

        radios = page.locator(
            'input[type="radio"][name="gender"]:visible'
        )

        if radios.count():

            return (
                "gender",
                _clean_text(
                    page.locator(
                        "body"
                    ).inner_text()
                ),
            )

    # ---------------------------------------------------------
    # Radio questions.
    # ---------------------------------------------------------

    radios = page.locator(
        'input[type="radio"]:visible'
    )

    seen_names: set[str] = set()

    for i in range(
        radios.count()
    ):

        radio = radios.nth(i)

        try:

            name = radio.get_attribute(
                "name"
            )

            if not name:
                continue

            if name in seen_names:
                continue

            seen_names.add(
                name
            )

            if (
                name in QUESTION_FIELDS
                and name not in answered_fields
            ):

                return (
                    name,
                    _clean_text(
                        page.locator(
                            "body"
                        ).inner_text()
                    ),
                )

        except Exception:
            continue

    # ---------------------------------------------------------
    # Named selects.
    # ---------------------------------------------------------

    selects = page.locator(
        "select:visible"
    )

    for i in range(
        selects.count()
    ):

        select = selects.nth(i)

        try:

            name = select.get_attribute(
                "name"
            )

            if (
                name in QUESTION_FIELDS
                and name not in answered_fields
            ):

                return (
                    name,
                    _clean_text(
                        page.locator(
                            "body"
                        ).inner_text()
                    ),
                )

        except Exception:
            continue

    # ---------------------------------------------------------
    # Unnamed selects.
    # ---------------------------------------------------------

    inferred = _infer_unnamed_select_field(
        page,
        profile,
        answered_fields,
    )

    if inferred:

        return (
            inferred,
            _clean_text(
                page.locator(
                    "body"
                ).inner_text()
            ),
        )

    # ---------------------------------------------------------
    # Number/text inputs.
    # ---------------------------------------------------------

    for selector in [
        'input[type="number"]:visible',
        'input[type="text"]:visible',
    ]:

        elements = page.locator(
            selector
        )

        for i in range(
            elements.count()
        ):

            element = elements.nth(i)

            try:

                name = element.get_attribute(
                    "name"
                )

                if (
                    name in QUESTION_FIELDS
                    and name not in answered_fields
                ):

                    return (
                        name,
                        _clean_text(
                            page.locator(
                                "body"
                            ).inner_text()
                        ),
                    )

            except Exception:
                continue

    return None, ""


def _debug_dom(
    page,
) -> None:

    print()
    print("=" * 60)
    print("MYSCHEME DOM DEBUG")
    print("=" * 60)

    try:

        print()
        print("URL:")
        print(page.url)

        print()
        print("TITLE:")
        print(page.title())

        print()
        print("VISIBLE BODY TEXT:")

        print(
            _clean_text(
                page.locator(
                    "body"
                ).inner_text()
            )
        )

    except Exception as exc:

        print(
            f"Could not read body: {exc}"
        )

    print()
    print("VISIBLE INPUTS:")

    try:

        inputs = page.locator(
            "input:visible"
        )

        print(
            f"Input count: "
            f"{inputs.count()}"
        )

        for i in range(
            inputs.count()
        ):

            element = inputs.nth(i)

            input_type = (
                element.get_attribute(
                    "type"
                )
                or ""
            )

            checked = "N/A"

            if input_type == "radio":

                try:

                    checked = element.is_checked()

                except Exception:

                    checked = "?"

            print(
                f"[INPUT {i}] "
                f"type='{input_type}' "
                f"name='{element.get_attribute('name')}' "
                f"value='{element.get_attribute('value')}' "
                f"id='{element.get_attribute('id')}' "
                f"checked={checked}"
            )

    except Exception as exc:

        print(
            f"Could not inspect inputs: {exc}"
        )

    print()
    print("VISIBLE SELECTS:")

    try:

        selects = page.locator(
            "select:visible"
        )

        print(
            f"Select count: "
            f"{selects.count()}"
        )

        for i in range(
            selects.count()
        ):

            select = selects.nth(i)

            print(
                f"[SELECT {i}] "
                f"name='{select.get_attribute('name')}' "
                f"id='{select.get_attribute('id')}' "
                f"value='{select.input_value()}' "
                f"options={select.locator('option').count()}"
            )

    except Exception as exc:

        print(
            f"Could not inspect selects: {exc}"
        )

    print()
    print("VISIBLE LABELS:")

    try:

        labels = page.locator(
            "label:visible"
        )

        print(
            f"Label count: "
            f"{labels.count()}"
        )

        for i in range(
            labels.count()
        ):

            label = labels.nth(i)

            print(
                f"[LABEL {i}] "
                f"for='{label.get_attribute('for')}' "
                f"text='{_clean_text(label.inner_text())}'"
            )

    except Exception as exc:

        print(
            f"Could not inspect labels: {exc}"
        )

    print()
    print("VISIBLE BUTTONS:")

    try:

        buttons = page.locator(
            "button:visible"
        )

        print(
            f"Button count: "
            f"{buttons.count()}"
        )

        for i in range(
            buttons.count()
        ):

            button = buttons.nth(i)

            print(
                f"[BUTTON {i}] "
                f"text='{_clean_text(button.inner_text())}' "
                f"type='{button.get_attribute('type')}'"
            )

    except Exception as exc:

        print(
            f"Could not inspect buttons: {exc}"
        )

    print("=" * 60)
    print()


def _select_age(
    page,
    value: Any,
) -> bool:

    age = str(
        value
    ).strip()

    selects = page.locator(
        "select:visible"
    )

    for i in range(
        selects.count()
    ):

        select = selects.nth(i)

        if not _is_age_select(
            select
        ):
            continue

        print(
            f"Selecting age value: "
            f"{age}"
        )

        try:

            select.select_option(
                value=age
            )

            page.wait_for_timeout(
                300
            )

            current = select.input_value()

            print(
                f"Age select value after "
                f"selection: '{current}'"
            )

            if current == age:

                print(
                    "Age selection "
                    "verified successfully."
                )

                return True

        except Exception as exc:

            print(
                f"Age value selection "
                f"failed: {exc}"
            )

        try:

            select.select_option(
                label=age
            )

            page.wait_for_timeout(
                300
            )

            current = select.input_value()

            if current == age:

                print(
                    "Age selection "
                    "verified successfully."
                )

                return True

        except Exception:
            pass

    return False


def _select_value(
    page,
    field_name: str,
    value: Any,
) -> bool:

    desired = str(
        value
    ).strip()

    # ---------------------------------------------------------
    # Named select.
    # ---------------------------------------------------------

    select = page.locator(
        f'select[name="{field_name}"]:visible'
    )

    if select.count():

        select = select.first

        try:

            select.select_option(
                label=desired
            )

            page.wait_for_timeout(
                300
            )

            return True

        except Exception:
            pass

        try:

            select.select_option(
                value=desired
            )

            page.wait_for_timeout(
                300
            )

            return True

        except Exception:
            pass

        options = select.locator(
            "option"
        )

        for i in range(
            options.count()
        ):

            option = options.nth(i)

            text = _normalise_text(
                option.inner_text()
            )

            if (
                text
                == _normalise_text(desired)
            ):

                option_value = (
                    option.get_attribute(
                        "value"
                    )
                )

                if option_value is None:
                    continue

                try:

                    select.select_option(
                        value=option_value
                    )

                    page.wait_for_timeout(
                        300
                    )

                    return True

                except Exception:
                    continue

    # ---------------------------------------------------------
    # Unnamed select.
    # ---------------------------------------------------------

    selects = page.locator(
        "select:visible"
    )

    for i in range(
        selects.count()
    ):

        candidate = selects.nth(i)

        try:

            name = candidate.get_attribute(
                "name"
            )

            if name:
                continue

            options = candidate.locator(
                "option"
            )

            for j in range(
                options.count()
            ):

                option = options.nth(j)

                text = _normalise_text(
                    option.inner_text()
                )

                if (
                    text
                    == _normalise_text(desired)
                ):

                    option_value = (
                        option.get_attribute(
                            "value"
                        )
                    )

                    if option_value is None:
                        continue

                    candidate.select_option(
                        value=option_value
                    )

                    page.wait_for_timeout(
                        300
                    )

                    return True

        except Exception:
            continue

    return False


def _fill_input(
    page,
    name: str,
    value: Any,
) -> bool:

    field = page.locator(
        f'input[name="{name}"]:visible'
    )

    if field.count() == 0:
        return False

    try:

        field.first.fill(
            str(value)
        )

        return True

    except Exception:
        return False


def _profile_answer(
    profile: dict[str, Any],
    field_name: str,
) -> Any:

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
            "area",
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
        "isBpl": (
            "is_bpl",
            "isBpl",
        ),
        "annualFamilyIncome": (
            "annual_family_income",
            "family_income",
        ),
        "annualParentIncome": (
            "annual_parent_income",
            "parent_income",
        ),
    }

    keys = mapping.get(
        field_name,
        (),
    )

    return _get_profile_value(
        profile,
        *keys,
    )


def _answer_current_question(
    page,
    profile: dict[str, Any],
    field_name: str,
) -> bool:

    answer = _profile_answer(
        profile,
        field_name,
    )

    if answer is None:

        raise ValueError(
            f"myScheme requires profile field "
            f"'{field_name}', but SkillSetu "
            f"does not have it."
        )

    print(
        f"Profile answer for "
        f"'{field_name}': {answer!r}"
    )

    # ---------------------------------------------------------
    # Radio.
    # ---------------------------------------------------------

    radio = page.locator(
        f'input[type="radio"][name="{field_name}"]'
    )

    if radio.count():

        if _select_radio(
            page,
            field_name,
            answer,
        ):

            return True

        _debug_dom(
            page
        )

        raise RuntimeError(
            f"Could not answer myScheme "
            f"field '{field_name}' with "
            f"value '{answer}'."
        )

    # ---------------------------------------------------------
    # Age.
    # ---------------------------------------------------------

    if field_name == "age":

        if _select_age(
            page,
            answer,
        ):

            return True

        _debug_dom(
            page
        )

        raise RuntimeError(
            f"Could not select age "
            f"'{answer}'."
        )

    # ---------------------------------------------------------
    # Select.
    # ---------------------------------------------------------

    if _select_value(
        page,
        field_name,
        answer,
    ):

        return True

    # ---------------------------------------------------------
    # Text/number.
    # ---------------------------------------------------------

    if _fill_input(
        page,
        field_name,
        answer,
    ):

        return True

    _debug_dom(
        page
    )

    raise RuntimeError(
        f"Could not answer visible "
        f"myScheme field "
        f"'{field_name}' "
        f"with value '{answer}'."
    )


def _click_next(
    page,
) -> bool:

    selectors = [
        'button:has-text("Next"):visible',
        'button:has-text("Submit"):visible',
        'input[type="submit"]:visible',
    ]

    for selector in selectors:

        buttons = page.locator(
            selector
        )

        for i in range(
            buttons.count()
        ):

            button = buttons.nth(i)

            try:

                text = _clean_text(
                    button.inner_text()
                ).lower()

                button_type = (
                    button.get_attribute(
                        "type"
                    )
                    or ""
                ).lower()

                if (
                    "next" not in text
                    and "submit" not in text
                    and button_type != "submit"
                ):

                    continue

                print(
                    f"Clicking questionnaire control: "
                    f"text='{text}' "
                    f"type='{button_type}'"
                )

                button.click(
                    force=True,
                    timeout=5000,
                )

                return True

            except Exception as exc:

                print(
                    f"Questionnaire control "
                    f"click failed: {exc}"
                )

    return False


def _normalise_scheme_url(
    url: str,
) -> str:

    """
    Normalize an official myScheme URL.

    Only official myScheme hosts are accepted.
    """

    if not url:
        return ""

    url = url.strip()

    if url.startswith("//"):

        url = "https:" + url

    elif url.startswith("/"):

        url = urljoin(
            MYSCHEME_SEARCH_URL,
            url,
        )

    parsed = urlparse(
        url
    )

    if parsed.scheme.lower() != "https":
        return ""

    host = (
        parsed.netloc
        or ""
    ).lower()

    if host not in MYSCHEME_OFFICIAL_HOSTS:
        return ""

    # Remove fragments because they do not identify a
    # different scheme resource.
    normalized = (
        f"https://{host}"
        f"{parsed.path}"
    )

    if parsed.query:

        normalized += (
            f"?{parsed.query}"
        )

    return normalized


def _is_real_scheme_url(
    url: str,
) -> bool:

    normalized = _normalise_scheme_url(
        url
    )

    if not normalized:
        return False

    parsed = urlparse(
        normalized
    )

    path = (
        parsed.path
        or ""
    ).lower()

    return (
        "/schemes/" in path
    )


def _extract_scheme_cards(
    page,
) -> list[dict[str, str]]:

    cards: list[
        dict[str, str]
    ] = []

    seen_urls: set[str] = set()

    links = page.locator(
        'a[href*="/schemes/"]'
    )

    print(
        f"Found {links.count()} "
        f"candidate scheme links."
    )

    for i in range(
        links.count()
    ):

        link = links.nth(i)

        try:

            href = link.get_attribute(
                "href"
            )

            if not href:
                continue

            raw_url = urljoin(
                MYSCHEME_SEARCH_URL,
                href,
            )

            url = _normalise_scheme_url(
                raw_url
            )

            print(
                f"Candidate link "
                f"{i + 1}: "
                f"href='{href}' "
                f"-> normalized='{url}'"
            )

            if not _is_real_scheme_url(
                url
            ):

                continue

            if url in seen_urls:
                continue

            seen_urls.add(
                url
            )

            text = _clean_text(
                link.inner_text()
            )

            card_text = text

            try:

                ancestor = link.locator(
                    "xpath=ancestor::*"
                    "[self::article or @role='article'][1]"
                )

                if ancestor.count():

                    card_text = _clean_text(
                        ancestor.first.inner_text()
                    )

            except Exception:
                pass

            cards.append(
                {
                    "url": url,
                    "card_text": card_text,
                }
            )

        except Exception as exc:

            print(
                f"Could not process "
                f"candidate link: {exc}"
            )

    print(
        f"Recovered {len(cards)} "
        f"real scheme links."
    )

    return cards


def _parse_scheme_page(
    page,
    url: str,
    state: str,
) -> dict[str, Any] | None:

    normalized_url = _normalise_scheme_url(
        url
    )

    if not _is_real_scheme_url(
        normalized_url
    ):

        print(
            f"Skipping non-scheme URL: "
            f"{url}"
        )

        return None

    try:

        print(
            f"Loading scheme page: "
            f"{normalized_url}"
        )

        page.goto(
            normalized_url,
            wait_until="domcontentloaded",
            timeout=30_000,
        )

        page.wait_for_timeout(
            1000
        )

        html = page.content()

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        for element in soup(
            [
                "script",
                "style",
                "noscript",
                "svg",
            ]
        ):

            element.decompose()

        visible_text = _clean_text(
            soup.get_text(" ")
        )

        if not visible_text:

            print(
                "Scheme page contained "
                "no visible text."
            )

            return None

        title = ""

        if soup.title:

            title = _clean_text(
                soup.title.get_text()
            )

        h1 = soup.find(
            "h1"
        )

        if h1:

            h1_text = _clean_text(
                h1.get_text()
            )

            if h1_text:

                title = h1_text

        if not title:

            title = "myScheme scheme"

        return {
            "scheme_name": title,
            "description": visible_text,
            "eligibility_signals": "",
            "benefits": "",
            "application_info": "",
            "url": normalized_url,
            "source": SOURCE_NAME,
            "state": state,
            "category": "",
            "fetched_at": _now_iso(),
        }

    except Exception as exc:

        print(
            f"Scheme parsing failed: "
            f"{exc}"
        )

        return None


def _run_myscheme_questionnaire(
    page,
    profile: dict[str, Any],
) -> list[dict[str, str]]:

    page.goto(
        MYSCHEME_SEARCH_URL,
        wait_until="domcontentloaded",
        timeout=30_000,
    )

    page.wait_for_timeout(
        1500
    )

    find_button = page.get_by_text(
        "Find Schemes For You",
        exact=True,
    )

    if find_button.count() == 0:

        raise RuntimeError(
            "Could not find myScheme "
            "'Find Schemes For You' button."
        )

    print(
        "Clicking 'Find Schemes For You'..."
    )

    find_button.first.click(
        force=True
    )

    page.wait_for_timeout(
        1000
    )

    answered_fields: set[str] = set()

    max_steps = 30

    for step in range(
        1,
        max_steps + 1,
    ):

        page.wait_for_timeout(
            700
        )

        print()
        print(
            f"Questionnaire step {step}: "
            f"{page.url}"
        )

        # -----------------------------------------------------
        # Results page.
        # -----------------------------------------------------

        if (
            "/search/user-journey"
            in page.url
        ):

            print(
                "Reached myScheme "
                "results page."
            )

            cards = _extract_scheme_cards(
                page
            )

            if cards:

                return cards

            page.wait_for_timeout(
                1500
            )

            return _extract_scheme_cards(
                page
            )

        # -----------------------------------------------------
        # Current question.
        # -----------------------------------------------------

        field_name, question_text = (
            _visible_question(
                page,
                answered_fields,
                profile,
            )
        )

        if not field_name:

            print(
                "No unanswered questionnaire "
                "control detected."
            )

            _debug_dom(
                page
            )

            page.wait_for_timeout(
                1500
            )

            field_name, question_text = (
                _visible_question(
                    page,
                    answered_fields,
                    profile,
                )
            )

            if not field_name:

                raise RuntimeError(
                    "myScheme reached an "
                    "unknown questionnaire "
                    f"state: {page.url}"
                )

        print(
            f"Current question: "
            f"{field_name}"
        )

        print(
            f"Question text: "
            f"{question_text}"
        )

        # -----------------------------------------------------
        # Answer.
        # -----------------------------------------------------

        _answer_current_question(
            page,
            profile,
            field_name,
        )

        answered_fields.add(
            field_name
        )

        print(
            f"Answered: "
            f"{field_name}"
        )

        # -----------------------------------------------------
        # Verify gender.
        # -----------------------------------------------------

        if field_name == "gender":

            expected = str(
                profile.get(
                    "gender"
                )
            ).strip()

            radio = _find_matching_radio(
                page,
                "gender",
                expected,
            )

            if (
                radio is None
                or not radio.is_checked()
            ):

                _debug_dom(
                    page
                )

                raise RuntimeError(
                    f"Gender selection was "
                    f"not verified: "
                    f"expected '{expected}'."
                )

            print(
                f"Verified gender before Next: "
                f"'{expected}'"
            )

        # -----------------------------------------------------
        # Verify age.
        # -----------------------------------------------------

        if field_name == "age":

            expected_age = str(
                profile.get(
                    "age"
                )
            ).strip()

            age_verified = False

            selects = page.locator(
                "select:visible"
            )

            for i in range(
                selects.count()
            ):

                select = selects.nth(i)

                if _is_age_select(
                    select
                ):

                    if (
                        select.input_value()
                        == expected_age
                    ):

                        age_verified = True
                        break

            if not age_verified:

                _debug_dom(
                    page
                )

                raise RuntimeError(
                    f"Age selection was "
                    f"not verified: "
                    f"expected "
                    f"'{expected_age}'."
                )

            print(
                f"Verified age before Next: "
                f"'{expected_age}'"
            )

        # -----------------------------------------------------
        # Verify radio questions.
        # -----------------------------------------------------

        if field_name in {
            "gender",
            "caste",
            "disability",
            "minority",
            "isStudent",
            "isBpl",
        }:

            expected_answer = (
                _profile_answer(
                    profile,
                    field_name,
                )
            )

            verified_radio = (
                _find_matching_radio(
                    page,
                    field_name,
                    expected_answer,
                )
            )

            if (
                verified_radio is not None
                and verified_radio.is_checked()
            ):

                print(
                    f"Verified "
                    f"{field_name} before Next: "
                    f"{verified_radio.get_attribute('value')}"
                )

            else:

                _debug_dom(
                    page
                )

                raise RuntimeError(
                    f"{field_name} selection "
                    f"was not verified."
                )

        # -----------------------------------------------------
        # Next / Submit.
        # -----------------------------------------------------

        if not _click_next(
            page
        ):

            _debug_dom(
                page
            )

            raise RuntimeError(
                f"Could not find "
                f"Next/Submit after "
                f"answering "
                f"'{field_name}'."
            )

        print(
            f"Clicked Next/Submit after "
            f"{field_name}"
        )

        page.wait_for_timeout(
            1000
        )

    raise RuntimeError(
        "myScheme questionnaire exceeded "
        f"the safety limit of "
        f"{max_steps} steps."
    )


def fetch_schemes(
    profile: dict[str, Any],
) -> list[dict[str, Any]]:

    profile = _normalise_profile(
        profile
    )

    print(
        "Starting myScheme live retrieval..."
    )

    print(
        f"Profile used: {profile}"
    )

    try:

        with sync_playwright() as playwright:

            print(
                "Launching Chromium..."
            )

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

                print(
                    f"Opening myScheme: "
                    f"{MYSCHEME_SEARCH_URL}"
                )

                cards = (
                    _run_myscheme_questionnaire(
                        page,
                        profile,
                    )
                )

                print(
                    f"myScheme returned "
                    f"{len(cards)} "
                    f"scheme links."
                )

                if not cards:

                    print(
                        "No real scheme links "
                        "were returned."
                    )

                    return []

                state = str(
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

                for index, card in enumerate(
                    cards,
                    start=1,
                ):

                    url = card.get(
                        "url",
                        "",
                    )

                    print()
                    print(
                        f"Parsing scheme "
                        f"{index}/{len(cards)}: "
                        f"{url}"
                    )

                    if not _is_real_scheme_url(
                        url
                    ):

                        continue

                    try:

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

                    except PlaywrightTimeoutError:

                        print(
                            f"Timeout loading "
                            f"{url}"
                        )

                    except Exception as exc:

                        print(
                            f"Error loading "
                            f"{url}: {exc}"
                        )

                print()
                print(
                    f"Successfully parsed "
                    f"{len(schemes)} "
                    f"live scheme records."
                )

                return schemes

            finally:

                browser.close()

    except Exception as exc:

        print()
        print("=" * 60)
        print("fetch_schemes FAILED")
        print("=" * 60)
        print(
            f"Error type: "
            f"{type(exc).__name__}"
        )
        print(
            f"Error: {exc}"
        )
        print("=" * 60)

        return []


if __name__ == "__main__":

    print(
        "Running myScheme live retrieval "
        "smoke test..."
    )

    test_profile = {
        "gender": "Male",
        "age": 18,
        "state": "Andhra Pradesh",
        "location": "Andhra Pradesh",
        "residence": "Rural",
        "caste": "SC",
        "disability": "No",
        "minority": "No",
        "is_student": True,
        "is_bpl": False,
    }

    results = fetch_schemes(
        test_profile
    )

    print()
    print(
        f"RESULT COUNT: "
        f"{len(results)}"
    )

    for index, scheme in enumerate(
        results,
        start=1,
    ):

        print()
        print(
            f"[{index}] "
            f"{scheme.get('scheme_name')}"
        )

        print(
            f"URL: "
            f"{scheme.get('url')}"
        )

        print(
            f"SOURCE: "
            f"{scheme.get('source')}"
        )

        print(
            f"STATE: "
            f"{scheme.get('state')}"
        )

        print(
            f"FETCHED_AT: "
            f"{scheme.get('fetched_at')}"
        )
