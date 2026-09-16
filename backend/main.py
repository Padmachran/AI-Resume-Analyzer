import os
import re
import io

from fastapi import FastAPI, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pypdf import PdfReader
from google import genai


# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    raise RuntimeError("GEMINI_API_KEY not found")


# Gemini client
client = genai.Client(api_key=api_key)


# Create FastAPI application
app = FastAPI(
    title="AI Resume Analyzer API",
    description="Backend API for AI Resume Analyzer",
    version="1.0.0"
)


# Allow frontend requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Home / health check
@app.get("/")
def home():
    return {
        "message": "AI Resume Analyzer API is running",
        "status": "ok"
    }


# Resume analysis endpoint
@app.post("/analyze-resume")
async def analyze_resume(
    resume: UploadFile = File(...)
):

    if not resume.filename.lower().endswith(".pdf"):
        return {
            "success": False,
            "error": "Please upload a PDF resume."
        }

    file_bytes = await resume.read()

    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)

        resume_text = ""

        for page in reader.pages:
            text = page.extract_text()

            if text:
                resume_text += text + "\n"

    except Exception:
        return {
            "success": False,
            "error": "Could not read the PDF."
        }

    if not resume_text.strip():
        return {
            "success": False,
            "error": "Could not extract text from this PDF."
        }

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

    try:
        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            input=prompt
        )

        analysis = interaction.output_text

    except Exception as e:
        return {
            "success": False,
            "error": "Gemini analysis failed.",
            "details": str(e)
        }

    score_match = re.search(
        r"ATS Score.*?(\d+)\s*/\s*100",
        analysis,
        re.IGNORECASE | re.DOTALL
    )

    ats_score = None

    if score_match:
        ats_score = int(score_match.group(1))
        ats_score = max(0, min(100, ats_score))

    return {
        "success": True,
        "filename": resume.filename,
        "ats_score": ats_score,
        "analysis": analysis
    }


# Job matching endpoint
@app.post("/job-match")
async def job_match(
    resume: UploadFile = File(...),
    job_description: str = Form(...)
):

    file_bytes = await resume.read()

    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)

        resume_text = ""

        for page in reader.pages:
            text = page.extract_text()

            if text:
                resume_text += text + "\n"

    except Exception:
        return {
            "success": False,
            "error": "Could not read the PDF."
        }

    if not resume_text.strip():
        return {
            "success": False,
            "error": "Could not extract text from the resume."
        }

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

    try:
        interaction = client.interactions.create(
            model="gemini-3.6-flash",
            input=job_prompt
        )

        analysis = interaction.output_text

    except Exception as e:
        return {
            "success": False,
            "error": "Gemini analysis failed.",
            "details": str(e)
        }

    match_score = re.search(
        r"Job Match Score.*?(\d+)\s*/\s*100",
        analysis,
        re.IGNORECASE | re.DOTALL
    )

    score = None

    if match_score:
        score = int(match_score.group(1))
        score = max(0, min(100, score))

    return {
        "success": True,
        "filename": resume.filename,
        "job_match_score": score,
        "analysis": analysis
    }