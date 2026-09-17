import streamlit as st

from features.livelihood import (
    create_livelihood_profile,
    get_livelihood_opportunities,
    get_livelihood_summary,
)


def render_livelihood_ui():

    st.title("🌾 SkillSetu")
    st.subheader("Livelihood & Rural Opportunity Assistant")

    st.caption(
        "Profile → Live Opportunities → Government Schemes → "
        "Regional Language Guidance"
    )

    if "livelihood_profile" not in st.session_state:
        st.session_state.livelihood_profile = None

    if "livelihood_jobs" not in st.session_state:
        st.session_state.livelihood_jobs = []

    profile_tab, jobs_tab, schemes_tab = st.tabs(
        [
            "👤 My Profile",
            "💼 Opportunities",
            "🏛️ Government Schemes",
        ]
    )

    # --------------------------------------------------------
    # PROFILE
    # --------------------------------------------------------

    with profile_tab:

        st.header("Tell us about yourself")

        st.write(
            "SkillSetu uses your skills, location and work preference "
            "to find suitable livelihood opportunities."
        )

        with st.form("livelihood_profile_form"):

            name = st.text_input(
                "Name",
                key="livelihood_name",
            )

            location = st.text_input(
                "Location",
                placeholder="e.g. Guntur",
                key="livelihood_location",
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
            )

            occupation = st.text_input(
                "Current occupation",
                placeholder="e.g. Farmer, Driver, Daily wage worker",
            )

            skills_text = st.text_input(
                "Your skills",
                placeholder="e.g. Driving, Farming, Smartphone",
            )

            target_role = st.text_input(
                "Work you are looking for",
                placeholder="e.g. Driver, Delivery, Agricultural Work",
            )

            experience = st.selectbox(
                "Experience",
                [
                    "fresher",
                    "beginner",
                    "1-3 years",
                    "3+ years",
                ],
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

            submitted = st.form_submit_button(
                "Create My Profile"
            )

        if submitted:

            if not name.strip():
                st.error("Please enter your name.")

            elif not location.strip():
                st.error("Please enter your location.")

            else:

                skills = [
                    skill.strip()
                    for skill in skills_text.split(",")
                    if skill.strip()
                ]

                profile = create_livelihood_profile(
                    name=name,
                    location=location,
                    skills=skills,
                    education=education,
                    occupation=occupation,
                    target_role=target_role,
                    experience=experience,
                    work_preference=work_preference,
                    language=language,
                )

                st.session_state.livelihood_profile = profile
                st.session_state.livelihood_jobs = []

                st.success("Profile created successfully.")

        if st.session_state.livelihood_profile:

            st.divider()

            summary = get_livelihood_summary(
                st.session_state.livelihood_profile
            )

            st.subheader("Your Profile")

            col1, col2 = st.columns(2)

            with col1:
                st.write(
                    "**Location:**",
                    summary["location"],
                )
                st.write(
                    "**Education:**",
                    summary["education"],
                )
                st.write(
                    "**Skills:**",
                    summary["skills"],
                )

            with col2:
                st.write(
                    "**Current occupation:**",
                    summary["occupation"],
                )
                st.write(
                    "**Looking for:**",
                    summary["target_role"],
                )
                st.write(
                    "**Language:**",
                    summary["language"],
                )

    # --------------------------------------------------------
    # LIVE OPPORTUNITIES
    # --------------------------------------------------------

    with jobs_tab:

        st.header("Live Opportunities")

        profile = st.session_state.livelihood_profile

        if profile is None:

            st.info(
                "Create your profile first so SkillSetu "
                "can find suitable opportunities."
            )

        else:

            st.write(
                "Jobs are fetched from a live source and ranked "
                "using SkillSetu's shared matching engine."
            )

            if st.button(
                "🔎 Find Opportunities",
                key="find_livelihood_jobs",
            ):

                with st.spinner(
                    "Searching live opportunities..."
                ):

                    results = get_livelihood_opportunities(
                        profile,
                        limit=5,
                    )

                    st.session_state.livelihood_jobs = results

            results = st.session_state.livelihood_jobs

            if results:

                st.success(
                    f"Found {len(results)} ranked opportunities."
                )

                for result in results:

                    job = result["opportunity"]

                    with st.container(border=True):

                        col1, col2 = st.columns(
                            [4, 1]
                        )

                        with col1:

                            st.subheader(
                                job.get(
                                    "title",
                                    "Opportunity",
                                )
                            )

                            st.write(
                                job.get(
                                    "company",
                                    "Company not specified",
                                )
                            )

                        with col2:

                            st.metric(
                                "Match",
                                f'{result["score"]}%'
                            )

                        st.write(
                            "📍",
                            job.get(
                                "location",
                                "Location not specified",
                            ),
                        )

                        if result["matched_skills"]:

                            st.write(
                                "**Matched skills:**",
                                ", ".join(
                                    result[
                                        "matched_skills"
                                    ]
                                ),
                            )

                        if result["missing_skills"]:

                            st.write(
                                "**Skills to improve:**",
                                ", ".join(
                                    result[
                                        "missing_skills"
                                    ]
                                ),
                            )

                        for reason in result["reasons"]:
                            st.caption(f"✓ {reason}")

                        job_url = job.get("url")

                        if job_url:
                            st.link_button(
                                "View Opportunity",
                                job_url,
                            )

                        st.caption(
                            f'Source: {job.get("source", "Live job provider")}'
                        )

            elif st.session_state.livelihood_jobs == []:

                st.caption(
                    "Click Find Opportunities to search live jobs."
                )

    # --------------------------------------------------------
    # GOVERNMENT SCHEMES
    # --------------------------------------------------------

    with schemes_tab:

        st.header("Government Schemes")

        st.info(
            "Next integration: retrieve relevant government "
            "schemes from official myScheme sources using "
            "SkillSetu's existing retrieval/RAG pipeline."
        )

        if st.session_state.livelihood_profile:

            profile = st.session_state.livelihood_profile

            st.write(
                "Scheme recommendations will use:"
            )

            st.write(
                f"📍 Location: **{profile.location}**"
            )

            st.write(
                f"🛠 Skills: **{', '.join(profile.skills) or 'Not specified'}**"
            )

            st.write(
                f"🗣 Language: **{profile.language}**"
            )