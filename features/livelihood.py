"""
SkillSetu - Livelihood Backend

Shared jobs:
Profile -> Live Jobs -> Shared matching_engine()

Government schemes:
Profile -> Live myScheme -> Profile Fit Filter
        -> RAG -> Ranked Recommendations

IMPORTANT:
Scheme fit is recommendation relevance.
It is NOT a guarantee of legal/official eligibility.
"""

from dataclasses import dataclass, field, asdict
from typing import List
import re

from core.matching_engine import matching_engine
from core.retrieval import index_schemes, retrieve_schemes
from data.jobs import fetch_jobs
from data.schemes import fetch_schemes


# ============================================================
# PROFILE
# ============================================================

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
        employment_status=str(
            employment_status
        ).strip(),
        marital_status=str(
            marital_status
        ).strip(),
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
    limit=30,
):
    if profile is None:
        return []

    try:
        jobs = fetch_jobs(profile)

    except Exception as exc:
        print(
            "Live job retrieval failed:",
            repr(exc),
        )
        return []

    if not jobs:
        return []

    try:
        ranked_jobs = matching_engine(
            profile,
            jobs,
        )

    except Exception as exc:
        print(
            "Shared matching engine failed:",
            repr(exc),
        )
        return []

    return ranked_jobs[:limit]


# ============================================================
# MYSCHEME PROFILE
# ============================================================

def build_myscheme_profile(profile):
    if profile is None:
        return {}

    data = asdict(profile)

    data["isStudent"] = (
        profile.is_student
    )

    data["employmentStatus"] = (
        profile.employment_status
    )

    data["maritalStatus"] = (
        profile.marital_status
    )

    data["isBpl"] = (
        profile.is_bpl
    )

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
# SCHEME FIT HELPERS
# ============================================================

def _normalize(value):
    return " ".join(
        str(value or "")
        .lower()
        .strip()
        .split()
    )


def _contains_phrase(
    text,
    phrase,
):
    text = _normalize(text)
    phrase = _normalize(phrase)

    if not text or not phrase:
        return False

    pattern = (
        r"\b"
        + re.escape(phrase)
        + r"\b"
    )

    return bool(
        re.search(
            pattern,
            text,
            flags=re.IGNORECASE,
        )
    )


def _scheme_full_text(scheme):
    parts = [
        scheme.get(
            "scheme_name",
            "",
        ),
        scheme.get(
            "name",
            "",
        ),
        scheme.get(
            "description",
            "",
        ),
        scheme.get(
            "eligibility_signals",
            "",
        ),
        scheme.get(
            "benefits",
            "",
        ),
        scheme.get(
            "application_info",
            "",
        ),
        scheme.get(
            "category",
            "",
        ),
        scheme.get(
            "state",
            "",
        ),
    ]

    return _normalize(
        " ".join(
            str(part)
            for part in parts
            if part
        )
    )


# ============================================================
# SCHEME PROFILE-FIT ENGINE
# ============================================================

def evaluate_scheme_fit(
    scheme,
    profile,
):
    """
    Rank a LIVE myScheme result against the livelihood
    profile.

    This determines recommendation relevance only.

    It deliberately does NOT return "Eligible" or
    "Not Eligible".
    """

    text = _scheme_full_text(
        scheme
    )

    score = 40

    reasons = []
    warnings = []

    # --------------------------------------------------------
    # STATE
    # --------------------------------------------------------

    profile_state = _normalize(
        profile.state
    )

    scheme_state = _normalize(
        scheme.get(
            "state",
            "",
        )
    )

    national_values = {
        "",
        "all india",
        "india",
        "central",
        "national",
        "central government",
    }

    if scheme_state:
        if (
            profile_state
            and (
                profile_state in scheme_state
                or scheme_state in profile_state
            )
        ):
            score += 15

            reasons.append(
                f"Scheme location matches "
                f"{profile.state}."
            )

        elif (
            scheme_state
            not in national_values
        ):
            score -= 25

            warnings.append(
                "Scheme may be associated with "
                f"{scheme.get('state')} rather than "
                f"{profile.state}."
            )

    else:
        reasons.append(
            "No conflicting state restriction was "
            "identified in the retrieved metadata."
        )

    # --------------------------------------------------------
    # OCCUPATION
    # --------------------------------------------------------

    occupation = _normalize(
        profile.occupation
    )

    if (
        occupation
        and _contains_phrase(
            text,
            occupation,
        )
    ):
        score += 15

        reasons.append(
            "Scheme information relates to your "
            f"occupation: {profile.occupation}."
        )

    # Common livelihood occupation groups.

    occupation_groups = {
        "farmer": [
            "farmer",
            "farmers",
            "agriculture",
            "agricultural",
            "farming",
            "crop",
            "cultivation",
            "kisan",
        ],

        "driver": [
            "driver",
            "driving",
            "transport",
            "vehicle",
            "commercial vehicle",
        ],

        "artisan": [
            "artisan",
            "handicraft",
            "handloom",
            "craft",
            "weaver",
        ],

        "fisher": [
            "fisher",
            "fisherman",
            "fisheries",
            "fishing",
        ],

        "worker": [
            "worker",
            "labour",
            "labor",
            "wage worker",
            "unorganised worker",
            "unorganized worker",
        ],
    }

    profile_terms = " ".join(
        [
            _normalize(
                profile.occupation
            ),
            _normalize(
                profile.target_role
            ),
            " ".join(
                _normalize(skill)
                for skill in profile.skills
            ),
        ]
    )

    occupation_group_match = False

    for group, terms in (
        occupation_groups.items()
    ):
        profile_in_group = any(
            _contains_phrase(
                profile_terms,
                term,
            )
            for term in terms
        )

        scheme_in_group = any(
            _contains_phrase(
                text,
                term,
            )
            for term in terms
        )

        if (
            profile_in_group
            and scheme_in_group
        ):
            occupation_group_match = True

            score += 10

            reasons.append(
                f"Scheme aligns with your "
                f"{group}-related livelihood."
            )

            break

    # --------------------------------------------------------
    # SKILLS
    # --------------------------------------------------------

    matched_skills = []

    for skill in profile.skills:
        if _contains_phrase(
            text,
            skill,
        ):
            matched_skills.append(
                skill
            )

    if matched_skills:
        score += min(
            12,
            4 * len(
                matched_skills
            ),
        )

        reasons.append(
            "Related skills found: "
            + ", ".join(
                matched_skills
            )
            + "."
        )

    # --------------------------------------------------------
    # RURAL PROFILE
    # --------------------------------------------------------

    if (
        _normalize(
            profile.residence
        )
        == "rural"
    ):
        rural_terms = [
            "rural",
            "village",
            "gram",
            "agriculture",
            "farmer",
            "panchayat",
        ]

        if any(
            _contains_phrase(
                text,
                term,
            )
            for term in rural_terms
        ):
            score += 8

            reasons.append(
                "Scheme contains rural/livelihood "
                "signals matching your residence."
            )

    # --------------------------------------------------------
    # EMPLOYMENT
    # --------------------------------------------------------

    employment = _normalize(
        profile.employment_status
    )

    if employment == "unemployed":
        employment_terms = [
            "unemployed",
            "employment",
            "livelihood",
            "skill development",
            "training",
            "self employment",
            "self-employment",
        ]

        if any(
            _contains_phrase(
                text,
                term,
            )
            for term in employment_terms
        ):
            score += 8

            reasons.append(
                "Scheme relates to employment, "
                "livelihood or skill development."
            )

    # --------------------------------------------------------
    # BPL
    # --------------------------------------------------------

    bpl_terms = [
        "bpl",
        "below poverty line",
        "economically weaker",
        "low income",
        "poor families",
    ]

    scheme_mentions_bpl = any(
        _contains_phrase(
            text,
            term,
        )
        for term in bpl_terms
    )

    if (
        profile.is_bpl
        and scheme_mentions_bpl
    ):
        score += 12

        reasons.append(
            "Scheme contains BPL / low-income signals "
            "matching your profile."
        )

    # --------------------------------------------------------
    # ECONOMIC DISTRESS
    # --------------------------------------------------------

    distress_terms = [
        "economic distress",
        "destitute",
        "penury",
        "extreme hardship",
        "financial assistance",
    ]

    if (
        profile.is_economic_distress
        and any(
            _contains_phrase(
                text,
                term,
            )
            for term in distress_terms
        )
    ):
        score += 10

        reasons.append(
            "Scheme contains financial-distress "
            "assistance signals."
        )

    # --------------------------------------------------------
    # STUDENT-SPECIFIC SCHEMES
    # --------------------------------------------------------

    student_terms = [
        "student",
        "students",
        "scholarship",
        "education scholarship",
    ]

    student_specific = any(
        _contains_phrase(
            text,
            term,
        )
        for term in student_terms
    )

    if (
        profile.is_student
        and student_specific
    ):
        score += 15

        reasons.append(
            "Scheme contains student or scholarship "
            "signals matching your profile."
        )

    elif (
        not profile.is_student
        and student_specific
    ):
        score -= 18

        warnings.append(
            "Scheme appears student/education focused "
            "while your profile says you are not "
            "currently a student."
        )

    # --------------------------------------------------------
    # DISABILITY-SPECIFIC SCHEMES
    # --------------------------------------------------------

    disability_terms = [
        "person with disability",
        "persons with disabilities",
        "disabled person",
        "disability",
        "divyang",
        "pwd",
    ]

    disability_specific = any(
        _contains_phrase(
            text,
            term,
        )
        for term in disability_terms
    )

    has_disability = (
        _normalize(
            profile.disability
        )
        == "yes"
    )

    if (
        has_disability
        and disability_specific
    ):
        score += 15

        reasons.append(
            "Scheme contains disability-related "
            "support matching your profile."
        )

    elif (
        not has_disability
        and disability_specific
    ):
        score -= 25

        warnings.append(
            "Scheme appears disability-focused while "
            "your profile does not indicate a disability."
        )

    # --------------------------------------------------------
    # MINORITY-SPECIFIC SCHEMES
    # --------------------------------------------------------

    minority_terms = [
        "minority",
        "minorities",
        "minority community",
    ]

    minority_specific = any(
        _contains_phrase(
            text,
            term,
        )
        for term in minority_terms
    )

    belongs_to_minority = (
        _normalize(
            profile.minority
        )
        == "yes"
    )

    if (
        belongs_to_minority
        and minority_specific
    ):
        score += 12

        reasons.append(
            "Scheme contains minority-support signals "
            "matching your profile."
        )

    elif (
        not belongs_to_minority
        and minority_specific
    ):
        score -= 20

        warnings.append(
            "Scheme appears minority-focused while "
            "your profile does not indicate minority "
            "status."
        )

    # --------------------------------------------------------
    # GENDER-SPECIFIC SCHEMES
    # --------------------------------------------------------

    female_terms = [
        "women only",
        "woman only",
        "for women",
        "female beneficiary",
        "women beneficiaries",
        "girl child",
    ]

    female_specific = any(
        _contains_phrase(
            text,
            term,
        )
        for term in female_terms
    )

    if female_specific:
        if (
            _normalize(
                profile.gender
            )
            == "female"
        ):
            score += 12

            reasons.append(
                "Scheme contains women-focused support "
                "matching your profile."
            )

        elif (
            _normalize(
                profile.gender
            )
            == "male"
        ):
            score -= 30

            warnings.append(
                "Scheme appears women-specific while "
                "your profile gender is Male."
            )

    # --------------------------------------------------------
    # ARTISAN-SPECIFIC MISMATCH
    # --------------------------------------------------------

    artisan_terms = [
        "artisan",
        "artisans",
        "handicraft",
        "handloom",
        "weaver",
        "craftsperson",
    ]

    artisan_specific = any(
        _contains_phrase(
            text,
            term,
        )
        for term in artisan_terms
    )

    profile_is_artisan = any(
        _contains_phrase(
            profile_terms,
            term,
        )
        for term in artisan_terms
    )

    if (
        artisan_specific
        and not profile_is_artisan
    ):
        score -= 15

        warnings.append(
            "Scheme appears artisan/handicraft focused "
            "and that livelihood is not present in "
            "your profile."
        )

    # --------------------------------------------------------
    # FARMER-SPECIFIC MISMATCH
    # --------------------------------------------------------

    farmer_terms = [
        "farmer",
        "farmers",
        "agriculture",
        "agricultural",
        "kisan",
        "cultivation",
    ]

    farmer_specific = any(
        _contains_phrase(
            text,
            term,
        )
        for term in farmer_terms
    )

    profile_is_farmer = any(
        _contains_phrase(
            profile_terms,
            term,
        )
        for term in farmer_terms
    )

    if (
        farmer_specific
        and not profile_is_farmer
    ):
        score -= 10

        warnings.append(
            "Scheme appears agriculture/farmer focused "
            "but farming is not present in your profile."
        )

    # --------------------------------------------------------
    # FINAL SCORE
    # --------------------------------------------------------

    score = max(
        0,
        min(
            100,
            score,
        ),
    )

    if score >= 70:
        fit_label = "Strong fit"

    elif score >= 45:
        fit_label = "Possible fit"

    else:
        fit_label = "Weak fit"

    if not reasons:
        reasons.append(
            "Returned by live myScheme for the "
            "submitted profile."
        )

    return {
        "fit_score": score,
        "fit_label": fit_label,
        "fit_reasons": reasons,
        "fit_warnings": warnings,
        "matched_skills": matched_skills,
        "occupation_group_match": (
            occupation_group_match
        ),
    }


# ============================================================
# LIVE SCHEME -> UI ITEM
# ============================================================

def _scheme_to_retrieved_item(
    scheme,
    profile=None,
):
    scheme_name = (
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
            "description"
        )
        or ""
    )

    benefits = (
        scheme.get(
            "benefits"
        )
        or ""
    )

    eligibility = (
        scheme.get(
            "eligibility_signals"
        )
        or ""
    )

    application_info = (
        scheme.get(
            "application_info"
        )
        or ""
    )

    text_parts = []

    if description:
        text_parts.append(
            description
        )

    if eligibility:
        text_parts.append(
            f"Eligibility information: "
            f"{eligibility}"
        )

    if benefits:
        text_parts.append(
            f"Benefits: {benefits}"
        )

    if application_info:
        text_parts.append(
            f"Application: "
            f"{application_info}"
        )

    text = "\n\n".join(
        text_parts
    )

    if not text:
        text = (
            "Live government scheme returned "
            "by the official myScheme service."
        )

    item = {
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

        "ranking_method": (
            "profile_fit"
        ),
    }

    if profile is not None:
        fit = evaluate_scheme_fit(
            scheme,
            profile,
        )

        item.update(
            fit
        )

    return item


# ============================================================
# PROFILE-FIT RANKING
# ============================================================

def _rank_live_schemes(
    schemes,
    profile,
):
    ranked = []

    seen = set()

    for scheme in schemes:
        url = str(
            scheme.get(
                "url",
                "",
            )
        ).strip()

        name = str(
            scheme.get(
                "scheme_name",
                scheme.get(
                    "name",
                    "",
                ),
            )
        ).strip()

        identity = (
            url
            or name.lower()
        )

        if not identity:
            continue

        if identity in seen:
            continue

        seen.add(
            identity
        )

        item = (
            _scheme_to_retrieved_item(
                scheme,
                profile=profile,
            )
        )

        ranked.append(
            item
        )

    ranked.sort(
        key=lambda item: (
            item.get(
                "fit_score",
                0,
            )
        ),
        reverse=True,
    )

    return ranked


# ============================================================
# MAP RAG RESULTS TO LIVE SCHEMES
# ============================================================

def _find_live_scheme(
    rag_item,
    schemes,
):
    rag_url = _normalize(
        rag_item.get(
            "url",
            "",
        )
    )

    rag_name = _normalize(
        rag_item.get(
            "scheme_name",
            "",
        )
    )

    for scheme in schemes:
        live_url = _normalize(
            scheme.get(
                "url",
                "",
            )
        )

        live_name = _normalize(
            scheme.get(
                "scheme_name",
                scheme.get(
                    "name",
                    "",
                ),
            )
        )

        if (
            rag_url
            and live_url
            and rag_url == live_url
        ):
            return scheme

        if (
            rag_name
            and live_name
            and rag_name == live_name
        ):
            return scheme

    return None


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
        "all_ranked": [],
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
    print(
        "LIVELIHOOD -> LIVE MYSCHEME "
        "-> PROFILE FIT -> RAG"
    )
    print("=" * 60)

    # --------------------------------------------------------
    # 1. LIVE MYSCHEME
    # --------------------------------------------------------

    try:
        schemes = fetch_schemes(
            myscheme_profile
        )

    except Exception as exc:
        print(
            "myScheme exception:",
            repr(exc),
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
        "Live schemes:",
        len(schemes),
    )

    # --------------------------------------------------------
    # 2. PROFILE FIT ALL LIVE SCHEMES
    # --------------------------------------------------------

    all_ranked = (
        _rank_live_schemes(
            schemes,
            profile,
        )
    )

    result["all_ranked"] = (
        all_ranked
    )

    print()
    print(
        "PROFILE FIT RESULTS"
    )

    for item in all_ranked:
        print(
            item.get(
                "fit_score"
            ),
            item.get(
                "fit_label"
            ),
            "-",
            item.get(
                "scheme_name"
            ),
        )

    # Safe fallback = best profile-fit schemes.

    result["retrieved"] = (
        all_ranked[:limit]
    )

    result["ranking_method"] = (
        "profile_fit"
    )

    # --------------------------------------------------------
    # 3. INDEX LIVE SCHEMES
    # --------------------------------------------------------

    try:
        indexed_chunks = (
            index_schemes(
                schemes
            )
        )

        result["indexed_chunks"] = (
            indexed_chunks
        )

        print(
            "Indexed chunks:",
            indexed_chunks,
        )

    except Exception as exc:
        print(
            "RAG indexing unavailable:",
            repr(exc),
        )

        # Profile-fit results are already available.
        result["error"] = ""

        return result

    # --------------------------------------------------------
    # 4. RAG QUERY
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

        (
            "student scholarship"
            if profile.is_student
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
    # 5. RETRIEVE MORE THAN FINAL LIMIT
    # --------------------------------------------------------

    try:
        rag_results = (
            retrieve_schemes(
                query,
                top_k=max(
                    10,
                    limit * 2,
                ),
            )
        )

    except Exception as exc:
        print(
            "RAG retrieval unavailable:",
            repr(exc),
        )

        result["error"] = ""
        return result

    if not rag_results:
        print(
            "RAG returned zero results. "
            "Using profile-fit ranking."
        )

        return result

    # --------------------------------------------------------
    # 6. COMBINE RAG + PROFILE FIT
    # --------------------------------------------------------

    combined = []

    seen = set()

    total_rag = len(
        rag_results
    )

    for rag_index, rag_item in enumerate(
        rag_results
    ):
        live_scheme = (
            _find_live_scheme(
                rag_item,
                schemes,
            )
        )

        if live_scheme is None:
            continue

        item = (
            _scheme_to_retrieved_item(
                live_scheme,
                profile=profile,
            )
        )

        identity = (
            item.get(
                "url"
            )
            or item.get(
                "scheme_name",
                "",
            ).lower()
        )

        if identity in seen:
            continue

        seen.add(
            identity
        )

        # Higher-ranked semantic result gets
        # a small bonus.
        rag_bonus = max(
            0,
            15 - (
                rag_index * 2
            ),
        )

        item[
            "rag_bonus"
        ] = rag_bonus

        item[
            "combined_score"
        ] = min(
            100,
            item.get(
                "fit_score",
                0,
            )
            + rag_bonus,
        )

        item[
            "ranking_method"
        ] = (
            "profile_fit_plus_rag"
        )

        combined.append(
            item
        )

    # --------------------------------------------------------
    # 7. INCLUDE LIVE SCHEMES RAG MAY HAVE MISSED
    # --------------------------------------------------------

    for item in all_ranked:
        identity = (
            item.get(
                "url"
            )
            or item.get(
                "scheme_name",
                "",
            ).lower()
        )

        if identity in seen:
            continue

        seen.add(
            identity
        )

        copy_item = dict(
            item
        )

        copy_item[
            "rag_bonus"
        ] = 0

        copy_item[
            "combined_score"
        ] = copy_item.get(
            "fit_score",
            0,
        )

        combined.append(
            copy_item
        )

    # --------------------------------------------------------
    # 8. FINAL SORT
    # --------------------------------------------------------

    combined.sort(
        key=lambda item: (
            item.get(
                "combined_score",
                item.get(
                    "fit_score",
                    0,
                ),
            )
        ),
        reverse=True,
    )

    result["all_ranked"] = (
        combined
    )

    # Recommended section.
    #
    # Prefer Strong + Possible fits.
    recommended = [
        item
        for item in combined
        if item.get(
            "fit_label"
        )
        in {
            "Strong fit",
            "Possible fit",
        }
    ]

    # Never leave UI empty merely because
    # all scores are weak.
    if not recommended:
        recommended = combined

    result["retrieved"] = (
        recommended[:limit]
    )

    result["ranking_method"] = (
        "profile_fit_plus_rag"
    )

    result["error"] = ""

    print()
    print(
        "FINAL RECOMMENDATIONS:"
    )

    for item in result[
        "retrieved"
    ]:
        print(
            item.get(
                "combined_score",
                item.get(
                    "fit_score",
                    0,
                ),
            ),
            item.get(
                "fit_label"
            ),
            "-",
            item.get(
                "scheme_name"
            ),
        )

    return result


# ============================================================
# PROFILE SUMMARY
# ============================================================

def get_livelihood_summary(
    profile,
):
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
        "experience": profile.experience,
        "work_preference": (
            profile.work_preference
        ),
        "language": profile.language,
        "caste": profile.caste,
        "disability": profile.disability,
        "minority": profile.minority,

        "employment_status": (
            profile.employment_status
        ),

        "marital_status": (
            profile.marital_status
        ),

        "is_bpl": profile.is_bpl,

        "is_economic_distress": (
            profile.is_economic_distress
        ),
    }