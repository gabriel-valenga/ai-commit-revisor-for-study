import subprocess
import os
import requests
import textwrap

# Environment variables
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
GITHUB_TOKEN = os.environ["GITHUB_TOKEN"]
REPO = os.environ["GITHUB_REPOSITORY"]
COMMIT_SHA = os.environ["GITHUB_SHA"]

# 1. Get the diff of the last commit
diff = subprocess.check_output(
    ["git", "show", "--format=", COMMIT_SHA],
    text=True
)

# 2. Limit diff size to control cost
MAX_DIFF_SIZE = 6000
if len(diff) > MAX_DIFF_SIZE:
    diff = diff[:MAX_DIFF_SIZE] + "\n\n[Diff truncated for review]"

# 3. Build the prompt
prompt = f"""
You are an experienced Python code reviewer.
Your role is to act as a mentor reviewing code *after* a commit has been made.

RULES:
- Do NOT write code for the developer
- Do NOT reimplement features
- Do NOT provide ready-made solutions
- Explain issues, risks, and improvement opportunities
- Focus on learning and reasoning, not on final answers

Analyze ONLY the diff below:

{diff}
"""

# 4. Call OpenAI API
response = requests.post(
    "https://api.openai.com/v1/chat/completions",
    headers={
        "Authorization": f"Bearer {OPENAI_API_KEY}",
        "Content-Type": "application/json",
    },
    json={
        "model": "gpt-4.1-mini",
        "temperature": 0.3,
        "messages": [
            {"role": "user", "content": prompt}
        ],
    },
)

review_text = response.json()["choices"][0]["message"]["content"]

# 5. Post comment on the commit
comment_body = textwrap.dedent(f"""
### 🤖 AI Code Review

This comment was automatically generated **after the commit** with a focus on learning and code quality.

---

{review_text}

---

📌 *Apply the suggestions manually before your next commit.*
""")

requests.post(
    f"https://api.github.com/repos/{REPO}/commits/{COMMIT_SHA}/comments",
    headers={
        "Authorization": f"Bearer {GITHUB_TOKEN}",
        "Accept": "application/vnd.github+json",
    },
    json={"body": comment_body},
)

print("GitHub response:", response.status_code)
print(response.text)
