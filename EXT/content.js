// content.js - Enhanced version for structured data extraction
function extractStructuredJobData() {
  const container = document.querySelector('[data-automation-id="jobPostingPage"]');
  if (!container) {
    return { 
      success: false, 
      error: "❌ jobPostingPage not found",
      data: null 
    };
  }

  // Helper function to safely extract text from automation-id elements
  function getElementText(automationId, context = document) {
    const element = context.querySelector(`[data-automation-id="${automationId}"]`);
    if (!element) return null;
    
    let text = element.innerText?.trim() || element.textContent?.trim() || "";
    
    // Clean up specific patterns for each field
    if (automationId === "time") {
      const dl = element.querySelector("dl");
      if (dl) {
        const dd = dl.querySelector("dd");
        text = dd?.innerText?.trim() || dd?.textContent?.trim() || "";
      }
    }else if (automationId === "requisitionId") {
      // Extract job ID - remove "job requisition id" prefix
      text = text.replace(/^job\s*requisition\s*id\s*/i, '').trim();
    } else if (automationId === "locations") {
      // Keep location as is, but clean whitespace
      text = text.replace(/\s+/g, ' ').trim();
    } else if (automationId === "jobPostingHeader") {
      // Clean job title
      text = text.replace(/\s+/g, ' ').trim();
    }
    
    // General cleanup
    text = text.replace(/\s+/g, ' ').trim();
    
    return text || null;
  }

  // Helper function to get all text content for full job description
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

  // Extract structured data
  const jobData = {
    // Basic job information
    jobTitle: getElementText("jobPostingHeader", container),
    location: getElementText("locations", container),
    employmentType: getElementText("time", container),
    jobId: getElementText("requisitionId", container),
    aboutCompany: getElementText("jobSidebar", container),
    
    // Full job description for analysis
    fullJobDescription: getFullJobText(container),
    
    // Additional metadata
    url: window.location.href,
    scrapedAt: new Date().toISOString(),
    platform: "workday"
  };

  // Clean up any null values and provide fallbacks
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