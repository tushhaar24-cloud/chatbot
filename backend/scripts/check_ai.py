"""Verify the AI provider credentials and list available models.

    python -m scripts.check_ai

This is a diagnostic, not application code - the real integration lands in
app/services/ai_service.py in Milestone 6. Running it now answers three
questions before any of that exists:

    1. Is AI_API_KEY valid?
    2. Is AI_MODEL a name the provider still serves?
    3. What does a real chat-completion response look like?

It talks to the provider over plain HTTP with httpx. No provider SDK: per
BRD rule 8, understand the wire format first.
"""

import sys

import httpx

from app.core.config import settings


def main() -> int:
    if not settings.AI_API_KEY:
        print("AI_API_KEY is empty in backend/.env - nothing to check.")
        return 1

    headers = {"Authorization": f"Bearer {settings.AI_API_KEY}"}
    print(f"provider : {settings.AI_PROVIDER}")
    print(f"base_url : {settings.AI_BASE_URL}")
    print(f"model    : {settings.AI_MODEL}\n")

    with httpx.Client(base_url=settings.AI_BASE_URL, timeout=settings.AI_TIMEOUT_SECONDS) as client:
        # --- 1. Which models does this key have access to? ---
        try:
            resp = client.get("/models", headers=headers)
        except httpx.RequestError as exc:
            print(f"NETWORK ERROR: cannot reach {settings.AI_BASE_URL} ({exc.__class__.__name__})")
            return 1

        if resp.status_code == 401:
            print("HTTP 401 - the API key was rejected. Check AI_API_KEY in backend/.env.")
            return 1
        if resp.status_code != 200:
            print(f"HTTP {resp.status_code} listing models: {resp.text[:300]}")
            return 1

        model_ids = sorted(m["id"] for m in resp.json().get("data", []))
        print(f"{len(model_ids)} models available to this key:")
        for mid in model_ids:
            marker = "  <-- AI_MODEL" if mid == settings.AI_MODEL else ""
            print(f"  {mid}{marker}")

        if settings.AI_MODEL not in model_ids:
            print(f"\nWARNING: AI_MODEL={settings.AI_MODEL!r} is not in that list.")
            print("Pick one from above and set AI_MODEL in backend/.env.")
            return 1

        # --- 2. One real chat completion, in the shape Milestone 6 will use ---
        print("\nSending a test chat completion...")
        payload = {
            "model": settings.AI_MODEL,
            "messages": [
                {"role": "system", "content": "You are a helpful AI assistant. Be concise."},
                {"role": "user", "content": "Reply with exactly: connection working"},
            ],
            "temperature": settings.AI_TEMPERATURE,
            "max_tokens": settings.AI_MAX_TOKENS,
        }

        try:
            resp = client.post("/chat/completions", headers=headers, json=payload)
        except httpx.TimeoutException:
            print(f"TIMEOUT after {settings.AI_TIMEOUT_SECONDS}s - this is BRD FR-10's 'AI timeout'.")
            return 1

        if resp.status_code == 429:
            print("HTTP 429 - rate limited. Free tiers cap requests per minute; wait and retry.")
            return 1
        if resp.status_code != 200:
            print(f"HTTP {resp.status_code}: {resp.text[:400]}")
            return 1

        body = resp.json()
        print(f"\nreply  : {body['choices'][0]['message']['content']!r}")
        print(f"finish : {body['choices'][0]['finish_reason']}")

        # Token usage is what BRD section 26 asks us to log for every AI call.
        usage = body.get("usage", {})
        print(
            f"tokens : prompt={usage.get('prompt_tokens')} "
            f"completion={usage.get('completion_tokens')} "
            f"total={usage.get('total_tokens')}"
        )

    print("\nOK - credentials valid and the model responds.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
