const tokenStorageKey = "smartcrm_access_token";
const userStorageKey = "smartcrm_username";
const loginForm = document.querySelector("#login-form");
const usernameInput = document.querySelector("#username");
const passwordInput = document.querySelector("#password");
const submitButton = document.querySelector("#submit-button");
const formMessage = document.querySelector("#form-message");
const workspacePanel = document.querySelector("#workspace-panel");
const signedInUser = document.querySelector("#signed-in-user");
const logoutButton = document.querySelector("#logout-button");
const customerForm = document.querySelector("#customer-form");
const customerList = document.querySelector("#customer-list");
const customerMessage = document.querySelector("#customer-message");
const deviceForm = document.querySelector("#device-form");
const deviceList = document.querySelector("#device-list");
const deviceMessage = document.querySelector("#device-message");
const deviceCustomer = document.querySelector("#device-customer");
const issueDescription = document.querySelector("#issue-description");
const classifyButton = document.querySelector("#classify-button");
const classifyResult = document.querySelector("#classify-result");
let customers = [];
const customerDevices = new Map();
const expandedCustomerIds = new Set();
const customerDeviceErrors = new Map();
let customerDevicesNeedRefresh = false;

class ApiError extends Error {
  constructor(message, code) {
    super(message);
    this.code = code;
  }
}

class SessionExpiredError extends Error {}

async function apiRequest(path, options = {}) {
  const token = sessionStorage.getItem(tokenStorageKey);
  const headers = { ...options.headers };
  if (options.body) headers["Content-Type"] = "application/json";
  if (token) headers.Authorization = `Bearer ${token}`;

  const response = await fetch(path, { ...options, headers });
  if (response.status === 401) {
    clearSession("Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.");
    throw new SessionExpiredError();
  }
  if (response.status === 204) return null;

  const body = await response.json();
  if (!response.ok) {
    throw new ApiError(
      body.error?.message || "Không thể hoàn tất yêu cầu.",
      body.error?.code,
    );
  }
  return body;
}

function showLoggedInState(username) {
  document.body.classList.add("is-authenticated");
  loginForm.hidden = true;
  workspacePanel.hidden = false;
  signedInUser.textContent = username;
  formMessage.textContent = "";
  loadCustomers();
}

function clearSession(message = "") {
  document.body.classList.remove("is-authenticated");
  sessionStorage.removeItem(tokenStorageKey);
  sessionStorage.removeItem(userStorageKey);
  workspacePanel.hidden = true;
  loginForm.hidden = false;
  classifyResult.textContent = "";
  formMessage.textContent = message;
  formMessage.className = "message";
}

function showMessage(element, message, isError = false) {
  element.textContent = message;
  element.className = isError ? "message error" : "message success";
}

function makeButton(label, action, id, className = "record-action") {
  const button = document.createElement("button");
  button.type = "button";
  button.className = className;
  button.textContent = label;
  button.dataset.action = action;
  button.dataset.id = id;
  return button;
}

function renderCustomers() {
  customerList.replaceChildren();
  for (const customer of customers) {
    const item = document.createElement("article");
    item.className = "customer-record";
    const details = document.createElement("div");
    const name = document.createElement("strong");
    name.textContent = customer.full_name;
    const summary = document.createElement("p");
    summary.textContent = `${customer.phone}${customer.address ? ` · ${customer.address}` : ""}`;
    details.append(name, summary);

    const actions = document.createElement("div");
    actions.className = "record-actions";
    const devices = customerDevices.get(customer.customer_id);
    const deviceButton = makeButton(
      devices
        ? `Thiết bị bảo hành: ${countActiveWarranties(devices)}`
        : "Thiết bị",
      "devices",
      customer.customer_id,
    );
    deviceButton.setAttribute("aria-expanded", String(expandedCustomerIds.has(customer.customer_id)));
    deviceButton.setAttribute("aria-controls", `customer-devices-${customer.customer_id}`);
    actions.append(
      deviceButton,
      makeButton("Sửa", "edit", customer.customer_id),
      makeButton("Xóa", "delete", customer.customer_id),
    );

    const header = document.createElement("div");
    header.className = "customer-record-header";
    header.append(details, actions);
    item.append(header);

    const devicePanel = document.createElement("div");
    devicePanel.id = `customer-devices-${customer.customer_id}`;
    devicePanel.className = "customer-device-panel";
    devicePanel.hidden = !expandedCustomerIds.has(customer.customer_id);
    if (!devicePanel.hidden) {
      if (customerDeviceErrors.has(customer.customer_id)) {
        const error = document.createElement("p");
        error.className = "empty-state error-text";
        error.textContent = customerDeviceErrors.get(customer.customer_id);
        const retry = makeButton("Thử lại", "devices-retry", customer.customer_id);
        devicePanel.append(error, retry);
      } else if (!devices) {
        const loading = document.createElement("p");
        loading.className = "empty-state";
        loading.textContent = "Đang tải danh sách thiết bị...";
        devicePanel.append(loading);
      } else {
        renderCustomerDeviceTable(devicePanel, devices);
      }
    }

    item.append(devicePanel);
    customerList.append(item);
  }
  if (!customers.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "Chưa có khách hàng. Hãy thêm hồ sơ đầu tiên.";
    customerList.append(empty);
  }
}

function countActiveWarranties(devices) {
  return devices.filter((device) => {
    const expiry = warrantyExpiry(device);
    return expiry !== null && expiry >= todayDateString();
  }).length;
}

function todayDateString() {
  const today = new Date();
  return [
    today.getFullYear(),
    String(today.getMonth() + 1).padStart(2, "0"),
    String(today.getDate()).padStart(2, "0"),
  ].join("-");
}

function warrantyExpiry(device) {
  if (!device.purchase_date) return null;
  const [year, month, day] = device.purchase_date.split("-").map(Number);
  const targetMonth = month - 1 + device.warranty_months;
  const targetYear = year + Math.floor(targetMonth / 12);
  const normalizedMonth = targetMonth % 12;
  const lastDay = new Date(targetYear, normalizedMonth + 1, 0).getDate();
  const expiryDay = Math.min(day, lastDay);
  return `${targetYear}-${String(normalizedMonth + 1).padStart(2, "0")}-${String(expiryDay).padStart(2, "0")}`;
}

function formatWarranty(device) {
  const expiry = warrantyExpiry(device);
  if (!expiry) return { label: "Chưa xác định · thiếu ngày mua", active: false };
  const date = expiry.split("-").reverse().join("/");
  const active = expiry >= todayDateString();
  return {
    label: `${active ? "Còn bảo hành đến" : "Hết bảo hành"} ${date}`,
    active,
  };
}

function renderCustomerDeviceTable(container, devices) {
  const activeCount = countActiveWarranties(devices);
  const summary = document.createElement("p");
  summary.className = "warranty-summary";
  summary.textContent = `${activeCount}/${devices.length} thiết bị còn bảo hành`;
  container.append(summary);

  if (!devices.length) {
    const empty = document.createElement("p");
    empty.className = "empty-state";
    empty.textContent = "Khách hàng này chưa có thiết bị.";
    container.append(empty);
    return;
  }

  const wrapper = document.createElement("div");
  wrapper.className = "device-table-wrap";
  const table = document.createElement("table");
  table.className = "device-table";
  const header = document.createElement("thead");
  const headerRow = document.createElement("tr");
  for (const label of ["Thiết bị", "Serial/IMEI", "Bảo hành", "Ưu tiên", "Ghi chú"]) {
    const cell = document.createElement("th");
    cell.scope = "col";
    cell.textContent = label;
    headerRow.append(cell);
  }
  header.append(headerRow);

  const body = document.createElement("tbody");
  for (const device of devices) {
    const row = document.createElement("tr");
    const model = document.createElement("td");
    const modelName = document.createElement("strong");
    modelName.textContent = device.model_name;
    const purchase = document.createElement("span");
    purchase.className = "table-secondary";
    purchase.textContent = device.purchase_date
      ? `Mua ngày ${device.purchase_date.split("-").reverse().join("/")}`
      : "Chưa rõ ngày mua";
    model.append(modelName, purchase);

    const serial = document.createElement("td");
    serial.textContent = device.serial_no;
    const warrantyCell = document.createElement("td");
    const warranty = formatWarranty(device);
    const warrantyBadge = document.createElement("span");
    warrantyBadge.className = `status-badge ${warranty.active ? "status-active" : "status-inactive"}`;
    warrantyBadge.textContent = warranty.label;
    const duration = document.createElement("span");
    duration.className = "table-secondary";
    duration.textContent = `${device.warranty_months} tháng`;
    warrantyCell.append(warrantyBadge, duration);

    const priority = document.createElement("td");
    const priorityBadge = document.createElement("span");
    const priorityLabels = {
      CAO: ["Cao", "priority-high"],
      TRUNG_BINH: ["Trung bình", "priority-medium"],
      THAP: ["Thấp", "priority-low"],
    };
    const priorityInfo = priorityLabels[device.priority];
    priorityBadge.className = `status-badge ${priorityInfo ? priorityInfo[1] : "priority-none"}`;
    priorityBadge.textContent = priorityInfo ? priorityInfo[0] : "Chưa có phiếu";
    priority.append(priorityBadge);

    const note = document.createElement("td");
    note.textContent = device.note || "—";
    row.append(model, serial, warrantyCell, priority, note);
    body.append(row);
  }
  table.append(header, body);
  wrapper.append(table);
  container.append(wrapper);
}

function populateCustomerSelect() {
  const previous = deviceCustomer.value;
  deviceCustomer.replaceChildren();
  const empty = document.createElement("option");
  empty.value = "";
  empty.textContent = "Chọn khách hàng";
  deviceCustomer.append(empty);

  for (const customer of customers) {
    const option = document.createElement("option");
    option.value = String(customer.customer_id);
    option.textContent = `${customer.full_name} · ${customer.phone}`;
    deviceCustomer.append(option);
  }
  if (customers.some((customer) => String(customer.customer_id) === previous)) {
    deviceCustomer.value = previous;
  }
  deviceForm.querySelectorAll("input, button[type=submit]").forEach((element) => {
    element.disabled = !deviceCustomer.value;
  });
}

async function loadCustomers() {
  try {
    customers = await apiRequest("/api/customers");
    customerDevices.clear();
    customerDeviceErrors.clear();
    expandedCustomerIds.clear();
    renderCustomers();
    populateCustomerSelect();
    if (deviceCustomer.value) await loadDevices();
  } catch (error) {
    if (!(error instanceof SessionExpiredError)) {
      showMessage(customerMessage, error.message, true);
    }
  }
}

async function loadDevices() {
  deviceList.replaceChildren();
  if (!deviceCustomer.value) return;

  try {
    const devices = await apiRequest(
      `/api/customers/${deviceCustomer.value}/devices`,
    );
    for (const device of devices) {
      const item = document.createElement("article");
      item.className = "record-card";
      const details = document.createElement("div");
      const model = document.createElement("strong");
      model.textContent = device.model_name;
      const summary = document.createElement("p");
      summary.textContent =
        `${device.serial_no} · ${device.warranty_months} tháng bảo hành` +
        (device.purchase_date ? ` · mua ngày ${device.purchase_date}` : "");
      details.append(model, summary);
      const actions = document.createElement("div");
      actions.className = "record-actions";
      actions.append(
        makeButton("Sửa", "edit", device.device_id),
        makeButton("Xóa", "delete", device.device_id),
      );
      item.append(details, actions);
      deviceList.append(item);
    }
    if (!devices.length) {
      const empty = document.createElement("p");
      empty.className = "empty-state";
      empty.textContent = "Khách hàng này chưa có thiết bị.";
      deviceList.append(empty);
    }
  } catch (error) {
    if (!(error instanceof SessionExpiredError)) {
      showMessage(deviceMessage, error.message, true);
    }
  }
}

function resetCustomerForm() {
  customerForm.reset();
  document.querySelector("#customer-id").value = "";
  document.querySelector("#customer-phone").required = true;
  document.querySelector("#customer-phone").placeholder = "";
  document.querySelector("#customer-submit").textContent = "Thêm khách hàng";
  document.querySelector("#customer-cancel").hidden = true;
}

function resetDeviceForm() {
  deviceForm.reset();
  document.querySelector("#device-id").value = "";
  document.querySelector("#device-warranty").value = "12";
  document.querySelector("#device-submit").textContent = "Thêm thiết bị";
  document.querySelector("#device-cancel").hidden = true;
  populateCustomerSelect();
}

function selectScreen(screen) {
  document.querySelectorAll("[data-screen-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.screenPanel !== screen;
  });
  document.querySelectorAll(".tab-button").forEach((button) => {
    const active = button.dataset.screen === screen;
    button.classList.toggle("active", active);
    button.setAttribute("aria-current", active ? "page" : "false");
  });
  if (screen === "devices") loadDevices();
  if (screen === "customers" && customerDevicesNeedRefresh) {
    customerDevicesNeedRefresh = false;
    loadCustomers();
  }
}

document.querySelectorAll(".tab-button").forEach((button) => {
  button.addEventListener("click", () => selectScreen(button.dataset.screen));
});

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

customerForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const id = document.querySelector("#customer-id").value;
  const payload = {
    full_name: document.querySelector("#customer-name").value,
    address: document.querySelector("#customer-address").value || null,
  };
  const phone = document.querySelector("#customer-phone").value.trim();
  if (!id || phone) payload.phone = phone;
  try {
    await apiRequest(id ? `/api/customers/${id}` : "/api/customers", {
      method: id ? "PATCH" : "POST",
      body: JSON.stringify(payload),
    });
    showMessage(customerMessage, id ? "Đã cập nhật khách hàng." : "Đã thêm khách hàng.");
    resetCustomerForm();
    await loadCustomers();
  } catch (error) {
    if (!(error instanceof SessionExpiredError)) {
      showMessage(customerMessage, error.message, true);
    }
  }
});

customerList.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const customer = customers.find(
    (item) => String(item.customer_id) === button.dataset.id,
  );
  if (!customer) return;

  if (button.dataset.action === "devices") {
    if (expandedCustomerIds.has(customer.customer_id)) {
      expandedCustomerIds.delete(customer.customer_id);
      renderCustomers();
    } else {
      expandedCustomerIds.add(customer.customer_id);
      customerDeviceErrors.delete(customer.customer_id);
      renderCustomers();
      if (!customerDevices.has(customer.customer_id)) {
        try {
          const devices = await apiRequest(
            `/api/customers/${customer.customer_id}/devices`,
          );
          customerDevices.set(customer.customer_id, devices);
          renderCustomers();
        } catch (error) {
          if (!(error instanceof SessionExpiredError)) {
            customerDeviceErrors.set(customer.customer_id, error.message);
            renderCustomers();
          }
        }
      }
    }
  } else if (button.dataset.action === "devices-retry") {
    customerDevices.delete(customer.customer_id);
    customerDeviceErrors.delete(customer.customer_id);
    renderCustomers();
    try {
      const devices = await apiRequest(
        `/api/customers/${customer.customer_id}/devices`,
      );
      customerDevices.set(customer.customer_id, devices);
      renderCustomers();
    } catch (error) {
      if (!(error instanceof SessionExpiredError)) {
        customerDeviceErrors.set(customer.customer_id, error.message);
        renderCustomers();
      }
    }
  } else if (button.dataset.action === "edit") {
    document.querySelector("#customer-id").value = customer.customer_id;
    document.querySelector("#customer-name").value = customer.full_name;
    document.querySelector("#customer-phone").value = "";
    document.querySelector("#customer-phone").required = false;
    document.querySelector("#customer-phone").placeholder = "Để trống để giữ nguyên";
    document.querySelector("#customer-address").value = customer.address || "";
    document.querySelector("#customer-submit").textContent = "Lưu thay đổi";
    document.querySelector("#customer-cancel").hidden = false;
    selectScreen("customers");
  } else if (
    button.dataset.action === "delete" &&
    window.confirm(`Xóa khách hàng ${customer.full_name}?`)
  ) {
    try {
      await apiRequest(`/api/customers/${customer.customer_id}`, {
        method: "DELETE",
      });
      showMessage(customerMessage, "Đã xóa khách hàng.");
      await loadCustomers();
    } catch (error) {
      if (!(error instanceof SessionExpiredError)) {
        showMessage(customerMessage, error.message, true);
      }
    }
  }
});

document.querySelector("#customer-cancel").addEventListener("click", resetCustomerForm);
document.querySelector("#customer-refresh").addEventListener("click", loadCustomers);

deviceCustomer.addEventListener("change", () => {
  resetDeviceForm();
  loadDevices();
});

deviceForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  if (!deviceCustomer.value) return;
  const id = document.querySelector("#device-id").value;
  const payload = {
    model_name: document.querySelector("#device-model").value,
    serial_no: document.querySelector("#device-serial").value,
    purchase_date: document.querySelector("#device-purchase-date").value || null,
    warranty_months: Number(document.querySelector("#device-warranty").value),
    note: document.querySelector("#device-note").value,
  };
  const url = id
    ? `/api/devices/${id}`
    : `/api/customers/${deviceCustomer.value}/devices`;
  try {
    await apiRequest(url, {
      method: id ? "PATCH" : "POST",
      body: JSON.stringify(payload),
    });
    customerDevices.delete(Number(deviceCustomer.value));
    customerDevicesNeedRefresh = true;
    showMessage(deviceMessage, id ? "Đã cập nhật thiết bị." : "Đã thêm thiết bị.");
    resetDeviceForm();
    await loadDevices();
  } catch (error) {
    if (!(error instanceof SessionExpiredError)) {
      showMessage(deviceMessage, error.message, true);
    }
  }
});

deviceList.addEventListener("click", async (event) => {
  const button = event.target.closest("button[data-action]");
  if (!button) return;
  const id = button.dataset.id;
  if (button.dataset.action === "edit") {
    try {
      const device = await apiRequest(`/api/devices/${id}`);
      document.querySelector("#device-id").value = device.device_id;
      document.querySelector("#device-model").value = device.model_name;
      document.querySelector("#device-serial").value = device.serial_no;
      document.querySelector("#device-purchase-date").value =
        device.purchase_date || "";
      document.querySelector("#device-warranty").value = device.warranty_months;
      document.querySelector("#device-note").value = device.note || "";
      document.querySelector("#device-submit").textContent = "Lưu thay đổi";
      document.querySelector("#device-cancel").hidden = false;
    } catch (error) {
      if (!(error instanceof SessionExpiredError)) {
        showMessage(deviceMessage, error.message, true);
      }
    }
  } else if (
    button.dataset.action === "delete" &&
    window.confirm("Xóa thiết bị này?")
  ) {
    try {
      await apiRequest(`/api/devices/${id}`, { method: "DELETE" });
      customerDevices.delete(Number(deviceCustomer.value));
      customerDevicesNeedRefresh = true;
      showMessage(deviceMessage, "Đã xóa thiết bị.");
      await loadDevices();
    } catch (error) {
      if (!(error instanceof SessionExpiredError)) {
        showMessage(deviceMessage, error.message, true);
      }
    }
  }
});

document.querySelector("#device-cancel").addEventListener("click", resetDeviceForm);

classifyButton.addEventListener("click", async () => {
  classifyResult.className = "result loading";
  classifyResult.textContent = "Đang gửi yêu cầu...";
  classifyButton.disabled = true;

  try {
    const body = await apiRequest("/api/classify", {
      method: "POST",
      body: JSON.stringify({ issue_desc: issueDescription.value }),
    });
    classifyResult.className = "result success";
    classifyResult.textContent = `Đề xuất: ${body.category_name} · Ưu tiên ${body.priority}`;
  } catch (error) {
    if (!(error instanceof SessionExpiredError)) {
      classifyResult.className = "result error";
      classifyResult.textContent = error.message;
    }
  } finally {
    classifyButton.disabled = false;
  }
});

const existingToken = sessionStorage.getItem(tokenStorageKey);
const existingUsername = sessionStorage.getItem(userStorageKey);
if (existingToken && existingUsername) showLoggedInState(existingUsername);
