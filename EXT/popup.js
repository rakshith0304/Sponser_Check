// popup.js - Enhanced version with structured data handling
document.getElementById("checkBtn").addEventListener("click", () => {
  const statusDiv = document.getElementById("status");
  const resultDiv = document.getElementById("result");
  const detailsDiv = document.getElementById("details");
  const checkBtn = document.getElementById("checkBtn");
  
  // Reset UI
  statusDiv.innerText = "Scraping job data and analyzing...";
  resultDiv.style.display = "none";
  detailsDiv.style.display = "none";
  checkBtn.disabled = true;

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.scripting.executeScript({
      target: { tabId: tabs[0].id },
      function: extractAndAnalyzeStructuredJob,
    });
  });
});

function extractAndAnalyzeStructuredJob() {
  // Extract structured job data
  const result = extractStructuredJobData();
  
  if (!result.success) {
    chrome.runtime.sendMessage({
      type: "analysis_result",
      error: result.error || "Failed to extract job data"
    });
    return;
  }

  const jobData = result.data;

  // Send structured data to backend
  fetch("http://127.0.0.1:8000/analyze-job", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(jobData),
  })
    .then((res) => res.json())
    .then((data) => {
      // Send result to popup with job data
      chrome.runtime.sendMessage({
        type: "analysis_result",
        data: data,
        jobData: jobData
      });
    })
    .catch((err) => {
      chrome.runtime.sendMessage({
        type: "analysis_result",
        error: "Error connecting to analysis server: " + err.message
      });
    });

  // Helper function for structured data extraction (same as in content.js)
  function extractStructuredJobData() {
    const container = document.querySelector('[data-automation-id="jobPostingPage"]');
    if (!container) {
      return { 
        success: false, 
        error: "❌ jobPostingPage not found. Make sure you're on a Workday job posting page.",
        data: null 
      };
    }

    function getElementText(automationId, context = document) {
      const element = context.querySelector(`[data-automation-id="${automationId}"]`);
      if (!element) return null;
      
      let text = "";
      
      // Special handling for time field - extract from dd element
      if (automationId === "time") {
        const dl = element.querySelector("dl");
        if (dl) {
          const dd = dl.querySelector("dd");
          text = dd?.innerText?.trim() || dd?.textContent?.trim() || "";
        } else {
          text = element.innerText?.trim() || element.textContent?.trim() || "";
        }
      } else {
        text = element.innerText?.trim() || element.textContent?.trim() || "";
        
        // Clean up specific patterns for other fields
        if (automationId === "requisitionId") {
          // Extract job ID - remove "job requisition id" prefix
          text = text.replace(/^job\s*requisition\s*id\s*/i, '').trim();
        } else if (automationId === "locations") {
          // Keep location as is, but clean whitespace
          text = text.replace(/\s+/g, ' ').trim();
        } else if (automationId === "jobPostingHeader") {
          // Clean job title
          text = text.replace(/\s+/g, ' ').trim();
        }
      }
      
      // General cleanup
      text = text.replace(/\s+/g, ' ').trim();
      
      return text || null;
    }

    function getFullJobText(element) {
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

    const jobData = {
      jobTitle: getElementText("jobPostingHeader", container),
      location: getElementText("locations", container),
      employmentType: getElementText("time", container),
      jobId: getElementText("requisitionId", container),
      aboutCompany: getElementText("jobSidebar", container),
      fullJobDescription: getFullJobText(container),
      url: window.location.href,
      scrapedAt: new Date().toISOString(),
      platform: "workday"
    };

    // Clean up null values
    Object.keys(jobData).forEach(key => {
      if (jobData[key] === null || jobData[key] === "") {
        jobData[key] = "Not found";
      }
    });

    return {
      success: true,
      error: null,
      data: jobData
    };
  }
}

// Enhanced message listener with structured data display
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  const statusDiv = document.getElementById("status");
  const resultDiv = document.getElementById("result");
  const detailsDiv = document.getElementById("details");
  const checkBtn = document.getElementById("checkBtn");
  
  if (message.type === "analysis_result") {
    checkBtn.disabled = false;
    statusDiv.innerText = "";
    
    if (message.error) {
      resultDiv.className = "result-no";
      resultDiv.innerHTML = "❌ ERROR<br>" + message.error;
      resultDiv.style.display = "block";
      return;
    }
    
    const data = message.data;
    const jobData = message.jobData;
    
    // Show sponsorship result
    resultDiv.className = `result-${data.status}`;
    resultDiv.innerHTML = `${data.message}<br><small>Confidence: ${(data.confidence * 100).toFixed(0)}%</small>`;
    resultDiv.style.display = "block";
    
    // Enhanced details with job information
    let detailsHTML = "";
    
    // Job Information Section
    if (jobData) {
      detailsHTML += `<div class="job-info">
        <h3>Job Information</h3>
        <div class="job-details">
          <strong>Title:</strong> ${jobData.jobTitle}<br>
          <strong>Location:</strong> ${jobData.location}<br>
          <strong>Work Type:</strong> ${jobData.employmentType}<br>
          <strong>Job ID:</strong> ${jobData.jobId}<br>
        </div>
      </div>`;
    }
    
    // Analysis Results Section
    detailsHTML += `<div class="analysis-info">
      <h3>Analysis Results</h3>
      <div class="confidence">Reasoning: ${data.reasoning}</div>
    `;
    
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
    
    detailsHTML += `</div>`; // Close analysis-info
    
    detailsDiv.innerHTML = detailsHTML;
    detailsDiv.style.display = "block";
  }
});