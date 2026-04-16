import requests
import pandas as pd
import time
import json
import re
from datetime import datetime

# ─────────────────────────────────────────────
#  SOURCE 1: RemoteOK (free public JSON API)
# ─────────────────────────────────────────────
def scrape_remoteok():
    print("🌐 Fetching RemoteOK jobs...")
    headers = {"User-Agent": "JobMarketResearcher/1.0 (academic project)"}
    try:
        response = requests.get("https://remoteok.com/api", headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        jobs = []
        for job in data[1:]:  # first item is metadata
            jobs.append({
                "title": job.get("position", ""),
                "company": job.get("company", ""),
                "description": job.get("description", ""),
                "tags": ", ".join(job.get("tags", [])),
                "salary_min": job.get("salary_min", None),
                "salary_max": job.get("salary_max", None),
                "location": job.get("location", "Remote"),
                "date": job.get("date", ""),
                "source": "RemoteOK"
            })
        print(f"   ✅ Got {len(jobs)} jobs from RemoteOK")
        return jobs
    except Exception as e:
        print(f"   ⚠️ RemoteOK failed: {e}")
        return []


# ─────────────────────────────────────────────
#  SOURCE 2: HackerNews "Who's Hiring" thread
# ─────────────────────────────────────────────
def scrape_hackernews_hiring():
    print("🌐 Fetching HackerNews Who's Hiring...")
    try:
        # Find the latest "Ask HN: Who is hiring?" thread
        search_url = "https://hn.algolia.com/api/v1/search?query=Ask+HN+Who+is+hiring&tags=story,ask_hn&hitsPerPage=5"
        r = requests.get(search_url, timeout=10)
        results = r.json().get("hits", [])

        thread_id = None
        for hit in results:
            if "who is hiring" in hit.get("title", "").lower():
                thread_id = hit["objectID"]
                print(f"   📌 Found thread: {hit['title']}")
                break

        if not thread_id:
            print("   ⚠️ Could not find HN hiring thread")
            return []

        # Fetch comments from that thread
        comments_url = f"https://hn.algolia.com/api/v1/search?tags=comment,story_{thread_id}&hitsPerPage=100"
        r2 = requests.get(comments_url, timeout=10)
        comments = r2.json().get("hits", [])

        jobs = []
        for c in comments:
            text = c.get("comment_text", "") or ""
            # Clean HTML tags
            clean = re.sub(r'<[^>]+>', ' ', text)
            clean = re.sub(r'\s+', ' ', clean).strip()
            if len(clean) > 100:  # filter trivial comments
                jobs.append({
                    "title": extract_title_from_hn(clean),
                    "company": extract_company_from_hn(clean),
                    "description": clean[:2000],
                    "tags": "",
                    "salary_min": None,
                    "salary_max": None,
                    "location": extract_location_from_hn(clean),
                    "date": c.get("created_at", ""),
                    "source": "HackerNews"
                })
        print(f"   ✅ Got {len(jobs)} posts from HackerNews")
        return jobs

    except Exception as e:
        print(f"   ⚠️ HackerNews failed: {e}")
        return []


def extract_title_from_hn(text):
    roles = ["engineer", "developer", "scientist", "analyst", "designer",
             "manager", "lead", "architect", "devops", "backend", "frontend",
             "fullstack", "full stack", "ml engineer", "data engineer"]
    text_lower = text.lower()
    for role in roles:
        if role in text_lower:
            # grab surrounding words
            idx = text_lower.find(role)
            snippet = text[max(0, idx-20):idx+len(role)+20].strip()
            return snippet.split('|')[0].split('.')[0].strip()
    return "Software Engineer"


def extract_company_from_hn(text):
    # HN posts often start with "CompanyName |" or "CompanyName -"
    match = re.match(r'^([A-Z][^\|\-\n]{2,40}?)[\|\-]', text)
    if match:
        return match.group(1).strip()
    return "Unknown"


def extract_location_from_hn(text):
    patterns = [r'Remote', r'Hybrid', r'On[- ]?site',
                r'New York', r'San Francisco', r'London', r'Berlin',
                r'Bangalore', r'India', r'NYC', r'SF', r'Europe']
    for p in patterns:
        if re.search(p, text, re.IGNORECASE):
            return re.search(p, text, re.IGNORECASE).group(0)
    return "Not specified"


# ─────────────────────────────────────────────
#  FALLBACK: Rich demo data (realistic)
# ─────────────────────────────────────────────
FALLBACK_DATA = [
    {"title": "Senior ML Engineer", "company": "OpenAI", "description": "We need strong Python, PyTorch, and distributed training experience. Familiarity with LLMs, transformers architecture, RLHF. Docker and Kubernetes for deployment.", "tags": "python,pytorch,ml", "salary_min": 180000, "salary_max": 300000, "location": "Remote", "date": "", "source": "Fallback"},
    {"title": "Backend Engineer", "company": "Stripe", "description": "Ruby, Python, or Go for high-scale payment APIs. PostgreSQL, Redis, Kafka. Strong understanding of REST and gRPC. AWS infrastructure.", "tags": "python,go,postgres", "salary_min": 150000, "salary_max": 220000, "location": "Remote", "date": "", "source": "Fallback"},
    {"title": "Data Scientist", "company": "Netflix", "description": "Python, R, SQL. Machine learning with scikit-learn and TensorFlow. A/B testing, statistical analysis, causal inference. Spark for big data.", "tags": "python,sql,ml", "salary_min": 160000, "salary_max": 250000, "location": "Remote", "date": "", "source": "Fallback"},
    {"title": "Frontend Engineer", "company": "Figma", "description": "React, TypeScript, WebGL. Performance optimization, accessibility. CSS-in-JS, design systems experience. Node.js for tooling.", "tags": "react,typescript,css", "salary_min": 140000, "salary_max": 200000, "location": "Hybrid", "date": "", "source": "Fallback"},
    {"title": "DevOps Engineer", "company": "HashiCorp", "description": "Terraform, Kubernetes, AWS/GCP/Azure. CI/CD pipelines with GitHub Actions or Jenkins. Python or Go scripting. Security hardening, SRE practices.", "tags": "kubernetes,aws,terraform", "salary_min": 145000, "salary_max": 210000, "location": "Remote", "date": "", "source": "Fallback"},
    {"title": "Full Stack Developer", "company": "Shopify", "description": "React, Ruby on Rails, GraphQL. PostgreSQL, Redis. Docker. Experience with e-commerce platforms, Liquid templating.", "tags": "react,ruby,graphql", "salary_min": 130000, "salary_max": 190000, "location": "Remote", "date": "", "source": "Fallback"},
    {"title": "Data Engineer", "company": "Airbnb", "description": "Apache Spark, Kafka, Airflow. Python, SQL, Scala. Data warehouse design with BigQuery or Snowflake. dbt for transformations.", "tags": "spark,python,sql", "salary_min": 155000, "salary_max": 230000, "location": "Hybrid", "date": "", "source": "Fallback"},
    {"title": "Android Engineer", "company": "Duolingo", "description": "Kotlin, Jetpack Compose, Coroutines. MVVM architecture, unit testing, CI/CD. GraphQL, REST APIs. Accessibility and internationalization.", "tags": "kotlin,android,jetpack", "salary_min": 135000, "salary_max": 195000, "location": "Remote", "date": "", "source": "Fallback"},
    {"title": "Security Engineer", "company": "Cloudflare", "description": "Network security, cryptography, Rust or C++. Penetration testing, threat modelling. Python scripting for automation. Zero Trust architecture.", "tags": "security,rust,python", "salary_min": 160000, "salary_max": 240000, "location": "Remote", "date": "", "source": "Fallback"},
    {"title": "Product Analyst", "company": "Notion", "description": "SQL, Python, Looker or Tableau. A/B experiment analysis, funnel analysis, cohort analysis. Strong communication skills, stakeholder management.", "tags": "sql,python,tableau", "salary_min": 120000, "salary_max": 170000, "location": "Hybrid", "date": "", "source": "Fallback"},
    {"title": "NLP Research Engineer", "company": "Cohere", "description": "Python, HuggingFace Transformers, PyTorch. Large language models, fine-tuning, RLHF. Research background preferred. Docker, FastAPI for serving.", "tags": "python,nlp,pytorch", "salary_min": 170000, "salary_max": 280000, "location": "Remote", "date": "", "source": "Fallback"},
    {"title": "Cloud Architect", "company": "Databricks", "description": "AWS, Azure, GCP. Spark, Delta Lake, MLflow. Terraform, Python. Designing multi-cloud data platforms. Kafka for streaming.", "tags": "aws,spark,terraform", "salary_min": 175000, "salary_max": 260000, "location": "Remote", "date": "", "source": "Fallback"},
    {"title": "iOS Developer", "company": "Spotify", "description": "Swift, SwiftUI, Combine. MVVM or TCA architecture. Core Data, CloudKit. Instruments for performance profiling. REST APIs, GraphQL.", "tags": "swift,ios,swiftui", "salary_min": 140000, "salary_max": 200000, "location": "Remote", "date": "", "source": "Fallback"},
    {"title": "Site Reliability Engineer", "company": "LinkedIn", "description": "Kubernetes, Prometheus, Grafana. Python, Go, or Java. On-call rotations, incident response. Chaos engineering, capacity planning. Kafka, Hadoop.", "tags": "kubernetes,go,python", "salary_min": 155000, "salary_max": 225000, "location": "Hybrid", "date": "", "source": "Fallback"},
    {"title": "Generative AI Engineer", "company": "Anthropic", "description": "Python, PyTorch, Transformer models. Prompt engineering, RAG pipelines, LangChain. Vector databases like Pinecone or Weaviate. FastAPI, Docker.", "tags": "python,llm,pytorch", "salary_min": 190000, "salary_max": 320000, "location": "Remote", "date": "", "source": "Fallback"},
]


# ─────────────────────────────────────────────
#  MAIN RUNNER
# ─────────────────────────────────────────────
def run_scraper():
    print("=" * 50)
    print("🚀 Job Market Intelligence — Scraper")
    print("=" * 50)

    all_jobs = []

    # Attempt live sources
    remoteok_jobs = scrape_remoteok()
    all_jobs.extend(remoteok_jobs)
    time.sleep(1)  # be respectful

    hn_jobs = scrape_hackernews_hiring()
    all_jobs.extend(hn_jobs)

    # Fallback if live scraping failed or returned too little
    if len(all_jobs) < 10:
        print(f"\n⚠️  Only got {len(all_jobs)} live jobs. Enriching with fallback data...")
        all_jobs.extend(FALLBACK_DATA)

    # Deduplicate and clean
    df = pd.DataFrame(all_jobs).drop_duplicates(subset=["title", "company"])
    df = df[df["description"].str.len() > 50].reset_index(drop=True)

    df.to_csv("jobs_raw.csv", index=False)
    print(f"\n✅ Saved {len(df)} jobs to jobs_raw.csv")
    print(f"   Sources: {df['source'].value_counts().to_dict()}")
    print("=" * 50)


if __name__ == "__main__":
    run_scraper()
