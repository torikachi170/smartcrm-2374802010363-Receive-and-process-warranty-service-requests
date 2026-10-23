const tokenStorageKey = "smartcrm_access_token";
const userStorageKey = "smartcrm_username";
const loginForm = document.querySelector("#login-form");
const usernameInput = document.querySelector("#username");
const passwordInput = document.querySelector("#password");
const submitButton = document.querySelector("#submit-button");
const formMessage = document.querySelector("#form-message");
const classifyPanel = document.querySelector("#classify-panel");
const signedInUser = document.querySelector("#signed-in-user");
const logoutButton = document.querySelector("#logout-button");
const issueDescription = document.querySelector("#issue-description");
const classifyButton = document.querySelector("#classify-button");
const classifyResult = document.querySelector("#classify-result");

function showLoggedInState(username) {
  loginForm.hidden = true;
  classifyPanel.hidden = false;
  signedInUser.textContent = username;
  formMessage.textContent = "";
}

function clearSession(message = "") {
  sessionStorage.removeItem(tokenStorageKey);
  sessionStorage.removeItem(userStorageKey);
  classifyPanel.hidden = true;
  loginForm.hidden = false;
  classifyResult.textContent = "";
  formMessage.textContent = message;
  formMessage.className = "message";
}

const existingToken = sessionStorage.getItem(tokenStorageKey);
const existingUsername = sessionStorage.getItem(userStorageKey);
if (existingToken && existingUsername) showLoggedInState(existingUsername);

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  formMessage.textContent = "";
  submitButton.disabled = true;
  submitButton.firstElementChild.textContent = "Đang xác thực...";

  try {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: usernameInput.value.trim(),
        password: passwordInput.value,
      }),
    });
    const body = await response.json();
    if (!response.ok) {
      formMessage.textContent = body.error?.message || "Không đăng nhập được.";
      return;
    }

    sessionStorage.setItem(tokenStorageKey, body.access_token);
    sessionStorage.setItem(userStorageKey, usernameInput.value.trim());
    passwordInput.value = "";
    showLoggedInState(usernameInput.value.trim());
  } catch {
    formMessage.textContent = "Không kết nối được tới hệ thống. Kiểm tra máy chủ rồi thử lại.";
  } finally {
    submitButton.disabled = false;
    submitButton.firstElementChild.textContent = "Đăng nhập";
  }
});

logoutButton.addEventListener("click", () => clearSession("Bạn đã đăng xuất."));

classifyButton.addEventListener("click", async () => {
  classifyResult.className = "result loading";
  classifyResult.textContent = "Đang gửi yêu cầu...";
  classifyButton.disabled = true;

  try {
    const response = await fetch("/api/classify", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${sessionStorage.getItem(tokenStorageKey)}`,
      },
      body: JSON.stringify({ issue_desc: issueDescription.value }),
    });
    const body = await response.json();
    if (response.status === 401) {
      clearSession("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.");
      return;
    }
    if (!response.ok) {
      classifyResult.className = "result error";
      classifyResult.textContent = body.error?.message || "Không thể phân loại mô tả này.";
      return;
    }

    classifyResult.className = "result success";
    classifyResult.textContent = `Đề xuất: ${body.category_name} · Ưu tiên ${body.priority}`;
  } catch {
    classifyResult.className = "result error";
    classifyResult.textContent = "Không kết nối được tới hệ thống. Vui lòng thử lại.";
  } finally {
    classifyButton.disabled = false;
  }
});
