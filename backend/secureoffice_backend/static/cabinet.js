// SecureOffice — браузерный кабинет сотрудника

// ─── Переключатель темы ────────────────────────────────────────────────
(function () {
  const STORAGE_KEY = "secureoffice-theme";
  const root = document.documentElement;

  const detectActive = () => {
    const saved = root.getAttribute("data-theme");
    if (saved === "light" || saved === "dark") return saved;
    return window.matchMedia("(prefers-color-scheme: light)").matches ? "light" : "dark";
  };

  const refreshLabels = () => {
    const active = detectActive();
    document.querySelectorAll("[data-theme-label-dark]").forEach((el) => {
      el.hidden = active !== "dark";
    });
    document.querySelectorAll("[data-theme-label-light]").forEach((el) => {
      el.hidden = active !== "light";
    });
  };

  document.addEventListener("click", (event) => {
    const toggle = event.target.closest("[data-theme-toggle]");
    if (!toggle) return;
    const next = detectActive() === "dark" ? "light" : "dark";
    root.setAttribute("data-theme", next);
    try {
      localStorage.setItem(STORAGE_KEY, next);
    } catch (e) { /* localStorage не доступен */ }
    refreshLabels();
  });

  refreshLabels();
})();


document.addEventListener("click", async (event) => {
  const toggle = event.target.closest("[data-toggle-password]");
  if (toggle) {
    const row = toggle.closest("[data-password-row]");
    const value = row.querySelector(".password-value");
    const hidden = value.classList.toggle("is-hidden");
    toggle.textContent = hidden ? "Показать" : "Скрыть";
    if (!hidden) {
      setTimeout(() => {
        value.classList.add("is-hidden");
        toggle.textContent = "Показать";
      }, 10000);
    }
    return;
  }

  const copy = event.target.closest("[data-copy]");
  if (copy) {
    const row = copy.closest("[data-password-row]");
    const value = row.querySelector(".password-value").dataset.password;
    try {
      await navigator.clipboard.writeText(value);
      copy.textContent = "Скопировано";
    } catch {
      copy.textContent = "Не удалось";
    }
    setTimeout(() => {
      copy.textContent = "Копировать";
    }, 1400);
  }
});

// Полоска стойкости пароля в форме записи
(function () {
  const input = document.getElementById("password");
  const meter = document.getElementById("strength");
  if (!input || !meter) return;

  const update = () => {
    const value = input.value || "";
    let score = 0;
    if (value.length >= 8) score++;
    if (value.length >= 12) score++;
    if (value.length >= 16) score++;
    let classes = 0;
    if (/[a-z]/.test(value)) classes++;
    if (/[A-Z]/.test(value)) classes++;
    if (/\d/.test(value)) classes++;
    if (/[^A-Za-z0-9]/.test(value)) classes++;
    score += Math.max(0, classes - 1);
    score = Math.min(5, Math.max(0, score));
    meter.dataset.score = String(score);
  };
  input.addEventListener("input", update);
  update();
})();
