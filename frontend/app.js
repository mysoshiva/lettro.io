document.getElementById("letterUpload").addEventListener("change", (event) => {
  const file = event.target.files[0];
  if (!file) return;
  const imagePreview = document.getElementById("imagePreview");
  imagePreview.innerHTML = `<img src="${URL.createObjectURL(file)}" class="img-fluid" />`;
});

document.getElementById("scanBtn").addEventListener("click", async () => {
  const fileInput = document.getElementById("letterUpload");
  const file = fileInput.files[0];
  if (!file) {
    alert("Please upload or capture an image first.");
    return;
  }

  const targetLanguage = document.getElementById("targetLanguage").value;
  const resultsDiv = document.getElementById("results");
  resultsDiv.innerHTML = `<p>Processing... Please wait.</p>`;

  try {
    // Step 1: OCR
    const formData = new FormData();
    formData.append("image", file);

    const ocrResponse = await fetch("http://localhost:8000/ocr", {
      method: "POST",
      body: formData,
    });
    const ocrData = await ocrResponse.json();
    const text = ocrData.text;

    // Step 2: Analyze
    const analyzeResponse = await fetch("http://localhost:8000/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, target_language: targetLanguage }),
    });
    const analysisData = await analyzeResponse.json();
    const analysis = analysisData.analysis;

    // Display results
    resultsDiv.innerHTML = `<pre>${JSON.stringify(analysis, null, 2)}</pre>`;

    // Step 3: Save scan
    await fetch("http://localhost:8000/save_scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, target_language: targetLanguage, analysis: JSON.stringify(analysis) }),
    });
  } catch (error) {
    resultsDiv.innerHTML = `<p class="text-danger">Error: ${error.message}</p>`;
  }
});

// Camera Capture
document.getElementById("captureBtn").addEventListener("click", async () => {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ video: true });
    const video = document.createElement("video");
    video.srcObject = stream;
    video.play();

    const imagePreview = document.getElementById("imagePreview");
    imagePreview.innerHTML = "";
    imagePreview.appendChild(video);

    const captureButton = document.createElement("button");
    captureButton.textContent = "Capture";
    captureButton.className = "btn btn-primary mt-2";
    captureButton.addEventListener("click", () => {
      const canvas = document.createElement("canvas");
      canvas.width = video.videoWidth;
      canvas.height = video.videoHeight;
      const ctx = canvas.getContext("2d");
      ctx.drawImage(video, 0, 0, canvas.width, canvas.height);

      stream.getTracks().forEach(track => track.stop());

      canvas.toBlob((blob) => {
        const file = new File([blob], "captured-image.jpg", { type: "image/jpeg" });
        const fileInput = document.getElementById("letterUpload");
        fileInput.files = [file];
        imagePreview.innerHTML = `<img src="${URL.createObjectURL(file)}" class="img-fluid" />`;
      }, "image/jpeg");
    });

    imagePreview.appendChild(captureButton);
  } catch (error) {
    alert(`Error accessing camera: ${error.message}`);
  }
});

// History
document.getElementById("historyBtn").addEventListener("click", async () => {
  const historyDiv = document.getElementById("historyDiv");
  historyDiv.style.display = historyDiv.style.display === "none" ? "block" : "none";

  const historyList = document.getElementById("historyList");
  historyList.innerHTML = "<p>Loading...</p>";

  try {
    const response = await fetch("http://localhost:8000/history");
    const data = await response.json();
    historyList.innerHTML = "";

    data.history.forEach((scan) => {
      const scanDiv = document.createElement("div");
      scanDiv.className = "card mb-2";
      scanDiv.innerHTML = `
        <div class="card-body">
          <h5>Scan #${scan.id} (${scan.timestamp})</h5>
          <p><strong>Language:</strong> ${scan.target_language}</p>
          <pre>${scan.analysis}</pre>
        </div>
      `;
      historyList.appendChild(scanDiv);
    });
  } catch (error) {
    historyList.innerHTML = `<p class="text-danger">Error: ${error.message}</p>`;
  }
