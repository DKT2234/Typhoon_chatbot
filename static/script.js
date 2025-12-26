const chat = document.getElementById("chat");
const form = document.getElementById("form");
const input = document.getElementById("msg");
const send = document.getElementById("send");

function addBubble(text, who) {
  const div = document.createElement("div");
  div.className = `bubble ${who}`;
  div.textContent = text;
  chat.appendChild(div);
  chat.scrollTop = chat.scrollHeight;
}

addBubble("Hello, I’m Typhoon. Ask me about modern fighter jets.", "bot");

form.addEventListener("submit", async (e) => {
  e.preventDefault();

  const text = input.value.trim();
  if (!text) return;

  input.value = "";
  addBubble(text, "user");

  send.disabled = true;
  addBubble("Thinking…", "bot");
  const thinkingBubble = chat.lastChild;

  try {
    const res = await fetch("/chatbot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ prompt: text })
    });

    const data = await res.json();
    thinkingBubble.textContent = data.response || "No response returned.";
  } catch (err) {
    thinkingBubble.textContent = "Typhoon hit an error: " + err.message;
  } finally {
    send.disabled = false;
    input.focus();
  }
});
