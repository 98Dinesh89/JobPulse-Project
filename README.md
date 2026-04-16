# 🚀 SkillPulse - Real-Time Job Market Intelligence & Resume Gap Analyzer

SkillPulse is an AI-powered job market intelligence platform that scrapes public job postings, extracts trending skills, and compares them against user’s resume to identify personalized skill gaps.

Built for **MindCase x IIT Roorkee MID PREP 2026**, this project transforms raw public web data into actionable career insights.

---

## 🎯 Problem Statement

Students and professionals often struggle to answer:

- Which skills are currently trending?
- Which skills am I missing for my target role?
- Which role best matches my current profile?
- What should I learn next for better opportunities?

SkillPulse solves this by combining **public web scraping + AI-based resume analysis + market trend intelligence**.

---

## ✨ Features

- 📄 **Resume Skill Extraction**
  - Upload resume as PDF/image
  - Extracts technical + soft skills

- 🌐 **Job Market Scraping**
  - Scrapes public job postings
  - Collects job titles, roles, salaries, and required skills

- 📈 **Trend Analysis**
  - Detects top in-demand skills
  - Shows market frequency and role trends

- 🎯 **Role Matching**
  - Predicts closest matching job role
  - Compares user skills with real market demand

- 📚 **Skill Gap Recommendations**
  - Shows missing high-demand skills
  - Personalized learning roadmap suggestions

- ⚡ **Fast UI**
  - Streamlit-based clean interface
  - Real-time insights and skill pills

---

## 🛠️ Tech Stack

### **Frontend**

- Streamlit

### **Backend / Analysis**

- Python
- Pandas
- NumPy

### **AI / NLP**

- Groq LLM
- Resume skill extraction
- Skill taxonomy normalization
- Role classification

### **Data Collection**

- Requests
- BeautifulSoup
- CSV pipelines

### **Deployment Ready**

- Docker
- FastAPI-ready modular architecture

---

## 🧠 How It Works

### 1️⃣ Data Scraping

Public job postings are scraped from job boards and company career pages.

Extracted fields:

- job title
- company
- salary (if available)
- location
- required skills
- experience level

---

### 2️⃣ Market Skill Intelligence

The scraped data is analyzed to:

- detect trending skills
- calculate frequency
- identify top roles
- estimate market demand

---

### 3️⃣ Resume Analysis

The user uploads a resume.

The system:

- extracts text from PDF/image
- detects technical + soft skills
- normalizes them using taxonomy mapping

---

### 4️⃣ Gap Detection

Resume skills are compared with top market skills.

The platform outputs:

- matched skills
- missing skills
- closest role match
- learning recommendations

---

## 📂 Project Structure

```bash
SkillPulse/
│
├── app.py
├── analyzer.py
├── llm_extractor.py
├── vision_extractor.py
├── requirements.txt
├── jobs.csv
└── README.md
```

---

## ▶️ Run Locally

### 1) Clone repo

```bash
git clone https://github.com/98Dinesh89/JobPulse-Project.git
cd SkillPulse
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) API key

API Keys are already added

### 4) Run app

```bash
streamlit run app.py
```

---

## 📸 Demo Workflow

1. Upload resume
2. Extract skills
3. Compare with live market trends
4. View:
   - closest role match
   - matched skills
   - missing skills
   - learning recommendations

---

## 🌍 Real-World Use Cases

- 🎓 Students planning internships
- 💼 Professionals switching careers
- 🏫 Colleges aligning curriculum
- 📊 Bootcamps analyzing market demand
- 🧑‍💻 Recruiters understanding skill gaps

---

## 🚀 Future Scope

- live scheduled scraping pipelines
- salary prediction
- role transition graph
- personalized course recommendations
- job alert automation
- company-specific skill demand trends

---

## 👨‍💻 Team

Built for **MindCase x IIT Roorkee MID PREP 2026**

Team Name: Forged

Members:

- Dinesh
- Mayank
- Lakshya
- Mangesh

---

## 🏆 Why This Stands Out

Unlike typical trend dashboards, SkillPulse directly connects:

> **public job market demand → individual resume → personalized growth roadmap**

This makes the platform actionable, practical, and highly useful for real users.
