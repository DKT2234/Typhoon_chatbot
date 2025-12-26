from __future__ import annotations

import os
import re
from typing import List, Dict, Tuple

from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Hugging Face Inference Providers (OpenAI-compatible)
HF_BASE_URL = "https://router.huggingface.co/v1"
HF_TOKEN = os.getenv("HF_TOKEN", "").strip()

# You can set this in Space Settings → Variables
HF_MODEL = os.getenv("HF_MODEL", "google/gemma-2-2b-it").strip()

client = OpenAI(base_url=HF_BASE_URL, api_key=HF_TOKEN)

# Optional knowledge base notes (keep short, rewritten, public info)
try:
    with open("fighter_jet_kb.txt", "r", encoding="utf-8") as f:
        FIGHTER_JET_KB = f.read().strip()
except FileNotFoundError:
    FIGHTER_JET_KB = ""

# In-memory conversation history (per server instance)
conversation: List[str] = []
MAX_TURNS_TO_KEEP = 3  # keep short to reduce truncation risk


def clean_plain_text(text: str) -> str:
    """
    Remove common markdown formatting without deleting content.
    """
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("**", "").replace("__", "").replace("`", "")

    cleaned_lines = []
    for line in text.split("\n"):
        s = line.strip()
        s = re.sub(r"^#{1,6}\s*", "", s)          # headings like ### Title
        s = re.sub(r"^[-*•—–]\s+", "", s)         # bullets like -, *, •
        s = s.lstrip("*_")
        cleaned_lines.append(s)

    # collapse repeated blank lines
    out = []
    for ln in cleaned_lines:
        if ln == "" and out and out[-1] == "":
            continue
        out.append(ln)

    return "\n".join(out).strip()


def build_messages(prompt: str) -> List[Dict[str, str]]:
    recent = conversation[-(MAX_TURNS_TO_KEEP * 2):]
    messages: List[Dict[str, str]] = []

    messages.append({
        "role": "system",
        "content": (
            "You are Typhoon, a specialist assistant focused on modern fighter aircraft "
            "(F-16, F-15EX, Rafale, Gripen, Su-35, J-20, F-35 and more). "
            "Keep answers educational and based on publicly available information. "
            "If details are uncertain or vary by source/configuration, say so clearly. "
            "Do not provide tactical combat instructions.\n\n"
            "Formatting rules:\n"
            "Plain text only. No markdown.\n"
            "Do not use asterisks, underscores, backticks, hashtags, or bullet symbols.\n"
            "If listing items, use numbering like:\n"
            "1. Item: sentence.\n"
            "2. Item: sentence.\n\n"
            "If your response is long, it is OK to continue across multiple messages."
        )
    })

    if FIGHTER_JET_KB:
        messages.append({
            "role": "system",
            "content": "Reference notes (public, simplified):\n" + FIGHTER_JET_KB
        })

    for i, text in enumerate(recent):
        role = "user" if i % 2 == 0 else "assistant"
        messages.append({"role": role, "content": text})

    messages.append({"role": "user", "content": prompt})
    return messages


def call_llm(messages: List[Dict[str, str]], max_tokens: int = 900) -> Tuple[str, str]:
    """
    Calls the HF router chat completions endpoint.
    Returns (reply_text, finish_reason).
    """
    completion = client.chat.completions.create(
        model=HF_MODEL,
        messages=messages,
        max_tokens=max_tokens,
        temperature=0.35,
        top_p=0.9,
    )
    choice = completion.choices[0]
    reply = (choice.message.content or "").strip()
    finish_reason = getattr(choice, "finish_reason", "") or ""
    return reply, finish_reason


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/chatbot", methods=["POST"])
def chatbot():
    if not HF_TOKEN:
        return jsonify({"response": "HF_TOKEN is missing. Add it in Space Settings → Secrets, then restart the Space."}), 500

    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"response": "Please type a message for Typhoon."}), 400

    messages = build_messages(prompt)

    try:
        parts: List[str] = []
        finish = ""

        # Auto-continue up to 3 extra times if the provider cuts output short
        for _ in range(4):  # first answer + up to 3 continues
            reply, finish = call_llm(messages, max_tokens=900)
            reply = clean_plain_text(reply)

            if reply:
                parts.append(reply)

            # If it was cut due to length, ask to continue
            if finish == "length":
                # Add the assistant chunk to the conversation, then request continuation
                messages.append({"role": "assistant", "content": reply or ""})
                messages.append({"role": "user", "content": "continue"})
                continue

            break

        full_reply = "\n\n".join([p for p in parts if p]).strip()

        if not full_reply:
            full_reply = "I didn’t get a usable response that time. Please try again."

        # If we still ended due to length after multiple continues, tell the user
        if finish == "length":
            full_reply += "\n\nNote: Output may still be cut short. Ask 'continue' again."

    except Exception as e:
        return jsonify({"response": f"Typhoon error calling Hugging Face: {e}"}), 500

    conversation.append(prompt)
    conversation.append(full_reply)

    return jsonify({"response": full_reply})


if __name__ == "__main__":
    # Local dev (Spaces uses gunicorn on 7860)
    app.run(host="0.0.0.0", port=5001, debug=True)
