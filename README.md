# Typhoon

Typhoon is a web-based chatbot focused on modern fighter aircraft (f-16, f-15ex, rafale, gripen, su-35, j-20, f-35 and more). it runs as a public demo on hugging face spaces and uses a hosted foundation model via hugging face inference providers.

The goal of this project is to show an end-to-end ai application: a clean chat interface, a flask backend, model integration, and a deployable setup.

## live demo
hugging face space: https://huggingface.co/spaces/DKT2234/Typhoon


## project structure
templates/
- index.html

static/
- style.css
- script.js
- images (avatar/background)

app.py
- flask server + chatbot route

dockerfile
- container build for hugging face spaces

requirements.txt
- python dependencies

fighter_jet_kb.txt
- optional rewritten notes (public info)

## quick start (local)
requirements
- python 3.10+
- pip
