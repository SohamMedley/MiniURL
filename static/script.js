document.addEventListener("DOMContentLoaded", () => {
  const originalUrlInput = document.getElementById("original-url");
  const customTextInput = document.getElementById("custom-text");
  const shortenBtn = document.getElementById("shorten-btn");
  const resultContainer = document.getElementById("result-container");
  const shortenedUrlInput = document.getElementById("shortened-url");
  const copyBtn = document.getElementById("copy-btn");
  const originalUrlDisplay = document.getElementById("original-url-display");
  const createdDate = document.getElementById("created-date");

  // When deployed, update API_URL to point to your backend domain if needed.
  const API_URL = "/api/shorten";

  shortenBtn.addEventListener("click", async () => {
    const originalUrl = originalUrlInput.value.trim();
    const customText = customTextInput.value.trim();

    if (!originalUrl) {
      alert("Please enter a valid URL");
      return;
    }

    try {
      shortenBtn.textContent = "Shortening...";
      shortenBtn.disabled = true;

      const response = await fetch(API_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: originalUrl, custom_text: customText }),
      });

      const data = await response.json();

      if (response.ok) {
        shortenedUrlInput.value = data.short_url;
        originalUrlDisplay.textContent = truncateText(originalUrl, 50);
        createdDate.textContent = new Date().toLocaleString();
        resultContainer.style.display = "flex";
        resultContainer.scrollIntoView({ behavior: "smooth" });
      } else {
        alert(data.error || "Failed to shorten URL");
      }
    } catch (error) {
      console.error("Error:", error);
      alert("An error occurred. Please try again.");
    } finally {
      shortenBtn.textContent = "Shorten";
      shortenBtn.disabled = false;
    }
  });

  copyBtn.addEventListener("click", () => {
    if (navigator.clipboard && window.isSecureContext) {
      navigator.clipboard.writeText(shortenedUrlInput.value).then(() => {
        const originalText = copyBtn.innerHTML;
        copyBtn.innerHTML = '<i class="fas fa-check"></i>';
        setTimeout(() => { copyBtn.innerHTML = originalText; }, 2000);
      }).catch(err => {
        console.error('Failed to copy: ', err);
      });
    } else {
      shortenedUrlInput.select();
      document.execCommand("copy");
      const originalText = copyBtn.innerHTML;
      copyBtn.innerHTML = '<i class="fas fa-check"></i>';
      setTimeout(() => { copyBtn.innerHTML = originalText; }, 2000);
    }
  });

  function truncateText(text, maxLength) {
    return text.length <= maxLength ? text : text.substring(0, maxLength) + "...";
  }

  // Fallback for older browsers (optional)
  if (!window.fetch) {
    window.fetch = (url, options) =>
      new Promise((resolve) => {
        setTimeout(() => {
          const body = JSON.parse(options.body);
          const customText = body.custom_text || generateRandomString(6);
          resolve({
            ok: true,
            json: () => Promise.resolve({
              short_url: `http://your-production-domain.com/go/${customText}`,
              original_url: body.url,
            }),
          });
        }, 1000);
      });
  }

  function generateRandomString(length) {
    const chars = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789";
    let result = "";
    for (let i = 0; i < length; i++) {
      result += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    return result;
  }
});
