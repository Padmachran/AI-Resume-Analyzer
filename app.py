import os
import re

import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from google import genai


# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="centered"
)


# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("Gemini API key not found. Please check your .env file.")
    st.stop()


# -----------------------------
# Gemini client
# -----------------------------
client = genai.Client(api_key=api_key)


# -----------------------------
# App title
# -----------------------------
st.title("📄 AI Resume Analyzer")
st.write(
    "Upload your resume and get an AI-powered analysis "
    "using Gemini."
)


# -----------------------------
# Resume upload
# -----------------------------
resume = st.file_uploader(
    "Upload your resume (PDF)",
    type=["pdf"]
)


if resume is not None:

    st.success(f"Resume uploaded: {resume.name}")

    # -----------------------------
    # Extract text from PDF
    # -----------------------------
    try:
        reader = PdfReader(resume)

        resume_text = ""

        for page in reader.pages:
            text = page.extract_text()

            if text:
                resume_text += text + "\n"

    except Exception as e:
        st.error("Could not read this PDF.")
        st.stop()


    # -----------------------------
    # Check extracted text
    # -----------------------------
    if resume_text.strip():

        # Show extracted resume text
        with st.expander("📖 View Extracted Resume Text"):
            st.text_area(
                "Resume content",
                resume_text,
                height=300
            )


        # -----------------------------
        # Analyze button
        # -----------------------------
        if st.button("🤖 Analyze Resume", type="primary"):

            prompt = f"""
You are an expert resume analyzer and ATS (Applicant Tracking System) specialist.

Analyze the following resume carefully.

Give the analysis using exactly these sections:

## Overall Summary

Give a short summary of the candidate's profile.

## ATS Score

Give an estimated ATS score out of 100.

Also explain briefly why the resume received this score.

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

Suggest job roles that match the candidate's current skills and experience.

Keep the analysis clear, practical, and easy to understand.

Do not invent information that is not present in the resume.

Resume:

{resume_text}
"""

            # -----------------------------
            # Call Gemini
            # -----------------------------
            with st.spinner("Gemini is analyzing your resume..."):

                try:

                    interaction = client.interactions.create(
                        model="gemini-3.6-flash",
                        input=prompt
                    )

                    analysis = interaction.output_text

                except Exception as e:

                    st.error(
                        "Gemini is temporarily unavailable. "
                        "Please try again."
                    )

                    st.stop()


            # -----------------------------
            # Extract ATS score
            # -----------------------------
            score_match = re.search(
                r"ATS Score.*?(\d+)\s*/\s*100",
                analysis,
                re.IGNORECASE | re.DOTALL
            )

            if score_match:

                ats_score = int(score_match.group(1))

                st.subheader("📊 ATS Score")

                st.metric(
                    label="Resume ATS Score",
                    value=f"{ats_score}/100"
                )

            else:

                st.subheader("📊 ATS Score")
                st.info(
                    "Gemini did not return the ATS score "
                    "in the expected format."
                )


            # -----------------------------
            # Full AI analysis
            # -----------------------------
            st.subheader("🤖 Gemini Resume Analysis")

            st.markdown(analysis)


    else:

        st.warning(
            "Could not extract text from this PDF. "
            "Please upload a text-based PDF."
        )