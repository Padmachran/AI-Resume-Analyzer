import os

import streamlit as st
from dotenv import load_dotenv
from pypdf import PdfReader
from google import genai


# Load .env
load_dotenv()

# Page settings
st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="📄",
    layout="centered"
)

st.title("📄 AI Resume Analyzer")
st.write("Upload your resume and get an AI-powered analysis using Gemini.")


# Get Gemini API key
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    st.error("Gemini API key not found. Please check your .env file.")
    st.stop()


# Create Gemini client
client = genai.Client(api_key=api_key)


# Upload resume
resume = st.file_uploader(
    "Upload your resume (PDF)",
    type=["pdf"]
)


if resume is not None:

    st.success(f"Resume uploaded: {resume.name}")

    # Extract text from PDF
    reader = PdfReader(resume)

    resume_text = ""

    for page in reader.pages:
        text = page.extract_text()

        if text:
            resume_text += text + "\n"

    if resume_text.strip():

        st.subheader("📖 Extracted Resume Text")

        st.text_area(
            "Resume content",
            resume_text,
            height=300
        )

        # Analyze button
        if st.button("🤖 Analyze Resume"):

            with st.spinner("Gemini is analyzing your resume..."):

                prompt = f"""
You are an expert resume analyzer.

Analyze the following resume.

Give the analysis using these sections:

## Overall Summary

## Key Skills

## Strengths

## Areas for Improvement

## Missing Skills

## Suggested Improvements

## Suitable Job Roles

Keep the analysis clear, practical, and easy to understand.

Resume:

{resume_text}
"""

                interaction = client.interactions.create(
                    model="gemini-3.6-flash",
                     input=prompt
                )

                analysis = interaction.output_text

            st.subheader("🤖 Gemini Resume Analysis")

            st.markdown(analysis)

    else:

        st.warning(
            "Could not extract text from this PDF. "
            "Please upload a text-based PDF."
        )