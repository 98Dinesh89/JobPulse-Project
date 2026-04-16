import pandas as pd
import numpy as np
import re
from collections import Counter
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.preprocessing import normalize
import warnings
warnings.filterwarnings("ignore")


# ─────────────────────────────────────────────
#  SKILL TAXONOMY  (extensible dictionary)
# ─────────────────────────────────────────────
SKILL_TAXONOMY = {
    "Languages": [
        "python", "javascript", "typescript", "java", "go", "golang", "rust",
        "c++", "c#", "ruby", "scala", "kotlin", "swift", "r", "php", "bash"
    ],
    "ML / AI": [
        "machine learning", "deep learning", "pytorch", "tensorflow", "keras",
        "scikit-learn", "sklearn", "nlp", "llm", "transformers", "huggingface",
        "rlhf", "langchain", "vector database", "pinecone", "weaviate", "rag",
        "fine-tuning", "generative ai", "openai", "stable diffusion", "xgboost"
    ],
    "Web & APIs": [
        "react", "nextjs", "next.js", "vue", "angular", "node.js", "nodejs",
        "fastapi", "django", "flask", "graphql", "rest", "grpc", "spring boot",
        "express", "svelte", "tailwind", "webgl", "css", "html"
    ],
    "Data & Databases": [
        "sql", "postgresql", "postgres", "mysql", "mongodb", "redis",
        "elasticsearch", "snowflake", "bigquery", "spark", "hadoop",
        "kafka", "airflow", "dbt", "databricks", "pandas", "numpy"
    ],
    "Cloud & DevOps": [
        "aws", "gcp", "azure", "kubernetes", "docker", "terraform",
        "ansible", "ci/cd", "github actions", "jenkins", "prometheus",
        "grafana", "linux", "nginx", "microservices", "serverless"
    ],
    "Soft Skills": [
        "communication", "leadership", "stakeholder", "agile", "scrum",
        "product thinking", "cross-functional", "mentoring"
    ]
}

# Flat skill list for fast lookup
ALL_SKILLS = {skill: category
              for category, skills in SKILL_TAXONOMY.items()
              for skill in skills}

ROLE_CLUSTERS = {
    0: "Backend / API Engineer",
    1: "ML / AI Engineer",
    2: "Frontend / UI Engineer",
    3: "Data Engineer / Analyst",
    4: "DevOps / Cloud / SRE",
}


# ─────────────────────────────────────────────
#  SKILL EXTRACTION
# ─────────────────────────────────────────────
def extract_skills(text: str) -> list[str]:
    text_lower = text.lower()
    found = []
    for skill in ALL_SKILLS:
        pattern = r'\b' + re.escape(skill) + r'\b'
        if re.search(pattern, text_lower):
            found.append(skill)
    return list(set(found))


def skills_from_df(df: pd.DataFrame) -> pd.DataFrame:
    """Add an extracted_skills column to the dataframe."""
    combined = df["description"].fillna("") + " " + df["tags"].fillna("")
    df["extracted_skills"] = combined.apply(extract_skills)
    return df

def map_to_taxonomy(skills):
    allowed = set(ALL_SKILLS.keys())
    mapped = []
    for skill in skills:
        s = skill.lower().strip()
        if s in allowed:          
            mapped.append(s)
            continue
        for allowed_skill in allowed:
            if s in allowed_skill or allowed_skill in s:
                mapped.append(allowed_skill)
                break
    return list(set(mapped))
# ─────────────────────────────────────────────
#  ROLE CLUSTERING (TF-IDF + KMeans)
# ─────────────────────────────────────────────
def cluster_roles(df: pd.DataFrame, n_clusters: int = 5) -> pd.DataFrame:
    """Cluster jobs into role families using TF-IDF."""
    if len(df) < n_clusters:
        df["cluster"] = 0
        df["role_family"] = "Software Engineer"
        return df, None, None 

    texts = (df["title"].fillna("") + " " + df["description"].fillna("")).tolist()
    vectorizer = TfidfVectorizer(max_features=300, stop_words="english", ngram_range=(1, 2))
    X = vectorizer.fit_transform(texts)
    X_norm = normalize(X)

    km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
    df["cluster"] = km.fit_predict(X_norm)
    df["role_family"] = df["cluster"].map(ROLE_CLUSTERS)
    return df, vectorizer, km


# ─────────────────────────────────────────────
#  SKILL FREQUENCY & SALARY ANALYSIS
# ─────────────────────────────────────────────
def skill_frequency(df: pd.DataFrame) -> pd.DataFrame:
    """Count how often each skill appears across all jobs."""
    all_skills = []
    for skills in df["extracted_skills"]:
        all_skills.extend(skills)
    counts = Counter(all_skills)
    freq_df = pd.DataFrame(counts.most_common(40), columns=["skill", "count"])
    freq_df["category"] = freq_df["skill"].map(ALL_SKILLS)
    freq_df["pct_of_jobs"] = (freq_df["count"] / len(df) * 100).round(1)
    return freq_df


def salary_by_skill(df: pd.DataFrame) -> pd.DataFrame:
    """Average salary range for jobs requiring each skill."""
    salary_df = df[df["salary_min"].notna() & (df["salary_min"] > 0)].copy()
    if salary_df.empty:
        return pd.DataFrame(columns=["skill", "avg_salary_min", "avg_salary_max", "job_count"])

    rows = []
    for _, row in salary_df.iterrows():
        for skill in row["extracted_skills"]:
            rows.append({
                "skill": skill,
                "salary_min": row["salary_min"],
                "salary_max": row["salary_max"]
            })

    if not rows:
        return pd.DataFrame(columns=["skill", "avg_salary_min", "avg_salary_max", "job_count"])

    skill_sal = pd.DataFrame(rows)
    agg = skill_sal.groupby("skill").agg(
        avg_salary_min=("salary_min", "mean"),
        avg_salary_max=("salary_max", "mean"),
        job_count=("salary_min", "count")
    ).reset_index().sort_values("avg_salary_max", ascending=False)
    return agg


def salary_by_role_family(df: pd.DataFrame) -> pd.DataFrame:
    salary_df = df[df["salary_min"].notna() & (df["salary_min"] > 0)].copy()
    if salary_df.empty:
        return pd.DataFrame()
    return salary_df.groupby("role_family").agg(
        avg_min=("salary_min", "mean"),
        avg_max=("salary_max", "mean"),
        count=("title", "count")
    ).reset_index().sort_values("avg_max", ascending=False)


# ─────────────────────────────────────────────
#  SKILL GAP ANALYSIS
# ─────────────────────────────────────────────
def gap_analysis(user_skills: list[str], freq_df: pd.DataFrame, top_n: int = 20) -> dict:
    """
    Compare user skills against market demand.
    Returns match score, missing skills, and recommendations.
    """
    user_set = set(s.lower().strip() for s in user_skills)
    top_skills = freq_df.head(top_n)["skill"].tolist()
    top_set = set(top_skills)

    matched = user_set & top_set
    missing = top_set - user_set

    # Score: % of top-N skills the user has
    score = round(len(matched) / len(top_set) * 100) if top_set else 0

    # Rank missing by demand
    missing_ranked = freq_df[freq_df["skill"].isin(missing)].sort_values("count", ascending=False)

    # Identify strongest role match
    role_match = _best_role_match(user_set)

    return {
        "score": score,
        "matched": sorted(matched),
        "missing_top": missing_ranked.head(8)["skill"].tolist(),
        "missing_with_counts": missing_ranked.head(8)[["skill", "count", "category", "pct_of_jobs"]].to_dict("records"),
        "role_match": role_match,
        "user_skill_count": len(user_set),
    }


def _best_role_match(user_set: set) -> str:
    role_keywords = {
        "ML / AI Engineer":          {"python", "pytorch", "tensorflow", "machine learning", "nlp", "llm"},
        "Backend / API Engineer":    {"python", "go", "java", "sql", "postgresql", "redis", "docker"},
        "Frontend / UI Engineer":    {"react", "typescript", "javascript", "css", "nextjs", "vue"},
        "Data Engineer / Analyst":   {"sql", "spark", "airflow", "dbt", "kafka", "snowflake", "python"},
        "DevOps / Cloud / SRE":      {"kubernetes", "aws", "docker", "terraform", "linux", "ci/cd"},
        "Generative AI Engineer":    {"llm", "langchain", "rag", "pytorch", "huggingface", "python"},
    }
    scores = {role: len(user_set & kw) for role, kw in role_keywords.items()}
    return max(scores, key=scores.get) if max(scores.values()) > 0 else "Software Engineer"


# ─────────────────────────────────────────────
#  LEARNING RESOURCE MAP
# ─────────────────────────────────────────────
RESOURCES = {
    "python":           ("Python Official Docs",        "https://docs.python.org/3/tutorial/"),
    "pytorch":          ("PyTorch 60-min Blitz",         "https://pytorch.org/tutorials/beginner/blitz/tensor_tutorial.html"),
    "tensorflow":       ("TF Beginner Guide",            "https://www.tensorflow.org/tutorials/quickstart/beginner"),
    "machine learning": ("fast.ai Practical ML",         "https://course.fast.ai/"),
    "llm":              ("Andrej Karpathy's makemore",   "https://github.com/karpathy/makemore"),
    "langchain":        ("LangChain Quickstart",         "https://python.langchain.com/docs/get_started/quickstart"),
    "react":            ("React Official Docs",          "https://react.dev/learn"),
    "typescript":       ("TypeScript Handbook",          "https://www.typescriptlang.org/docs/handbook/intro.html"),
    "kubernetes":       ("Kubernetes Basics",            "https://kubernetes.io/docs/tutorials/kubernetes-basics/"),
    "docker":           ("Docker Getting Started",       "https://docs.docker.com/get-started/"),
    "aws":              ("AWS Free Tier Tutorials",      "https://aws.amazon.com/getting-started/"),
    "sql":              ("SQLZoo Interactive",           "https://sqlzoo.net/"),
    "spark":            ("Spark by Example",             "https://sparkbyexamples.com/"),
    "go":               ("A Tour of Go",                 "https://go.dev/tour/"),
    "rust":             ("The Rust Book",                "https://doc.rust-lang.org/book/"),
    "kafka":            ("Kafka Quickstart",             "https://kafka.apache.org/quickstart"),
    "terraform":        ("HashiCorp Learn Terraform",    "https://developer.hashicorp.com/terraform/tutorials"),
    "dbt":              ("dbt Learn",                    "https://learn.getdbt.com/"),
}

def get_resources(skills: list[str]) -> list[dict]:
    out = []
    for s in skills:
        if s in RESOURCES:
            name, url = RESOURCES[s]
            out.append({"skill": s, "resource": name, "url": url})
        else:
            out.append({"skill": s, "resource": f"Search '{s} tutorial'",
                        "url": f"https://www.google.com/search?q={s.replace(' ', '+')}+tutorial"})
    return out


# ─────────────────────────────────────────────
#  FULL PIPELINE  (called by app.py)
# ─────────────────────────────────────────────
def run_full_analysis(csv_path: str = "jobs_raw.csv"):
    df = pd.read_csv(csv_path)
    df = skills_from_df(df)
    result = cluster_roles(df)
    if isinstance(result, tuple):
        df, vectorizer, km = result
    else:
        df = result
        vectorizer, km = None, None

    freq = skill_frequency(df)
    sal_skill = salary_by_skill(df)
    sal_role = salary_by_role_family(df)

    return {
        "df": df,
        "freq": freq,
        "sal_skill": sal_skill,
        "sal_role": sal_role,
        "vectorizer": vectorizer,
        "km": km
    }


if __name__ == "__main__":
    result = run_full_analysis()
    print("Top 10 skills:")
    print(result["freq"].head(10).to_string(index=False))
