"""Post one focused OpenAI-powered review comment for the current pull request."""

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path


MAX_DIFF_CHARS = 100_000
MARKER = "<!-- ai-pr-review -->"


def request_json(url, *, method="GET", payload=None, headers=None, parse_json=True):
    request_headers = {"Accept": "application/vnd.github+json"}
    request_headers.update(headers or {})
    data = json.dumps(payload).encode() if payload is not None else None
    request = urllib.request.Request(url, data=data, headers=request_headers, method=method)
    with urllib.request.urlopen(request, timeout=60) as response:
        body = response.read().decode()
        if not body:
            return None
        return json.loads(body) if parse_json else body


def github_api(path, *, method="GET", payload=None, accept=None, parse_json=True):
    token = os.environ["GITHUB_TOKEN"]
    headers = {"Authorization": f"Bearer {token}", "X-GitHub-Api-Version": "2022-11-28"}
    if accept:
        headers["Accept"] = accept
    return request_json(
        f"https://api.github.com{path}",
        method=method,
        payload=payload,
        headers=headers,
        parse_json=parse_json,
    )


def response_text(response):
    return "".join(
        part.get("text", "")
        for item in response.get("output", [])
        for part in item.get("content", [])
        if part.get("type") == "output_text"
    )


def review_diff(instructions, diff):
    api_key = os.environ["OPENAI_API_KEY"]
    prompt = f"""{instructions}

Return valid JSON only, matching this exact shape:
{{"summary":"one sentence", "findings":[{{"priority":"P0|P1|P2", "file":"path", "line":1, "title":"short title", "body":"explanation and concrete fix"}}]}}

The line must be a line in the new version of a changed file. Here is the PR diff:

{diff}"""
    return request_json(
        "https://api.openai.com/v1/responses",
        method="POST",
        payload={
            "model": os.getenv("OPENAI_MODEL", "gpt-5.6-terra"),
            "input": prompt,
            "store": False,
        },
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
    )


def format_comment(review, sha):
    findings = review.get("findings", [])
    heading = "## AI PR review"
    if not findings:
        return f"{MARKER}\n{heading}\n\nNo actionable issues found in `{sha[:7]}`."

    lines = [MARKER, heading, "", review.get("summary", "Actionable findings:"), ""]
    for finding in findings:
        priority = finding.get("priority", "P2")
        file_name = finding.get("file", "unknown file")
        line = finding.get("line", "?")
        title = finding.get("title", "Issue")
        body = finding.get("body", "")
        lines.extend([f"### {priority}: {title}", f"`{file_name}:{line}`", body, ""])
    return "\n".join(lines).strip()


def upsert_comment(repository, pull_number, body):
    comments = github_api(f"/repos/{repository}/issues/{pull_number}/comments?per_page=100")
    existing = next((comment for comment in comments if MARKER in comment["body"]), None)
    if existing:
        github_api(
            f"/repos/{repository}/issues/comments/{existing['id']}",
            method="PATCH",
            payload={"body": body},
        )
    else:
        github_api(
            f"/repos/{repository}/issues/{pull_number}/comments",
            method="POST",
            payload={"body": body},
        )


def main():
    if not os.getenv("OPENAI_API_KEY"):
        print("OPENAI_API_KEY is not configured; skipping AI review.")
        return 0

    event = json.loads(Path(os.environ["GITHUB_EVENT_PATH"]).read_text())
    pull_request = event["pull_request"]
    repository = event["repository"]["full_name"]
    pull_number = pull_request["number"]
    diff_url = f"/repos/{repository}/pulls/{pull_number}"
    diff = github_api(
        diff_url, accept="application/vnd.github.v3.diff", parse_json=False
    )
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n\n[Diff truncated due to review size limit.]"

    instructions = Path(".github/ai-review-instructions.md").read_text()
    raw_review = response_text(review_diff(instructions, diff))
    try:
        review = json.loads(raw_review)
    except json.JSONDecodeError as error:
        print(f"The model returned invalid review JSON: {error}", file=sys.stderr)
        return 1
    upsert_comment(repository, pull_number, format_comment(review, pull_request["head"]["sha"]))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (KeyError, urllib.error.HTTPError, urllib.error.URLError) as error:
        print(f"AI PR review failed: {error}", file=sys.stderr)
        raise SystemExit(1)
