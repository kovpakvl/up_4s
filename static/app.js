document.addEventListener("click", async (event) => {
    const copyButton = event.target.closest("[data-copy]");
    if (copyButton) {
        const target = document.querySelector(copyButton.dataset.copy);
        if (!target) return;
        const value = target.value || target.textContent;
        await navigator.clipboard.writeText(value.trim());
        copyButton.textContent = "Скопировано";
        setTimeout(() => {
            copyButton.textContent = copyButton.classList.contains("primary-button")
                ? "Копировать пароль"
                : "Копировать";
        }, 1400);
    }

    const toggleButton = event.target.closest("[data-toggle-password]");
    if (toggleButton) {
        const target = document.querySelector(toggleButton.dataset.togglePassword);
        if (!target) return;
        const hidden = target.type === "password";
        target.type = hidden ? "text" : "password";
        toggleButton.textContent = hidden ? "Скрыть" : "Показать";
    }
});
