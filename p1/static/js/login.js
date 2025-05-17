document.addEventListener("DOMContentLoaded", function () {
  const phoneInput = document.getElementById("phone");

  if (phoneInput) {
    phoneInput.addEventListener("input", function () {
      let raw = phoneInput.value.replace(/\D/g, "");

      if (raw.startsWith("91")) raw = raw.slice(2);
      if (raw.length > 10) raw = raw.slice(0, 10);

      phoneInput.value = raw.length > 0 ? "+91" + raw : "";
    });

    phoneInput.addEventListener("focus", function () {
      if (phoneInput.value.trim() === "") phoneInput.value = "+91";
    });

    phoneInput.addEventListener("blur", function () {
      if (phoneInput.value === "+91") phoneInput.value = "";
    });

    phoneInput.addEventListener("input", function () {
      this.value = this.value.replace(/[^0-9+]/g, '');
    });
  }

  const passwordInput = document.querySelector('input[name="pswd"]');
  if (passwordInput) {
    passwordInput.addEventListener("input", function () {
      this.setCustomValidity(this.value.length < 8 ? 'Password must be at least 8 characters' : '');
    });
  }

  // Show JS alert if there's a message saying "Invalid password"
  const messageElements = document.querySelectorAll(".messages p");
  messageElements.forEach(el => {
    if (el.textContent.trim() === "Invalid password") {
      alert("Invalid password");
    }
  });
});
