function renderAnalysis(analysis) {
  const resultsDiv = document.getElementById("results");
  const actionTag = analysis.requires_action ? 'success' : 'warning';
  const actionLabel = analysis.requires_action ? 'Action required' : 'No action required';

  const deadlineText = analysis.deadline && analysis.deadline.date
    ? analysis.deadline.date
    : (analysis.deadline && analysis.deadline.raw_text ? analysis.deadline.raw_text : 'No deadline stated');

  const requiredActions = Array.isArray(analysis.required_actions) && analysis.required_actions.length
    ? analysis.required_actions.map((item) => `<li>${item.action}</li>`).join('')
    : '<li>No immediate action is required.</li>';

  const consequences = analysis.consequences_if_missed || 'No explicit consequence was stated in the letter.';

  resultsDiv.innerHTML = `
    <div class="result-card">
      <h3>${analysis.sender || 'Unknown sender'}</h3>
      <div class="tag ${actionTag}">${actionLabel}</div>
      <p><strong>Type:</strong> ${analysis.letter_type || 'Unknown'}</p>
      <p><strong>Detected language:</strong> ${analysis.detected_language || 'Unknown'}</p>
      <p><strong>Overall confidence:</strong> ${analysis.overall_confidence || 'low'}</p>
    </div>

    <div class="result-card">
      <h4>Summary</h4>
      <p>${analysis.summary}</p>
    </div>

    <div class="result-card">
      <h4>Deadline</h4>
      <p>${deadlineText}</p>
    </div>

    <div class="result-card">
      <h4>Required actions</h4>
      <ul>${requiredActions}</ul>
    </div>

    <div class="result-card">
      <h4>What happens if you miss it?</h4>
      <p>${consequences}</p>
    </div>
  `;
}

async function loadSampleLetters() {
  const select = document.getElementById('sampleLetterSelect');
  try {
    const response = await fetch('http://localhost:8000/sample_letters');
    const data = await response.json();
    select.innerHTML = '';
    data.letters.forEach((filename) => {
      const option = document.createElement('option');
      option.value = filename;
      option.textContent = filename;
      select.appendChild(option);
    });
  } catch (error) {
    select.innerHTML = '<option value="">Could not load samples</option>';
  }
}

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
  resultsDiv.innerHTML = '<p>Processing... Please wait.</p>';

  try {
    const formData = new FormData();
    formData.append("image", file);

    const ocrResponse = await fetch("http://localhost:8000/ocr", {
      method: "POST",
      body: formData,
    });

    if (!ocrResponse.ok) {
      const errorData = await ocrResponse.json();
      throw new Error(errorData.detail || 'OCR failed');
    }

    const ocrData = await ocrResponse.json();
    const text = ocrData.text;

    const analyzeResponse = await fetch("http://localhost:8000/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, target_language: targetLanguage }),
    });

    if (!analyzeResponse.ok) {
      const errorData = await analyzeResponse.json();
      throw new Error(errorData.detail || 'Analysis failed');
    }

    const analysisData = await analyzeResponse.json();
    const analysis = analysisData.analysis;
    renderAnalysis(analysis);

    await fetch("http://localhost:8000/save_scan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, target_language: targetLanguage, analysis: JSON.stringify(analysis) }),
    });
  } catch (error) {
    resultsDiv.innerHTML = `<p class="text-danger">Error: ${error.message}</p>`;
  }
});

document.getElementById("runSampleBtn").addEventListener("click", async () => {
  const filename = document.getElementById("sampleLetterSelect").value;
  const targetLanguage = document.getElementById("targetLanguage").value;
  const resultsDiv = document.getElementById("results");

  if (!filename) {
    resultsDiv.innerHTML = '<p class="text-danger">No sample letter selected.</p>';
    return;
  }

  resultsDiv.innerHTML = '<p>Running sample letter...</p>';

  try {
    const response = await fetch("http://localhost:8000/run_sample", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ filename, target_language: targetLanguage }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Sample execution failed');
    }

    const data = await response.json();
    renderAnalysis(data.analysis);
  } catch (error) {
    resultsDiv.innerHTML = `<p class="text-danger">Error: ${error.message}</p>`;
  }
});

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
});

loadSampleLetters();
