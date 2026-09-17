"""
SkillSetu - Livelihood Worker Streamlit UI

Includes:
- Livelihood profile
- Live opportunity matching
- User-controlled opportunity filtering
- Live myScheme recommendations
- Scheme result filtering
- Telugu / English / Hindi voice assistant
"""

import streamlit as st

from features.livelihood import (
    create_livelihood_profile,
    get_livelihood_opportunities,
    get_livelihood_schemes,
    get_livelihood_summary,
)

from features.voice import (
    build_livelihood_voice_response,
    process_voice_turn,
    translate_text,
    text_to_speech,
)


# ============================================================
# HELPERS
# ============================================================

def _split_skills(value):
    if not value:
        return []

    return [
        skill.strip()
        for skill in value.split(",")
        if skill.strip()
    ]


def _get_match_score(result):
    """
    Supports the different score keys used during
    SkillSetu development.
    """
    try:
        return int(
            result.get(
                "score",
                result.get(
                    "match_score",
                    result.get(
                        "match_percentage",
                        0,
                    ),
                ),
            )
            or 0
        )
    except (TypeError, ValueError):
        return 0


def _filter_opportunities(
    jobs,
    role_keyword="",
    minimum_match=0,
    work_mode="All",
):
    """
    Filter AFTER the shared matching engine.

    This is intentional:
    - live jobs are still fetched normally
    - matching_engine() still ranks them
    - user can narrow the displayed results
    """

    filtered = []

    keyword = str(
        role_keyword or ""
    ).strip().lower()

    for result in jobs or []:
        opportunity = result.get(
            "opportunity",
            {},
        )

        title = str(
            opportunity.get(
                "title",
                "",
            )
        ).lower()

        score = _get_match_score(
            result
        )

        remote = bool(
            opportunity.get(
                "remote",
                False,
            )
        )

        # Job-title filter
        if keyword:
            if keyword not in title:
                continue

        # Match percentage filter
        if score < minimum_match:
            continue

        # Work-mode filter
        if (
            work_mode == "Remote"
            and not remote
        ):
            continue

        if (
            work_mode == "On-site"
            and remote
        ):
            continue

        filtered.append(
            result
        )

    return filtered


def _scheme_search_text(item):
    """
    Build searchable text for a scheme result.

    We only filter what live myScheme / RAG already returned.
    We do NOT invent eligibility.
    """

    values = [
        item.get("scheme_name", ""),
        item.get("text", ""),
        item.get("state", ""),
        item.get("category", ""),
        item.get("source", ""),
    ]

    return " ".join(
        str(value)
        for value in values
        if value
    ).lower()


def _filter_schemes(
    retrieved,
    keyword="",
    state_filter="All",
):
    """
    Simple transparent filter over live myScheme results.

    This is NOT an eligibility engine.
    """

    filtered = []

    keyword = str(
        keyword or ""
    ).strip().lower()

    for item in retrieved or []:
        searchable = _scheme_search_text(
            item
        )

        if keyword:
            if keyword not in searchable:
                continue

        item_state = str(
            item.get(
                "state",
                "",
            )
        ).strip()

        if state_filter == "My State":
            # State filtering is handled in the UI because
            # we need the active profile there.
            pass

        filtered.append(
            item
        )

    return filtered


# ============================================================
# MAIN UI
# ============================================================

def render_livelihood_ui():
    st.title("🌾 SkillSetu")

    st.subheader(
        "Livelihood & Rural Opportunity Assistant"
    )

    st.caption(
        "Live opportunities, government schemes "
        "and livelihood guidance from one shared engine."
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
    # PROFILE
    # ========================================================

    with tabs[0]:
        st.subheader(
            "Create your livelihood profile"
        )

        st.info(
            "These details help SkillSetu search "
            "for relevant jobs and government schemes."
        )

        with st.form(
            "livelihood_profile_form"
        ):
            col1, col2 = st.columns(2)

            with col1:
                name = st.text_input(
                    "Name",
                    value="Ravi",
                )

                location = st.text_input(
                    "Location / District",
                    value="Guntur",
                )

                state = st.selectbox(
                    "State",
                    [
                        "Andhra Pradesh",
                        "Arunachal Pradesh",
                        "Assam",
                        "Bihar",
                        "Chhattisgarh",
                        "Goa",
                        "Gujarat",
                        "Haryana",
                        "Himachal Pradesh",
                        "Jharkhand",
                        "Karnataka",
                        "Kerala",
                        "Madhya Pradesh",
                        "Maharashtra",
                        "Manipur",
                        "Meghalaya",
                        "Mizoram",
                        "Nagaland",
                        "Odisha",
                        "Punjab",
                        "Rajasthan",
                        "Sikkim",
                        "Tamil Nadu",
                        "Telangana",
                        "Tripura",
                        "Uttar Pradesh",
                        "Uttarakhand",
                        "West Bengal",
                        "Delhi",
                        "Jammu and Kashmir",
                        "Ladakh",
                        "Puducherry",
                    ],
                )

                age = st.number_input(
                    "Age",
                    min_value=1,
                    max_value=115,
                    value=25,
                    step=1,
                )

                gender = st.selectbox(
                    "Gender",
                    [
                        "Male",
                        "Female",
                        "Transgender",
                    ],
                )

                residence = st.selectbox(
                    "Area of residence",
                    [
                        "Rural",
                        "Urban",
                    ],
                )

                education = st.selectbox(
                    "Education",
                    [
                        "No formal education",
                        "10th",
                        "12th",
                        "Diploma",
                        "Graduate",
                        "Other",
                    ],
                    index=2,
                )

                occupation = st.text_input(
                    "Current occupation",
                    value="Farmer",
                )

                skills_text = st.text_input(
                    "Skills",
                    value=(
                        "Driving, Farming, Smartphone"
                    ),
                    help=(
                        "Separate multiple skills "
                        "with commas."
                    ),
                )

            with col2:
                target_role = st.text_input(
                    "Target role",
                    value="Driver",
                )

                experience = st.selectbox(
                    "Experience",
                    [
                        "fresher",
                        "beginner",
                        "1-3 years",
                        "3+ years",
                    ],
                    index=2,
                )

                work_preference = st.selectbox(
                    "Work preference",
                    [
                        "local",
                        "remote",
                        "Any",
                    ],
                )

                language = st.selectbox(
                    "Preferred language",
                    [
                        "Telugu",
                        "English",
                        "Hindi",
                    ],
                )

                caste = st.selectbox(
                    "Social category",
                    [
                        "General",
                        "OBC",
                        "SC",
                        "ST",
                        "PVTG",
                        "DNT",
                    ],
                )

                disability = st.selectbox(
                    "Person with disability?",
                    [
                        "No",
                        "Yes",
                    ],
                )

                minority = st.selectbox(
                    "Belong to minority?",
                    [
                        "No",
                        "Yes",
                    ],
                )

                is_student = st.checkbox(
                    "Currently a student",
                    value=False,
                )

                employment_status = st.selectbox(
                    "Current employment status",
                    [
                        "Unemployed",
                        "Employed",
                        "Self-Employed/ Entrepreneur",
                    ],
                )

                marital_status = st.selectbox(
                    "Marital status",
                    [
                        "Never Married",
                        "Married",
                        "Divorced",
                        "Separated",
                        "Widowed",
                    ],
                )

                is_bpl = st.checkbox(
                    "Belong to BPL category",
                    value=True,
                )

                is_economic_distress = st.checkbox(
                    (
                        "Destitute / Penury / Extreme "
                        "Hardship / Distress"
                    ),
                    value=False,
                    help=(
                        "Select this only if this "
                        "condition applies to you."
                    ),
                )

            st.markdown(
                "#### Income information"
            )

            income_col1, income_col2 = (
                st.columns(2)
            )

            with income_col1:
                annual_family_income = (
                    st.number_input(
                        "Annual family income (₹)",
                        min_value=0,
                        value=0,
                        step=10000,
                    )
                )

            with income_col2:
                annual_parent_income = (
                    st.number_input(
                        "Annual parent income (₹)",
                        min_value=0,
                        value=0,
                        step=10000,
                    )
                )

            submitted = st.form_submit_button(
                "Save Profile",
                type="primary",
            )

        if submitted:
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
                    work_preference=work_preference,
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

            st.session_state[
                "livelihood_jobs"
            ] = []

            st.session_state[
                "livelihood_jobs_searched"
            ] = False

            st.session_state[
                "livelihood_scheme_result"
            ] = None

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

            col1, col2, col3 = (
                st.columns(3)
            )

            with col1:
                st.write(
                    "**Name:**",
                    summary["name"],
                )

                st.write(
                    "**Age:**",
                    summary["age"],
                )

                st.write(
                    "**State:**",
                    summary["state"],
                )

                st.write(
                    "**Residence:**",
                    summary["residence"],
                )

            with col2:
                st.write(
                    "**Occupation:**",
                    summary["occupation"],
                )

                st.write(
                    "**Target role:**",
                    summary["target_role"],
                )

                st.write(
                    "**Skills:**",
                    summary["skills"],
                )

                st.write(
                    "**Employment:**",
                    summary[
                        "employment_status"
                    ],
                )

            with col3:
                st.write(
                    "**BPL:**",
                    (
                        "Yes"
                        if summary["is_bpl"]
                        else "No"
                    ),
                )

                st.write(
                    "**Economic distress:**",
                    (
                        "Yes"
                        if summary[
                            "is_economic_distress"
                        ]
                        else "No"
                    ),
                )

                st.write(
                    "**Language:**",
                    summary["language"],
                )

    # ========================================================
    # OPPORTUNITIES
    # ========================================================

    with tabs[1]:
        st.subheader(
            "Live Opportunities"
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
                "Jobs are fetched live and ranked using "
                "SkillSetu's shared matching engine. "
                "Use the filters below to narrow the results."
            )

            if st.button(
                "Find Live Opportunities",
                type="primary",
            ):
                with st.spinner(
                    "Fetching and matching live jobs..."
                ):
                    jobs = (
                        get_livelihood_opportunities(
                            profile,
                            # Fetch more so the user has
                            # enough results to filter.
                            limit=20,
                        )
                    )

                    st.session_state[
                        "livelihood_jobs"
                    ] = jobs

                    st.session_state[
                        "livelihood_jobs_searched"
                    ] = True

            jobs = st.session_state.get(
                "livelihood_jobs",
                [],
            )

            searched = st.session_state.get(
                "livelihood_jobs_searched",
                False,
            )

            if jobs:
                st.markdown(
                    "### 🔎 Filter Opportunities"
                )

                filter_col1, filter_col2, filter_col3 = (
                    st.columns(3)
                )

                with filter_col1:
                    role_filter = st.text_input(
                        "Job title contains",
                        value="",
                        placeholder=(
                            "Driver, Analyst, Developer..."
                        ),
                        key="livelihood_job_role_filter",
                    )

                with filter_col2:
                    minimum_match = st.slider(
                        "Minimum match %",
                        min_value=0,
                        max_value=100,
                        value=0,
                        step=5,
                        key="livelihood_min_match",
                    )

                with filter_col3:
                    work_mode = st.selectbox(
                        "Work mode",
                        [
                            "All",
                            "Remote",
                            "On-site",
                        ],
                        key="livelihood_work_mode_filter",
                    )

                filtered_jobs = (
                    _filter_opportunities(
                        jobs=jobs,
                        role_keyword=role_filter,
                        minimum_match=minimum_match,
                        work_mode=work_mode,
                    )
                )

                metric1, metric2 = (
                    st.columns(2)
                )

                with metric1:
                    st.metric(
                        "Live matches",
                        len(jobs),
                    )

                with metric2:
                    st.metric(
                        "After filters",
                        len(filtered_jobs),
                    )

                if role_filter.strip():
                    st.caption(
                        "Filtering job titles for: "
                        f"{role_filter.strip()}"
                    )

                if not filtered_jobs:
                    st.warning(
                        "No currently fetched live jobs "
                        "match these filters. Try removing "
                        "the title filter or lowering the "
                        "minimum match percentage."
                    )

                for index, result in enumerate(
                    filtered_jobs,
                    start=1,
                ):
                    opportunity = result.get(
                        "opportunity",
                        {}
                    )

                    with st.container(
                        border=True
                    ):
                        st.markdown(
                            "### "
                            f"{index}. "
                            f"{opportunity.get('title', 'Opportunity')}"
                        )

                        company = opportunity.get(
                            "company",
                            "Not specified",
                        )

                        location_value = (
                            opportunity.get(
                                "location",
                                "Not specified",
                            )
                        )

                        remote = bool(
                            opportunity.get(
                                "remote",
                                False,
                            )
                        )

                        st.write(
                            f"**Company:** {company}"
                        )

                        st.write(
                            "**Location:** "
                            f"{location_value}"
                        )

                        st.write(
                            "**Work mode:** "
                            + (
                                "Remote"
                                if remote
                                else "On-site / location based"
                            )
                        )

                        score = _get_match_score(
                            result
                        )

                        st.metric(
                            "Match",
                            f"{score}%",
                        )

                        matched = result.get(
                            "matched_skills",
                            [],
                        )

                        missing = result.get(
                            "missing_skills",
                            [],
                        )

                        if matched:
                            st.write(
                                "**Matched skills:** "
                                + ", ".join(
                                    matched
                                )
                            )

                        if missing:
                            st.write(
                                "**Skill gaps:** "
                                + ", ".join(
                                    missing
                                )
                            )

                        reasons = result.get(
                            "reasons",
                            [],
                        )

                        if reasons:
                            st.write(
                                "**Why this matches:**"
                            )

                            for reason in reasons:
                                st.write(
                                    f"- {reason}"
                                )

                        source = opportunity.get(
                            "source",
                            "Live job feed",
                        )

                        fetched_at = (
                            opportunity.get(
                                "fetched_at",
                                "",
                            )
                        )

                        st.caption(
                            f"Source: {source}"
                            + (
                                f" • Fetched: {fetched_at}"
                                if fetched_at
                                else ""
                            )
                        )

                        url = opportunity.get(
                            "url"
                        )

                        if url:
                            st.link_button(
                                "View Job",
                                url,
                            )

            elif searched:
                st.warning(
                    "The live job feed returned no "
                    "matching opportunities for this "
                    "profile right now."
                )

            else:
                st.info(
                    "Click Find Live Opportunities "
                    "to search the live job feed."
                )

    # ========================================================
    # GOVERNMENT SCHEMES
    # ========================================================

    with tabs[2]:
        st.subheader(
            "Government Schemes"
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
                "SkillSetu searches live myScheme, "
                "indexes official scheme information, "
                "and uses RAG to retrieve relevant results."
            )

            if st.button(
                "Find Government Schemes",
                type="primary",
            ):
                with st.spinner(
                    (
                        "Searching live myScheme and "
                        "building scheme recommendations..."
                    )
                ):
                    scheme_result = (
                        get_livelihood_schemes(
                            profile,
                            # Fetch more candidates so
                            # filters remain useful.
                            limit=10,
                        )
                    )

                    st.session_state[
                        "livelihood_scheme_result"
                    ] = scheme_result

            result = st.session_state.get(
                "livelihood_scheme_result"
            )

            if result:
                error = result.get(
                    "error",
                    "",
                )

                schemes = result.get(
                    "schemes",
                    [],
                )

                retrieved = result.get(
                    "retrieved",
                    [],
                )

                if error:
                    st.warning(error)

                if schemes:
                    metric1, metric2, metric3 = (
                        st.columns(3)
                    )

                    with metric1:
                        st.metric(
                            "Live schemes fetched",
                            len(schemes),
                        )

                    with metric2:
                        st.metric(
                            "RAG chunks indexed",
                            result.get(
                                "indexed_chunks",
                                0,
                            ),
                        )

                    with metric3:
                        ranking_method = (
                            result.get(
                                "ranking_method",
                                "live",
                            )
                        )

                        st.metric(
                            "Recommendations",
                            len(retrieved),
                        )

                    st.caption(
                        "Ranking method: "
                        f"{ranking_method}"
                    )

                if retrieved:
                    st.markdown(
                        "### 🔎 Filter Schemes"
                    )

                    scheme_col1, scheme_col2 = (
                        st.columns(2)
                    )

                    with scheme_col1:
                        scheme_keyword = (
                            st.text_input(
                                "Scheme keyword",
                                value="",
                                placeholder=(
                                    "farmer, agriculture, "
                                    "training, employment..."
                                ),
                                key=(
                                    "livelihood_scheme_keyword"
                                ),
                            )
                        )

                    with scheme_col2:
                        scheme_scope = (
                            st.selectbox(
                                "Scheme location",
                                [
                                    "All",
                                    "My State",
                                    "Central / National",
                                ],
                                key=(
                                    "livelihood_scheme_scope"
                                ),
                            )
                        )

                    filtered_schemes = (
                        _filter_schemes(
                            retrieved,
                            keyword=scheme_keyword,
                            state_filter=(
                                scheme_scope
                            ),
                        )
                    )

                    # ----------------------------------------
                    # STATE FILTER
                    # ----------------------------------------

                    if (
                        scheme_scope
                        == "My State"
                    ):
                        profile_state = str(
                            getattr(
                                profile,
                                "state",
                                "",
                            )
                        ).strip().lower()

                        state_filtered = []

                        for item in filtered_schemes:
                            item_state = str(
                                item.get(
                                    "state",
                                    "",
                                )
                            ).strip().lower()

                            # Keep blank-state schemes because
                            # many central schemes do not expose
                            # state metadata in every RAG chunk.
                            if (
                                not item_state
                                or not profile_state
                                or profile_state
                                in item_state
                                or item_state
                                in profile_state
                            ):
                                state_filtered.append(
                                    item
                                )

                        filtered_schemes = (
                            state_filtered
                        )

                    elif (
                        scheme_scope
                        == "Central / National"
                    ):
                        national_terms = {
                            "",
                            "all india",
                            "india",
                            "central",
                            "national",
                        }

                        national_filtered = []

                        for item in filtered_schemes:
                            item_state = str(
                                item.get(
                                    "state",
                                    "",
                                )
                            ).strip().lower()

                            if (
                                item_state
                                in national_terms
                            ):
                                national_filtered.append(
                                    item
                                )

                        filtered_schemes = (
                            national_filtered
                        )

                    st.caption(
                        f"Showing {len(filtered_schemes)} "
                        f"of {len(retrieved)} retrieved "
                        "scheme recommendations."
                    )

                    st.info(
                        "These are profile-relevant results "
                        "from live myScheme/RAG. Final "
                        "eligibility should be verified on "
                        "the official scheme page."
                    )

                    if not filtered_schemes:
                        st.warning(
                            "No retrieved schemes match "
                            "the current filters. Try "
                            "clearing the keyword or "
                            "selecting All."
                        )

                    seen_urls = set()

                    display_index = 0

                    for item in filtered_schemes:
                        url = item.get(
                            "url",
                            "",
                        )

                        if (
                            url
                            and url in seen_urls
                        ):
                            continue

                        if url:
                            seen_urls.add(
                                url
                            )

                        display_index += 1

                        scheme_name = item.get(
                            "scheme_name",
                            "Government Scheme",
                        )

                        with st.container(
                            border=True
                        ):
                            st.markdown(
                                f"### {display_index}. "
                                f"{scheme_name}"
                            )

                            # We deliberately say
                            # "Profile relevance", not
                            # "Eligible".
                            st.write(
                                "**Profile relevance:** "
                                "Potential match"
                            )

                            text = item.get(
                                "text",
                                "",
                            )

                            if text:
                                st.write(
                                    text[:1500]
                                )

                            state_value = item.get(
                                "state",
                                "",
                            )

                            if state_value:
                                st.write(
                                    "**Scheme location:** "
                                    f"{state_value}"
                                )

                            category = item.get(
                                "category",
                                "",
                            )

                            if category:
                                st.write(
                                    "**Category:** "
                                    f"{category}"
                                )

                            source = item.get(
                                "source",
                                "myScheme",
                            )

                            fetched_at = item.get(
                                "fetched_at",
                                "",
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
                                    "Open Official Scheme",
                                    url,
                                )

                    if display_index == 0:
                        st.warning(
                            "No unique schemes remain "
                            "after filtering."
                        )

                elif schemes:
                    st.info(
                        "Live schemes were fetched, but "
                        "semantic retrieval returned no "
                        "results."
                    )

                elif not error:
                    st.info(
                        "No live schemes were returned."
                    )

            else:
                st.info(
                    "Click Find Government Schemes "
                    "to search live myScheme."
                )

        st.divider()

        st.caption(
            "Architecture proof: Livelihood Profile → "
            "Live myScheme → ChromaDB → RAG. "
            "Jobs use the shared matching_engine(). "
            "Filters are applied after live retrieval."
        )

    # ========================================================
    # VOICE ASSISTANT
    # ========================================================

    with tabs[3]:
        st.subheader(
            "🎙️ Voice Assistant"
        )

        st.caption(
            "Speak in Telugu, English, or Hindi. "
            "Sarvam AI converts your speech to text, "
            "SkillSetu prepares guidance using your profile, "
            "and the answer is spoken back to you."
        )

        profile = st.session_state.get(
            "livelihood_profile"
        )

        if not profile:
            st.warning(
                "Create and save your livelihood profile "
                "before using the Voice Assistant."
            )

        else:
            preferred_language = getattr(
                profile,
                "language",
                "Telugu",
            )

            st.info(
                "Preferred response language: "
                f"{preferred_language}"
            )

            st.markdown(
                "#### 🎤 Speak to SkillSetu"
            )

            recorded_audio = st.audio_input(
                "Record your question"
            )

            if recorded_audio is not None:
                st.audio(
                    recorded_audio
                )

                if st.button(
                    "Ask with Voice",
                    type="primary",
                    key="livelihood_voice_ask",
                ):
                    try:
                        with st.spinner(
                            "Listening and preparing "
                            "your answer..."
                        ):
                            audio_bytes = (
                                recorded_audio.getvalue()
                            )

                            voice_result = (
                                process_voice_turn(
                                    audio_bytes=audio_bytes,
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
                            "Voice processing failed. "
                            "You can still use the text "
                            "question box below."
                        )

                        st.caption(
                            f"Technical detail: {exc}"
                        )

            voice_result = st.session_state.get(
                "livelihood_voice_result"
            )

            if voice_result:
                st.divider()

                st.markdown(
                    "#### 📝 What you said"
                )

                transcript = voice_result.get(
                    "transcript",
                    "",
                )

                st.write(
                    transcript
                    or "No transcript was returned."
                )

                detected_language = (
                    voice_result.get(
                        "detected_language",
                        "",
                    )
                )

                if detected_language:
                    st.caption(
                        "Detected language: "
                        f"{detected_language}"
                    )

                st.markdown(
                    "#### 🤖 SkillSetu response"
                )

                response_text = (
                    voice_result.get(
                        "response_text",
                        "",
                    )
                )

                if response_text:
                    st.write(
                        response_text
                    )

                response_audio = (
                    voice_result.get(
                        "audio_bytes"
                    )
                )

                if response_audio:
                    st.audio(
                        response_audio,
                        format="audio/wav",
                    )

            st.divider()

            st.markdown(
                "#### ⌨️ Text fallback"
            )

            st.caption(
                "If microphone permission or speech "
                "recognition does not work during the "
                "demo, type the same question here."
            )

            typed_question = st.text_input(
                "Ask about jobs, skills, or "
                "government schemes",
                key=(
                    "livelihood_voice_text_question"
                ),
                placeholder=(
                    "Example: నాకు ఉద్యోగాలు "
                    "ఏమైనా ఉన్నాయా?"
                ),
            )

            if st.button(
                "Ask with Text",
                key="livelihood_text_ask",
            ):
                if not typed_question.strip():
                    st.warning(
                        "Type a question first."
                    )

                else:
                    try:
                        with st.spinner(
                            "Preparing your answer..."
                        ):
                            english_response = (
                                build_livelihood_voice_response(
                                    typed_question,
                                    profile=profile,
                                )
                            )

                            try:
                                localized_response = (
                                    translate_text(
                                        english_response,
                                        target_language=(
                                            preferred_language
                                        ),
                                    )
                                )

                            except Exception:
                                localized_response = (
                                    english_response
                                )

                            try:
                                response_audio = (
                                    text_to_speech(
                                        localized_response,
                                        language=(
                                            preferred_language
                                        ),
                                    )
                                )

                            except Exception:
                                response_audio = None

                            st.session_state[
                                "livelihood_text_voice_result"
                            ] = {
                                "question": (
                                    typed_question
                                ),
                                "response_text": (
                                    localized_response
                                ),
                                "audio_bytes": (
                                    response_audio
                                ),
                            }

                    except Exception as exc:
                        st.error(
                            "Could not prepare "
                            "the response."
                        )

                        st.caption(
                            f"Technical detail: {exc}"
                        )

            text_result = st.session_state.get(
                "livelihood_text_voice_result"
            )

            if text_result:
                st.markdown(
                    "#### 🤖 SkillSetu response"
                )

                st.write(
                    text_result.get(
                        "response_text",
                        "",
                    )
                )

                text_audio = (
                    text_result.get(
                        "audio_bytes"
                    )
                )

                if text_audio:
                    st.audio(
                        text_audio,
                        format="audio/wav",
                    )

            st.divider()

            st.caption(
                "Voice pipeline: Microphone → "
                "Sarvam STT → SkillSetu livelihood "
                "guidance → Sarvam translation → "
                "Sarvam TTS."
            )