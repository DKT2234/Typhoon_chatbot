from flask import Flask, request, render_template, jsonify
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# Ollama chat endpoint (local service)
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
OLLAMA_MODEL = "typhoon"  # the model you created with `ollama create typhoon`

# Load knowledge base notes (optional but recommended)
try:
    with open("fighter_jet_kb.txt", "r", encoding="utf-8") as f:
        FIGHTER_JET_KB = f.read().strip()
except FileNotFoundError:
    FIGHTER_JET_KB = ""

# In-memory chat history for this server process
conversation = []
MAX_TURNS_TO_KEEP = 8  # roughly user+assistant pairs

@app.route("/", methods=["GET"])
def home():
    # Serve the webpage (HTML file in templates/)
    return render_template("index.html")

@app.route("/chatbot", methods=["POST"])
def chatbot():
    # 1) Read the message from the browser
    data = request.get_json(silent=True) or {}
    prompt = (data.get("prompt") or "").strip()

    if not prompt:
        return jsonify({"response": "Please type a message for Typhoon."}), 400

    # 2) Keep only the recent conversation (prevents unlimited growth)
    recent = conversation[-(MAX_TURNS_TO_KEEP * 2):]

    # 3) Build a message list in Ollama’s chat format
    messages = []

    # Put knowledge base in a system message so it influences replies
    if FIGHTER_JET_KB:
        messages.append({
            "role": "system",
            "content": "Reference notes (public, simplified):\n" + FIGHTER_JET_KB
        })

    # Add previous user/assistant turns
    for i, text in enumerate(recent):
        role = "user" if i % 2 == 0 else "assistant"
        messages.append({"role": role, "content": text})

    # Add the current user prompt
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False
    }

    # 4) Send the request to Ollama and read the reply
    try:
        r = requests.post(OLLAMA_URL, json=payload, timeout=120)
        r.raise_for_status()
        out = r.json()
        reply = out["message"]["content"].strip()
    except Exception as e:
        return jsonify({"response": f"Typhoon couldn’t reach Ollama: {e}"}), 500

    # 5) Save the new turn so the next message has context
    conversation.append(prompt)
    conversation.append(reply)

    # 6) Return JSON to the browser
    return jsonify({"response": reply})

if __name__ == "__main__":
    # host=0.0.0.0 helps for Cloud IDE / containers
    app.run(host="0.0.0.0", port=5001, debug=True)
