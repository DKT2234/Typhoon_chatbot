from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import os
import re

from openai import OpenAI

app = Flask(__name__)
CORS(app)

# Hugging Face routed chat-completions endpoint (OpenAI-compatible)
# Docs: https://router.huggingface.co/v1 :contentReference[oaicite:10]{index=10}
HF_BASE_URL = "https://router.huggingface.co/v1"

# A small, sensible default model for demos (you can change this later).
# "Recommended models" list is in HF docs. :contentReference[oaicite:11]{index=11}
HF_MODEL = os.getenv("HF_MODEL", "google/gemma-2-2b-it")

HF_TOKEN = os.getenv("HF_TOKEN", "")
client = OpenAI(base_url=HF_BASE_URL, api_key=HF_TOKEN)

# Optional knowledge base notes
try:
    with open("fighter_jet_kb.txt", "r", encoding="utf-8") as f:
        FIGHTER_JET_KB = f.read().strip()
except FileNotFoundError:
    FIGHTER_JET_KB = ""

conversation = []
MAX_TURNS_TO_KEEP = 8


def clean_plain_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("**", "").replace("__", "").replace("`", "")

    cleaned_lines = []
    for line in text.split("\n"):
        s = line.strip()
        s = re.sub(r"^#{1,6}\s*", "", s)          # headings like ### Title
        s = re.sub(r"^[-*•—–]\s+", "", s)         # bullets like -, *, •
        s = s.lstrip("*_")
        cleaned_lines.append(s)

    out = []
    for ln in cleaned_lines:
        if ln == "" and out and out[-1] == "":
            continue
        out.append(ln)

    return "\n".join(out).strip()


@app.route("/", methods=["GET"])
def home():
    return render_template("index.html")


@app.route("/chatbot", methods=["POST"])
def chatbot():
    if not HF_TOKEN:
        return jsonify({"response": "Server is missing HF_TOKEN. Add it in Space Settings → Secrets."}), 500

    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()
    if not prompt:
        return jsonify({"response": "Please type a message for Typhoon."}), 400

    recent = conversation[-(MAX_TURNS_TO_KEEP * 2):]
    messages = []

    # Typhoon identity + safety + formatting
    messages.append({
        "role": "system",
        "content": (
            "You are Typhoon, a specialist assistant focused on modern fighter aircraft "
            "(F-16, F-15EX, Rafale, Gripen, Su-35, J-20, F-35 and more). "
            "Keep answers educational and based on publicly available information. "
            "If details are uncertain or vary by source/configuration, say so clearly. "
            "Do not provide tactical combat instructions.\n\n"
            "Formatting rules:\n"
            "Plain text only.\n"
            "No markdown.\n"
            "Do not use asterisks (* or **), underscores, backticks, hashtags, or bullet symbols.\n"
            "If you list items, use numbering like:\n"
            "1. Item: sentence.\n"
            "2. Item: sentence."
        )
    })

    if FIGHTER_JET_KB:
        messages.append({
            "role": "system",
            "content": "Reference notes (public, simplified):\n" + FIGHTER_JET_KB
        })

    # Conversation memory
    for i, text in enumerate(recent):
        role = "user" if i % 2 == 0 else "assistant"
        messages.append({"role": role, "content": text})

    messages.append({"role": "user", "content": prompt})

    try:
        completion = client.chat.completions.create(
            model=HF_MODEL,
            messages=messages,
            max_tokens=220,
            temperature=0.35,
            top_p=0.9,
        )
        reply = (completion.choices[0].message.content or "").strip()
        reply = clean_plain_text(reply)
    except Exception as e:
        return jsonify({"response": f"Typhoon error calling Hugging Face: {e}"}), 500

    conversation.append(prompt)
    conversation.append(reply)
    return jsonify({"response": reply})


if __name__ == "__main__":
    # Local dev only (Spaces uses gunicorn)
    app.run(host="0.0.0.0", port=5001, debug=True)
