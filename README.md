# 🌉 SkillSetu

### AI Career & Livelihood Guidance Agent

**From where you are → to where you can go.**

SkillSetu is an AI-powered career and livelihood guidance platform built to support both **students** and **livelihood workers** through one shared guidance architecture.

It combines live opportunity discovery, skill assessment, skill-gap analysis, adaptive roadmaps, government scheme discovery, RAG-based recommendations, mock interviews, and multilingual voice assistance.

---

## 🎯 Problem

Career and livelihood guidance is often fragmented.

Students may know the career they want but not:

- Which skills they are missing
- Which jobs match their current abilities
- What they should learn next
- How prepared they are for interviews

Livelihood and informal workers face a different challenge:

- Discovering relevant work opportunities
- Finding government schemes
- Understanding which schemes may fit their profile
- Language and accessibility barriers

SkillSetu brings these workflows into one platform.

---

# ✨ Two Experiences — One Engine

## 🎓 Student Journey

```text
Student Profile
      ↓
Dynamic Skill Assessment
      ↓
Live Job Opportunities
      ↓
Shared Matching Engine
      ↓
Skill Gap Analysis
      ↓
Adaptive Learning Roadmap
      ↓
Mock Interview
      ↓
Specific Feedback
```

Students can:

- Create a career profile
- Select a target role
- Take a dynamic role-based skill assessment
- Discover live job opportunities
- View skill-match percentages
- Identify missing skills
- Generate a personalized learning roadmap
- Simulate skill improvement
- Compare before/after roadmap changes
- Practice target-role interview questions
- Receive structured interview feedback

---

## 🌾 Livelihood Worker Journey

```text
Livelihood Profile
       ↓
 ┌─────┴─────────────┐
 ↓                   ↓
Live Jobs       Live myScheme
 ↓                   ↓
Shared          Profile Fit
Matching             ↓
Engine          ChromaDB RAG
 ↓                   ↓
Opportunities   Scheme Recommendations
       \             /
        └─────┬─────┘
              ↓
      Multilingual Voice
```

Livelihood users can:

- Create a profile using skills, occupation and location
- Search live work opportunities
- Receive target-role recommendations
- Explore government schemes from live myScheme results
- View profile-relevance scores
- Understand why a scheme may match
- Open the official scheme source for eligibility verification
- Ask questions through a voice interface
- Receive Telugu, English or Hindi voice responses

---

# 🧠 Dynamic Skill Assessment

The Student Skill Assessment changes according to the student's:

- Target career role
- Existing skills

For example:

### Data Analyst

```text
Python
Excel
SQL
Statistics
Power BI
```

### Web Developer

```text
HTML
CSS
JavaScript
Git
React
```

Assessment results are converted into a structured skill state that is used by the roadmap system.

---

# 💼 Live Opportunity Matching

SkillSetu retrieves jobs from a live external job feed.

The same shared matching architecture is used to evaluate opportunities using signals such as:

- Skills
- Location
- Experience
- Work preference

The livelihood interface additionally validates job titles against the user's target role so unrelated opportunities are not presented as direct target-role recommendations.

> **Current MVP limitation:** the current live job source is primarily European. SkillSetu therefore does not claim that these results represent local Indian vacancies. An India-focused provider can be connected through the same data-source architecture.

---

# 🗺️ Adaptive Career Roadmap

SkillSetu converts assessment results into skill levels and compares them against target-role requirements.

The roadmap identifies:

```text
Current Skills
      ↓
Required Skills
      ↓
Skill Gaps
      ↓
Learning Priorities
```

SkillSetu can also simulate skill improvement.

```text
Before Learning
Python: 0.60

       ↓ Learn / Improve

After Learning
Python: 0.80

       ↓

Roadmap Recalculated
```

This demonstrates that the roadmap adapts as the user's skill state changes.

---

# 🎤 Mock Interview

Students can practice interview questions based on their target role.

The interview workflow provides structured feedback including:

- Answer score
- Strengths
- Missing points
- Areas for improvement
- Improved answer guidance
- Suggested next action

---

# 🏛️ Live Government Scheme Discovery

SkillSetu integrates live results from **myScheme** rather than maintaining a hardcoded scheme list.

Pipeline:

```text
User Profile
     ↓
Live myScheme Retrieval
     ↓
Profile-Fit Analysis
     ↓
Scheme Content Extraction
     ↓
ChromaDB Index
     ↓
Semantic Retrieval
     ↓
Profile Fit + RAG Ranking
     ↓
Recommendations
```

Recommendations are displayed as:

- 🟢 Strong fit
- 🟡 Possible fit
- ⚪ Weak fit

These labels indicate **profile relevance**, not confirmed government eligibility.

Users are directed to the official myScheme source to verify final eligibility and application requirements.

---

# 🔎 Retrieval-Augmented Generation (RAG)

Government scheme information is processed through a RAG pipeline.

SkillSetu uses:

- Scheme descriptions
- Eligibility information
- Benefits
- Application information
- State/category metadata

The content is embedded and indexed using **ChromaDB** and **Sentence Transformers**.

Semantic retrieval then helps rank scheme information against the user's livelihood profile.

---

# 🎙️ Multilingual Voice Assistant

SkillSetu includes a voice interface powered by Sarvam AI.

```text
Microphone
    ↓
Sarvam Speech-to-Text
    ↓
SkillSetu Guidance
    ↓
Translation
    ↓
Sarvam Text-to-Speech
    ↓
Voice Response
```

Supported MVP languages include:

- Telugu
- English
- Hindi

Telugu-first voice support helps make livelihood guidance more accessible to users who may prefer regional-language interaction.

---

# 🏗️ Architecture

```text
                     ┌──────────────────┐
                     │    Streamlit     │
                     │       UI         │
                     └────────┬─────────┘
                              │
                ┌─────────────┴─────────────┐
                │                           │
          Student Flow              Livelihood Flow
                │                           │
                └─────────────┬─────────────┘
                              │
                    ┌─────────▼─────────┐
                    │  Shared SkillSetu │
                    │      Core         │
                    └─────────┬─────────┘
                              │
           ┌──────────────────┼──────────────────┐
           │                  │                  │
           ▼                  ▼                  ▼
     Matching Engine     Roadmap Engine      Retrieval
           │                                     │
           ▼                                     ▼
     Live Job API                         Live myScheme
                                                 │
                                                 ▼
                                      ChromaDB + Embeddings

                              │
                              ▼
                       AI / LLM Layer

                              │
                              ▼
                       Sarvam AI Voice
```

A core design principle of SkillSetu is that the Student and Livelihood experiences do **not** operate as two unrelated applications.

They reuse shared profile, matching, skill-gap and guidance components.

---

# 🛠️ Technology Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | Python |
| AI / LLM | Gemini |
| Voice | Sarvam AI |
| Speech-to-Text | Sarvam Saaras |
| Text-to-Speech | Sarvam Bulbul |
| Live Jobs | Arbeitnow API |
| Government Schemes | myScheme |
| Vector Database | ChromaDB |
| Embeddings | Sentence Transformers |
| Web Retrieval | Requests / BeautifulSoup / Playwright |
| Data Processing | Pandas |
| Version Control | GitHub |
| Deployment | Streamlit Community Cloud |

---

# 📂 Project Structure

```text
SkillSetu/
│
├── app.py
│
├── core/
│   ├── matching_engine.py
│   ├── profile.py
│   ├── retrieval.py
│   └── roadmap_engine.py
│
├── data/
│   ├── jobs.py
│   └── schemes.py
│
├── features/
│   ├── student.py
│   ├── student_jobs.py
│   ├── student_roadmap.py
│   ├── interview.py
│   ├── livelihood.py
│   ├── livelihood_ui.py
│   └── voice.py
│
├── requirements.txt
└── README.md
```

---

# 🚀 Local Setup

Clone the repository:

```bash
git clone https://github.com/ValenBloodhunter/SkillSetu.git
cd SkillSetu
```

Switch to the development branch:

```bash
git checkout deb-branch
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it.

### macOS / Linux

```bash
source .venv/bin/activate
```

### Windows

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

---

# 🔐 Secrets

Create:

```text
.streamlit/secrets.toml
```

Add the API keys required by the application.

Example:

```toml
SARVAM_API_KEY = "your-key"
GEMINI_API_KEY = "your-key"
```

**Never commit real API keys to GitHub.**

Make sure `.streamlit/secrets.toml` is included in `.gitignore`.

---

# ▶️ Run SkillSetu

```bash
python -m streamlit run app.py
```

Then open the local Streamlit address shown in the terminal.

---

# 🧪 Suggested Demo

## Student

Create a student such as:

```text
Education: B.Tech
Location: Hyderabad
Skills: Python, Excel
Target Role: Data Analyst
```

Demonstrate:

```text
Profile
→ Dynamic Skill Assessment
→ Live Jobs
→ Skill Gaps
→ Roadmap
→ Simulated Skill Improvement
→ Updated Roadmap
→ Mock Interview
```

## Livelihood Worker

Create a livelihood profile and demonstrate:

```text
Profile
→ Live Opportunities
→ Government Schemes
→ Profile Fit + RAG
→ Official myScheme Source
→ Telugu Voice Assistant
```

---

# ⚠️ MVP Limitations

SkillSetu was developed as a hackathon MVP.

Current limitations include:

- Job coverage depends on the external live job provider
- The current job source is primarily European
- Government-scheme ranking uses profile-based heuristics combined with semantic retrieval and requires further calibration
- Scheme recommendations represent potential matches, not confirmed eligibility
- Production deployment requires secure API-secret configuration
- Live web sources may occasionally change their structure or availability

---

# 🔮 Future Scope

Future versions can include:

- India-focused live job providers
- More adaptive assessments
- Additional regional languages
- Deeper voice-driven navigation
- Improved scheme-ranking calibration
- More government data integrations
- Resume analysis
- Employer-side skill matching
- Persistent user progress
- Improved accessibility for low-bandwidth environments

---

# 🌉 SkillSetu

### From where you are → to where you can go.

A unified AI guidance system connecting **skills, opportunities, learning and livelihood support**.