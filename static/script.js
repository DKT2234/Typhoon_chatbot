const chat = document.getElementById("chat");
const form = document.getElementById("form");
const input = document.getElementById("msg");
const send = document.getElementById("send");
const clearBtn = document.getElementById("clear");

function addBubble(text, who) {
  const row = document.createElement("div");
  row.className = `row ${who}`;

  // Avatar for bot messages
  if (who === "bot") {
    const avatar = document.createElement("img");
    avatar.className = "avatar";
    avatar.src = "/static/typhoon-avatar.png";
    avatar.alt = "Typhoon";
    row.appendChild(avatar);
  }

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  bubble.textContent = text;

  row.appendChild(bubble);
  chat.appendChild(row);
  chat.scrollTop = chat.scrollHeight;

  return bubble;
}

function setInputEnabled(enabled) {
  send.disabled = !enabled;
  input.disabled = !enabled;
}

clearBtn.addEventListener("click", () => {
  chat.innerHTML = "";
  addBubble("Hello, I’m Typhoon. Ask me about modern fighter jets.", "bot");
  input.focus();
});

// First greeting
addBubble("Hello, I’m Typhoon. Ask me about modern fighter jets.", "bot");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const text = input.value.trim();
  if (!text) return;

  input.value = "";
  addBubble(text, "user");

  setInputEnabled(false);
  const typingBubble = addBubble("Typing…", "bot");

  try {
    const res = await fetch("/chatbot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: text })
    });

    const data = await res.json();
    typingBubble.textContent = (data && data.response) ? data.response : "No response returned.";
  } catch (err) {
    typingBubble.textContent = "Typhoon hit an error: " + err.message;
  } finally {
    setInputEnabled(true);
    input.focus();
  }
});
