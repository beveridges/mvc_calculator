document.addEventListener("DOMContentLoaded", () => {
  const triggers = document.querySelectorAll(".lightbox-trigger");
  if (!triggers.length) {
    return;
  }

  const overlay = document.createElement("div");
  overlay.className = "lightbox-overlay";
  overlay.innerHTML = `
    <img class="lightbox-overlay-image" alt="" />
    <button type="button" class="lightbox-close" aria-label="Close image">&times;</button>
  `;
  document.body.appendChild(overlay);

  const imageEl = overlay.querySelector(".lightbox-overlay-image");
  const closeBtn = overlay.querySelector(".lightbox-close");

  const close = () => {
    overlay.classList.remove("is-visible");
    imageEl.src = "";
    imageEl.alt = "";
  };

  triggers.forEach((trigger) => {
    trigger.addEventListener("click", (event) => {
      event.preventDefault();
      const fullSrc = trigger.getAttribute("data-full") || trigger.src;
      if (!fullSrc) {
        return;
      }
      imageEl.src = fullSrc;
      imageEl.alt = trigger.alt || "";
      overlay.classList.add("is-visible");
    });
  });

  overlay.addEventListener("click", (event) => {
    if (event.target === overlay || event.target === closeBtn) {
      close();
    }
  });

  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && overlay.classList.contains("is-visible")) {
      close();
    }
  });
});

