---
title: Typhoon
sdk: docker
app_port: 7860
---

Typhoon is a web chatbot focused on modern fighter aircraft (F-16, F-15EX, Rafale, Gripen, Su-35, J-20, F-35 and more). It’s designed to give clear, educational answers based on public information, with sensible caveats where details vary by source or configuration.

How it works
The site is a simple web interface served by a Flask backend.
When you send a message, the backend calls a hosted language model (configured via environment variables) and returns the response to the browser.

Project layout
templates/
  index.html
static/
  style.css
  script.js
app.py
requirements.txt
Dockerfile
fighter_jet_kb.txt

Local development
1. Install dependencies
python3.10 -m pip install -r requirements.txt

2. Run the server
python3.10 app.py

3. Open the website
http://127.0.0.1:5001

Notes
- Port 5001 is used in local development to avoid macOS conflicts with port 5000.
- The Hugging Face Space runs on port 7860 inside Docker (that is the default for Spaces).

Hugging Face Spaces deployment
1. Create a Space using Docker
Create a new Space on Hugging Face and choose Docker.

2. Add required secrets
In the Space settings, add a Secret:
HF_TOKEN = your Hugging Face token value (it usually starts with hf_...)

If you are using a configurable model name, you can also set:
HF_MODEL = a model id (example: google/gemma-2-2b-it)

3. Push the repo to the Space
git push hf main

Updating the fighter aircraft notes
Edit fighter_jet_kb.txt with short, rewritten notes. Wikipedia is fine as a reference, but avoid pasting large sections verbatim. Keep it factual and add caveats when specs are uncertain or disputed.

Then commit and push:
git add fighter_jet_kb.txt
git commit -m "Update fighter aircraft notes"
git push hf main
