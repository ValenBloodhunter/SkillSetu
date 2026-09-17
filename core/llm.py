"""
SkillSetu - Gemini LLM Utility

AI service layer for:
- Interview question generation
- Interview feedback
- Roadmap explanations
- Job explanations
- Multilingual career assistance

Deterministic business logic such as matching scores and
skill-gap calculations remains outside this module.
"""

import json
import os
from typing import Any, Dict, Optional

from google import genai
from google.genai import types


DEFAULT_MODEL = "gemini-3.8-flash"


def _get_client() -> Optional[genai.Client]:
    """Create a Gemini client from GEMINI_API_KEY."""
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        return None

    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def _generate(
    prompt: str,
    model_name: str = DEFAULT_MODEL,
) -> Optional[str]:
    """
    Generate text using Gemini.

    Returns None if the API key is missing or the API call fails.
    """
    client = _get_client()

    if client is None:
        return None

    try:
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
        )

        if response and getattr(response, "text", None):
            return response.text.strip()

    except Exception:
        return None

    return None


def generate_interview_question(
    role: str,
    difficulty: str = "beginner",
) -> str:
    """Generate one role-specific interview question."""

    prompt = f"""
You are an interview question generator for a career guidance application.

Target role: {role}
Difficulty: {difficulty}

Generate exactly ONE practical interview question.

Requirements:
- Relevant to the target role.
- Appropriate for the specified difficulty.
- Do not provide the answer.
- Do not add explanations.
- Do not add numbering.
"""

    result = _generate(prompt)

    if result:
        return result

    return (
        f"Explain how you would approach a typical problem "
        f"you might face as a {role}."
    )


def evaluate_interview(
    question: str,
    answer: str,
    role: str,
) -> Dict[str, Any]:
    """
    Evaluate an interview answer.

    Returns:
        score
        strengths
        issues
        missing_points
        improved_answer
        next_action
    """

    prompt = f"""
You are evaluating a mock interview answer.

Target role: {role}

Question:
{question}

Candidate answer:
{answer}

Return ONLY valid JSON with exactly these fields:

{{
    "score": <integer from 0 to 100>,
    "strengths": [<specific strengths>],
    "issues": [<specific issues>],
    "missing_points": [<important missing points>],
    "improved_answer": "<a concise improved answer>",
    "next_action": "<one concrete action>"
}}

Rules:
- Feedback must be specific to the question and role.
- Do not give generic advice such as "improve communication".
- Do not claim the candidate is certified or professionally qualified.
"""

    result = _generate(prompt)

    if result:
        try:
            cleaned = result.strip()

            if cleaned.startswith("```"):
                cleaned = cleaned.replace("```json", "")
                cleaned = cleaned.replace("```", "")
                cleaned = cleaned.strip()

            parsed = json.loads(cleaned)

            required_fields = {
                "score",
                "strengths",
                "issues",
                "missing_points",
                "improved_answer",
                "next_action",
            }

            if required_fields.issubset(parsed.keys()):
                parsed["score"] = max(
                    0,
                    min(100, int(parsed["score"])),
                )
                return parsed

        except (json.JSONDecodeError, TypeError, ValueError):
            pass

    return _fallback_interview_feedback(question, answer, role)


def _fallback_interview_feedback(
    question: str,
    answer: str,
    role: str,
) -> Dict[str, Any]:
    """Deterministic fallback when Gemini is unavailable."""

    answer_text = answer.strip()

    if not answer_text:
        return {
            "score": 0,
            "strengths": [],
            "issues": ["No answer was provided."],
            "missing_points": [
                "Provide a direct answer to the question."
            ],
            "improved_answer": (
                f"For this {role} question, I would first identify "
                "the requirements, explain my approach, and validate "
                "the result."
            ),
            "next_action": (
                "Answer the question with one concrete example."
            ),
        }

    word_count = len(answer_text.split())

    if word_count < 15:
        score = 35
        issues = [
            "The answer is too brief to demonstrate the reasoning clearly."
        ]
        missing_points = [
            "Explain the approach.",
            "Include a concrete example or technical detail.",
        ]

    elif word_count < 40:
        score = 60
        issues = [
            "The answer provides some detail but the reasoning "
            "could be clearer."
        ]
        missing_points = [
            "Add a concrete example or implementation detail."
        ]

    else:
        score = 75
        issues = [
            "The answer could be strengthened with more "
            "role-specific evidence."
        ]
        missing_points = [
            "Connect the explanation to a concrete real-world outcome."
        ]

    return {
        "score": score,
        "strengths": [
            "The candidate provided a substantive response."
        ],
        "issues": issues,
        "missing_points": missing_points,
        "improved_answer": (
            f"A stronger answer would directly address the question, "
            f"explain the approach step by step, and include a concrete "
            f"example relevant to a {role} role."
        ),
        "next_action": (
            "Practice answering this question using a specific "
            "example and clear reasoning."
        ),
    }


def explain_roadmap(
    role: str,
    roadmap: Dict[str, Any],
) -> str:
    """Explain a deterministic roadmap in natural language."""

    prompt = f"""
Explain this career roadmap to a student targeting the role:
{role}

Roadmap data:
{json.dumps(roadmap, indent=2)}

Explain:
1. What skills should be developed first.
2. Why those skills matter.
3. What the student should do next.

Keep the explanation concise and practical.

Do not:
- change the roadmap priorities
- invent skill requirements
- invent job-market facts
"""

    result = _generate(prompt)

    if result:
        return result

    items = roadmap.get("roadmap", [])

    if not items:
        return (
            "Your current skills meet the defined requirements "
            "for this role."
        )

    first = items[0]

    return (
        f"Focus first on {first.get('skill', 'the highest-priority skill')}. "
        f"It currently has a {first.get('gap', 0)}-level gap toward "
        f"the target level. Start with practical learning and exercises."
    )


def explain_job(
    job: Dict[str, Any],
    profile: Any,
) -> str:
    """Explain an opportunity using only supplied job/profile data."""

    if isinstance(profile, dict):
        profile_data = profile
    else:
        profile_data = vars(profile)

    prompt = f"""
Explain this job opportunity to a candidate.

Candidate:
{json.dumps(profile_data, indent=2)}

Job:
{json.dumps(job, indent=2)}

Give a short explanation covering:
- Why the opportunity may fit.
- Relevant skills.
- Skills the candidate may need to improve.

Use ONLY information present in the supplied data.
Do not invent job facts.
"""

    result = _generate(prompt)

    if result:
        return result

    return (
        "Review this opportunity against your matched skills, "
        "missing skills, location, experience, and work preference."
    )


def generate_assistance(
    message: str,
    language: str = "English",
) -> str:
    """Provide general multilingual career assistance."""

    prompt = f"""
You are a career guidance assistant.

Respond to the user's message in {language}.

User message:
{message}

Give a concise, practical response.

Do not invent factual job information or government-scheme information.
"""

    result = _generate(prompt)

    if result:
        return result

    return (
        "I could not connect to the AI service right now. "
        "Please try again shortly."
    )