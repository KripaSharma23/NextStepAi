from langchain_groq import ChatGroq
from typing import List
import os
from dotenv import load_dotenv

load_dotenv()

llm = ChatGroq(
    api_key=os.getenv("GROQ_API_KEY"),
    model="llama-3.3-70b-versatile",
    temperature=0.5
)

def chat_with_resume(resume_data: dict, job_description: str, user_question: str, chat_history: List[dict]) -> str:
    """
    Takes resume data, job description, user question and chat history.
    Returns AI response as plain text.
    """
    # Build resume context
    resume_context = f"""
    Candidate Name: {resume_data.get('name')}
    Email: {resume_data.get('email')}
    Years of Experience: {resume_data.get('total_years_experience')}
    Skills: {', '.join(resume_data.get('skills', []))}
    
    Experience:
    """
    for exp in resume_data.get("experience", []):
        resume_context += f"\n{exp['job_title']} at {exp['company']} ({exp['duration']})\n"
        for bullet in exp.get("description", []):
            resume_context += f"  {bullet}\n"

    resume_context += f"\nJob Description:\n{job_description}"

    # Build chat history text
    history_text = ""
    for msg in chat_history[-6:]:
        role = "User" if msg["role"] == "user" else "Assistant"
        history_text += f"{role}: {msg['content']}\n"

    # Full prompt
    prompt = f"""
    You are a helpful career advisor who has full access to the candidate's resume.
    Answer questions about their resume, skills, experience and career advice.
    Be specific, honest and encouraging.
    Always refer to specific details from their resume in your answers.
    
    RESUME DATA:
    {resume_context}
    
    CONVERSATION HISTORY:
    {history_text}
    
    USER QUESTION:
    {user_question}
    
    Give a helpful specific answer based on the resume data above.
    """

    response = llm.invoke(prompt)
    return response.content