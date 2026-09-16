import os
import re

import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from google import genai


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="wide"
)


# ============================================================
# LOAD API KEY
# ============================================================

load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("Gemini API key not found. Please check your .env file.")
    st.stop()


# ============================================================
# GEMINI CLIENT
# ============================================================

client = genai.Client(api_key=api_key)


# ============================================================
# HEADER
# ============================================================

st.title("📄 AI Resume Analyzer")

st.markdown(
    "Upload your resume to get an **AI-powered resume analysis, "
    "ATS score, and job description match**."
)

st.divider()


# ============================================================
# RESUME UPLOAD
# ============================================================

st.subheader("📤 Upload Your Resume")

resume = st.file_uploader(
    "Choose a PDF resume",
    type=["pdf"]
)


# ============================================================
# PROCESS RESUME
# ============================================================

if resume is not None:

    st.success(f"✅ Resume uploaded: {resume.name}")

    # --------------------------------------------------------
    # Extract PDF text
    # --------------------------------------------------------

    try:

        reader = PdfReader(resume)

        resume_text = ""

        for page in reader.pages:

            text = page.extract_text()

            if text:
                resume_text += text + "\n"

    except Exception:

        st.error(
            "❌ Could not read this PDF. "
            "Please upload a valid text-based PDF."
        )

        st.stop()


    # --------------------------------------------------------
    # Check extracted text
    # --------------------------------------------------------

    if not resume_text.strip():

        st.warning(
            "⚠️ Could not extract text from this PDF. "
            "Please upload a text-based PDF."
        )

        st.stop()


    # --------------------------------------------------------
    # Resume preview
    # --------------------------------------------------------

    with st.expander("📖 View Extracted Resume Text"):

        st.text_area(
            "Resume content",
            resume_text,
            height=300
        )


    # ========================================================
    # RESUME ANALYSIS
    # ========================================================

    st.subheader("🤖 Resume Analysis")

    if st.button(
        "Analyze Resume",
        type="primary",
        use_container_width=True
    ):

        prompt = f"""
You are an expert resume analyzer and ATS specialist.

Analyze the following resume carefully.

Give the analysis using these sections:

## Overall Summary

Give a short summary of the candidate's profile.

## ATS Score

Give an estimated ATS score out of 100.

Explain briefly why the resume received this score.

Consider:
- Resume formatting
- Standard headings
- Relevant keywords
- Technical skills
- Action verbs
- Quantifiable achievements
- Job-related terminology
- Contact/profile links

## Key Skills

List the important technical and soft skills found in the resume.

## Strengths

List the strongest parts of the resume.

## Areas for Improvement

Explain what could be improved.

## Missing Skills

Mention important skills or keywords that appear to be missing.

## Suggested Improvements

Give practical suggestions to improve the resume.

## Suitable Job Roles

Suggest job roles that match the candidate's current skills
and experience.

Important:
- Only use information actually present in the resume.
- Do not invent experience, skills, education, or achievements.
- Keep the analysis clear and practical.

Resume:

{resume_text}
"""

        with st.spinner("🤖 Gemini is analyzing your resume..."):

            try:

                interaction = client.interactions.create(
                    model="gemini-3.6-flash",
                    input=prompt
                )

                analysis = interaction.output_text

            except Exception:

                st.error(
                    "Gemini is temporarily unavailable. "
                    "Please try again."
                )

                st.stop()


        # ----------------------------------------------------
        # Extract ATS score
        # ----------------------------------------------------

        score_match = re.search(
            r"ATS Score.*?(\d+)\s*/\s*100",
            analysis,
            re.IGNORECASE | re.DOTALL
        )


        if score_match:

            ats_score = int(score_match.group(1))

            # Keep score between 0 and 100
            ats_score = max(0, min(100, ats_score))

            st.subheader("📊 ATS Score")

            col1, col2 = st.columns([1, 2])

            with col1:

                st.metric(
                    "Resume ATS Score",
                    f"{ats_score}/100"
                )

            with col2:

                st.progress(
                    ats_score / 100
                )

                st.caption(
                    f"ATS compatibility score: {ats_score}%"
                )


        # ----------------------------------------------------
        # Full analysis
        # ----------------------------------------------------

        st.subheader("📋 Detailed Analysis")

        st.markdown(analysis)


    # ========================================================
    # JOB DESCRIPTION MATCHING
    # ========================================================

    st.divider()

    st.subheader("🎯 Job Description Matching")

    st.write(
        "Paste a job description below to see how well "
        "your resume matches the role."
    )


    job_description = st.text_area(
        "Job Description",
        height=250,
        placeholder=(
            "Paste the job description here...\n\n"
            "Example:\n"
            "We are looking for a Python developer with "
            "experience in FastAPI, SQL, REST APIs, Git, "
            "Docker and AWS."
        )
    )


    if st.button(
        "🎯 Analyze Job Match",
        use_container_width=True
    ):

        if not job_description.strip():

            st.warning(
                "⚠️ Please paste a job description first."
            )

        else:

            job_prompt = f"""
You are an expert recruiter and resume-job matching system.

Compare the resume with the job description.

Give the result using these sections:

## Job Match Score

Give a match score from 0 to 100.

## Matching Skills

List skills and requirements from the job description
that are clearly present in the resume.

## Missing Skills

List important skills or requirements from the job description
that are not clearly present in the resume.

## Matching Keywords

List important keywords that appear in both the resume
and job description.

## Recommendations

Give practical suggestions for improving the resume
for this specific job.

Important:
- Only use information actually present in the resume.
- Do not claim the candidate has a skill that is not shown.
- Keep the result clear and practical.

RESUME:

{resume_text}

JOB DESCRIPTION:

{job_description}
"""


            with st.spinner(
                "🎯 Gemini is comparing your resume with the job..."
            ):

                try:

                    job_interaction = client.interactions.create(
                        model="gemini-3.6-flash",
                        input=job_prompt
                    )

                    job_analysis = job_interaction.output_text

                except Exception:

                    st.error(
                        "Gemini is temporarily unavailable. "
                        "Please try again."
                    )

                    st.stop()


            # ------------------------------------------------
            # Extract job match score
            # ------------------------------------------------

            match_score = re.search(
                r"Job Match Score.*?(\d+)\s*/\s*100",
                job_analysis,
                re.IGNORECASE | re.DOTALL
            )


            if match_score:

                score = int(match_score.group(1))

                # Keep score between 0 and 100
                score = max(0, min(100, score))

                st.subheader("🎯 Job Match Score")

                col1, col2 = st.columns([1, 2])

                with col1:

                    st.metric(
                        "Resume ↔ Job Match",
                        f"{score}/100"
                    )

                with col2:

                    st.progress(
                        score / 100
                    )

                    st.caption(
                        f"Job compatibility score: {score}%"
                    )


            # ------------------------------------------------
            # Job analysis
            # ------------------------------------------------

            st.subheader("🔍 Job Matching Analysis")

            st.markdown(job_analysis)


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "AI Resume Analyzer • Powered by Gemini"
)