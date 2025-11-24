console.log("App.js loaded - version 2.0");

const $ = (id) => document.getElementById(id);

const authPanel = $("auth");
const chatPanel = $("chat");
const messagesDiv = $("messages");
const usernameInput = $("username");
const passwordInput = $("password");
const authMsg = $("authMsg");

const signupBtn = $("signupBtn");
const loginBtn = $("loginBtn");
const logoutBtn = $("logoutBtn");
const clearBtn = $("clearBtn");
const chatInput = $("chatInput");
const sendBtn = $("sendBtn");

console.log("Clear button element:", clearBtn);

const API = location.origin + "/api";
let token = localStorage.getItem("token") || "";
let ws;
let isLoadingMessages = false; // Prevent multiple simultaneous loads

// Clear error message when user starts typing
usernameInput.addEventListener("input", () => {
  authMsg.textContent = "";
});
passwordInput.addEventListener("input", () => {
  authMsg.textContent = "";
});

function showAuth() {
  authPanel.classList.remove("hidden");
  chatPanel.classList.add("hidden");
  // Clear messages when returning to auth screen
  messagesDiv.innerHTML = "";
}

function showChat() {
  authPanel.classList.add("hidden");
  chatPanel.classList.remove("hidden");
}

async function callAPI(path, method = "GET", body) {
  const headers = {"Content-Type": "application/json"};
  if (token) headers["Authorization"] = "Bearer " + token;
  const res = await fetch(API + path, {
    method, headers, body: body ? JSON.stringify(body) : undefined
  });
  if (!res.ok) {
    // If unauthorized, clear token and show auth screen
    if (res.status === 401) {
      token = "";
      localStorage.removeItem("token");
      localStorage.removeItem("currentUser");
      showAuth();
    }
    // Try to get error detail from response
    let errorMessage = "HTTP " + res.status;
    try {
      const errorData = await res.json();
      if (errorData && errorData.detail) {
        errorMessage = errorData.detail;
      }
    } catch (parseError) {
      // If JSON parsing fails, use default HTTP status message
    }
    throw new Error(errorMessage);
  }
  return res.json();
}

function addMessage(m) {
  // Ensure message has an ID
  if (!m.id) {
    console.error("Message missing ID, cannot add:", m);
    return;
  }
  
  // Prevent duplicate messages - check if message already exists
  const existingMsg = messagesDiv.querySelector(`[data-message-id="${m.id}"]`);
  if (existingMsg) {
    console.log("Skipping duplicate message ID:", m.id, "Content:", m.content.substring(0, 50));
    return; // Message already displayed, skip
  }
  
  console.log("Adding NEW message ID:", m.id, "from:", m.username, "Content:", m.content.substring(0, 50));
  const el = document.createElement("div");
  el.className = "message" + (m.is_bot ? " bot" : "");
  el.dataset.messageId = m.id;
  
  const meta = document.createElement("div");
  meta.className = "meta";
  meta.textContent = `${m.username || "unknown"} • ${new Date(m.created_at).toLocaleString()}`;
  
  const body = document.createElement("div");
  body.className = "message-body";
  body.textContent = m.content;
  
  el.appendChild(meta);
  el.appendChild(body);
  messagesDiv.appendChild(el);
  messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function loadMessages() {
  if (isLoadingMessages) {
    console.log("loadMessages() already in progress, skipping");
    return;
  }
  
  console.log("loadMessages() called");
  isLoadingMessages = true;
  
  try {
    const data = await callAPI("/messages");
    console.log("Received", data.messages.length, "messages from API");
    
    // Only clear and reload if we have no messages currently displayed
    // This prevents duplicate messages when WebSocket is already updating in real-time
    const currentMessageCount = messagesDiv.querySelectorAll('[data-message-id]').length;
    console.log("Currently displaying", currentMessageCount, "messages");
    
    if (currentMessageCount === 0) {
      // First load - clear and add all messages
      console.log("First load - clearing and adding all messages");
      messagesDiv.innerHTML = "";
      for (const m of data.messages) addMessage(m);
    } else {
      // Already have messages - only add new ones that don't exist
      console.log("Incremental load - checking for new messages");
      for (const m of data.messages) {
        const exists = messagesDiv.querySelector(`[data-message-id="${m.id}"]`);
        if (!exists) {
          console.log("Adding missing message ID:", m.id);
          addMessage(m);
        }
      }
    }
  } finally {
    isLoadingMessages = false;
  }
}

function connectWS() {
  // Prevent multiple WebSocket connections
  if (ws && (ws.readyState === WebSocket.CONNECTING || ws.readyState === WebSocket.OPEN)) {
    console.log("WebSocket already connected, skipping");
    return;
  }
  
  console.log("Creating new WebSocket connection");
  const proto = location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${proto}://${location.host}/ws`);
  
  ws.onopen = () => {
    console.log("WebSocket connected");
  };
  
  ws.onmessage = (ev) => {
    try {
      const data = JSON.parse(ev.data);
      console.log("WebSocket message received:", data.type);
      if (data.type === "message") {
        addMessage(data.message);
      }
    } catch (e) {
      console.error("WebSocket message parse error:", e);
    }
  };
  
  ws.onclose = () => {
    console.log("WebSocket closed");
    ws = null;
    // Only try to reconnect if user is still logged in
    if (token && localStorage.getItem("token")) {
      console.log("Attempting to reconnect in 2 seconds...");
      setTimeout(connectWS, 2000);
    }
  };
  
  ws.onerror = (error) => {
    console.error("WebSocket error:", error);
  };
}



signupBtn.onclick = async () => {
  try {
    const username = usernameInput.value.trim();
    const password = passwordInput.value.trim();
    
    // Validate inputs
    if (!username || username.length < 3) {
      authMsg.textContent = "Username must be at least 3 characters long";
      return;
    }
    if (!password || password.length < 6) {
      authMsg.textContent = "Password must be at least 6 characters long";
      return;
    }
    
    authMsg.textContent = "Creating account...";
    const out = await callAPI("/signup", "POST", {
      username: username,
      password: password
    });
    token = out.token;
    localStorage.setItem("token", token);
    localStorage.setItem("currentUser", username);
    authMsg.textContent = "Success! Loading chat...";
    await loadMessages();
    connectWS();
    showChat();
  } catch (e) {
    authMsg.textContent = e.message;
  }
};

loginBtn.onclick = async () => {
  try {
    const username = usernameInput.value.trim();
    const password = passwordInput.value.trim();
    
    // Validate inputs
    if (!username || !password) {
      authMsg.textContent = "Please enter your username and password as both are compulsory";
      return;
    }
    
    authMsg.textContent = "Logging in...";
    const out = await callAPI("/login", "POST", {
      username: username,
      password: password
    });
    token = out.token;
    localStorage.setItem("token", token);
    localStorage.setItem("currentUser", username);
    authMsg.textContent = "Success! Loading chat...";
    await loadMessages();
    connectWS();
    showChat();
  } catch (e) {
    authMsg.textContent = e.message;
  }
};

logoutBtn.onclick = () => {
  token = "";
  localStorage.removeItem("token");
  localStorage.removeItem("currentUser");
  // Close WebSocket connection
  if (ws) {
    ws.close();
    ws = null;
  }
  showAuth();
};

if (clearBtn) {
  clearBtn.onclick = async () => {
    console.log("Clear button clicked!");
    if (!confirm("Are you sure you want to clear all messages? This cannot be undone.")) {
      console.log("User cancelled clear");
      return;
    }
    try {
      console.log("Attempting to clear messages...");
      const result = await callAPI("/messages", "DELETE");
      console.log("Clear successful:", result);
      messagesDiv.innerHTML = "";
      // Reload messages to ensure sync
      await loadMessages();
    } catch (e) {
      console.error("Clear failed:", e);
      alert("Failed to clear messages: " + e.message);
    }
  };
} else {
  console.error("Clear button not found!");
}

sendBtn.onclick = async () => {
  const text = chatInput.value.trim();
  if (!text) return;
  chatInput.value = "";
  await callAPI("/messages", "POST", {content: text});
};

if (token) {
  loadMessages().then(()=>{
    connectWS();
    showChat();
  }).catch(()=>showAuth());
} else {
  showAuth();
}
