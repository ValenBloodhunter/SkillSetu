"""
SkillSetu - Student Interview Agent

Handles the student-facing mock interview workflow.

This module:
- Generates role-specific interview questions.
- Evaluates student answers.
- Returns structured, actionable feedback.
- Provides deterministic fallbacks when Gemini is unavailable.

It does NOT handle:
- Live job matching
- Skill-gap calculations
- Roadmap generation
"""

from __future__ import annotations

from typing import Any, Dict, List

from core.llm import evaluate_interview, generate_interview_question


# ---------------------------------------------------------------------------
# Role-specific question bank
# ---------------------------------------------------------------------------

INTERVIEW_QUESTIONS = {
    "data analyst": [
        "What is SQL used for in data analysis?",
        "How would you handle missing values in a dataset?",
        "What is the difference between a metric and a dimension?",
        "How would you explain a data insight to a non-technical person?",
        "How would you use Excel to analyze a large dataset?",
    ],
    "software developer": [
        "What is the difference between a list and a tuple in Python?",
        "How would you debug a program that is producing incorrect output?",
        "What is an API?",
        "Explain the importance of version control.",
        "How would you approach solving a programming problem you have never seen before?",
    ],
    "web developer": [
        "What is the difference between HTML, CSS, and JavaScript?",
        "What happens when you enter a URL into a browser?",
        "What is responsive web design?",
        "What is an API and how can a frontend application use one?",
        "How would you debug a webpage that is not displaying correctly?",
    ],
    "business analyst": [
        "What is the role of a business analyst?",
        "How would you gather requirements from a stakeholder?",
        "How would you handle conflicting requirements?",
        "How would you explain a business problem to a technical team?",
        "How would you measure whether a proposed solution was successful?",
    ],
    "marketing analyst": [
        "What metrics would you use to measure a marketing campaign?",
        "How would you analyze customer behavior?",
        "What is conversion rate?",
        "How would you identify why campaign performance decreased?",
        "How would you communicate campaign results to a manager?",
    ],
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalize_role(role: str) -> str:
    """Normalize a role for question-bank lookup."""
    return str(role or "").strip().lower()


def _fallback_question(role: str) -> str:
    """Return a useful deterministic question when Gemini is unavailable."""
    normalized_role = _normalize_role(role)

    questions = INTERVIEW_QUESTIONS.get(normalized_role)

    if questions:
        return questions[0]

    return (
        f"Explain one important skill you would use in a "
        f"{role or 'professional'} role and give a practical example."
    )


# ---------------------------------------------------------------------------
# Public interview functions
# ---------------------------------------------------------------------------

def get_interview_question(
    role: str,
    difficulty: str = "beginner",
) -> str:
    """
    Generate a role-specific interview question.

    Gemini is used when available. If generation fails, a deterministic
    role-specific question is returned.
    """
    role = str(role or "").strip()

    if not role:
        role = "General Professional"

    try:
        question = generate_interview_question(
            role=role,
            difficulty=difficulty,
        )

        if question and isinstance(question, str):
            return question.strip()

    except Exception:
        pass

    return _fallback_question(role)


def evaluate_student_answer(
    question: str,
    answer: str,
    role: str,
) -> Dict[str, Any]:
    """
    Evaluate a student's interview answer.

    Returns a structured result containing:
    - score
    - strengths
    - issues
    - missing_points
    - improved_answer
    - next_action

    The evaluation function in core/llm.py already provides a deterministic
    fallback if Gemini is unavailable.
    """
    question = str(question or "").strip()
    answer = str(answer or "").strip()
    role = str(role or "").strip()

    if not question:
        return {
            "score": 0,
            "strengths": [],
            "issues": ["No interview question was provided."],
            "missing_points": [],
            "improved_answer": "",
            "next_action": "Provide an interview question and try again.",
        }

    if not answer:
        return {
            "score": 0,
            "strengths": [],
            "issues": ["No answer was provided."],
            "missing_points": [
                "Answer the question directly.",
                "Explain your reasoning.",
                "Include a relevant example where possible.",
            ],
            "improved_answer": (
                "Start by directly answering the question, then explain "
                "your reasoning and provide a relevant example."
            ),
            "next_action": (
                "Try answering the question in 2–4 clear sentences."
            ),
        }

    try:
        feedback = evaluate_interview(
            question=question,
            answer=answer,
            role=role,
        )

        if isinstance(feedback, dict):
            return _normalize_feedback(feedback)

    except Exception:
        pass

    # This should normally not be reached because core/llm.py has its own
    # fallback, but keeping a second safe fallback makes this module robust.
    return _fallback_evaluation(question, answer, role)


def _normalize_feedback(feedback: Dict[str, Any]) -> Dict[str, Any]:
    """
    Ensure feedback always follows the expected structured contract.
    """
    score = feedback.get("score", 0)

    try:
        score = int(float(score))
    except (TypeError, ValueError):
        score = 0

    score = max(0, min(100, score))

    strengths = feedback.get("strengths", [])
    issues = feedback.get("issues", [])
    missing_points = feedback.get("missing_points", [])

    if isinstance(strengths, str):
        strengths = [strengths]

    if isinstance(issues, str):
        issues = [issues]

    if isinstance(missing_points, str):
        missing_points = [missing_points]

    return {
        "score": score,
        "strengths": list(strengths),
        "issues": list(issues),
        "missing_points": list(missing_points),
        "improved_answer": str(
            feedback.get("improved_answer", "")
        ).strip(),
        "next_action": str(
            feedback.get("next_action", "")
        ).strip(),
    }


def _fallback_evaluation(
    question: str,
    answer: str,
    role: str,
) -> Dict[str, Any]:
    """
    Deterministic fallback evaluation.

    This is intentionally simple and transparent. It is not presented as
    a certification or authoritative interview score.
    """
    answer_length = len(answer.split())

    if answer_length < 8:
        score = 35
        issues = [
            "The answer is too brief to demonstrate the reasoning clearly."
        ]
        missing_points = [
            "Explain the approach.",
            "Include a concrete example or technical detail.",
        ]
        next_action = (
            "Practice answering this question using a specific example "
            "and clear reasoning."
        )
    elif answer_length < 25:
        score = 60
        issues = [
            "The answer has useful information but could explain the "
            "reasoning in more detail."
        ]
        missing_points = [
            "Add a concrete example.",
            "Explain the result or expected outcome.",
        ]
        next_action = (
            "Expand the answer with a practical example and explain "
            "why your approach would work."
        )
    else:
        score = 80
        issues = [
            "The answer could be made stronger with a more specific "
            "example or measurable result."
        ]
        missing_points = [
            "Add a concrete example if one is available.",
        ]
        next_action = (
            "Practice giving the same answer more concisely while keeping "
            "the technical details and example."
        )

    return {
        "score": score,
        "strengths": [
            "The candidate provided a substantive response."
        ],
        "issues": issues,
        "missing_points": missing_points,
        "improved_answer": (
            f"For a {role or 'professional'} interview, a stronger answer "
            "would directly address the question, explain the approach "
            "step by step, and include a concrete example."
        ),
        "next_action": next_action,
    }


# ---------------------------------------------------------------------------
# Interview session helper
# ---------------------------------------------------------------------------

def run_interview_turn(
    role: str,
    question: str,
    answer: str,
) -> Dict[str, Any]:
    """
    Process one complete mock-interview turn.

    Useful for the Streamlit UI later.
    """
    feedback = evaluate_student_answer(
        question=question,
        answer=answer,
        role=role,
    )

    return {
        "role": role,
        "question": question,
        "answer": answer,
        "feedback": feedback,
    }


def get_role_question_bank(role: str) -> List[str]:
    """Return the deterministic question bank for a role."""
    return list(
        INTERVIEW_QUESTIONS.get(
            _normalize_role(role),
            [],
        )
    )


# ---------------------------------------------------------------------------
# Local test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("SkillSetu Interview Module Test")
    print("--------------------------------")

    role = "Data Analyst"

    question = get_interview_question(role)

    print("Role:", role)
    print("Question:", question)

    answer = (
        "SQL is used to work with databases and retrieve data "
        "for analysis."
    )

    feedback = evaluate_student_answer(
        question=question,
        answer=answer,
        role=role,
    )

    print("\nFeedback:")
    print("Score:", feedback["score"])
    print("Strengths:", feedback["strengths"])
    print("Issues:", feedback["issues"])
    print("Missing points:", feedback["missing_points"])
    print("Improved answer:", feedback["improved_answer"])
    print("Next action:", feedback["next_action"])