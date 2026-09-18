"""
SkillSetu - Livelihood Worker UI

Features:
- Livelihood profile
- Live job opportunities
- Target-role filtering
- Live government schemes from myScheme
- Profile-fit + RAG scheme recommendations
- All live schemes view
- Sarvam AI voice assistant
"""

import re

import streamlit as st

from features.livelihood import (
    create_livelihood_profile,
    get_livelihood_opportunities,
    get_livelihood_schemes,
    get_livelihood_summary,
)

from features.voice import (
    process_voice_turn,
)


# ============================================================
# HELPERS
# ============================================================

def _split_skills(value):
    """
    Convert comma-separated skills into a clean list.
    """

    if not value:
        return []

    return [
        skill.strip()
        for skill in str(value).split(",")
        if skill.strip()
    ]


def _normalize(value):
    return " ".join(
        str(value or "")
        .lower()
        .strip()
        .split()
    )


def _get_profile_value(
    profile,
    key,
    default="",
):
    """
    Supports both dataclass/object profiles
    and dictionary profiles.
    """

    if profile is None:
        return default

    if isinstance(profile, dict):
        return profile.get(
            key,
            default,
        )

    return getattr(
        profile,
        key,
        default,
    )


def _get_score(item):
    """
    Safely retrieve a job match score.
    """

    try:
        return float(
            item.get(
                "score",
                0,
            )
        )
    except Exception:
        return 0.0


# ============================================================
# TARGET ROLE FAMILIES
# ============================================================

ROLE_FAMILIES = {
    "driver": [
        "driver",
        "delivery driver",
        "truck driver",
        "van driver",
        "cab driver",
        "taxi driver",
        "chauffeur",
        "courier driver",
    ],

    "farmer": [
        "farmer",
        "farm worker",
        "agriculture worker",
        "agricultural worker",
    ],

    "data analyst": [
        "data analyst",
        "business analyst",
        "reporting analyst",
        "analytics analyst",
        "bi analyst",
    ],

    "software developer": [
        "software developer",
        "software engineer",
        "application developer",
        "programmer",
    ],

    "web developer": [
        "web developer",
        "frontend developer",
        "front end developer",
        "backend developer",
        "back end developer",
        "full stack developer",
        "full-stack developer",
    ],

    "electrician": [
        "electrician",
        "electrical technician",
        "electrical worker",
    ],

    "mechanic": [
        "mechanic",
        "automobile mechanic",
        "automotive mechanic",
        "service technician",
    ],

    "sales": [
        "sales executive",
        "sales representative",
        "sales associate",
        "sales officer",
    ],

    "accountant": [
        "accountant",
        "accounts executive",
        "accounts assistant",
        "bookkeeper",
    ],

    "teacher": [
        "teacher",
        "school teacher",
        "tutor",
        "instructor",
    ],
}


def _role_terms(target_role):
    target = _normalize(
        target_role
    )

    if not target:
        return []

    if target in ROLE_FAMILIES:
        return ROLE_FAMILIES[
            target
        ]

    # Check whether entered role contains
    # one of our known role families.
    for family, terms in (
        ROLE_FAMILIES.items()
    ):
        if (
            family in target
            or target in family
        ):
            return terms

    return [target]


def _phrase_in_title(
    title,
    phrase,
):
    title = _normalize(
        title
    )

    phrase = _normalize(
        phrase
    )

    if not title or not phrase:
        return False

    pattern = (
        r"\b"
        + re.escape(
            phrase
        )
        + r"\b"
    )

    return bool(
        re.search(
            pattern,
            title,
            flags=re.IGNORECASE,
        )
    )


def _is_target_role_job(
    item,
    target_role,
):
    """
    IMPORTANT:

    Direct target-role recommendations are based
    on the JOB TITLE.

    We deliberately do not use description text here,
    because a Data Scientist description could contain
    a word such as "driving" and incorrectly appear as
    a Driver recommendation.
    """

    opportunity = item.get(
        "opportunity",
        {},
    )

    title = opportunity.get(
        "title",
        "",
    )

    terms = _role_terms(
        target_role
    )

    if not terms:
        return True

    return any(
        _phrase_in_title(
            title,
            term,
        )
        for term in terms
    )


# ============================================================
# JOB FILTERS
# ============================================================

def _filter_jobs(
    jobs,
    keyword="",
    minimum_score=0,
    work_mode="All",
):
    keyword = _normalize(
        keyword
    )

    filtered = []

    for item in jobs:
        opportunity = item.get(
            "opportunity",
            {},
        )

        score = _get_score(
            item
        )

        if score < minimum_score:
            continue

        if keyword:
            searchable = _normalize(
                " ".join(
                    [
                        opportunity.get(
                            "title",
                            "",
                        ),
                        opportunity.get(
                            "company",
                            "",
                        ),
                        opportunity.get(
                            "location",
                            "",
                        ),
                        " ".join(
                            opportunity.get(
                                "tags",
                                [],
                            )
                            or []
                        ),
                    ]
                )
            )

            if keyword not in searchable:
                continue

        if work_mode == "Remote":
            if not opportunity.get(
                "remote",
                False,
            ):
                continue

        elif work_mode == "On-site":
            if opportunity.get(
                "remote",
                False,
            ):
                continue

        filtered.append(
            item
        )

    return filtered


# ============================================================
# JOB CARD
# ============================================================

def _render_job_card(
    item,
    index,
    key_prefix,
):
    opportunity = item.get(
        "opportunity",
        {},
    )

    title = opportunity.get(
        "title",
        "Opportunity",
    )

    company = opportunity.get(
        "company",
        "Company not specified",
    )

    location = opportunity.get(
        "location",
        "Location not specified",
    )

    score = _get_score(
        item
    )

    matched_skills = item.get(
        "matched_skills",
        [],
    )

    missing_skills = item.get(
        "missing_skills",
        [],
    )

    reasons = item.get(
        "reasons",
        [],
    )

    remote = opportunity.get(
        "remote",
        False,
    )

    source = opportunity.get(
        "source",
        "Live API",
    )

    fetched_at = opportunity.get(
        "fetched_at",
        "",
    )

    url = opportunity.get(
        "url",
        "",
    )

    description = opportunity.get(
        "description",
        "",
    )

    with st.container(
        border=True
    ):
        st.markdown(
            f"### {index}. {title}"
        )

        st.write(
            f"**Company:** {company}"
        )

        st.write(
            f"**Location:** {location}"
        )

        st.write(
            "**Work mode:** "
            + (
                "Remote"
                if remote
                else "On-site / Not specified"
            )
        )

        st.metric(
            "SkillSetu Match",
            f"{score:.0f}%",
        )

        if matched_skills:
            st.write(
                "**Matched skills:** "
                + ", ".join(
                    matched_skills
                )
            )

        if missing_skills:
            st.write(
                "**Potential skill gaps:** "
                + ", ".join(
                    missing_skills[:8]
                )
            )

        if reasons:
            with st.expander(
                "Why this match?"
            ):
                for reason in reasons:
                    st.write(
                        f"• {reason}"
                    )

        if description:
            with st.expander(
                "Job description"
            ):
                st.write(
                    description[:1800]
                )

        st.caption(
            f"Source: {source}"
            + (
                f" • Fetched: {fetched_at}"
                if fetched_at
                else ""
            )
        )

        if url:
            st.link_button(
                "Open Live Job",
                url,
                key=(
                    f"{key_prefix}_"
                    f"{index}"
                ),
            )


# ============================================================
# SCHEME CARD
# ============================================================

def _render_scheme_card(
    item,
    index,
    key_prefix,
    detailed=True,
):
    name = item.get(
        "scheme_name",
        "Government Scheme",
    )

    fit_score = item.get(
        "fit_score",
        0,
    )

    combined_score = item.get(
        "combined_score",
        fit_score,
    )

    fit_label = item.get(
        "fit_label",
        "Possible fit",
    )

    reasons = item.get(
        "fit_reasons",
        [],
    )

    warnings = item.get(
        "fit_warnings",
        [],
    )

    text = item.get(
        "text",
        "",
    )

    state = item.get(
        "state",
        "",
    )

    category = item.get(
        "category",
        "",
    )

    source = item.get(
        "source",
        "myScheme",
    )

    fetched_at = item.get(
        "fetched_at",
        "",
    )

    url = item.get(
        "url",
        "",
    )

    with st.container(
        border=True
    ):
        st.markdown(
            f"### {index}. {name}"
        )

        col1, col2 = st.columns(
            [1, 2]
        )

        with col1:
            st.metric(
                "Profile Fit",
                f"{fit_score}%",
            )

        with col2:
            if fit_label == "Strong fit":
                st.success(
                    "🟢 Strong fit"
                )

            elif fit_label == "Possible fit":
                st.info(
                    "🟡 Possible fit"
                )

            else:
                st.warning(
                    "⚪ Weak fit"
                )

        if (
            combined_score
            != fit_score
        ):
            st.caption(
                "Combined profile + RAG score: "
                f"{combined_score}"
            )

        if text:
            if detailed:
                st.write(
                    text[:1400]
                )
            else:
                st.write(
                    text[:550]
                )

        if detailed and reasons:
            st.markdown(
                "**Why this may match your profile:**"
            )

            for reason in reasons:
                st.write(
                    f"✓ {reason}"
                )

        if detailed and warnings:
            with st.expander(
                "⚠️ Things to verify"
            ):
                for warning in warnings:
                    st.write(
                        f"• {warning}"
                    )

        if state:
            st.write(
                f"**State:** {state}"
            )

        if category:
            st.write(
                f"**Category:** {category}"
            )

        st.caption(
            f"Source: {source}"
            + (
                f" • Fetched: {fetched_at}"
                if fetched_at
                else ""
            )
        )

        if url:
            st.link_button(
                "Open Official myScheme Page",
                url,
                key=(
                    f"{key_prefix}_"
                    f"{index}"
                ),
            )


# ============================================================
# MAIN LIVELIHOOD UI
# ============================================================

def render_livelihood_ui():
    st.title(
        "🌾 SkillSetu Livelihood Assistant"
    )

    st.write(
        "Discover live opportunities, government "
        "schemes and guidance using one shared "
        "SkillSetu profile."
    )

    tabs = st.tabs(
        [
            "👤 My Profile",
            "💼 Opportunities",
            "🏛️ Government Schemes",
            "🎙️ Voice Assistant",
        ]
    )

    # ========================================================
    # TAB 1 - PROFILE
    # ========================================================

    with tabs[0]:
        st.subheader(
            "👤 Build Your Profile"
        )

        st.caption(
            "Your profile is used by the same "
            "SkillSetu matching and recommendation "
            "pipeline."
        )

        existing = st.session_state.get(
            "livelihood_profile"
        )

        with st.form(
            "livelihood_profile_form"
        ):
            name = st.text_input(
                "Name",
                value=_get_profile_value(
                    existing,
                    "name",
                    "",
                ),
            )

            col1, col2 = st.columns(2)

            with col1:
                location = st.text_input(
                    "City / District",
                    value=_get_profile_value(
                        existing,
                        "location",
                        "",
                    ),
                    placeholder="Guntur",
                )

            with col2:
                state_options = [
                    "Andhra Pradesh",
                    "Telangana",
                    "Tamil Nadu",
                    "Karnataka",
                    "Kerala",
                    "Maharashtra",
                    "Odisha",
                    "Other",
                ]

                existing_state = (
                    _get_profile_value(
                        existing,
                        "state",
                        "Andhra Pradesh",
                    )
                )

                state_index = 0

                if (
                    existing_state
                    in state_options
                ):
                    state_index = (
                        state_options.index(
                            existing_state
                        )
                    )

                state = st.selectbox(
                    "State",
                    state_options,
                    index=state_index,
                )

            col1, col2, col3 = (
                st.columns(3)
            )

            with col1:
                age = st.number_input(
                    "Age",
                    min_value=14,
                    max_value=100,
                    value=int(
                        _get_profile_value(
                            existing,
                            "age",
                            25,
                        )
                    ),
                )

            with col2:
                gender_options = [
                    "Male",
                    "Female",
                    "Other",
                ]

                existing_gender = (
                    _get_profile_value(
                        existing,
                        "gender",
                        "Male",
                    )
                )

                gender_index = 0

                if (
                    existing_gender
                    in gender_options
                ):
                    gender_index = (
                        gender_options.index(
                            existing_gender
                        )
                    )

                gender = st.selectbox(
                    "Gender",
                    gender_options,
                    index=gender_index,
                )

            with col3:
                residence_options = [
                    "Rural",
                    "Urban",
                ]

                existing_residence = (
                    _get_profile_value(
                        existing,
                        "residence",
                        "Rural",
                    )
                )

                residence_index = 0

                if (
                    existing_residence
                    in residence_options
                ):
                    residence_index = (
                        residence_options.index(
                            existing_residence
                        )
                    )

                residence = st.selectbox(
                    "Residence",
                    residence_options,
                    index=residence_index,
                )

            education = st.text_input(
                "Education",
                value=_get_profile_value(
                    existing,
                    "education",
                    "",
                ),
                placeholder="12th Pass",
            )

            occupation = st.text_input(
                "Current Occupation",
                value=_get_profile_value(
                    existing,
                    "occupation",
                    "",
                ),
                placeholder="Farmer",
            )

            skills_value = ", ".join(
                _get_profile_value(
                    existing,
                    "skills",
                    [],
                )
                or []
            )

            skills_text = st.text_input(
                "Skills",
                value=skills_value,
                placeholder=(
                    "Driving, Farming, Smartphone"
                ),
                help=(
                    "Enter skills separated by commas."
                ),
            )

            target_role = st.text_input(
                "Target Role",
                value=_get_profile_value(
                    existing,
                    "target_role",
                    "",
                ),
                placeholder="Driver",
            )

            col1, col2 = st.columns(2)

            with col1:
                experience_options = [
                    "Fresher",
                    "0-1 years",
                    "1-3 years",
                    "3-5 years",
                    "5+ years",
                ]

                existing_experience = (
                    _get_profile_value(
                        existing,
                        "experience",
                        "Fresher",
                    )
                )

                experience_index = 0

                if (
                    existing_experience
                    in experience_options
                ):
                    experience_index = (
                        experience_options.index(
                            existing_experience
                        )
                    )

                experience = st.selectbox(
                    "Experience",
                    experience_options,
                    index=experience_index,
                )

            with col2:
                preference_options = [
                    "local",
                    "remote",
                    "any",
                ]

                existing_preference = (
                    _normalize(
                        _get_profile_value(
                            existing,
                            "work_preference",
                            "local",
                        )
                    )
                )

                preference_index = 0

                if (
                    existing_preference
                    in preference_options
                ):
                    preference_index = (
                        preference_options.index(
                            existing_preference
                        )
                    )

                work_preference = (
                    st.selectbox(
                        "Work Preference",
                        preference_options,
                        index=preference_index,
                    )
                )

            language_options = [
                "Telugu",
                "English",
                "Hindi",
            ]

            existing_language = (
                _get_profile_value(
                    existing,
                    "language",
                    "Telugu",
                )
            )

            language_index = 0

            if (
                existing_language
                in language_options
            ):
                language_index = (
                    language_options.index(
                        existing_language
                    )
                )

            language = st.selectbox(
                "Preferred Language",
                language_options,
                index=language_index,
            )

            st.markdown(
                "### Government Scheme Profile"
            )

            col1, col2 = st.columns(2)

            with col1:
                caste_options = [
                    "General",
                    "OBC",
                    "SC",
                    "ST",
                    "Other",
                ]

                existing_caste = (
                    _get_profile_value(
                        existing,
                        "caste",
                        "General",
                    )
                )

                caste_index = 0

                if (
                    existing_caste
                    in caste_options
                ):
                    caste_index = (
                        caste_options.index(
                            existing_caste
                        )
                    )

                caste = st.selectbox(
                    "Social Category",
                    caste_options,
                    index=caste_index,
                )

                disability_options = [
                    "No",
                    "Yes",
                ]

                existing_disability = (
                    _get_profile_value(
                        existing,
                        "disability",
                        "No",
                    )
                )

                disability_index = (
                    1
                    if existing_disability
                    == "Yes"
                    else 0
                )

                disability = st.selectbox(
                    "Person with Disability?",
                    disability_options,
                    index=disability_index,
                )

                minority_options = [
                    "No",
                    "Yes",
                ]

                existing_minority = (
                    _get_profile_value(
                        existing,
                        "minority",
                        "No",
                    )
                )

                minority_index = (
                    1
                    if existing_minority
                    == "Yes"
                    else 0
                )

                minority = st.selectbox(
                    "Minority Community?",
                    minority_options,
                    index=minority_index,
                )

            with col2:
                employment_options = [
                    "Unemployed",
                    "Employed",
                    "Self Employed",
                    "Daily Wage Worker",
                    "Other",
                ]

                existing_employment = (
                    _get_profile_value(
                        existing,
                        "employment_status",
                        "Unemployed",
                    )
                )

                employment_index = 0

                if (
                    existing_employment
                    in employment_options
                ):
                    employment_index = (
                        employment_options.index(
                            existing_employment
                        )
                    )

                employment_status = (
                    st.selectbox(
                        "Employment Status",
                        employment_options,
                        index=employment_index,
                    )
                )

                marital_options = [
                    "Never Married",
                    "Married",
                    "Widowed",
                    "Divorced",
                    "Separated",
                ]

                existing_marital = (
                    _get_profile_value(
                        existing,
                        "marital_status",
                        "Never Married",
                    )
                )

                marital_index = 0

                if (
                    existing_marital
                    in marital_options
                ):
                    marital_index = (
                        marital_options.index(
                            existing_marital
                        )
                    )

                marital_status = (
                    st.selectbox(
                        "Marital Status",
                        marital_options,
                        index=marital_index,
                    )
                )

                is_student = st.checkbox(
                    "Currently a Student",
                    value=bool(
                        _get_profile_value(
                            existing,
                            "is_student",
                            False,
                        )
                    ),
                )

            col1, col2 = st.columns(2)

            with col1:
                is_bpl = st.checkbox(
                    "BPL / Below Poverty Line",
                    value=bool(
                        _get_profile_value(
                            existing,
                            "is_bpl",
                            False,
                        )
                    ),
                )

            with col2:
                is_economic_distress = (
                    st.checkbox(
                        "Economic Distress",
                        value=bool(
                            _get_profile_value(
                                existing,
                                "is_economic_distress",
                                False,
                            )
                        ),
                    )
                )

            col1, col2 = st.columns(2)

            with col1:
                annual_family_income = (
                    st.number_input(
                        "Annual Family Income (₹)",
                        min_value=0,
                        value=int(
                            _get_profile_value(
                                existing,
                                "annual_family_income",
                                0,
                            )
                        ),
                        step=10000,
                    )
                )

            with col2:
                annual_parent_income = (
                    st.number_input(
                        "Annual Parent Income (₹)",
                        min_value=0,
                        value=int(
                            _get_profile_value(
                                existing,
                                "annual_parent_income",
                                0,
                            )
                        ),
                        step=10000,
                    )
                )

            save_profile = (
                st.form_submit_button(
                    "Save Profile",
                    type="primary",
                )
            )

        if save_profile:
            profile = (
                create_livelihood_profile(
                    name=name,
                    location=location,
                    skills=_split_skills(
                        skills_text
                    ),
                    education=education,
                    occupation=occupation,
                    target_role=target_role,
                    experience=experience,
                    work_preference=(
                        work_preference
                    ),
                    language=language,
                    age=age,
                    gender=gender,
                    state=state,
                    residence=residence,
                    caste=caste,
                    disability=disability,
                    minority=minority,
                    is_student=is_student,
                    employment_status=(
                        employment_status
                    ),
                    marital_status=(
                        marital_status
                    ),
                    is_bpl=is_bpl,
                    is_economic_distress=(
                        is_economic_distress
                    ),
                    annual_family_income=(
                        annual_family_income
                    ),
                    annual_parent_income=(
                        annual_parent_income
                    ),
                )
            )

            st.session_state[
                "livelihood_profile"
            ] = profile

            # Clear old results because the
            # profile has changed.
            st.session_state.pop(
                "livelihood_jobs",
                None,
            )

            st.session_state.pop(
                "livelihood_scheme_result",
                None,
            )

            st.success(
                "Profile saved successfully."
            )

        profile = st.session_state.get(
            "livelihood_profile"
        )

        if profile:
            st.divider()

            st.subheader(
                "Current Profile"
            )

            summary = (
                get_livelihood_summary(
                    profile
                )
            )

            col1, col2 = st.columns(2)

            with col1:
                st.write(
                    "**Name:**",
                    summary.get(
                        "name",
                        "",
                    ),
                )

                st.write(
                    "**Location:**",
                    summary.get(
                        "location",
                        "",
                    ),
                )

                st.write(
                    "**State:**",
                    summary.get(
                        "state",
                        "",
                    ),
                )

                st.write(
                    "**Occupation:**",
                    summary.get(
                        "occupation",
                        "",
                    ),
                )

                st.write(
                    "**Target Role:**",
                    summary.get(
                        "target_role",
                        "",
                    ),
                )

            with col2:
                st.write(
                    "**Skills:**",
                    summary.get(
                        "skills",
                        "",
                    ),
                )

                st.write(
                    "**Experience:**",
                    summary.get(
                        "experience",
                        "",
                    ),
                )

                st.write(
                    "**Residence:**",
                    summary.get(
                        "residence",
                        "",
                    ),
                )

                st.write(
                    "**Employment:**",
                    summary.get(
                        "employment_status",
                        "",
                    ),
                )

                st.write(
                    "**Language:**",
                    summary.get(
                        "language",
                        "",
                    ),
                )

    # ========================================================
    # TAB 2 - OPPORTUNITIES
    # ========================================================

    with tabs[1]:
        st.subheader(
            "💼 Live Opportunities"
        )

        profile = st.session_state.get(
            "livelihood_profile"
        )

        if not profile:
            st.warning(
                "Create your profile first."
            )

        else:
            target_role = (
                _get_profile_value(
                    profile,
                    "target_role",
                    "",
                )
            )

            st.write(
                "**Target role:** "
                + (
                    target_role
                    or "Open to opportunities"
                )
            )

            st.caption(
                "SkillSetu fetches a live external "
                "job feed and ranks it using the "
                "shared matching engine."
            )

            if st.button(
                "Find Live Opportunities",
                type="primary",
            ):
                with st.spinner(
                    "Fetching live opportunities..."
                ):
                    jobs = (
                        get_livelihood_opportunities(
                            profile,
                            limit=30,
                        )
                    )

                    st.session_state[
                        "livelihood_jobs"
                    ] = jobs

            jobs = st.session_state.get(
                "livelihood_jobs"
            )

            if jobs is not None:
                if not jobs:
                    st.warning(
                        "No live opportunities were "
                        "returned by the current source."
                    )

                else:
                    target_jobs = []

                    other_jobs = []

                    for item in jobs:
                        if _is_target_role_job(
                            item,
                            target_role,
                        ):
                            target_jobs.append(
                                item
                            )
                        else:
                            other_jobs.append(
                                item
                            )

                    st.markdown(
                        "### Filters"
                    )

                    f1, f2, f3 = (
                        st.columns(3)
                    )

                    with f1:
                        job_keyword = (
                            st.text_input(
                                "Search jobs",
                                key=(
                                    "livelihood_"
                                    "job_keyword"
                                ),
                                placeholder=(
                                    "driver, python..."
                                ),
                            )
                        )

                    with f2:
                        minimum_score = (
                            st.slider(
                                "Minimum match %",
                                min_value=0,
                                max_value=100,
                                value=0,
                                step=5,
                                key=(
                                    "livelihood_"
                                    "minimum_score"
                                ),
                            )
                        )

                    with f3:
                        work_mode = (
                            st.selectbox(
                                "Work mode",
                                [
                                    "All",
                                    "Remote",
                                    "On-site",
                                ],
                                key=(
                                    "livelihood_"
                                    "work_mode"
                                ),
                            )
                        )

                    filtered_target = (
                        _filter_jobs(
                            target_jobs,
                            keyword=job_keyword,
                            minimum_score=(
                                minimum_score
                            ),
                            work_mode=(
                                work_mode
                            ),
                        )
                    )

                    filtered_other = (
                        _filter_jobs(
                            other_jobs,
                            keyword=job_keyword,
                            minimum_score=(
                                minimum_score
                            ),
                            work_mode=(
                                work_mode
                            ),
                        )
                    )

                    m1, m2, m3 = (
                        st.columns(3)
                    )

                    with m1:
                        st.metric(
                            "Live Jobs Processed",
                            len(jobs),
                        )

                    with m2:
                        st.metric(
                            "Target-Role Matches",
                            len(
                                filtered_target
                            ),
                        )

                    with m3:
                        st.metric(
                            "Other Live Jobs",
                            len(
                                filtered_other
                            ),
                        )

                    st.divider()

                    st.markdown(
                        "## 🎯 Recommended for "
                        "Your Target Role"
                    )

                    if filtered_target:
                        for index, item in enumerate(
                            filtered_target,
                            start=1,
                        ):
                            _render_job_card(
                                item,
                                index,
                                "target_job",
                            )

                    else:
                        st.info(
                            "No live job titles matching "
                            f"'{target_role}' were found "
                            "in the current feed. "
                            "SkillSetu will not label "
                            "unrelated roles as direct "
                            "target-role recommendations."
                        )

                    if filtered_other:
                        st.divider()

                        with st.expander(
                            "🌐 Other Live Opportunities "
                            f"({len(filtered_other)})"
                        ):
                            st.caption(
                                "These jobs are from the "
                                "live feed but do not match "
                                "your target-role title. "
                                "They are shown only for "
                                "exploration."
                            )

                            for index, item in enumerate(
                                filtered_other,
                                start=1,
                            ):
                                _render_job_card(
                                    item,
                                    index,
                                    "other_job",
                                )

                    st.caption(
                        "Current live opportunity source "
                        "is primarily European. "
                        "SkillSetu therefore does not "
                        "claim these are local Guntur "
                        "or India vacancies."
                    )

            else:
                st.info(
                    "Click **Find Live Opportunities** "
                    "to search the live job feed."
                )

    # ========================================================
    # TAB 3 - GOVERNMENT SCHEMES
    # ========================================================

    with tabs[2]:
        st.subheader(
            "🏛️ Government Schemes"
        )

        profile = st.session_state.get(
            "livelihood_profile"
        )

        if not profile:
            st.warning(
                "Create your profile first."
            )

        else:
            st.caption(
                "SkillSetu searches live myScheme "
                "results, evaluates profile relevance "
                "and uses RAG for semantic ranking."
            )

            if st.button(
                "Find Government Schemes",
                type="primary",
            ):
                with st.spinner(
                    "Searching live myScheme..."
                ):
                    result = (
                        get_livelihood_schemes(
                            profile,
                            limit=5,
                        )
                    )

                    st.session_state[
                        "livelihood_scheme_result"
                    ] = result

            result = st.session_state.get(
                "livelihood_scheme_result"
            )

            if result:
                error = result.get(
                    "error",
                    "",
                )

                live_schemes = result.get(
                    "schemes",
                    [],
                )

                recommended = result.get(
                    "retrieved",
                    [],
                )

                all_ranked = result.get(
                    "all_ranked",
                    [],
                )

                indexed_chunks = result.get(
                    "indexed_chunks",
                    0,
                )

                ranking_method = result.get(
                    "ranking_method",
                    "",
                )

                if error:
                    st.warning(
                        error
                    )

                # --------------------------------------------
                # METRICS
                # --------------------------------------------

                m1, m2, m3 = (
                    st.columns(3)
                )

                with m1:
                    st.metric(
                        "Live Schemes",
                        len(
                            live_schemes
                        ),
                    )

                with m2:
                    st.metric(
                        "Recommended",
                        len(
                            recommended
                        ),
                    )

                with m3:
                    st.metric(
                        "RAG Chunks",
                        indexed_chunks,
                    )

                if ranking_method:
                    pretty_method = (
                        ranking_method
                        .replace(
                            "_plus_",
                            " + ",
                        )
                        .replace(
                            "_",
                            " ",
                        )
                        .title()
                    )

                    st.caption(
                        "Recommendation method: "
                        + pretty_method
                    )

                st.info(
                    "Scheme scores indicate profile "
                    "relevance, not guaranteed official "
                    "eligibility. Verify final eligibility "
                    "on the official myScheme page."
                )

                # --------------------------------------------
                # OPTIONAL UI FILTER
                # --------------------------------------------

                scheme_keyword = (
                    st.text_input(
                        "Filter schemes",
                        key=(
                            "livelihood_"
                            "scheme_keyword"
                        ),
                        placeholder=(
                            "farmer, training, "
                            "financial assistance..."
                        ),
                    )
                )

                normalized_keyword = (
                    _normalize(
                        scheme_keyword
                    )
                )

                if normalized_keyword:
                    recommended_display = [
                        item
                        for item in recommended
                        if normalized_keyword
                        in _normalize(
                            " ".join(
                                [
                                    item.get(
                                        "scheme_name",
                                        "",
                                    ),
                                    item.get(
                                        "text",
                                        "",
                                    ),
                                    item.get(
                                        "category",
                                        "",
                                    ),
                                ]
                            )
                        )
                    ]

                    all_display = [
                        item
                        for item in all_ranked
                        if normalized_keyword
                        in _normalize(
                            " ".join(
                                [
                                    item.get(
                                        "scheme_name",
                                        "",
                                    ),
                                    item.get(
                                        "text",
                                        "",
                                    ),
                                    item.get(
                                        "category",
                                        "",
                                    ),
                                ]
                            )
                        )
                    ]

                else:
                    recommended_display = (
                        recommended
                    )

                    all_display = (
                        all_ranked
                    )

                # --------------------------------------------
                # RECOMMENDED
                # --------------------------------------------

                if recommended_display:
                    st.divider()

                    st.markdown(
                        "## ⭐ Recommended for You"
                    )

                    st.caption(
                        "The strongest profile-relevant "
                        "schemes from the current live "
                        "myScheme results."
                    )

                    for index, item in enumerate(
                        recommended_display,
                        start=1,
                    ):
                        _render_scheme_card(
                            item,
                            index,
                            "recommended_scheme",
                            detailed=True,
                        )

                elif recommended:
                    st.info(
                        "No recommended schemes match "
                        "the current UI filter."
                    )

                elif live_schemes:
                    st.warning(
                        "Live schemes were found, but "
                        "no recommendation was produced."
                    )

                # --------------------------------------------
                # ALL LIVE SCHEMES
                # --------------------------------------------

                if all_ranked:
                    st.divider()

                    with st.expander(
                        "📋 View All Live Schemes "
                        f"({len(all_display)})"
                    ):
                        st.caption(
                            "All unique live schemes "
                            "returned for this search, "
                            "ordered by SkillSetu's "
                            "profile-relevance ranking."
                        )

                        if not all_display:
                            st.info(
                                "No live schemes match "
                                "the current UI filter."
                            )

                        for index, item in enumerate(
                            all_display,
                            start=1,
                        ):
                            _render_scheme_card(
                                item,
                                index,
                                "all_scheme",
                                detailed=False,
                            )

                # --------------------------------------------
                # OLD SESSION / FALLBACK SUPPORT
                # --------------------------------------------

                elif live_schemes:
                    st.divider()

                    with st.expander(
                        "📋 View All Live Schemes "
                        f"({len(live_schemes)})"
                    ):
                        st.caption(
                            "These are the live myScheme "
                            "results returned for the "
                            "current profile."
                        )

                        for index, scheme in enumerate(
                            live_schemes,
                            start=1,
                        ):
                            name = (
                                scheme.get(
                                    "scheme_name"
                                )
                                or scheme.get(
                                    "name"
                                )
                                or "Government Scheme"
                            )

                            description = (
                                scheme.get(
                                    "description",
                                    "",
                                )
                            )

                            url = scheme.get(
                                "url",
                                "",
                            )

                            with st.container(
                                border=True
                            ):
                                st.markdown(
                                    f"### {index}. "
                                    f"{name}"
                                )

                                if description:
                                    st.write(
                                        description[
                                            :600
                                        ]
                                    )

                                st.caption(
                                    "Live result from "
                                    "myScheme."
                                )

                                if url:
                                    st.link_button(
                                        "Open Official "
                                        "myScheme Page",
                                        url,
                                        key=(
                                            "raw_scheme_"
                                            f"{index}"
                                        ),
                                    )

                if (
                    not live_schemes
                    and not error
                ):
                    st.warning(
                        "No live schemes were returned "
                        "for this profile."
                    )

            else:
                st.info(
                    "Click **Find Government Schemes** "
                    "to search live myScheme."
                )

        st.divider()

        st.caption(
            "Live myScheme → Profile Fit → "
            "ChromaDB RAG → Ranked Recommendations"
        )

    # ========================================================
    # TAB 4 - VOICE ASSISTANT
    # ========================================================

    with tabs[3]:
        st.subheader(
            "🎙️ Voice Assistant"
        )

        profile = st.session_state.get(
            "livelihood_profile"
        )

        if not profile:
            st.warning(
                "Create your profile first."
            )

        else:
            preferred_language = (
                _get_profile_value(
                    profile,
                    "language",
                    "Telugu",
                )
            )

            st.write(
                "**Preferred language:** "
                f"{preferred_language}"
            )

            st.caption(
                "Speak naturally. SkillSetu uses "
                "Sarvam AI for speech-to-text, "
                "translation and speech output."
            )

            audio_value = st.audio_input(
                "Ask SkillSetu about jobs, "
                "skills or government schemes"
            )

            if audio_value is not None:
                audio_bytes = (
                    audio_value.getvalue()
                )

                if st.button(
                    "Process Voice Question",
                    type="primary",
                ):
                    try:
                        with st.spinner(
                            "Understanding your "
                            "question..."
                        ):
                            voice_result = (
                                process_voice_turn(
                                    audio_bytes,
                                    profile=profile,
                                    preferred_language=(
                                        preferred_language
                                    ),
                                    suffix=".wav",
                                )
                            )

                        st.session_state[
                            "livelihood_voice_result"
                        ] = voice_result

                    except Exception as exc:
                        st.error(
                            "Voice assistant error: "
                            f"{exc}"
                        )

            voice_result = (
                st.session_state.get(
                    "livelihood_voice_result"
                )
            )

            if voice_result:
                transcript = (
                    voice_result.get(
                        "transcript",
                        "",
                    )
                )

                detected_language = (
                    voice_result.get(
                        "detected_language",
                        "",
                    )
                )

                response_text = (
                    voice_result.get(
                        "response_text",
                        "",
                    )
                )

                audio_response = (
                    voice_result.get(
                        "audio_bytes"
                    )
                )

                if transcript:
                    st.markdown(
                        "### You said"
                    )

                    st.write(
                        transcript
                    )

                if detected_language:
                    st.caption(
                        "Detected language: "
                        f"{detected_language}"
                    )

                if response_text:
                    st.markdown(
                        "### SkillSetu"
                    )

                    st.write(
                        response_text
                    )

                if audio_response:
                    st.audio(
                        audio_response,
                        format="audio/wav",
                    )

            st.divider()

            st.caption(
                "Voice pipeline: "
                "Microphone → Sarvam STT → "
                "SkillSetu Guidance → Translation → "
                "Sarvam TTS"
            )

    # ========================================================
    # ARCHITECTURE / JUDGE PROOF
    # ========================================================

    st.divider()

    with st.expander(
        "🧠 How SkillSetu Works"
    ):
        st.markdown(
            """
**One shared guidance architecture**

**Opportunities**

`Livelihood Profile → Live Job API → Shared Matching Engine → Target-Role Validation → Recommendations`

**Government Schemes**

`Livelihood Profile → Live myScheme → Profile-Fit Ranking → ChromaDB RAG → Recommendations`

**Voice**

`Microphone → Sarvam AI STT → SkillSetu → Translation → Sarvam AI TTS`

SkillSetu keeps live-data sources visible and does not treat a recommendation as guaranteed scheme eligibility.
"""
        )