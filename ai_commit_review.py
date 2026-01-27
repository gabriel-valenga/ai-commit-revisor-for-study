import subprocess
import os
import sys
import requests
import textwrap


def require_env(name):
    value = os.getenv(name)
    if not value:
        print(f"❌ Missing required environment variable: {name}")
        sys.exit(10)
    return value

OPENAI_API_KEY = require_env("OPENAI_API_KEY")
GITHUB_TOKEN = require_env("GITHUB_TOKEN")
REPO = require_env("GITHUB_REPOSITORY")
COMMIT_SHA = require_env("GITHUB_SHA")

def get_openai_response(prompt):
    try:
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
            timeout=30
        )
        response.raise_for_status()
        data = response.json()

        if "choices" not in data or not data["choices"]:
            print("OpenAI returned no choices:", data)
            raise RuntimeError("OpenAI returned no choices")

        return data["choices"][0]["message"]["content"]
    except requests.exceptions.HTTPError as e:
        if e.response is not None:
            print(
                "OpenAI HTTP error:",
                e.response.status_code,
                e.response.text
            )
        raise
    except requests.exceptions.RequestException as e:
        print("OpenAI request failed:", str(e))
        raise
    except Exception as e:
        print("Unexpected error during OpenAI API call:", str(e))
        raise

def run_review():

    try:
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
        review_text = get_openai_response(prompt)

        # 5. Post comment on the commit
        comment_body = textwrap.dedent(f"""
        ### 🤖 AI Code Review

        This comment was automatically generated **after the commit** with a focus on learning and code quality.

        ---

        {review_text}

        ---

        📌 *Apply the suggestions manually before your next commit.*
        """)

        response = requests.post(
            f"https://api.github.com/repos/{REPO}/commits/{COMMIT_SHA}/comments",
            headers={
                "Authorization": f"Bearer {GITHUB_TOKEN}",
                "Accept": "application/vnd.github+json",
            },
            json={"body": comment_body},
        )
        print("GitHub response:", response.status_code)
        response.raise_for_status()
        print(response.text)
    except Exception as e:
        print("Error occurred during review process:", str(e))
        sys.exit(1)

if __name__ == "__main__":
    run_review()
