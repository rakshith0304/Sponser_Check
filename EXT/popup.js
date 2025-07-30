document.getElementById("checkBtn").addEventListener("click", () => {
  const statusDiv = document.getElementById("status");
  const resultDiv = document.getElementById("result");
  const detailsDiv = document.getElementById("details");
  const checkBtn = document.getElementById("checkBtn");
  
  // Reset UI
  statusDiv.innerText = "Analyzing job posting...";
  resultDiv.style.display = "none";
  detailsDiv.style.display = "none";
  checkBtn.disabled = true;

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.scripting.executeScript({
      target: { tabId: tabs[0].id },
      function: extractAndAnalyzeJobPosting,
    });
  });
});

function extractAndAnalyzeJobPosting() {
  const container = document.querySelector('[data-automation-id="jobPostingPage"]');
  
  if (!container) {
    // Send error to popup
    chrome.runtime.sendMessage({
      type: "analysis_result",
      error: "Job posting page not found. Make sure you're on a Workday job posting page."
    });
    return;
  }

  // Extract text content
  function getVisibleText(element) {
    const walker = document.createTreeWalker(element, NodeFilter.SHOW_TEXT, {
      acceptNode: (node) => {
        if (!node.parentElement) return NodeFilter.FILTER_REJECT;
        const style = window.getComputedStyle(node.parentElement);
        return (style.display !== "none" && style.visibility !== "hidden")
          ? NodeFilter.FILTER_ACCEPT
          : NodeFilter.FILTER_REJECT;
      }
    });

    let text = "";
    while (walker.nextNode()) {
      text += walker.currentNode.nodeValue.trim() + "\n";
    }
    return text.trim();
  }

  const textContent = getVisibleText(container);

  // Send to backend for analysis
  fetch("http://127.0.0.1:8000/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text: textContent }),
  })
    .then((res) => res.json())
    .then((data) => {
      // Send result to popup
      chrome.runtime.sendMessage({
        type: "analysis_result",
        data: data
      });
    })
    .catch((err) => {
      chrome.runtime.sendMessage({
        type: "analysis_result",
        error: "Error connecting to analysis server: " + err.message
      });
    });
}

// Listen for messages from content script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const statusDiv = document.getElementById("status");
  const resultDiv = document.getElementById("result");
  const detailsDiv = document.getElementById("details");
  const checkBtn = document.getElementById("checkBtn");
  
  if (message.type === "analysis_result") {
    checkBtn.disabled = false;
    statusDiv.innerText = "";
    
    if (message.error) {
      // Show error
      resultDiv.className = "result-no";
      resultDiv.innerHTML = "❌ ERROR<br>" + message.error;
      resultDiv.style.display = "block";
      return;
    }
    
    const data = message.data;
    
    // Show result based on status
    resultDiv.className = `result-${data.status}`;
    resultDiv.innerHTML = `${data.message}<br><small>Confidence: ${(data.confidence * 100).toFixed(0)}%</small>`;
    resultDiv.style.display = "block";
    
    // Show details
    let detailsHTML = `<div class="confidence">Reasoning: ${data.reasoning}</div>`;
    
    if (data.positive_indicators && data.positive_indicators.length > 0) {
      detailsHTML += `<div class="indicators">
        <strong>Positive Indicators:</strong>
        <ul>`;
      data.positive_indicators.forEach(indicator => {
        detailsHTML += `<li>${indicator}</li>`;
      });
      detailsHTML += `</ul></div>`;
    }
    
    if (data.negative_indicators && data.negative_indicators.length > 0) {
      detailsHTML += `<div class="indicators">
        <strong>Negative Indicators:</strong>
        <ul>`;
      data.negative_indicators.forEach(indicator => {
        detailsHTML += `<li>${indicator}</li>`;
      });
      detailsHTML += `</ul></div>`;
    }
    
    detailsDiv.innerHTML = detailsHTML;
    detailsDiv.style.display = "block";
  }
});s