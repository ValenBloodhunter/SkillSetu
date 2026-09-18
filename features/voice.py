"""
SkillSetu Voice Assistant

Sarvam AI:
Audio -> Speech-to-Text
Text  -> Telugu/English translation
Text  -> Speech

The API key must come from Streamlit secrets.
Never hardcode keys here.
"""

import base64
import os
import tempfile

import streamlit as st
from sarvamai import SarvamAI


LANGUAGE_CODES = {
    "Telugu": "te-IN",
    "English": "en-IN",
    "Hindi": "hi-IN",
}


def _get_api_key():
    try:
        key = st.secrets["SARVAM_API_KEY"]

        if key:
            return str(key).strip()

    except Exception:
        pass

    key = os.getenv("SARVAM_API_KEY", "")

    return key.strip()


def _client():
    api_key = _get_api_key()

    if not api_key:
        raise RuntimeError(
            "SARVAM_API_KEY is missing. "
            "Add it to .streamlit/secrets.toml."
        )

    return SarvamAI(
        api_subscription_key=api_key
    )


def language_code(language="Telugu"):
    return LANGUAGE_CODES.get(
        language,
        "te-IN",
    )


# ============================================================
# SPEECH TO TEXT
# ============================================================

def speech_to_text(
    audio_bytes,
    suffix=".wav",
):
    """
    Convert recorded speech to text.

    Sarvam automatically recognizes supported
    Indian languages using Saaras.
    """

    if not audio_bytes:
        raise ValueError(
            "No audio was provided."
        )

    client = _client()

    temp_path = None

    try:
        with tempfile.NamedTemporaryFile(
            suffix=suffix,
            delete=False,
        ) as temp_file:
            temp_file.write(audio_bytes)
            temp_path = temp_file.name

        with open(temp_path, "rb") as audio_file:
            response = (
                client.speech_to_text.transcribe(
                    file=audio_file,
                    model="saaras:v4",
                    mode="transcribe",
                )
            )

        transcript = getattr(
            response,
            "transcript",
            "",
        )

        detected_language = getattr(
            response,
            "language_code",
            "",
        )

        return {
            "text": transcript or "",
            "language_code": (
                detected_language or ""
            ),
        }

    finally:
        if (
            temp_path
            and os.path.exists(temp_path)
        ):
            try:
                os.remove(temp_path)
            except OSError:
                pass


# ============================================================
# TRANSLATION
# ============================================================

def translate_text(
    text,
    target_language="Telugu",
):
    """
    Translate SkillSetu's response into the
    user's preferred language.
    """

    text = str(text or "").strip()

    if not text:
        return ""

    target_code = language_code(
        target_language
    )

    if target_code == "en-IN":
        return text

    client = _client()

    response = client.text.translate(
        input=text,
        source_language_code="auto",
        target_language_code=target_code,
    )

    translated = getattr(
        response,
        "translated_text",
        None,
    )

    if translated:
        return translated

    # SDK response compatibility fallback.
    translated = getattr(
        response,
        "translation",
        None,
    )

    if translated:
        return translated

    return str(response)


# ============================================================
# TEXT TO SPEECH
# ============================================================

def text_to_speech(
    text,
    language="Telugu",
):
    """
    Generate playable WAV audio.

    Returns raw WAV bytes.
    """

    text = str(text or "").strip()

    if not text:
        raise ValueError(
            "Cannot generate speech from empty text."
        )

    # Keep demo responses short and fast.
    text = text[:2200]

    client = _client()

    response = (
        client.text_to_speech.convert(
            text=text,
            language_code=language_code(
                language
            ),
            model="bulbul:v3",
            speaker="shubh",
            output_audio_codec="wav",
        )
    )

    audios = getattr(
        response,
        "audios",
        None,
    )

    if not audios:
        raise RuntimeError(
            "Sarvam returned no audio."
        )

    return base64.b64decode(
        audios[0]
    )


# ============================================================
# SIMPLE LIVELIHOOD RESPONSE
# ============================================================

def build_livelihood_voice_response(
    user_text,
    profile=None,
):
    """
    Fast deterministic response for the hackathon MVP.

    This keeps voice usable even if Gemini is unavailable.
    """

    question = str(
        user_text or ""
    ).strip()

    question_lower = question.lower()

    if not question:
        return (
            "Please ask me about jobs, skills, "
            "or government schemes."
        )

    if profile is None:
        return (
            "Please create your SkillSetu profile first. "
            "Then I can guide you about jobs, skills, "
            "and government schemes."
        )

    name = getattr(
        profile,
        "name",
        "there",
    )

    target_role = getattr(
        profile,
        "target_role",
        "",
    )

    location = getattr(
        profile,
        "location",
        "",
    )

    skills = getattr(
        profile,
        "skills",
        [],
    )

    if any(
        word in question_lower
        for word in [
            "scheme",
            "government",
            "పథకం",
            "పథకాలు",
            "ప్రభుత్వ",
        ]
    ):
        return (
            f"{name}, open the Government Schemes tab "
            f"to search live myScheme recommendations "
            f"using your profile for {location}. "
            "SkillSetu will show the official scheme "
            "source and relevant information."
        )

    if any(
        word in question_lower
        for word in [
            "job",
            "work",
            "opportunity",
            "ఉద్యోగ",
            "పని",
        ]
    ):
        role_text = (
            target_role
            if target_role
            else "your preferred role"
        )

        return (
            f"{name}, SkillSetu can search live "
            f"opportunities for {role_text} and rank "
            f"them using your skills and location "
            f"{location}. Open the Opportunities tab "
            "and select Find Live Opportunities."
        )

    if any(
        word in question_lower
        for word in [
            "skill",
            "skills",
            "నైపుణ్యం",
            "నైపుణ్యాలు",
        ]
    ):
        skill_text = (
            ", ".join(skills)
            if skills
            else "no skills entered yet"
        )

        return (
            f"Your current SkillSetu skills are "
            f"{skill_text}. Your target role is "
            f"{target_role or 'not specified'}. "
            "SkillSetu uses these skills in the "
            "shared matching engine."
        )

    return (
        f"Hello {name}. I am the SkillSetu voice "
        "assistant. You can ask me about live jobs, "
        "your skills, or government schemes."
    )


# ============================================================
# COMPLETE VOICE TURN
# ============================================================

def process_voice_turn(
    audio_bytes,
    profile=None,
    preferred_language="Telugu",
    suffix=".wav",
):
    """
    Full voice pipeline:

    Audio
      -> Sarvam STT
      -> SkillSetu response
      -> Sarvam translation
      -> Sarvam TTS
    """

    stt = speech_to_text(
        audio_bytes,
        suffix=suffix,
    )

    user_text = stt["text"]

    english_response = (
        build_livelihood_voice_response(
            user_text,
            profile=profile,
        )
    )

    try:
        localized_response = translate_text(
            english_response,
            target_language=preferred_language,
        )

    except Exception:
        # Text fallback if translation fails.
        localized_response = english_response

    audio_response = text_to_speech(
        localized_response,
        language=preferred_language,
    )

    return {
        "transcript": user_text,
        "detected_language": stt.get(
            "language_code",
            "",
        ),
        "response_text": localized_response,
        "audio_bytes": audio_response,
    }