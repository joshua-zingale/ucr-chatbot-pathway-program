const chatContainer = document.getElementById("chat-container");
const sidebarMessages = document.getElementById("sidebar-messages");
const userMessageTextarea = document.getElementById("userMessage");

let conversationId = null;
let isNewConversation = false;


// Detect if this is a new conversation or not (for the sidebar)
const path = window.location.pathname;
if (path.startsWith("/new_conversation/")) {
  isNewConversation = true;
} else if (path.startsWith("/conversation/")) {
  conversationId = path.split("/").pop();
}


async function loadAllConversationsForUser() {
  sidebarMessages.innerHTML = "";

  const res = await fetch("/api/conversations/get_conversations", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
  });

  const conversationIds = await res.json();
  conversationIds.reverse();

  for (const convoId of conversationIds) {
    addSidebarMessage(`Conversation ${convoId}`, convoId);
  }
}


if (!isNewConversation && conversationId) {
  loadConversation(conversationId);
}


loadAllConversationsForUser();

// Send message on Enter key press
userMessageTextarea.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    handleSend(event);
  }
});

// Send message to interface
async function handleSend(e) {
  e.preventDefault();
  const textarea = document.getElementById("userMessage");
  const message = textarea.value.trim();
  if (!message) return;

  appendMessage("user", message);
  addSidebarMessage(message); // this just adds every message to the sidebar - needs to summarize conversations like chatgpt
  textarea.value = "";
   // Create new conversation
  if (isNewConversation) {
    const courseId = Number(path.split("/")[2]);
    const res = await fetch("/api/create_conversation", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ courseId, message }),
    });

    const data = await res.json();
    conversationId = data.conversationId;
    isNewConversation = false;


    window.history.replaceState({}, "", `/conversation/${conversationId}`);

    // Add this conversation to the sidebar
    addSidebarMessage(`Conversation ${conversationId}`, conversationId);

    // Get bot response and show to interface
    const botResponse = await fetchBotReply(conversationId, message);
    appendMessage("bot", botResponse);
  } else {
    await sendMessage(conversationId, message);
    const botResponse = await fetchBotReply(conversationId, message);
    appendMessage("bot", botResponse);
  }
}

function appendMessage(sender, text) {
  const div = document.createElement("div");
  div.classList.add("message", sender);
  div.textContent = text;
  chatContainer.appendChild(div);
  chatContainer.scrollTop = chatContainer.scrollHeight;
}

// Add convo to sidebar
function addSidebarMessage(label, convoId) {
  if (document.querySelector(`[data-convo-id="${convoId}"]`)) return;

  const item = document.createElement("div");
  item.classList.add("conversation-item");
  item.textContent = label;
  item.dataset.convoId = convoId;

  item.addEventListener("click", () => {
    window.history.replaceState({}, "", `/conversation/${convoId}`);
    conversationId = convoId;
    chatContainer.innerHTML = "";
    loadConversation(convoId);
  });

  if (window.location.pathname.endsWith(convoId)) {
    item.classList.add("active");
  }


  sidebarMessages.insertBefore(item, sidebarMessages.firstChild);
}

// FIX
// On click, leads to new conversation page for that conversation
async function loadConversation(id) {
  const res = await fetch(`/api/conversations/${id}`);
  const data = await res.json();

  chatContainer.innerHTML = "";

  data.messages.forEach((msg) => {
    appendMessage(msg.sender === "StudentMessage" ? "user" : "bot", msg.body);
  });
}

// FIX
// Sends a message to LM
async function sendMessage(id, message) {
  await fetch(`/api/conversations/${id}/send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message }),
  });
}

// FIX
// Gets message from LM
async function fetchBotReply(id, userMessage) {
  const res = await fetch(`/api/conversations/${id}/reply`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ userMessage }),
  });

  const data = await res.json();
  return data.reply;
}
