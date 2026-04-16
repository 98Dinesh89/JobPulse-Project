import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from llm_extractor import extract_resume_entities
import plotly.graph_objects as go
import os, re
from vision_extractor import extract_skills_from_image
from analyzer import map_to_taxonomy

from analyzer import (
    run_full_analysis, gap_analysis, get_resources,
    extract_skills, SKILL_TAXONOMY, ALL_SKILLS
)

# ─────────────────────────────────────────────
#  PAGE CONFIG & CUSTOM CSS
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="JobPulse — Job Market Intelligence",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Mono:wght@400;700&family=Inter:wght@300;400;600&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
    background-color: #0a0a0f;
    color: #e2e2e2;
}

.stApp { background-color: #0a0a0f; }

/* Header */
.hero {
    background: linear-gradient(135deg, #0a0a0f 0%, #111128 100%);
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 2rem 2.5rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
}
.hero::before {
    content: '';
    position: absolute;
    top: -50%; left: -50%;
    width: 200%; height: 200%;
    background: radial-gradient(circle at 70% 40%, rgba(99,102,241,0.08) 0%, transparent 60%);
    pointer-events: none;
}
.hero h1 {
    font-family: 'Space Mono', monospace;
    font-size: 2.4rem;
    font-weight: 700;
    color: #ffffff;
    margin: 0 0 0.3rem 0;
    letter-spacing: -1px;
}
.hero p {
    color: #9090b0;
    font-size: 1rem;
    margin: 0;
}
.accent { color: #6366f1; }

/* Metric cards */
.metric-row { display: flex; gap: 1rem; margin-bottom: 1.5rem; flex-wrap: wrap; }
.metric-card {
    background: #111128;
    border: 1px solid #2a2a4a;
    border-radius: 10px;
    padding: 1.2rem 1.5rem;
    flex: 1;
    min-width: 160px;
}
.metric-card .label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: #6060a0;
    margin-bottom: 0.3rem;
}
.metric-card .value {
    font-family: 'Space Mono', monospace;
    font-size: 1.8rem;
    font-weight: 700;
    color: #ffffff;
}
.metric-card .sub { font-size: 0.78rem; color: #8080b0; margin-top: 0.2rem; }

/* Score ring */
.score-wrap {
    display: flex;
    flex-direction: column;
    align-items: center;
    background: #111128;
    border: 1px solid #2a2a4a;
    border-radius: 12px;
    padding: 1.5rem;
}
.score-ring {
    width: 110px; height: 110px;
    border-radius: 50%;
    background: conic-gradient(#6366f1 var(--pct), #1e1e3a var(--pct));
    display: flex; align-items: center; justify-content: center;
    position: relative;
}
.score-ring::before {
    content: '';
    width: 80px; height: 80px;
    border-radius: 50%;
    background: #111128;
    position: absolute;
}
.score-ring span {
    font-family: 'Space Mono', monospace;
    font-size: 1.3rem;
    font-weight: 700;
    color: #fff;
    position: relative;
    z-index: 1;
}

/* Skill pill */
.pill {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 20px;
    font-size: 0.78rem;
    font-family: 'Space Mono', monospace;
    margin: 0.2rem;
}
.pill-green  { background: #0d2b1f; color: #34d399; border: 1px solid #065f46; }
.pill-red    { background: #2b0d0d; color: #f87171; border: 1px solid #7f1d1d; }
.pill-blue   { background: #0d1a2b; color: #60a5fa; border: 1px solid #1e3a5f; }
.pill-yellow { background: #2b260d; color: #fbbf24; border: 1px solid #7f6000; }

/* Section header */
.section-header {
    font-family: 'Space Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: #6366f1;
    margin-bottom: 0.8rem;
    border-bottom: 1px solid #1e1e3a;
    padding-bottom: 0.5rem;
}

/* Role badge */
.role-badge {
    background: linear-gradient(90deg, #312e81, #1e1b4b);
    border: 1px solid #4338ca;
    border-radius: 8px;
    padding: 0.8rem 1.2rem;
    font-family: 'Space Mono', monospace;
    font-size: 1.1rem;
    color: #a5b4fc;
    text-align: center;
    margin: 0.5rem 0 1rem 0;
}

/* Resource card */
.res-card {
    background: #0d1117;
    border: 1px solid #2a2a4a;
    border-left: 3px solid #6366f1;
    border-radius: 6px;
    padding: 0.7rem 1rem;
    margin-bottom: 0.5rem;
}
.res-card a { color: #818cf8; text-decoration: none; font-size: 0.88rem; }
.res-card .skill-name {
    font-family: 'Space Mono', monospace;
    font-size: 0.8rem;
    color: #6060a0;
    margin-bottom: 0.2rem;
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background-color: #0d0d1a !important;
    border-right: 1px solid #1e1e3a;
}
section[data-testid="stSidebar"] label { color: #9090b0 !important; }

/* Tab styling */
button[data-baseweb="tab"] { color: #9090b0 !important; }
button[data-baseweb="tab"][aria-selected="true"] {
    color: #6366f1 !important;
    border-bottom: 2px solid #6366f1 !important;
}
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  SIDEBAR — USER PROFILE
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📡 **JobPulse**")
    st.markdown("<small style='color:#6060a0'>Job Market Intelligence Engine</small>", unsafe_allow_html=True)
    st.divider()

    st.markdown("### 🧑‍💻 Your Profile")
    skill_input = st.text_area(
        "Your skills (comma-separated)",
        value="",
        height=80,
        help="Enter your skills as a comma-separated list. E.g. Python, React, AWS"
    )

    uploaded_file = st.file_uploader(
        "Upload Resume (PDF/Image)",
        type=["pdf", "jpg", "jpeg", "png"]
    )

    resume_text = st.text_area(
        "Or paste your resume / LinkedIn bio",
        height=120,
        placeholder="Paste any text and we'll auto-extract your skills…",
        help="Optional: paste any text and skills will be extracted automatically"
    )
    top_n = st.slider("Compare against top N skills", 10, 40, 20)
    run_btn = st.button("🔍 Analyse My Profile", use_container_width=True, type="primary")

    st.divider()
    st.caption("Data sources: RemoteOK · HackerNews Who's Hiring · Fallback dataset")
    st.caption("Skill extraction: rule-based NLP · Clustering: TF-IDF + KMeans")


# ─────────────────────────────────────────────
#  HERO HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div class="hero">
  <h1>📡 Job<span class="accent">Pulse</span></h1>
  <p>Real-time job market intelligence · NLP skill extraction · Personalised gap analysis</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  LOAD / CACHE DATA
# ─────────────────────────────────────────────
@st.cache_data(show_spinner="⚙️ Running NLP pipeline…")
def load_data():
    if not os.path.exists("jobs_raw.csv"):
        st.info("⚙️ No job data found. Fetching live jobs now — this takes ~15 seconds…")
        from scraper import run_scraper
        with st.spinner("Scraping jobs from RemoteOK & HackerNews…"):
            run_scraper()
        st.rerun()

    return run_full_analysis("jobs_raw.csv")

data = load_data()
df      = data["df"]
freq    = data["freq"]
sal_skill = data["sal_skill"]
sal_role  = data["sal_role"]


# ─────────────────────────────────────────────
#  TOP METRICS ROW
# ─────────────────────────────────────────────
n_jobs    = len(df)
n_skills  = len(freq)
n_sources = df["source"].nunique()
has_salary = df["salary_min"].notna().sum()
avg_max = int(df["salary_max"].dropna().mean()) if has_salary else 0

st.markdown(f"""
<div class="metric-row">
  <div class="metric-card">
    <div class="label">Jobs Analysed</div>
    <div class="value">{n_jobs}</div>
    <div class="sub">{n_sources} live sources</div>
  </div>
  <div class="metric-card">
    <div class="label">Unique Skills Found</div>
    <div class="value">{n_skills}</div>
    <div class="sub">NLP extracted</div>
  </div>
  <div class="metric-card">
    <div class="label">Avg Max Salary</div>
    <div class="value">${avg_max:,}</div>
    <div class="sub">USD · across {has_salary} postings</div>
  </div>
  <div class="metric-card">
    <div class="label">Role Clusters</div>
    <div class="value">{df['role_family'].nunique()}</div>
    <div class="sub">KMeans segments</div>
  </div>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  MAIN TABS
# ─────────────────────────────────────────────
tab1, tab2, tab3, tab4 = st.tabs([
    "🔥 Market Trends",
    "💡 My Gap Analysis",
    "💰 Salary Intelligence",
    "🗂 Raw Jobs"
])


# ══════════════════════════════════════════════
#  TAB 1 — MARKET TRENDS
# ══════════════════════════════════════════════
with tab1:
    col1, col2 = st.columns([3, 2])

    with col1:
        st.markdown('<div class="section-header">Top 20 In-Demand Skills</div>', unsafe_allow_html=True)
        top20 = freq.head(20).copy()
        color_map = {"Languages": "#6366f1", "ML / AI": "#a78bfa",
                     "Web & APIs": "#34d399", "Data & Databases": "#60a5fa",
                     "Cloud & DevOps": "#f59e0b", "Soft Skills": "#f87171"}
        top20["color"] = top20["category"].map(color_map).fillna("#9ca3af")

        fig = go.Figure(go.Bar(
            x=top20["count"],
            y=top20["skill"],
            orientation="h",
            marker_color=top20["color"],
            text=top20["pct_of_jobs"].apply(lambda x: f"{x}%"),
            textposition="outside",
        ))
        fig.update_layout(
            plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
            font=dict(color="#e2e2e2", family="Space Mono"),
            xaxis=dict(showgrid=False, color="#444"),
            yaxis=dict(showgrid=False, autorange="reversed"),
            margin=dict(l=10, r=60, t=10, b=10),
            height=480,
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown('<div class="section-header">Skills by Category</div>', unsafe_allow_html=True)
        cat_counts = freq.groupby("category")["count"].sum().reset_index()
        fig2 = go.Figure(go.Pie(
            labels=cat_counts["category"],
            values=cat_counts["count"],
            hole=0.55,
            marker_colors=list(color_map.values()),
            textinfo="label+percent",
            textfont=dict(size=11, color="#fff"),
        ))
        fig2.update_layout(
            plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
            font=dict(color="#e2e2e2"),
            margin=dict(l=10, r=10, t=10, b=10),
            showlegend=False, height=300,
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown('<div class="section-header">Role Family Distribution</div>', unsafe_allow_html=True)
        role_counts = df["role_family"].value_counts().reset_index()
        role_counts.columns = ["role", "count"]
        fig3 = go.Figure(go.Bar(
            x=role_counts["count"], y=role_counts["role"],
            orientation="h",
            marker_color="#6366f1",
        ))
        fig3.update_layout(
            plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
            font=dict(color="#e2e2e2", family="Space Mono"),
            xaxis=dict(showgrid=False),
            yaxis=dict(showgrid=False),
            margin=dict(l=10, r=10, t=10, b=10),
            height=240,
        )
        st.plotly_chart(fig3, use_container_width=True)


# ══════════════════════════════════════════════
#  TAB 2 — MY GAP ANALYSIS
# ══════════════════════════════════════════════

with tab2:
        user_skills_raw = []

        if uploaded_file:
            file_ext = uploaded_file.name.split(".")[-1].lower()

            if file_ext in ["jpg", "jpeg", "png"]:
                llm_data = extract_skills_from_image(uploaded_file)
                raw_skills = llm_data["skills"]
                user_skills_raw = map_to_taxonomy(raw_skills)

            elif file_ext == "pdf":
                extracted_text = extract_resume_text(uploaded_file)
                llm_data = extract_resume_entities(extracted_text)
                raw_skills = llm_data["skills"]
                user_skills_raw = map_to_taxonomy(raw_skills)

            st.success(f"📄 Extracted {len(user_skills_raw)} skills from uploaded resume")

        elif resume_text.strip():
            extracted = extract_skills(resume_text)
            user_skills_raw = extracted

        elif skill_input.strip():
            user_skills_raw = [
                s.strip().lower()
                for s in skill_input.split(",")
                if s.strip()
            ]

        if not user_skills_raw:
            st.warning("Upload a resume, paste text, or enter skills.")
            st.stop()

        gap = gap_analysis(user_skills_raw, freq, top_n=top_n)
        resources = get_resources(gap["missing_top"])

        col_a, col_b = st.columns([1, 2])

        with col_a:
            pct = gap["score"]
            st.markdown(f"""
            <div class="score-wrap">
                <div class="label" style="font-size:0.7rem;letter-spacing:2px;text-transform:uppercase;color:#6060a0;margin-bottom:1rem">
                    Market Alignment Score
                </div>
                <div class="score-ring" style="--pct:{pct*3.6}deg">
                    <span>{pct}%</span>
                </div>
                <div style="margin-top:1rem;font-size:0.85rem;color:#9090b0;text-align:center">
                    You have {len(sorted(user_skills_raw))} of top {top_n} skills
                </div>
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br>", unsafe_allow_html=True)

            st.markdown('<div class="section-header">Closest Role Match</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="role-badge">⚡ {gap["role_match"]}</div>', unsafe_allow_html=True)

            st.markdown('<div class="section-header">Extracted Resume Skills</div>', unsafe_allow_html=True)

            pills_html = "".join(
                f'<span class="pill pill-blue">{s}</span>'
                for s in sorted(user_skills_raw)
            )

            if not pills_html:
                pills_html = '<span style="color:#6060a0;font-size:0.85rem">No skills extracted from resume</span>'

            st.markdown(pills_html, unsafe_allow_html=True)

        with col_b:
            st.markdown('<div class="section-header">Skills Gap — High Demand, You Don\'t Have</div>', unsafe_allow_html=True)

            if gap["missing_with_counts"]:
                for item in gap["missing_with_counts"]:
                    skill = item["skill"]
                    count = item["count"]
                    pct_jobs = item["pct_of_jobs"]
                    cat = item["category"]
                    bar_width = min(int(pct_jobs * 4), 100)
                    st.markdown(f"""
                    <div style="background:#111128;border:1px solid #2a2a4a;border-radius:8px;
                                padding:0.8rem 1rem;margin-bottom:0.5rem;">
                      <div style="display:flex;justify-content:space-between;align-items:center;">
                        <span style="font-family:'Space Mono',monospace;color:#e2e2e2">{skill}</span>
                        <span style="font-size:0.75rem;color:#6060a0">{cat}</span>
                      </div>
                      <div style="background:#1e1e3a;border-radius:4px;height:6px;margin-top:0.5rem;">
                        <div style="background:#6366f1;width:{bar_width}%;height:6px;border-radius:4px;"></div>
                      </div>
                      <div style="font-size:0.72rem;color:#8080b0;margin-top:0.3rem">
                        In {count} jobs · {pct_jobs}% of market
                      </div>
                    </div>
                    """, unsafe_allow_html=True)
            else:
                st.success("🎉 You have all the top skills! You're well-aligned with the market.")

            st.markdown('<div class="section-header" style="margin-top:1.5rem">📚 Learning Roadmap</div>', unsafe_allow_html=True)
            for r in resources[:6]:
                st.markdown(f"""
                <div class="res-card">
                  <div class="skill-name">📌 {r['skill']}</div>
                  <a href="{r['url']}" target="_blank">→ {r['resource']}</a>
                </div>
                """, unsafe_allow_html=True)


# ══════════════════════════════════════════════
#  TAB 3 — SALARY INTELLIGENCE
# ══════════════════════════════════════════════
with tab3:
    if sal_skill.empty:
        st.info("💡 Salary data not available in the current dataset (scrape live data with `python scraper.py` to see real salaries).")
    else:
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('<div class="section-header">Avg Max Salary by Skill (Top 15)</div>', unsafe_allow_html=True)
            top_sal = sal_skill.head(15)
            fig_s = go.Figure(go.Bar(
                x=top_sal["avg_salary_max"],
                y=top_sal["skill"],
                orientation="h",
                marker_color="#6366f1",
                text=top_sal["avg_salary_max"].apply(lambda x: f"${x:,.0f}"),
                textposition="outside",
            ))
            fig_s.update_layout(
                plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
                font=dict(color="#e2e2e2", family="Space Mono"),
                xaxis=dict(showgrid=False, tickprefix="$"),
                yaxis=dict(showgrid=False, autorange="reversed"),
                margin=dict(l=10, r=80, t=10, b=10),
                height=420,
            )
            st.plotly_chart(fig_s, use_container_width=True)

        with col2:
            st.markdown('<div class="section-header">Salary Range by Role Family</div>', unsafe_allow_html=True)
            if not sal_role.empty:
                fig_r = go.Figure()
                fig_r.add_trace(go.Bar(
                    name="Min Salary", x=sal_role["role_family"], y=sal_role["avg_min"],
                    marker_color="#312e81",
                ))
                fig_r.add_trace(go.Bar(
                    name="Max Salary", x=sal_role["role_family"], y=sal_role["avg_max"],
                    marker_color="#6366f1",
                ))
                fig_r.update_layout(
                    barmode="group",
                    plot_bgcolor="#0a0a0f", paper_bgcolor="#0a0a0f",
                    font=dict(color="#e2e2e2", family="Space Mono"),
                    xaxis=dict(showgrid=False, tickangle=-20),
                    yaxis=dict(showgrid=False, tickprefix="$"),
                    margin=dict(l=10, r=10, t=10, b=10),
                    height=420, legend=dict(bgcolor="#111128"),
                )
                st.plotly_chart(fig_r, use_container_width=True)


# ══════════════════════════════════════════════
#  TAB 4 — RAW JOBS
# ══════════════════════════════════════════════
with tab4:
    st.markdown('<div class="section-header">All Scraped Jobs</div>', unsafe_allow_html=True)

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        family_filter = st.multiselect(
            "Filter by Role Family",
            options=df["role_family"].unique().tolist(),
            default=df["role_family"].unique().tolist()
        )
    with col_f2:
        source_filter = st.multiselect(
            "Filter by Source",
            options=df["source"].unique().tolist(),
            default=df["source"].unique().tolist()
        )

    filtered = df[df["role_family"].isin(family_filter) & df["source"].isin(source_filter)]

    display_cols = ["title", "company", "location", "role_family", "source", "salary_min", "salary_max"]
    available = [c for c in display_cols if c in filtered.columns]
    st.dataframe(
        filtered[available].reset_index(drop=True),
        use_container_width=True,
        height=500
    )
    st.caption(f"Showing {len(filtered)} of {len(df)} jobs")


# ─────────────────────────────────────────────
#  FOOTER
# ─────────────────────────────────────────────
st.markdown("""
<div style="text-align:center;padding:2rem 0 1rem;color:#3a3a5a;font-size:0.75rem;font-family:'Space Mono',monospace;">
  JobPulse · Built for MindCase × IIT Roorkee TGC 2026 · Real data · Real NLP
</div>
""", unsafe_allow_html=True)
