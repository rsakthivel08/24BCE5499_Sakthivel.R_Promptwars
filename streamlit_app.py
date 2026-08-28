import io
import os
import tempfile
import time
from pathlib import Path

import streamlit as st
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import project components
from app.config import get_settings
from app.extraction.document_parser import extract_text
from app.extraction.text_cleaner import clean_text
from app.graph.evaluation_graph import run_evaluation_pipeline
from app.voice.voice_debate_runner import generate_voice_debate

st.set_page_config(
    page_title="Multi-Agent AI Interview Panel",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS for modern clean styling
st.markdown(
    """
    <style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1E293B;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        font-size: 1.05rem;
        color: #64748B;
        margin-bottom: 1.5rem;
    }
    .badge-hire {
        background-color: #DCFCE7;
        color: #166534;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
    }
    .badge-reject {
        background-color: #FEE2E2;
        color: #991B1B;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
    }
    .badge-hold {
        background-color: #FEF3C7;
        color: #92400E;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
    }
    .badge-interview {
        background-color: #E0F2FE;
        color: #075985;
        padding: 4px 12px;
        border-radius: 12px;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# --- Sidebar Configuration ---
with st.sidebar:
    st.image("https://img.icons8.com/isometric/100/conference-call.png", width=70)
    st.title("Settings & Keys")
    
    # Check secrets or env
    env_groq_key = os.getenv("GROQ_API_KEY", "")
    env_sarvam_key = os.getenv("SARVAM_API_KEY", "")
    
    try:
        if "GROQ_API_KEY" in st.secrets:
            env_groq_key = st.secrets["GROQ_API_KEY"]
        if "SARVAM_API_KEY" in st.secrets:
            env_sarvam_key = st.secrets["SARVAM_API_KEY"]
    except Exception:
        pass

    groq_api_key = st.text_input(
        "Groq API Key",
        value=env_groq_key,
        type="password",
        help="Get your free API key at https://console.groq.com",
    )
    
    sarvam_api_key = st.text_input(
        "Sarvam AI Key (Optional)",
        value=env_sarvam_key,
        type="password",
        help="Required for Voice Debate feature (https://sarvam.ai)",
    )

    if groq_api_key:
        os.environ["GROQ_API_KEY"] = groq_api_key
    if sarvam_api_key:
        os.environ["SARVAM_API_KEY"] = sarvam_api_key

    st.markdown("---")
    st.subheader("🤖 Active AI Personas")
    st.markdown(
        """
        - **🛠️ Technical Agent**: Architecture, coding depth & technical fit against JD.
        - **🤝 HR / Culture Agent**: Communication, teamwork & soft skills.
        - **💼 Hiring Manager**: Business impact & role qualification match.
        - **🔍 Skeptic Agent**: Contradictions & unverified resume claims.
        - **⚖️ Judge Agent**: Evidence synthesis (No score averaging).
        """
    )
    st.markdown("---")
    st.caption("Powered by **Groq (qwen/qwen3.8-27b)** & **Sarvam AI (Bulbul V3)**")


# --- Helper: Extract text from UploadedFile ---
def process_uploaded_file(uploaded_file) -> str:
    if uploaded_file is None:
        return ""
    suffix = Path(uploaded_file.name).suffix.lower()
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(uploaded_file.getvalue())
        tmp_path = Path(tmp.name)
    try:
        raw_text = extract_text(tmp_path)
        return clean_text(raw_text)
    finally:
        if tmp_path.exists():
            tmp_path.unlink()


# --- Main App Header ---
st.markdown('<div class="main-header">🤖 Multi-Agent AI Interview Panel Simulator</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="sub-header">Autonomous 4-agent evaluation, evidence-grounded multi-round debate, and synthesis against company job requirements.</div>',
    unsafe_allow_html=True,
)

# --- Mode Selection ---
app_mode = st.radio(
    "Select Workflow Mode:",
    ["Single Candidate Evaluation", "Compare Two Candidates (Bonus)"],
    horizontal=True,
)

# Initialize Session State
if "eval_results" not in st.session_state:
    st.session_state.eval_results = {}
if "voice_debate" not in st.session_state:
    st.session_state.voice_debate = {}


# =========================================================================
# WORKFLOW 1: SINGLE CANDIDATE EVALUATION
# =========================================================================
if app_mode == "Single Candidate Evaluation":
    st.subheader("1. Company Job Description / Role Requirements")
    
    jd_tab1, jd_tab2 = st.tabs(["📁 Upload Job Description PDF / DOCX", "✍️ Enter / Customize Job Description Text"])
    
    with jd_tab1:
        jd_file = st.file_uploader(
            "Upload Company Job Description Document (PDF / DOCX / TXT)",
            type=["pdf", "docx", "doc", "txt"],
            key="single_jd_file",
            help="Upload the actual PDF job description from the company for full requirements matching.",
        )
    
    with jd_tab2:
        manual_jd_text = st.text_area(
            "Or Type / Paste Job Description & Requirements:",
            value="Job Title: Senior Software Engineer\n\nKey Responsibilities:\n- Design and implement scalable microservices using Python and FastAPI.\n- Build high-throughput data processing and AI/LLM pipelines.\n- Lead architectural reviews and mentor junior engineers.\n\nRequired Qualifications:\n- 3+ years of production experience in Python, AsyncIO, and relational databases (PostgreSQL).\n- Hands-on experience with Docker, Redis, and cloud services (AWS/GCP).\n- Strong understanding of distributed systems, error resilience, and system design.",
            height=130,
            key="single_jd_text",
        )

    st.subheader("2. Upload Candidate Documents")
    col1, col2 = st.columns(2)
    
    with col1:
        resume_file = st.file_uploader(
            "📄 Candidate Resume (PDF / DOCX / TXT)",
            type=["pdf", "docx", "doc", "txt"],
            key="single_resume",
        )
    with col2:
        transcript_file = st.file_uploader(
            "🎙️ Interview Transcript (PDF / DOCX / TXT)",
            type=["pdf", "docx", "doc", "txt"],
            key="single_transcript",
        )

    evaluate_btn = st.button("🚀 Run Multi-Agent Evaluation", type="primary", use_container_width=True)

    if evaluate_btn:
        if not groq_api_key:
            st.error("⚠️ Please enter a valid Groq API Key in the sidebar.")
        elif not resume_file:
            st.error("⚠️ Please upload at least a Candidate Resume.")
        else:
            with st.spinner("Extracting text from documents..."):
                resume_text = process_uploaded_file(resume_file)
                transcript_text = process_uploaded_file(transcript_file) if transcript_file else ""
                
                # Extract JD file if uploaded, else fallback to manual text
                if jd_file is not None:
                    jd_extracted = process_uploaded_file(jd_file)
                    final_target_role = f"Job Description:\n{jd_extracted}"
                else:
                    final_target_role = manual_jd_text.strip() if manual_jd_text.strip() else "Software Engineer"

            if not resume_text.strip():
                st.error("Could not extract text from the uploaded resume.")
            else:
                progress_bar = st.progress(10, text="1/4: Building Candidate Profile aligned with Job Description...")
                eval_id = f"eval_{int(time.time())}"
                
                try:
                    time.sleep(0.5)
                    progress_bar.progress(30, text="2/4: Running 4 Independent Agent Evaluations against Job Description...")
                    
                    results = run_evaluation_pipeline(
                        evaluation_id=eval_id,
                        resume_text=resume_text,
                        transcript_text=transcript_text,
                        target_role=final_target_role,
                    )
                    
                    progress_bar.progress(70, text="3/4: Conducting Multi-Round Agent Debate...")
                    time.sleep(0.5)
                    
                    progress_bar.progress(90, text="4/4: Synthesizing Final Decision Report...")
                    time.sleep(0.5)
                    
                    if results.get("error"):
                        progress_bar.empty()
                        st.error(f"Evaluation Pipeline Error: {results['error']}")
                    else:
                        progress_bar.progress(100, text="✅ Evaluation Complete!")
                        time.sleep(0.5)
                        progress_bar.empty()
                        st.session_state.eval_results[eval_id] = results
                        st.session_state.current_eval_id = eval_id
                        st.success("🎉 Multi-Agent Evaluation and Debate Completed Successfully!")
                        
                except Exception as exc:
                    progress_bar.empty()
                    st.error(f"Unexpected error: {str(exc)}")

    # Display Results if available
    current_id = st.session_state.get("current_eval_id")
    if current_id and current_id in st.session_state.eval_results:
        res = st.session_state.eval_results[current_id]
        profile = res.get("candidate_profile", {})
        opinions = res.get("opinions", [])
        debate = res.get("debate_transcript", {})
        report = res.get("final_report", {})

        st.markdown("---")
        st.subheader(f"📊 Evaluation Dashboard: {profile.get('candidate_name', 'Candidate')}")

        # Top Metric Banner
        rec = report.get("final_recommendation", "N/A")
        badge_style = "badge-hire" if "Hire" in rec else "badge-reject" if "Reject" in rec else "badge-hold" if "Hold" in rec else "badge-interview"
        
        mcol1, mcol2, mcol3 = st.columns([1.5, 1.5, 1.5])
        with mcol1:
            st.metric("Candidate Name", profile.get("candidate_name", "Unknown"))
        with mcol2:
            st.markdown(f"**Final Recommendation**<br><span class='{badge_style}'>{rec}</span>", unsafe_allow_html=True)
        with mcol3:
            st.metric("Confidence Score", f"{report.get('confidence_score', 0.0) * 100:.0f}% ({report.get('confidence_level', 'Medium')})")

        with st.expander("🏢 View Job Description / Requirements Evaluated Against", expanded=False):
            st.text(res.get("target_role", "Software Engineer"))

        # Result Tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📋 Candidate Profile",
            "👥 4 Agent Opinions",
            "⚔️ Multi-Agent Debate",
            "⚖️ Final Judge Report",
            "🎙️ Voice Debate (Audio)",
        ])

        # --- TAB 1: Profile ---
        with tab1:
            st.markdown("### Extracted Candidate Profile")
            st.caption("Shared source of truth extracted from resume and interview transcripts.")
            
            pcol1, pcol2 = st.columns(2)
            with pcol1:
                st.markdown(f"**📧 Email:** {profile.get('email', 'N/A')}")
                st.markdown(f"**📱 Phone:** {profile.get('phone', 'N/A')}")
                st.markdown(f"**🔗 LinkedIn:** {profile.get('linkedin', 'N/A')}")
                st.markdown(f"**🐙 GitHub:** {profile.get('github', 'N/A')}")
                
                edu = profile.get("education", {})
                st.markdown(f"**🎓 Education:** {edu.get('degree', '')} - {edu.get('institution', '')} (CGPA: {edu.get('cgpa', 'N/A')})")
                
            with pcol2:
                st.markdown("**🛠️ Technical Skills:**")
                skills = profile.get("skills", [])
                if skills:
                    st.write(", ".join([f"{s}" for s in skills]))
                
                langs = profile.get("programming_languages", [])
                if langs:
                    st.markdown(f"**💻 Languages:** {', '.join([f'{l}' for l in langs])}")

            st.markdown("#### 💼 Work Experience")
            for exp in profile.get("experience", []):
                st.markdown(f"- **{exp.get('role')}** at *{exp.get('company')}* ({exp.get('duration')})")
                for ach in exp.get("achievements", []):
                    st.markdown(f"  - {ach}")

            st.markdown("#### 🔍 Candidate Claims & Evidence Grounding")
            claims = profile.get("candidate_claims", [])
            if claims:
                for c in claims:
                    strength = c.get("evidence_strength", "moderate")
                    st.markdown(
                        f"- **Claim:** {c.get('claim')}<br>"
                        f"  *Evidence:* \"{c.get('evidence')}\" &nbsp; Strength: {strength}",
                        unsafe_allow_html=True,
                    )

        # --- TAB 2: Agent Opinions ---
        with tab2:
            st.markdown("### Independent Persona Evaluations")
            st.caption("Each agent evaluated the candidate specifically against the Job Description in complete isolation.")
            
            icons = {
                "Technical Agent": "🛠️",
                "HR Agent": "🤝",
                "Hiring Manager Agent": "💼",
                "Skeptic Agent": "🔍",
            }
            
            op_cols = st.columns(2)
            for idx, op in enumerate(opinions):
                col = op_cols[idx % 2]
                agent_name = op.get("agent", f"Agent {idx+1}")
                icon = icons.get(agent_name, "🤖")
                score = op.get("score", 0)
                conf = op.get("confidence", 0.0)
                assessment = op.get("overall_assessment", "N/A")
                
                with col:
                    with st.expander(f"{icon} **{agent_name}** — Score: {score}/10 | {assessment}", expanded=True):
                        st.markdown(f"**Assessment:** {assessment} | **Confidence:** {conf:.2f}")
                        st.markdown(f"**Summary:** {op.get('summary', '')}")
                        
                        st.markdown("**🟢 Strengths (with Evidence):**")
                        for s in op.get("strengths", []):
                            st.markdown(f"- **{s.get('point')}**<br>&nbsp;&nbsp;*Quote:* \"{s.get('evidence')}\"", unsafe_allow_html=True)
                            
                        st.markdown("**🔴 Concerns (with Evidence):**")
                        for c in op.get("concerns", []):
                            sev = c.get("severity", "medium")
                            st.markdown(f"- **{c.get('point')}** ({sev})<br>&nbsp;&nbsp;*Quote:* \"{c.get('evidence')}\"", unsafe_allow_html=True)
                            
                        st.markdown(f"**Recommendation:** {op.get('recommendation', '')}")

        # --- TAB 3: Debate ---
        with tab3:
            st.markdown("### 2-Round Multi-Agent Structured Debate")
            st.caption("Agents interact directly, challenging arguments, defending evidence, and updating opinions.")
            
            rounds = debate.get("rounds", [])
            for r in rounds:
                st.markdown(f"#### 🥊 Round {r.get('round_number')}")
                for turn in r.get("turns", []):
                    spk = turn.get("speaker", "Agent")
                    addr = turn.get("addressing", "All")
                    stance = turn.get("stance", "challenge")
                    msg = turn.get("message", "")
                    ev = turn.get("evidence_cited", "")
                    op_chg = turn.get("opinion_change", "none")
                    
                    stance_color = "orange" if "challenge" in stance else "green" if "agree" in stance else "blue"
                    
                    with st.chat_message(name=spk, avatar="🤖"):
                        st.markdown(f"**{spk}** ➔ *Responding to {addr}* &nbsp; :{stance_color}[{stance.upper()}]")
                        st.write(msg)
                        if ev:
                            st.caption(f"📑 **Evidence Cited:** \"{ev}\"")
                        if op_chg and op_chg != "none":
                            st.info(f"🔄 **Opinion Updated:** {op_chg}")

            st.markdown("---")
            st.markdown("#### 📝 Debate Summary & Consensus")
            dcol1, dcol2, dcol3 = st.columns(3)
            with dcol1:
                st.markdown("**🤝 Key Agreements:**")
                for a in debate.get("key_agreements", []):
                    st.markdown(f"- {a}")
            with dcol2:
                st.markdown("**⚡ Key Disagreements:**")
                for d in debate.get("key_disagreements", []):
                    st.markdown(f"- {d}")
            with dcol3:
                st.markdown("**❓ Unresolved Issues:**")
                for u in debate.get("unresolved_issues", []):
                    st.markdown(f"- {u}")

        # --- TAB 4: Final Judge Report ---
        with tab4:
            st.markdown("### ⚖️ Final Committee Decision Report")
            st.caption("Synthesized by Senior Judge Agent based on evidence weight and debate outcomes (No score averaging).")
            
            st.info(f"**Decision Reasoning:**\n\n{report.get('reasoning', '')}")
            
            jcol1, jcol2 = st.columns(2)
            with jcol1:
                st.markdown("#### 🌟 Key Strengths Weighted")
                for ks in report.get("key_strengths", []):
                    st.markdown(f"- **{ks.get('point')}**<br>&nbsp;&nbsp;*Evidence:* \"{ks.get('evidence')}\"", unsafe_allow_html=True)
            
            with jcol2:
                st.markdown("#### ⚠️ Key Concerns Weighted")
                for kc in report.get("key_concerns", []):
                    sev = kc.get("severity", "medium")
                    st.markdown(f"- **{kc.get('point')}** ({sev})<br>&nbsp;&nbsp;*Evidence:* \"{kc.get('evidence')}\"", unsafe_allow_html=True)

            unresolved = report.get("unresolved_disagreements", [])
            if unresolved:
                st.markdown("#### ⚖️ Unresolved Disagreements Handled by Committee")
                for ud in unresolved:
                    st.markdown(f"- **Topic:** {ud.get('topic')} (Status: {ud.get('status')})")
                    for ag, pos in ud.get("agent_positions", {}).items():
                        st.markdown(f"  - *{ag}:* {pos}")

            qs = report.get("suggested_interview_questions", [])
            if qs:
                st.markdown("#### 🎯 Suggested Deep-Dive Interview Questions")
                for q in qs:
                    st.markdown(f"1. {q}")

        # --- TAB 5: Voice Debate ---
        with tab5:
            st.markdown("### 🎙️ Multi-Persona Voice Debate Playback")
            st.caption("Listen to each agent persona debate using Sarvam AI Bulbul V3 multi-voice text-to-speech.")
            
            gen_voice_btn = st.button("🔊 Generate / Play Voice Audio", key="gen_voice_btn")
            
            if gen_voice_btn:
                if not sarvam_api_key:
                    st.warning("⚠️ Please provide a Sarvam API Key in the sidebar to generate voice audio.")
                else:
                    with st.spinner("Generating distinct persona voice audio clips..."):
                        voice_turns = generate_voice_debate(debate, current_id)
                        st.session_state.voice_debate[current_id] = voice_turns
            
            if current_id in st.session_state.voice_debate:
                voice_turns = st.session_state.voice_debate[current_id]
                for idx, vt in enumerate(voice_turns):
                    spk = vt.get("speaker", "Agent")
                    msg = vt.get("spoken_text", vt.get("message", ""))
                    audio_url = vt.get("audio_url")
                    
                    st.markdown(f"**Turn {idx+1}: {spk}**")
                    st.write(f"💬 \"{msg}\"")
                    
                    if audio_url:
                        audio_filename = audio_url.split("/")[-1]
                        audio_path = Path("data/audio") / audio_filename
                        if audio_path.exists():
                            st.audio(audio_path.read_bytes(), format="audio/wav")
                        else:
                            st.caption("Audio clip saved to cache.")
                    st.markdown("---")


# =========================================================================
# WORKFLOW 2: DUAL CANDIDATE COMPARISON (BONUS)
# =========================================================================
else:
    st.subheader("⚖️ Compare Two Candidates Against Job Description")
    st.caption("Evaluate and rank Candidate A vs Candidate B side-by-side against the same company job description.")
    
    st.markdown("#### 1. Company Job Description (Shared for Both Candidates)")
    comp_jd_tab1, comp_jd_tab2 = st.tabs(["📁 Upload Job Description PDF / DOCX", "✍️ Enter / Customize Job Description Text"])
    
    with comp_jd_tab1:
        comp_jd_file = st.file_uploader(
            "Upload Job Description Document (PDF / DOCX / TXT)",
            type=["pdf", "docx", "doc", "txt"],
            key="comp_jd_file",
        )
    with comp_jd_tab2:
        comp_jd_manual = st.text_area(
            "Or Enter Job Description Text:",
            value="Role: Senior Software Engineer\nRequirements: 3+ years Python/FastAPI, microservices, cloud deployments, strong system design and leadership.",
            height=100,
            key="comp_jd_manual",
        )

    st.markdown("#### 2. Candidate Documents")
    colA, colB = st.columns(2)
    
    with colA:
        st.markdown("### 👤 Candidate A")
        res_A = st.file_uploader("Candidate A Resume (PDF/DOCX)", type=["pdf", "docx", "txt"], key="comp_res_a")
        trn_A = st.file_uploader("Candidate A Transcript (PDF/DOCX)", type=["pdf", "docx", "txt"], key="comp_trn_a")
        
    with colB:
        st.markdown("### 👤 Candidate B")
        res_B = st.file_uploader("Candidate B Resume (PDF/DOCX)", type=["pdf", "docx", "txt"], key="comp_res_b")
        trn_B = st.file_uploader("Candidate B Transcript (PDF/DOCX)", type=["pdf", "docx", "txt"], key="comp_trn_b")
        
    comp_btn = st.button("🚀 Evaluate & Compare Both Candidates", type="primary", use_container_width=True)
    
    if comp_btn:
        if not groq_api_key:
            st.error("⚠️ Please enter a valid Groq API Key in the sidebar.")
        elif not res_A or not res_B:
            st.error("⚠️ Please upload resumes for both Candidate A and Candidate B.")
        else:
            with st.spinner("Extracting Job Description and Candidate documents..."):
                if comp_jd_file is not None:
                    shared_jd = process_uploaded_file(comp_jd_file)
                else:
                    shared_jd = comp_jd_manual.strip() if comp_jd_manual.strip() else "Software Engineer"
                
                text_res_A = process_uploaded_file(res_A)
                text_trn_A = process_uploaded_file(trn_A) if trn_A else ""
                text_res_B = process_uploaded_file(res_B)
                text_trn_B = process_uploaded_file(trn_B) if trn_B else ""

            with st.spinner("Evaluating Candidate A through 4-Agent Pipeline..."):
                res_A_eval = run_evaluation_pipeline("eval_A", text_res_A, text_trn_A, shared_jd)
                
            with st.spinner("Evaluating Candidate B through 4-Agent Pipeline..."):
                res_B_eval = run_evaluation_pipeline("eval_B", text_res_B, text_trn_B, shared_jd)
                
            st.session_state.comparison_results = {
                "A": res_A_eval,
                "B": res_B_eval,
            }
            st.success("🎉 Both Candidates Evaluated Successfully!")

    if "comparison_results" in st.session_state:
        comp = st.session_state.comparison_results
        repA = comp["A"].get("final_report", {})
        repB = comp["B"].get("final_report", {})
        profA = comp["A"].get("candidate_profile", {})
        profB = comp["B"].get("candidate_profile", {})
        
        st.markdown("---")
        st.subheader("🏆 Side-by-Side Comparison & Recommendation")
        
        cmp1, cmp2 = st.columns(2)
        with cmp1:
            st.markdown(f"### Candidate A: {profA.get('candidate_name', 'Candidate A')}")
            st.metric("Recommendation", repA.get("final_recommendation", "N/A"))
            st.metric("Confidence Score", f"{repA.get('confidence_score', 0.0)*100:.0f}%")
            st.info(f"**Judge Reasoning:**\n\n{repA.get('reasoning', '')}")
            
            st.markdown("**Key Strengths:**")
            for ks in repA.get("key_strengths", []):
                st.markdown(f"- {ks.get('point')}")
                
            st.markdown("**Key Concerns:**")
            for kc in repA.get("key_concerns", []):
                st.markdown(f"- {kc.get('point')} ({kc.get('severity', 'medium')})")
            
        with cmp2:
            st.markdown(f"### Candidate B: {profB.get('candidate_name', 'Candidate B')}")
            st.metric("Recommendation", repB.get("final_recommendation", "N/A"))
            st.metric("Confidence Score", f"{repB.get('confidence_score', 0.0)*100:.0f}%")
            st.info(f"**Judge Reasoning:**\n\n{repB.get('reasoning', '')}")
            
            st.markdown("**Key Strengths:**")
            for ks in repB.get("key_strengths", []):
                st.markdown(f"- {ks.get('point')}")
                
            st.markdown("**Key Concerns:**")
            for kc in repB.get("key_concerns", []):
                st.markdown(f"- {kc.get('point')} ({kc.get('severity', 'medium')})")
