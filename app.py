import streamlit as st
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from backend.parser import parse_pdf
from backend.extractor import extract_resume
from backend.agents.ats_auditor import run_ats_audit
from backend.agents.gap_analyst import run_gap_analysis
from backend.agents.rewriter import run_rewriter
from backend.agents.resume_chat import chat_with_resume

# --- Page Config ---
st.set_page_config(
    page_title="NextStep AI",
    page_icon="🚀",
    layout="wide"
)

# --- Header ---
st.title("🚀 NextStep AI — Career Navigator")
st.caption("Upload your resume and get a brutally honest recruiter audit.")
st.divider()

# --- Initialize session state ---
if "analysis_done" not in st.session_state:
    st.session_state.analysis_done = False
if "messages" not in st.session_state:
    st.session_state.messages = []
if "resume_dict" not in st.session_state:
    st.session_state.resume_dict = None
if "job_description" not in st.session_state:
    st.session_state.job_description = None
if "ats_result" not in st.session_state:
    st.session_state.ats_result = None
if "gap_result" not in st.session_state:
    st.session_state.gap_result = None
if "rewritten" not in st.session_state:
    st.session_state.rewritten = None

# --- Show upload form only if analysis not done ---
if not st.session_state.analysis_done:
    col1, col2 = st.columns(2)

    with col1:
        uploaded_file = st.file_uploader(
            "Upload your resume (PDF)",
            type=["pdf"]
        )

    with col2:
        job_description = st.text_area(
            "Paste the job description here",
            height=200,
            placeholder="Copy and paste the full job posting here..."
        )
        job_role = st.text_input(
            "Job role you are applying for",
            placeholder="e.g. Software Engineer, Marketing Manager..."
        )

    analyze_btn = st.button("Analyze My Resume", type="primary", use_container_width=True)

    if analyze_btn:
        if not uploaded_file:
            st.error("Please upload your resume PDF first.")
        elif not job_description:
            st.error("Please paste the job description.")
        elif not job_role:
            st.error("Please enter the job role.")
        else:
            with st.spinner("Step 1 of 4 — Reading your resume..."):
                raw_text = parse_pdf(uploaded_file.read())

            with st.spinner("Step 2 of 4 — Extracting resume data..."):
                resume_data = extract_resume(raw_text, job_role)
                resume_dict = resume_data.model_dump()

            with st.spinner("Step 3 of 4 — Running ATS audit and gap analysis..."):
                ats_result = run_ats_audit(resume_dict, job_description)
                gap_result = run_gap_analysis(resume_dict, job_description)

            with st.spinner("Step 4 of 4 — Rewriting your resume..."):
                rewritten = run_rewriter(
                    resume_dict,
                    job_description,
                    ats_result.missing_keywords
                )

            # Save everything to session state
            st.session_state.resume_dict = resume_dict
            st.session_state.job_description = job_description
            st.session_state.ats_result = ats_result
            st.session_state.gap_result = gap_result
            st.session_state.rewritten = rewritten
            st.session_state.analysis_done = True
            st.rerun()

# --- Show results if analysis is done ---
if st.session_state.analysis_done:

    # Button to start over
    if st.button("Analyze a new resume"):
        st.session_state.analysis_done = False
        st.session_state.messages = []
        st.session_state.resume_dict = None
        st.session_state.job_description = None
        st.session_state.ats_result = None
        st.session_state.gap_result = None
        st.session_state.rewritten = None
        st.rerun()

    st.success("Analysis complete!")
    st.divider()

    # Load from session state
    ats_result = st.session_state.ats_result
    gap_result = st.session_state.gap_result
    rewritten = st.session_state.rewritten
    resume_dict = st.session_state.resume_dict
    job_description = st.session_state.job_description

    tab1, tab2, tab3, tab4 = st.tabs([
        "🎯 Recruiter Audit",
        "📊 Skill Gap Roadmap",
        "✍️ Improved Resume",
        "💬 Chat with Resume"
    ])

    # ---- TAB 1: ATS AUDIT ----
    with tab1:
        st.subheader("Cynical Recruiter Audit")

        # ATS Decision Banner
        if ats_result.ats_decision == "Auto Rejected":
            st.error(f"🚫 ATS DECISION: {ats_result.ats_decision}")
        elif ats_result.ats_decision == "Maybe":
            st.warning(f"⚠️ ATS DECISION: {ats_result.ats_decision}")
        elif ats_result.ats_decision == "Good Candidate":
            st.info(f"✅ ATS DECISION: {ats_result.ats_decision}")
        else:
            st.success(f"🌟 ATS DECISION: {ats_result.ats_decision}")

        st.divider()

        # Score breakdown
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("Total ATS Score", f"{ats_result.ats_score}/100")
        with col2:
            st.metric("Keywords", f"{ats_result.keyword_score}/40")
        with col3:
            st.metric("Job Title", f"{ats_result.title_score}/20")
        with col4:
            st.metric("Experience", f"{ats_result.experience_score}/20")
        with col5:
            st.metric("Education", f"{ats_result.education_score}/20")

        st.divider()
        st.error(f"Recruiter says: {ats_result.verdict}")
        st.subheader("Top 3 Rejection Reasons")
        for i, reason in enumerate(ats_result.rejection_reasons, 1):
            st.warning(f"{i}. {reason}")

        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Missing Keywords")
            for kw in ats_result.missing_keywords:
                st.markdown(f"🔴 {kw}")
        with col2:
            st.subheader("Matched Keywords")
            for kw in ats_result.matched_keywords:
                st.markdown(f"🟢 {kw}")

    # ---- TAB 2: SKILL GAP ----
    with tab2:
        st.subheader("Skill Gap Roadmap")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Overall Match", f"{gap_result.overall_match_percentage}%")
        with col2:
            st.metric("Estimated Ready Time", gap_result.estimated_ready_time)

        st.divider()

        st.subheader("Your Strong Areas")
        for area in gap_result.strong_areas:
            st.success(f"✅ {area}")

        st.subheader("Skill Gaps to Fill")
        for gap in gap_result.skill_gaps:
            with st.expander(f"{gap.skill_name} — Priority: {gap.priority}"):
                st.write(f"**Why it matters:** {gap.reason}")
                st.write("**How to learn it:**")
                for resource in gap.how_to_learn:
                    st.markdown(f"- {resource}")

        st.subheader("Quick Wins")
        for win in gap_result.quick_wins:
            st.info(f"⚡ {win}")

   # ---- TAB 3: IMPROVED RESUME ----
        with tab3:
            st.subheader("✍️ Your Improved Resume")
            st.caption("AI has improved your resume. You can edit anything before downloading.")

            st.divider()

            # --- Editable Name ---
            st.markdown("### Personal Details")
            col1, col2 = st.columns(2)
            with col1:
                edited_name = st.text_input(
                    "Full Name",
                    value=rewritten.candidate_name
                )
            with col2:
                edited_email = st.text_input(
                    "Email",
                    value=resume_dict.get("email") or ""
                )

            col3, col4 = st.columns(2)
            with col3:
                edited_phone = st.text_input(
                    "Phone",
                    value=resume_dict.get("phone") or ""
                )
            with col4:
                edited_linkedin = st.text_input(
                    "LinkedIn URL (optional)",
                    placeholder="linkedin.com/in/yourname"
                )

            st.divider()

            # --- Editable Summary ---
            st.markdown("### Professional Summary")
            st.caption("AI generated this — edit it to sound more like you.")
            edited_summary = st.text_area(
                "Summary",
                value=rewritten.improved_summary,
                height=120,
                label_visibility="collapsed"
            )

            st.divider()

            # --- Editable Skills ---
            st.markdown("### Skills")
            st.caption("Add or remove skills separated by commas.")
            skills_str = ", ".join(rewritten.improved_skills)
            edited_skills = st.text_area(
                "Skills",
                value=skills_str,
                height=80,
                label_visibility="collapsed"
            )

            st.divider()

            # --- Editable Experience ---
            st.markdown("### Work Experience")
            st.caption("Edit any bullet point. Each line is a separate bullet.")

            edited_experience = []
            for i, exp in enumerate(rewritten.improved_experience):
                with st.expander(f"{exp.job_title} at {exp.company}", expanded=True):
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        e_title = st.text_input(
                            "Job Title",
                            value=exp.job_title,
                            key=f"title_{i}"
                        )
                    with col2:
                        e_company = st.text_input(
                            "Company",
                            value=exp.company,
                            key=f"company_{i}"
                        )
                    with col3:
                        e_duration = st.text_input(
                            "Duration",
                            value=exp.duration,
                            key=f"duration_{i}"
                        )

                    bullets_text = "\n".join(exp.improved_bullets)
                    e_bullets = st.text_area(
                        "Bullet points (one per line)",
                        value=bullets_text,
                        height=150,
                        key=f"bullets_{i}"
                    )

                    edited_experience.append({
                        "job_title": e_title,
                        "company": e_company,
                        "duration": e_duration,
                        "improved_bullets": [
                            b.strip() for b in e_bullets.split("\n")
                            if b.strip()
                        ]
                    })

            # --- Add new experience ---
            st.markdown("**➕ Add a new job (optional)**")
            with st.expander("Add new work experience"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_title = st.text_input("Job Title", key="new_title")
                with col2:
                    new_company = st.text_input("Company", key="new_company")
                with col3:
                    new_duration = st.text_input("Duration", key="new_duration")
                new_bullets = st.text_area(
                    "Bullet points (one per line)",
                    key="new_bullets",
                    height=120
                )
                if new_title and new_company:
                    edited_experience.append({
                        "job_title": new_title,
                        "company": new_company,
                        "duration": new_duration,
                        "improved_bullets": [
                            b.strip() for b in new_bullets.split("\n")
                            if b.strip()
                        ]
                    })

            st.divider()

            # --- Education (editable) ---
            st.markdown("### Education")
            edited_education = []
            for i, edu in enumerate(resume_dict.get("education", [])):
                col1, col2, col3 = st.columns(3)
                with col1:
                    e_degree = st.text_input(
                        "Degree",
                        value=edu.get("degree", ""),
                        key=f"degree_{i}"
                    )
                with col2:
                    e_institution = st.text_input(
                        "Institution",
                        value=edu.get("institution", ""),
                        key=f"institution_{i}"
                    )
                with col3:
                    e_year = st.text_input(
                        "Year",
                        value=edu.get("year", ""),
                        key=f"year_{i}"
                    )
                edited_education.append({
                    "degree": e_degree,
                    "institution": e_institution,
                    "year": e_year
                })

            # --- Add new education ---
            with st.expander("➕ Add new education (optional)"):
                col1, col2, col3 = st.columns(3)
                with col1:
                    new_degree = st.text_input("Degree", key="new_degree")
                with col2:
                    new_institution = st.text_input("Institution", key="new_institution")
                with col3:
                    new_year = st.text_input("Year", key="new_year")
                if new_degree and new_institution:
                    edited_education.append({
                        "degree": new_degree,
                        "institution": new_institution,
                        "year": new_year
                    })

            st.divider()

            # --- Extra sections user can add ---
            st.markdown("### Additional Information (optional)")
            col1, col2 = st.columns(2)
            with col1:
                extra_certifications = st.text_area(
                    "Certifications (one per line)",
                    placeholder="AWS Certified Developer — Amazon, 2024",
                    height=100
                )
            with col2:
                extra_achievements = st.text_area(
                    "Achievements (one per line)",
                    placeholder="Published research paper on ML, 2023",
                    height=100
                )

            st.divider()

            # --- Download button ---
            st.markdown("### Download Your Resume")
            st.caption("All your edits are saved. Click below to download.")

            # Page selection
            page_limit = st.radio(
                "Resume length:",
                options=["1 Page", "2 Pages", "Full (no limit)"],
                horizontal=True
            )

            # Build final data for download
            final_skills = [s.strip() for s in edited_skills.split(",") if s.strip()]

            # Parse extra certifications
            existing_certs = resume_dict.get("certifications", [])
            if extra_certifications:
                for cert_line in extra_certifications.split("\n"):
                    if cert_line.strip():
                        existing_certs.append({
                            "name": cert_line.strip(),
                            "issuer": "",
                            "year": ""
                        })

            # Parse extra achievements
            existing_achievements = resume_dict.get("achievements", [])
            if extra_achievements:
                for ach_line in extra_achievements.split("\n"):
                    if ach_line.strip():
                        existing_achievements.append(ach_line.strip())

            # Build final resume dict
            final_resume_dict = {
                **resume_dict,
                "name": edited_name,
                "email": edited_email,
                "phone": edited_phone,
                "linkedin": edited_linkedin,
                "education": edited_education,
                "certifications": existing_certs,
                "achievements": existing_achievements,
            }

            # Build final rewritten object substitute
            class FinalResume:
                candidate_name = edited_name
                improved_summary = edited_summary
                improved_skills = final_skills
                improved_experience = [
                    type('exp', (), {
                        'job_title': e['job_title'],
                        'company': e['company'],
                        'duration': e['duration'],
                        'improved_bullets': e['improved_bullets']
                    })()
                    for e in edited_experience
                ]
                improvement_notes = rewritten.improvement_notes

            # --- Validation before download ---
            errors = []

            if not edited_name.strip():
                errors.append("Name cannot be empty")

            if edited_email:
                import re
                email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
                if not re.match(email_pattern, edited_email):
                    errors.append("Email address is not valid — example: john@gmail.com")

            if edited_phone:
                phone_clean = edited_phone.replace("+", "").replace("-", "").replace(" ", "").replace("(", "").replace(")", "")
                if not phone_clean.isdigit():
                    errors.append("Phone number should contain only digits, spaces, dashes or + sign")
                elif len(phone_clean) < 9 or len(phone_clean) > 10:
                    errors.append("Phone number length is not valid — should be 10 digits")

            if edited_linkedin:
                if "linkedin.com" not in edited_linkedin.lower():
                    errors.append("LinkedIn URL should contain 'linkedin.com'")

            if len(final_skills) == 0:
                errors.append("Skills cannot be empty — please add at least one skill")

            # Show errors or proceed to download
            if errors:
                st.error("Please fix these errors before downloading:")
                for error in errors:
                    st.warning(f"⚠️ {error}")
            else:
                from backend.resume_generator import generate_resume_docx
                docx_bytes = generate_resume_docx(FinalResume(), final_resume_dict)
                st.download_button(
                    label="📥 Download Final Resume (.docx)",
                    data=docx_bytes,
                    file_name=f"{edited_name}_resume.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True,
                    type="primary",
                    key="download_resume_final"
                )
                from backend.resume_generator import generate_resume_docx
                docx_bytes = generate_resume_docx(FinalResume(), final_resume_dict, page_limit)
                st.download_button(
                    label="⬇️ Click here to save your resume",
                    data=docx_bytes,
                    file_name=f"{edited_name}_resume.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )

    # ---- TAB 4: CHAT WITH RESUME ----
    with tab4:
        st.subheader("💬 Chat with Your Resume")
        st.caption("Ask me anything about your resume, skills, or career advice.")

        # Clickable suggestion buttons
        st.markdown("**Try asking:**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("💪 What are my strongest skills?"):
                st.session_state.suggested_question = "What are my strongest skills for this job?"
            if st.button("📅 How much experience do I have?"):
                st.session_state.suggested_question = "How many years of experience do I have?"
        with col2:
            if st.button("🎯 What should I highlight in interview?"):
                st.session_state.suggested_question = "What should I highlight in my interview?"
            if st.button("⚠️ What is my biggest weakness?"):
                st.session_state.suggested_question = "What is my biggest weakness for this role?"

        st.divider()

        # Display chat history
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

        # Check for suggestion button click
        auto_question = st.session_state.pop("suggested_question", None)

        # Chat input
        user_question = st.chat_input("Ask about your resume...") or auto_question

        if user_question:
            with st.chat_message("user"):
                st.markdown(user_question)

            st.session_state.messages.append({
                "role": "user",
                "content": user_question
            })

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = chat_with_resume(
                        st.session_state.resume_dict,
                        st.session_state.job_description,
                        user_question,
                        st.session_state.messages
                    )
                st.markdown(response)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })