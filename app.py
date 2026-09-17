import streamlit as st

from features.livelihood import (
    create_livelihood_profile,
    get_livelihood_opportunities,
    get_livelihood_summary,
)

from features.student import (
    create_student_profile,
    get_skill_assessment_questions,
    assess_skills,
    get_assessment_summary,
)

from features.student_jobs import get_student_job_results

from features.student_roadmap import (
    generate_student_roadmap,
    simulate_roadmap_progress,
)

from features.interview import (
    get_interview_question,
    evaluate_student_answer,
)


# ============================================================
# PAGE CONFIG
# ============================================================

st.set_page_config(
    page_title="SkillSetu - Student Career Assistant",
    page_icon="🎓",
    layout="wide",
)

# ============================================================
# PERSONA SELECTION
# ============================================================

if "persona" not in st.session_state:
    st.session_state.persona = "Student"

st.sidebar.divider()
st.sidebar.subheader("Choose Experience")

st.session_state.persona = st.sidebar.radio(
    "I am a:",
    ["Student", "Livelihood Worker"],
)


# ============================================================
# SESSION STATE
# ============================================================

if "profile" not in st.session_state:
    st.session_state.profile = None

if "skill_state" not in st.session_state:
    st.session_state.skill_state = {}

if "assessment_done" not in st.session_state:
    st.session_state.assessment_done = False

if "roadmap_data" not in st.session_state:
    st.session_state.roadmap_data = None

if "updated_roadmap_data" not in st.session_state:
    st.session_state.updated_roadmap_data = None

if "interview_question" not in st.session_state:
    st.session_state.interview_question = None

if "interview_feedback" not in st.session_state:
    st.session_state.interview_feedback = None


# ============================================================
# HEADER
# ============================================================

st.title("🎓 SkillSetu")
st.subheader("AI Career & Livelihood Guidance Agent")

st.caption(
    "Student experience: Profile → Skills → Jobs → Roadmap → Interview"
)


# ============================================================
# SIDEBAR
# ============================================================

st.sidebar.title("Student Journey")

st.sidebar.markdown(
    """
**1. Profile**  
Create your student profile.

**2. Skill Assessment**  
Assess your current technical skills.

**3. Jobs**  
Find relevant live opportunities.

**4. Roadmap**  
Identify skill gaps and learning priorities.

**5. Mock Interview**  
Practice role-specific interview questions.
"""
)

if st.session_state.profile:
    st.sidebar.success("Profile created")

if st.session_state.assessment_done:
    st.sidebar.success("Skills assessed")


# ============================================================
# TABS
# ============================================================

profile_tab, assessment_tab, jobs_tab, roadmap_tab, interview_tab = st.tabs(
    [
        "👤 Profile",
        "🧠 Skill Assessment",
        "💼 Jobs",
        "🗺️ Roadmap",
        "🎤 Mock Interview",
    ]
)


# ============================================================
# PROFILE TAB
# ============================================================

with profile_tab:

    st.header("Student Profile")

    st.write(
        "Tell SkillSetu about yourself so it can personalize "
        "jobs, skill gaps, roadmap and interview practice."
    )

    with st.form("student_profile_form"):

        name = st.text_input("Name")

        location = st.text_input(
            "Location",
            placeholder="e.g. Hyderabad",
        )

        education = st.text_input(
            "Education",
            placeholder="e.g. B.Tech",
        )

        skills_text = st.text_input(
            "Current Skills",
            placeholder="e.g. Python, Excel",
        )

        target_role = st.text_input(
            "Target Role",
            placeholder="e.g. Data Analyst",
        )

        experience = st.selectbox(
            "Experience",
            [
                "Fresher",
                "0-1 years",
                "1-3 years",
                "3+ years",
            ],
        )

        work_preference = st.selectbox(
            "Work Preference",
            [
                "Any",
                "Remote",
                "On-site",
                "Hybrid",
            ],
        )

        language = st.selectbox(
            "Language",
            [
                "English",
                "Telugu",
                "Hindi",
            ],
        )

        submitted = st.form_submit_button(
            "Create Student Profile"
        )

    if submitted:

        if not name.strip():
            st.error("Please enter your name.")

        elif not location.strip():
            st.error("Please enter your location.")

        elif not target_role.strip():
            st.error("Please enter your target role.")

        else:

            skills = [
                skill.strip()
                for skill in skills_text.split(",")
                if skill.strip()
            ]

            st.session_state.profile = create_student_profile(
                name=name,
                location=location,
                education=education,
                skills=skills,
                target_role=target_role,
                experience=experience,
                work_preference=work_preference,
                language=language,
            )

            # Reset downstream state when profile changes.
            st.session_state.skill_state = {}
            st.session_state.assessment_done = False
            st.session_state.roadmap_data = None
            st.session_state.updated_roadmap_data = None
            st.session_state.interview_question = None
            st.session_state.interview_feedback = None

            st.success("Student profile created successfully.")

    if st.session_state.profile:

        st.divider()

        st.subheader("Current Profile")

        profile = st.session_state.profile

        col1, col2 = st.columns(2)

        with col1:
            st.write("**Name:**", profile["name"])
            st.write("**Location:**", profile["location"])
            st.write("**Education:**", profile["education"])
            st.write("**Target Role:**", profile["target_role"])

        with col2:
            st.write("**Experience:**", profile["experience"])
            st.write("**Work Preference:**", profile["work_preference"])
            st.write("**Language:**", profile["language"])
            st.write(
                "**Skills:**",
                ", ".join(profile["skills"]) if profile["skills"] else "None",
            )


# ============================================================
# SKILL ASSESSMENT TAB
# ============================================================

with assessment_tab:

    st.header("🧠 Skill Assessment")

    if not st.session_state.profile:

        st.info(
            "Create your student profile first."
        )

    else:

        st.write(
            "Answer these short questions from 1 to 5 based on "
            "your current confidence."
        )

        questions = get_skill_assessment_questions()

        responses = {}

        for question in questions:

            skill = question["skill"]

            st.markdown(
                f"**{skill.title()}**"
            )

            st.write(question["question"])

            responses[skill] = st.radio(
                f"Your confidence in {skill}",
                options=[1, 2, 3, 4, 5],
                horizontal=True,
                key=f"assessment_{skill}",
            )

        if st.button(
            "Calculate Skill Level",
            type="primary",
        ):

            st.session_state.skill_state = assess_skills(
                responses
            )

            st.session_state.assessment_done = True

            # Generate initial roadmap after assessment.
            st.session_state.roadmap_data = generate_student_roadmap(
                st.session_state.profile,
                st.session_state.skill_state,
            )

            st.session_state.updated_roadmap_data = None

            st.success(
                "Skill assessment completed."
            )

        if st.session_state.assessment_done:

            st.divider()

            st.subheader("Assessment Summary")

            summary = get_assessment_summary(
                st.session_state.skill_state
            )

            col1, col2 = st.columns(2)

            with col1:
                st.metric(
                    "Skills Assessed",
                    summary["skills_assessed"],
                )

            with col2:
                st.metric(
                    "Average Skill Level",
                    f"{summary['average_level']:.2f}",
                )

            st.write("### Current Skill State")

            for skill, level in st.session_state.skill_state.items():

                st.write(
                    f"**{skill.title()}** — {level:.2f}"
                )

                st.progress(
                    min(max(float(level), 0.0), 1.0)
                )


# ============================================================
# JOBS TAB
# ============================================================

with jobs_tab:

    st.header("💼 Live Job Opportunities")

    if not st.session_state.profile:

        st.info(
            "Create your student profile first."
        )

    else:

        st.write(
            "SkillSetu retrieves live job data and applies the "
            "shared matching engine to your profile."
        )

        if st.button(
            "Find Relevant Jobs",
            type="primary",
        ):

            with st.spinner(
                "Fetching live jobs..."
            ):

                try:

                    results = get_student_job_results(
                        st.session_state.profile
                    )

                    st.session_state.job_results = results

                except Exception as exc:

                    st.session_state.job_results = []

                    st.error(
                        f"Unable to load jobs: {exc}"
                    )

        if "job_results" in st.session_state:

            results = st.session_state.job_results

            if not results:

                st.warning(
                    "No relevant live jobs were returned. "
                    "The job provider may be unavailable or there "
                    "may currently be no matching results."
                )

            else:

                st.success(
                    f"{len(results)} relevant job results found."
                )

                for index, job in enumerate(results):

                    with st.container():

                        st.subheader(
                            job.get(
                                "title",
                                "Untitled Role",
                            )
                        )

                        st.write(
                            f"**Company:** "
                            f"{job.get('company', 'Unknown')}"
                        )

                        st.write(
                            f"**Location:** "
                            f"{job.get('location', 'Unknown')}"
                        )

                        match = job.get(
                            "match_percentage",
                            0,
                        )

                        st.metric(
                            "Match",
                            f"{match}%",
                        )

                        matched = job.get(
                            "matched_skills",
                            [],
                        )

                        missing = job.get(
                            "missing_skills",
                            [],
                        )

                        if matched:
                            st.write(
                                "**Matched Skills:** "
                                + ", ".join(matched)
                            )

                        if missing:
                            st.write(
                                "**Missing Skills:** "
                                + ", ".join(missing)
                            )

                        reasons = job.get(
                            "reasons",
                            [],
                        )

                        if reasons:

                            st.write("**Why this match:**")

                            for reason in reasons:
                                st.write(
                                    f"- {reason}"
                                )

                        url = job.get("url")

                        if url:
                            st.link_button(
                                "View Job",
                                url,
                            )

                        st.divider()


# ============================================================
# ROADMAP TAB
# ============================================================

with roadmap_tab:

    st.header("🗺️ Personalized Skill Roadmap")

    if not st.session_state.profile:

        st.info(
            "Create your student profile first."
        )

    elif not st.session_state.assessment_done:

        st.info(
            "Complete the skill assessment first."
        )

    else:

        if st.session_state.roadmap_data is None:

            st.session_state.roadmap_data = generate_student_roadmap(
                st.session_state.profile,
                st.session_state.skill_state,
            )

        roadmap_data = st.session_state.roadmap_data

        st.subheader(
            f"Roadmap for {roadmap_data.get('target_role', 'Target Role')}"
        )

        roadmap = roadmap_data.get(
            "roadmap",
            [],
        )

        if roadmap:

            for index, step in enumerate(roadmap, start=1):

                skill = step.get(
                    "skill",
                    "Unknown",
                )

                current = step.get(
                    "current_level",
                    "none",
                )

                target = step.get(
                    "target_level",
                    "unknown",
                )

                priority = step.get(
                    "priority",
                    "medium",
                )

                st.markdown(
                    f"### {index}. {skill.title()}"
                )

                col1, col2, col3 = st.columns(3)

                with col1:
                    st.write(
                        f"**Current:** {current}"
                    )

                with col2:
                    st.write(
                        f"**Target:** {target}"
                    )

                with col3:
                    st.write(
                        f"**Priority:** {priority}"
                    )

                st.divider()

        else:

            st.success(
                "No additional roadmap steps were returned."
            )

        # ----------------------------------------------------
        # Skill simulation
        # ----------------------------------------------------

        st.subheader("Simulate Skill Improvement")

        available_skills = list(
            st.session_state.skill_state.keys()
        )

        if available_skills:

            selected_skill = st.selectbox(
                "Choose a skill to improve",
                available_skills,
            )

            improvement = st.slider(
                "Simulated improvement",
                min_value=0.05,
                max_value=0.50,
                value=0.20,
                step=0.05,
            )

            if st.button(
                "Simulate Skill Update"
            ):

                st.session_state.updated_roadmap_data = (
                    simulate_roadmap_progress(
                        profile=st.session_state.profile,
                        skill_state=st.session_state.skill_state,
                        skill=selected_skill,
                        improvement=improvement,
                    )
                )

        # ----------------------------------------------------
        # Before / After
        # ----------------------------------------------------

        if st.session_state.updated_roadmap_data:

            simulation = (
                st.session_state.updated_roadmap_data
            )

            st.divider()

            st.subheader(
                "Before vs After"
            )

            before_state = simulation.get(
                "original_skill_state",
                {},
            )

            after_state = simulation.get(
                "updated_skill_state",
                {},
            )

            all_skills = sorted(
                set(before_state) | set(after_state)
            )

            for skill in all_skills:

                before = float(
                    before_state.get(skill, 0)
                )

                after = float(
                    after_state.get(skill, 0)
                )

                if before != after:

                    col1, col2, col3 = st.columns(3)

                    with col1:
                        st.write(
                            f"**{skill.title()}**"
                        )

                    with col2:
                        st.write(
                            f"Before: {before:.2f}"
                        )

                    with col3:
                        st.write(
                            f"After: {after:.2f}"
                        )

                    st.progress(
                        min(max(after, 0.0), 1.0)
                    )

            comparison = simulation.get(
                "comparison",
                {},
            )

            changes = comparison.get(
                "changes",
                [],
            )

            if changes:

                st.write("### Changed Skills")

                for change in changes:

                    st.write(
                        f"- **{change['skill'].title()}**: "
                        f"{change['before_value']:.2f} → "
                        f"{change['after_value']:.2f} "
                        f"(+{change['improvement']:.2f})"
                    )

            st.write(
                "### Updated Roadmap"
            )

            updated_roadmap = (
                simulation
                .get("after_roadmap", {})
                .get("roadmap", [])
            )

            for index, step in enumerate(
                updated_roadmap,
                start=1,
            ):

                st.write(
                    f"{index}. "
                    f"{step.get('skill', 'Unknown').title()} "
                    f"— {step.get('current_level', 'none')} "
                    f"→ {step.get('target_level', 'unknown')}"
                )


# ============================================================
# MOCK INTERVIEW TAB
# ============================================================

with interview_tab:

    st.header("🎤 Mock Interview")

    if not st.session_state.profile:

        st.info(
            "Create your student profile first."
        )

    else:

        role = st.session_state.profile[
            "target_role"
        ]

        st.write(
            f"Practice interview questions for: **{role}**"
        )

        difficulty = st.selectbox(
            "Difficulty",
            [
                "beginner",
                "intermediate",
                "advanced",
            ],
        )

        if st.button(
            "Generate Interview Question",
            type="primary",
        ):

            st.session_state.interview_question = (
                get_interview_question(
                    role=role,
                    difficulty=difficulty,
                )
            )

            st.session_state.interview_feedback = None

        if st.session_state.interview_question:

            st.divider()

            st.subheader("Interview Question")

            st.info(
                st.session_state.interview_question
            )

            answer = st.text_area(
                "Your Answer",
                height=180,
                placeholder=(
                    "Type your interview answer here..."
                ),
            )

            if st.button(
                "Evaluate My Answer"
            ):

                if not answer.strip():

                    st.warning(
                        "Please enter an answer first."
                    )

                else:

                    with st.spinner(
                        "Evaluating your answer..."
                    ):

                        st.session_state.interview_feedback = (
                            evaluate_student_answer(
                                question=(
                                    st.session_state
                                    .interview_question
                                ),
                                answer=answer,
                                role=role,
                            )
                        )

            if st.session_state.interview_feedback:

                feedback = (
                    st.session_state.interview_feedback
                )

                st.divider()

                st.subheader(
                    "Interview Feedback"
                )

                score = feedback.get(
                    "score",
                    0,
                )

                st.metric(
                    "Interview Score",
                    f"{score}/100",
                )

                st.write("### Strengths")

                for item in feedback.get(
                    "strengths",
                    [],
                ):
                    st.write(
                        f"✅ {item}"
                    )

                st.write("### Issues")

                for item in feedback.get(
                    "issues",
                    [],
                ):
                    st.write(
                        f"⚠️ {item}"
                    )

                st.write(
                    "### Missing Points"
                )

                for item in feedback.get(
                    "missing_points",
                    [],
                ):
                    st.write(
                        f"- {item}"
                    )

                st.write(
                    "### Improved Answer"
                )

                st.success(
                    feedback.get(
                        "improved_answer",
                        "",
                    )
                )

                st.write(
                    "### Next Action"
                )

                st.info(
                    feedback.get(
                        "next_action",
                        "",
                    )
                )