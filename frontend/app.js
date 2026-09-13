const API_BASE = (() => {
  const host = window.location.hostname;
  if (host === 'localhost' || host === '127.0.0.1' || host === '0.0.0.0') {
    return 'http://localhost:8000';
  }

  if (window.location.origin.includes(':8080')) {
    return window.location.origin.replace(/:8080$/, ':8000');
  }

  return 'http://localhost:8000';
})();

function renderAnalysis(analysis) {
  const resultsDiv = document.getElementById("results");
  const actionTag = analysis.requires_action ? 'action' : 'clear';
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

function renderSelectedFile(files) {
  const preview = document.getElementById("imagePreview");
  const selectedFiles = Array.from(files || []);

  if (!selectedFiles.length) {
    preview.className = 'image-preview empty-state';
    preview.innerHTML = `
      <div class="placeholder-copy">
        <strong>No document selected</strong>
        <span>PDF, JPG, PNG, WebP, TIFF</span>
      </div>
    `;
    return;
  }

  preview.className = 'image-preview';
  if (selectedFiles.length === 1) {
    const file = selectedFiles[0];
    const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf');

    if (isPdf) {
      preview.innerHTML = `
        <div class="file-card">
          <span class="file-type">PDF</span>
          <p class="file-name">${file.name}</p>
        </div>
      `;
      return;
    }

    preview.innerHTML = `<img src="${URL.createObjectURL(file)}" class="img-fluid" alt="Selected letter preview" />`;
    return;
  }

  const fileList = selectedFiles.map((file) => `
    <div class="file-card">
      <span class="file-type">${file.name.toLowerCase().endsWith('.pdf') ? 'PDF' : 'IMG'}</span>
      <p class="file-name">${file.name}</p>
    </div>
  `).join('');

  preview.innerHTML = `<div style="width:100%;display:flex;flex-direction:column;gap:10px;">${fileList}</div>`;
}

function validateUploadSelection(files) {
  const selectedFiles = Array.from(files || []);
  const maxFiles = 30;
  const maxTotalBytes = 20 * 1024 * 1024;

  if (!selectedFiles.length) {
    throw new Error('Please choose at least one file.');
  }

  if (selectedFiles.length > maxFiles) {
    throw new Error(`You can upload up to ${maxFiles} files at a time.`);
  }

  const totalBytes = selectedFiles.reduce((sum, file) => sum + (file.size || 0), 0);
  if (totalBytes > maxTotalBytes) {
    throw new Error(`Total file size must be under ${maxTotalBytes / (1024 * 1024)} MB.`);
  }

  const supported = ['pdf', 'png', 'jpg', 'jpeg', 'webp', 'tif', 'tiff'];
  const invalid = selectedFiles.filter((file) => {
    const extension = file.name.split('.').pop().toLowerCase();
    const type = file.type.toLowerCase();
    return !supported.includes(extension) && !type.startsWith('image/') && type !== 'application/pdf';
  });

  if (invalid.length) {
    throw new Error('Only PDF, PNG, JPG, JPEG, WebP, TIFF files are supported.');
  }
}

async function loadSampleLetters() {
  const select = document.getElementById('sampleLetterSelect');
  try {
    const response = await fetch(`${API_BASE}/sample_letters`);
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
  const files = event.target.files;
  if (!files || !files.length) {
    renderSelectedFile([]);
    return;
  }
  renderSelectedFile(files);
});

document.getElementById("scanBtn").addEventListener("click", async () => {
  const fileInput = document.getElementById("letterUpload");
  const files = Array.from(fileInput.files || []);

  const targetLanguage = document.getElementById("targetLanguage").value;
  const resultsDiv = document.getElementById("results");
  resultsDiv.innerHTML = '<p>Processing... Please wait.</p>';

  try {
    validateUploadSelection(files);

    const formData = new FormData();
    files.forEach((file) => formData.append('files', file));

    const ocrResponse = await fetch(`${API_BASE}/ocr`, {
      method: "POST",
      body: formData,
    });

    if (!ocrResponse.ok) {
      const errorData = await ocrResponse.json();
      throw new Error(errorData.detail || 'OCR failed');
    }

    const ocrData = await ocrResponse.json();
    const text = ocrData.text || (ocrData.documents || []).map((d) => d.text).join('\n\n');

    const analyzeResponse = await fetch(`${API_BASE}/analyze`, {
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

    await fetch(`${API_BASE}/save_scan`, {
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
    const response = await fetch(`${API_BASE}/run_sample`, {
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
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        fileInput.files = dataTransfer.files;
        renderSelectedFile(fileInput.files);
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
    const response = await fetch(`${API_BASE}/history`);
    const data = await response.json();
    historyList.innerHTML = "";

    data.history.forEach((scan) => {
      const scanDiv = document.createElement("div");
      scanDiv.className = "card mb-2";
      let formattedAnalysis = scan.analysis;
      try {
        formattedAnalysis = JSON.stringify(JSON.parse(scan.analysis), null, 2);
      } catch (e) {
        // leave as-is if it isn't valid JSON
      }
      scanDiv.innerHTML = `
        <div class="card-body">
          <h5>Scan #${scan.id} (${scan.timestamp})</h5>
          <p><strong>Language:</strong> ${scan.target_language}</p>
          <pre>${formattedAnalysis}</pre>
        </div>
      `;
      historyList.appendChild(scanDiv);
    });
  } catch (error) {
    historyList.innerHTML = `<p class="text-danger">Error: ${error.message}</p>`;
  }
});

async function updateModelStatus() {
  const badge = document.getElementById('modelStatus');
  if (!badge) return;

  try {
    const response = await fetch(`${API_BASE}/llm_status`);
    if (!response.ok) {
      throw new Error('Unable to check model status');
    }

    const status = await response.json();
    badge.classList.remove('neutral', 'ready', 'offline');

    const text = status.available ? (status.message || 'Local model ready') : (status.message || 'Local model unavailable');
    badge.querySelector('.status-text').textContent = text;

    if (status.available) {
      badge.classList.add('ready');
    } else {
      badge.classList.add('offline');
    }
  } catch (error) {
    badge.classList.remove('neutral', 'ready', 'offline');
    badge.classList.add('offline');
    badge.querySelector('.status-text').textContent = 'Local model unavailable';
  }
}

loadSampleLetters();
updateModelStatus();
