from core.retrieval import (
    _chunk_text,
    _scheme_to_text,
)


def test_chunking():
    text = "A" * 2000

    chunks = _chunk_text(
        text,
        chunk_size=900,
        overlap=120,
    )

    assert len(chunks) > 1
    assert all(chunks)


def test_scheme_to_text():
    scheme = {
        "scheme_name": "Example Scholarship",
        "description": "Education support.",
        "eligibility_signals": "Students.",
        "benefits": "Financial assistance.",
        "application_info": "Apply online.",
    }

    text = _scheme_to_text(scheme)

    assert "Example Scholarship" in text
    assert "Students." in text
    assert "Financial assistance." in text
    assert "Apply online." in text


def test_metadata_contract():
    scheme = {
        "scheme_name": "Example",
        "description": "Description",
        "eligibility_signals": "Eligibility",
        "benefits": "Benefits",
        "application_info": "Application",
        "url": "https://www.myscheme.gov.in/schemes/example",
        "source": "myScheme",
        "state": "Andhra Pradesh",
        "category": "Education & Learning",
        "fetched_at": "2026-09-17T00:00:00+00:00",
    }

    required = [
        "scheme_name",
        "description",
        "eligibility_signals",
        "benefits",
        "application_info",
        "url",
        "source",
        "state",
        "category",
        "fetched_at",
    ]

    for field in required:
        assert field in scheme