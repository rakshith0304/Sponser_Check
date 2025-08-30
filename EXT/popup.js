// popup.js - Updated to use simplified data extraction
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

  // Helper function for structured data extraction (simplified version)
  function extractStructuredJobData() {
    const container = document.querySelector('[data-automation-id="jobPostingPage"]');
    if (!container) {
      return { 
        success: false, 
        error: "❌ jobPostingPage not found. Make sure you're on a Workday job posting page.",
        data: null 
      };
    }

    // Helper function to extract JSON-LD company name only
    function extractJsonLdCompanyName() {
      try {
        const scriptElements = document.querySelectorAll('script[type="application/ld+json"]');
        if (!scriptElements.length) return null;

        const results = [];
        for (const script of scriptElements) {
          try {
            const jsonData = JSON.parse(script.textContent);
            if (Array.isArray(jsonData)) {
              jsonData.forEach(item => results.push(item));
            } else {
              results.push(jsonData);
            }
          } catch (e) {
            console.log('Error parsing JSON-LD:', e);
          }
        }

        const jobPosting = results.find(item => 
          item['@type'] === 'JobPosting' || 
          (Array.isArray(item['@type']) && item['@type'].includes('JobPosting'))
        );

        if (!jobPosting) return null;

        return jobPosting.hiringOrganization?.name || 
               jobPosting.hiringOrganization?.legalName || null;
      } catch (e) {
        console.log('Error extracting JSON-LD company name:', e);
        return null;
      }
    }

    function getElementText(automationId, context = document) {
      const element = context.querySelector(`[data-automation-id="${automationId}"]`);
      if (!element) return null;
      
      let text = "";
      
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
        
        if (automationId === "requisitionId") {
          text = text.replace(/^job\s*requisition\s*id\s*/i, '').trim();
        } else if (automationId === "locations") {
          text = text.replace(/\s+/g, ' ').trim();
        } else if (automationId === "jobPostingHeader") {
          text = text.replace(/\s+/g, ' ').trim();
        } else if (automationId === "header") {
          text = text.replace(/\s+/g, ' ').trim();
        }
      }
      
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

    const jsonLdCompanyName = extractJsonLdCompanyName();

    const jobData = {
      jobTitle: getElementText("jobPostingHeader", container),
      location: getElementText("locations", container),
      employmentType: getElementText("time", container),
      jobId: getElementText("requisitionId", container),
      aboutCompany: getElementText("jobSidebar", container),
      header: getElementText("header"),
      jsonLdCompanyName: jsonLdCompanyName,
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
          <strong>Job ID:</strong> ${jobData.jobId}<br>`;
      
      // Show final selected company name
      if (data.job_metadata && data.job_metadata.final_company_name) {
        detailsHTML += `<strong>Company:</strong> ${data.job_metadata.final_company_name}<br>`;
      }
      
      detailsHTML += `</div>
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

    // Show company analysis if available
    if (data.company_analysis && data.company_analysis.length > 0) {
      detailsHTML += `<div class="company-analysis">
        <strong>Company Analysis:</strong>
        <ul>`;
      data.company_analysis.forEach(analysis => {
        detailsHTML += `<li>${analysis}</li>`;
      });
      detailsHTML += `</ul></div>`;
    }
    
    detailsHTML += `</div>`; // Close analysis-info
    
    detailsDiv.innerHTML = detailsHTML;
    detailsDiv.style.display = "block";
  }
});