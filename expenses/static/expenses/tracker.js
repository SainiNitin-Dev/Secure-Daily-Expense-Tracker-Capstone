document.querySelectorAll(".password-toggle").forEach((toggle) => {
  const input = document.getElementById(toggle.getAttribute("aria-controls"));
  const label = input.labels[0].textContent.trim().replace(/:$/, "").toLowerCase();
  toggle.hidden = false;
  toggle.setAttribute("aria-label", `Show ${label}`);

  toggle.addEventListener("click", () => {
    const show = input.type === "password";
    input.type = show ? "text" : "password";
    toggle.textContent = show ? "Hide" : "Show";
    toggle.setAttribute("aria-label", `${toggle.textContent} ${label}`);
  });
});

const dateInput = document.querySelector("[data-today] input");
if (dateInput && !dateInput.value) {
  const today = new Date();
  const month = String(today.getMonth() + 1).padStart(2, "0");
  const day = String(today.getDate()).padStart(2, "0");
  dateInput.value = `${today.getFullYear()}-${month}-${day}`;
}

document.querySelector("[data-invalid-form] [aria-invalid='true']")?.focus();

const deleteDialog = document.getElementById("delete-dialog");
if (deleteDialog?.showModal) {
  let expenseForm;
  const deleteDescription = document.getElementById("delete-description");
  document.querySelectorAll("[data-delete]").forEach((form) => {
    form.addEventListener("submit", (event) => {
      event.preventDefault();
      expenseForm = form;
      deleteDescription.textContent = form.dataset.delete;
      deleteDialog.returnValue = "";
      deleteDialog.showModal();
    });
  });
  deleteDialog.addEventListener("close", () => {
    if (deleteDialog.returnValue === "delete") {
      expenseForm.submit();
    }
  });
}
