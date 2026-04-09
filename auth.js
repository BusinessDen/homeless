// Dreck Suite Authentication
// 30-day localStorage sessions, individual staff accounts

(function () {
  const USERS = {
    admin: "dreck2025",
    conrad: "homeless2026",
    aaron: "homeless2026",
    justin: "homeless2026",
    matt: "homeless2026",
    max: "homeless2026",
    thomas: "homeless2026",
  };

  const SESSION_KEY = "homeless_tracker_session";
  const SESSION_DAYS = 30;

  function getSession() {
    try {
      const raw = localStorage.getItem(SESSION_KEY);
      if (!raw) return null;
      const session = JSON.parse(raw);
      if (Date.now() > session.expires) {
        localStorage.removeItem(SESSION_KEY);
        return null;
      }
      return session;
    } catch {
      return null;
    }
  }

  function setSession(username) {
    const session = {
      user: username,
      created: Date.now(),
      expires: Date.now() + SESSION_DAYS * 24 * 60 * 60 * 1000,
    };
    localStorage.setItem(SESSION_KEY, JSON.stringify(session));
  }

  function showLogin() {
    document.body.innerHTML = "";
    document.body.style.cssText =
      "margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#0a0a0a;font-family:monospace;";

    const box = document.createElement("div");
    box.style.cssText =
      "background:#111;border:1px solid #333;padding:40px;width:300px;";

    box.innerHTML = `
      <div style="color:#e74c3c;font-size:13px;letter-spacing:3px;margin-bottom:24px;">HOMELESS TRACKER</div>
      <input id="auth-user" placeholder="username" style="display:block;width:100%;padding:10px;margin-bottom:12px;background:#0a0a0a;border:1px solid #333;color:#ccc;font-family:monospace;box-sizing:border-box;">
      <input id="auth-pass" type="password" placeholder="password" style="display:block;width:100%;padding:10px;margin-bottom:16px;background:#0a0a0a;border:1px solid #333;color:#ccc;font-family:monospace;box-sizing:border-box;">
      <button id="auth-btn" style="width:100%;padding:10px;background:#e74c3c;color:#fff;border:none;cursor:pointer;font-family:monospace;letter-spacing:1px;">LOGIN</button>
      <div id="auth-error" style="color:#e74c3c;margin-top:12px;font-size:12px;"></div>
    `;
    document.body.appendChild(box);

    const btn = document.getElementById("auth-btn");
    const userInput = document.getElementById("auth-user");
    const passInput = document.getElementById("auth-pass");
    const errorDiv = document.getElementById("auth-error");

    function attempt() {
      const u = userInput.value.trim().toLowerCase();
      const p = passInput.value;
      if (USERS[u] && USERS[u] === p) {
        setSession(u);
        location.reload();
      } else {
        errorDiv.textContent = "Invalid credentials";
        passInput.value = "";
      }
    }

    btn.addEventListener("click", attempt);
    passInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") attempt();
    });
    userInput.focus();
  }

  // Check session on load
  const session = getSession();
  if (!session) {
    if (document.readyState === "loading") {
      document.addEventListener("DOMContentLoaded", showLogin);
    } else {
      showLogin();
    }
  } else {
    // Expose current user
    window.DRECK_USER = session.user;
  }
})();
