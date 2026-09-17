"""
SkillSetu - Livelihood Worker Streamlit UI
"""

import streamlit as st

from features.livelihood import (
    create_livelihood_profile,
    get_livelihood_opportunities,
    get_livelihood_schemes,
    get_livelihood_summary,
)


def _split_skills(value):
    if not value:
        return []

    return [
        skill.strip()
        for skill in value.split(",")
        if skill.strip()
    ]


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
        ]
    )

    # ==================================================
    # PROFILE
    # ==================================================

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

    # ==================================================
    # OPPORTUNITIES
    # ==================================================

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
                "Live jobs are fetched at runtime "
                "and ranked using the same shared "
                "matching engine used by SkillSetu."
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
                            limit=5,
                        )
                    )

                    st.session_state[
                        "livelihood_jobs"
                    ] = jobs

            jobs = st.session_state.get(
                "livelihood_jobs",
                [],
            )

            if jobs:
                for index, result in enumerate(
                    jobs,
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

                        st.write(
                            f"**Company:** {company}"
                        )

                        st.write(
                            "**Location:** "
                            f"{location_value}"
                        )

                        score = result.get(
                            "score",
                            result.get(
                                "match_score",
                                result.get(
                                    "match_percentage",
                                    0,
                                ),
                            ),
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

            elif st.session_state.get(
                "livelihood_jobs"
            ) == []:
                st.info(
                    "Click Find Live Opportunities "
                    "to search the live job feed."
                )

    # ==================================================
    # GOVERNMENT SCHEMES
    # ==================================================

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
                "SkillSetu searches the live myScheme "
                "questionnaire, indexes the returned "
                "official scheme pages, and retrieves "
                "relevant information using RAG."
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
                            limit=5,
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
                    metric1, metric2 = (
                        st.columns(2)
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

                if retrieved:
                    st.success(
                        "Relevant government schemes found."
                    )

                    seen_urls = set()

                    for index, item in enumerate(
                        retrieved,
                        start=1,
                    ):
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
                            seen_urls.add(url)

                        scheme_name = item.get(
                            "scheme_name",
                            "Government Scheme",
                        )

                        with st.container(
                            border=True
                        ):
                            st.markdown(
                                f"### {scheme_name}"
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
                                    "**State:** "
                                    f"{state_value}"
                                )

                            st.caption(
                                "Source: "
                                + item.get(
                                    "source",
                                    "myScheme",
                                )
                            )

                            if url:
                                st.link_button(
                                    "Open Official Scheme",
                                    url,
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
            "Jobs use the shared matching_engine()."
        )