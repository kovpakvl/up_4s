document.addEventListener("click", async (event) => {
  const toggle = event.target.closest("[data-toggle-password]");
  if (toggle) {
    const row = toggle.closest("[data-password-row]");
    const value = row.querySelector(".password-value");
    const hidden = value.classList.toggle("is-hidden");
    toggle.textContent = hidden ? "Показать" : "Скрыть";
    return;
  }

  const copy = event.target.closest("[data-copy]");
  if (copy) {
    const row = copy.closest("[data-password-row]");
    const value = row.querySelector(".password-value").dataset.password;
    await navigator.clipboard.writeText(value);
    copy.textContent = "Скопировано";
    setTimeout(() => {
      copy.textContent = "Копировать";
    }, 1200);
  }
});
