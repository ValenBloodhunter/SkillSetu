"""
SkillSetu - Livelihood Backend

Shared flow:
Livelihood Profile
    -> Live Jobs
    -> Shared Matching Engine

Livelihood Profile
    -> Live myScheme
    -> Optional RAG Ranking
    -> Safe Live-Scheme Fallback
"""

from dataclasses import dataclass, field, asdict
from typing import List

from core.matching_engine import matching_engine
from core.retrieval import index_schemes, retrieve_schemes
from data.jobs import fetch_jobs
from data.schemes import fetch_schemes


@dataclass
class LivelihoodProfile:
    name: str
    location: str

    skills: List[str] = field(default_factory=list)

    education: str = ""
    occupation: str = ""
    target_role: str = ""

    experience: str = "fresher"
    work_preference: str = "local"
    language: str = "Telugu"

    # myScheme fields
    age: int = 18
    gender: str = "Male"
    state: str = "Andhra Pradesh"
    residence: str = "Rural"
    caste: str = "General"

    disability: str = "No"
    minority: str = "No"

    is_student: bool = False

    employment_status: str = "Unemployed"
    marital_status: str = "Never Married"

    is_bpl: bool = False
    is_economic_distress: bool = False

    annual_family_income: int = 0
    annual_parent_income: int = 0


def create_livelihood_profile(
    name,
    location,
    skills,
    education="",
    occupation="",
    target_role="",
    experience="fresher",
    work_preference="local",
    language="Telugu",
    age=18,
    gender="Male",
    state="Andhra Pradesh",
    residence="Rural",
    caste="General",
    disability="No",
    minority="No",
    is_student=False,
    employment_status="Unemployed",
    marital_status="Never Married",
    is_bpl=False,
    is_economic_distress=False,
    annual_family_income=0,
    annual_parent_income=0,
):
    clean_skills = []

    for skill in skills or []:
        skill = str(skill).strip()

        if skill:
            clean_skills.append(skill)

    return LivelihoodProfile(
        name=str(name).strip(),
        location=str(location).strip(),
        skills=clean_skills,
        education=str(education).strip(),
        occupation=str(occupation).strip(),
        target_role=str(target_role).strip(),
        experience=str(experience).strip(),
        work_preference=str(work_preference).strip(),
        language=str(language).strip(),
        age=int(age),
        gender=str(gender).strip(),
        state=str(state).strip(),
        residence=str(residence).strip(),
        caste=str(caste).strip(),
        disability=str(disability).strip(),
        minority=str(minority).strip(),
        is_student=bool(is_student),
        employment_status=str(employment_status).strip(),
        marital_status=str(marital_status).strip(),
        is_bpl=bool(is_bpl),
        is_economic_distress=bool(
            is_economic_distress
        ),
        annual_family_income=int(
            annual_family_income or 0
        ),
        annual_parent_income=int(
            annual_parent_income or 0
        ),
    )


# ============================================================
# LIVE JOBS
# ============================================================

def get_livelihood_opportunities(
    profile,
    limit=5,
):
    if profile is None:
        return []

    try:
        jobs = fetch_jobs(profile)

    except Exception as exc:
        print("Live job retrieval failed:")
        print(repr(exc))
        return []

    if not jobs:
        return []

    try:
        # IMPORTANT:
        # Student + Livelihood use the SAME engine.
        ranked_jobs = matching_engine(
            profile,
            jobs,
        )

    except Exception as exc:
        print("Shared matching engine failed:")
        print(repr(exc))
        return []

    return ranked_jobs[:limit]


# ============================================================
# MYSCHEME PROFILE
# ============================================================

def build_myscheme_profile(profile):
    if profile is None:
        return {}

    data = asdict(profile)

    # Exact aliases expected by live myScheme flow.
    data["isStudent"] = profile.is_student
    data["employmentStatus"] = (
        profile.employment_status
    )
    data["maritalStatus"] = (
        profile.marital_status
    )

    data["isBpl"] = profile.is_bpl

    data["isEconomicDistress"] = (
        profile.is_economic_distress
    )

    data["annualFamilyIncome"] = (
        profile.annual_family_income
    )

    data["annualParentIncome"] = (
        profile.annual_parent_income
    )

    return data


# ============================================================
# LIVE-SCHEME FALLBACK
# ============================================================

def _scheme_to_retrieved_item(scheme):
    """
    Convert a live myScheme result into the same basic
    structure expected by the Streamlit recommendation UI.

    This allows government schemes to remain visible even
    when sentence-transformers / ChromaDB fails.
    """

    scheme_name = (
        scheme.get("scheme_name")
        or scheme.get("name")
        or "Government Scheme"
    )

    description = (
        scheme.get("description")
        or ""
    )

    benefits = (
        scheme.get("benefits")
        or ""
    )

    eligibility = (
        scheme.get("eligibility_signals")
        or ""
    )

    application_info = (
        scheme.get("application_info")
        or ""
    )

    text_parts = []

    if description:
        text_parts.append(description)

    if eligibility:
        text_parts.append(
            f"Eligibility: {eligibility}"
        )

    if benefits:
        text_parts.append(
            f"Benefits: {benefits}"
        )

    if application_info:
        text_parts.append(
            f"Application: {application_info}"
        )

    text = "\n\n".join(text_parts)

    if not text:
        text = (
            "Live government scheme returned "
            "by the official myScheme service."
        )

    return {
        "scheme_name": scheme_name,
        "text": text,
        "source": scheme.get(
            "source",
            "myScheme",
        ),
        "url": scheme.get(
            "url",
            "",
        ),
        "state": scheme.get(
            "state",
            "",
        ),
        "category": scheme.get(
            "category",
            "",
        ),
        "fetched_at": scheme.get(
            "fetched_at",
            "",
        ),
        "ranking_method": "live_fallback",
    }


def _live_scheme_fallback(
    schemes,
    limit=5,
):
    """
    Demo-safe fallback.

    These are NOT invented schemes.
    They are the schemes already returned by live myScheme.
    """

    results = []

    seen = set()

    for scheme in schemes:
        url = scheme.get(
            "url",
            "",
        )

        name = scheme.get(
            "scheme_name",
            "",
        )

        identity = (
            url
            or name
        )

        if identity in seen:
            continue

        seen.add(identity)

        results.append(
            _scheme_to_retrieved_item(
                scheme
            )
        )

        if len(results) >= limit:
            break

    return results


# ============================================================
# GOVERNMENT SCHEMES
# ============================================================

def get_livelihood_schemes(
    profile,
    limit=5,
):
    result = {
        "schemes": [],
        "retrieved": [],
        "indexed_chunks": 0,
        "error": "",
        "ranking_method": "",
    }

    if profile is None:
        result["error"] = (
            "Create your livelihood profile first."
        )

        return result

    try:
        myscheme_profile = (
            build_myscheme_profile(
                profile
            )
        )

    except Exception as exc:
        result["error"] = (
            "Could not prepare myScheme profile: "
            f"{exc}"
        )

        return result

    print()
    print("=" * 60)
    print("LIVELIHOOD -> LIVE MYSCHEME")
    print("=" * 60)

    # --------------------------------------------------------
    # STEP 1: LIVE MYSCHEME
    # --------------------------------------------------------

    try:
        schemes = fetch_schemes(
            myscheme_profile
        )

    except Exception as exc:
        print(
            "myScheme exception:"
        )

        print(
            repr(exc)
        )

        result["error"] = (
            "Live myScheme retrieval failed: "
            f"{exc}"
        )

        return result

    result["schemes"] = schemes

    if not schemes:
        result["error"] = (
            "myScheme returned no live schemes "
            "for this profile."
        )

        return result

    print(
        "Live schemes received:",
        len(schemes),
    )

    # --------------------------------------------------------
    # STEP 2: CREATE SAFE FALLBACK FIRST
    # --------------------------------------------------------

    fallback_results = (
        _live_scheme_fallback(
            schemes,
            limit=limit,
        )
    )

    # We set this immediately.
    #
    # Therefore even if embeddings/ChromaDB explode later,
    # the UI STILL has real live schemes to display.

    result["retrieved"] = (
        fallback_results
    )

    result["ranking_method"] = (
        "live_myscheme_fallback"
    )

    # --------------------------------------------------------
    # STEP 3: TRY RAG
    # --------------------------------------------------------

    try:
        print()
        print(
            "Attempting RAG indexing..."
        )

        indexed_chunks = (
            index_schemes(
                schemes
            )
        )

        result["indexed_chunks"] = (
            indexed_chunks
        )

        print(
            "Indexed RAG chunks:",
            indexed_chunks,
        )

    except Exception as exc:
        print()
        print(
            "RAG indexing unavailable."
        )

        print(
            "Using live myScheme fallback."
        )

        print(
            repr(exc)
        )

        # IMPORTANT:
        # This is NOT fatal.
        # Live government schemes are already available.

        result["error"] = ""

        return result

    # --------------------------------------------------------
    # STEP 4: SEMANTIC QUERY
    # --------------------------------------------------------

    query_parts = [
        profile.occupation,
        profile.target_role,
        " ".join(
            profile.skills
        ),
        profile.education,
        profile.state,
        profile.residence,
        profile.employment_status,

        (
            "BPL"
            if profile.is_bpl
            else ""
        ),

        (
            "economic distress"
            if profile.is_economic_distress
            else ""
        ),

        "government scheme",
        "livelihood",
        "employment",
        "skill development",
        "financial assistance",
    ]

    query = " ".join(
        str(part).strip()
        for part in query_parts
        if str(part).strip()
    )

    print(
        "RAG query:",
        query,
    )

    # --------------------------------------------------------
    # STEP 5: TRY SEMANTIC RETRIEVAL
    # --------------------------------------------------------

    try:
        retrieved = retrieve_schemes(
            query,
            top_k=limit,
        )

        if retrieved:
            result["retrieved"] = (
                retrieved
            )

            result["ranking_method"] = (
                "rag_semantic"
            )

            print(
                "RAG recommendations:",
                len(retrieved),
            )

        else:
            print(
                "RAG returned zero results."
            )

            print(
                "Keeping live myScheme fallback."
            )

    except Exception as exc:
        print()
        print(
            "RAG retrieval unavailable."
        )

        print(
            "Keeping live myScheme fallback."
        )

        print(
            repr(exc)
        )

    # RAG failure is NOT an app failure.
    result["error"] = ""

    return result


# ============================================================
# PROFILE SUMMARY
# ============================================================

def get_livelihood_summary(profile):
    if profile is None:
        return {}

    skills = ", ".join(
        profile.skills
    )

    if not skills:
        skills = (
            "No skills entered"
        )

    return {
        "name": profile.name,
        "location": profile.location,
        "state": profile.state,
        "age": profile.age,
        "gender": profile.gender,
        "residence": profile.residence,

        "education": (
            profile.education
            or "Not specified"
        ),

        "occupation": (
            profile.occupation
            or "Not specified"
        ),

        "target_role": (
            profile.target_role
            or "Open to opportunities"
        ),

        "skills": skills,

        "experience": (
            profile.experience
        ),

        "work_preference": (
            profile.work_preference
        ),

        "language": (
            profile.language
        ),

        "caste": (
            profile.caste
        ),

        "disability": (
            profile.disability
        ),

        "minority": (
            profile.minority
        ),

        "employment_status": (
            profile.employment_status
        ),

        "marital_status": (
            profile.marital_status
        ),

        "is_bpl": (
            profile.is_bpl
        ),

        "is_economic_distress": (
            profile.is_economic_distress
        ),
    }