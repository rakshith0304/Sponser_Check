// content.js - Enhanced version with JSON-LD extraction for company name
function extractStructuredJobData() {
  const container = document.querySelector('[data-automation-id="jobPostingPage"]');
  if (!container) {
    return { 
      success: false, 
      error: "❌ jobPostingPage not found. Make sure you're on a Workday job posting page.",
      data: null 
    };
  }

  // Helper function to extract JSON-LD data
  function extractJsonLdData() {
    try {
      const scriptElements = document.querySelectorAll('script[type="application/ld+json"]');
      if (!scriptElements.length) return null;

      const results = [];
      for (const script of scriptElements) {
        try {
          const jsonData = JSON.parse(script.textContent);
          // Handle both single objects and arrays
          if (Array.isArray(jsonData)) {
            jsonData.forEach(item => results.push(item));
          } else {
            results.push(jsonData);
          }
        } catch (e) {
          console.log('Error parsing JSON-LD:', e);
        }
      }

      // Find the most relevant JobPosting data
      const jobPosting = results.find(item => 
        item['@type'] === 'JobPosting' || 
        (Array.isArray(item['@type']) && item['@type'].includes('JobPosting'))
      );

      if (!jobPosting) return null;

      return {
        companyName: jobPosting.hiringOrganization?.name || 
                   jobPosting.hiringOrganization?.legalName,
        companyUrl: jobPosting.hiringOrganization?.url,
        jobLocation: jobPosting.jobLocation?.address?.addressLocality,
        baseSalary: jobPosting.baseSalary,
        employmentType: jobPosting.employmentType
      };
    } catch (e) {
      console.log('Error extracting JSON-LD:', e);
      return null;
    }
  }

  // Helper function to safely extract text from automation-id elements
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
      } else if (automationId === "header") {
        // Clean header text (often contains company name and page title)
        text = text.replace(/\s+/g, ' ').trim();
      }
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

  // Extract JSON-LD data first
  const jsonLdData = extractJsonLdData();

  // Extract structured data
  const jobData = {
    // Basic job information
    jobTitle: getElementText("jobPostingHeader", container),
    location: getElementText("locations", container) || jsonLdData?.jobLocation,
    employmentType: getElementText("time", container) || jsonLdData?.employmentType,
    jobId: getElementText("requisitionId", container),
    aboutCompany: getElementText("jobSidebar", container),
    header: getElementText("header"),
    
    // Company information from JSON-LD
    companyName: jsonLdData?.companyName,
    companyUrl: jsonLdData?.companyUrl,
    
    // Full job description for analysis
    fullJobDescription: getFullJobText(container),
    
    // Additional metadata
    url: window.location.href,
    scrapedAt: new Date().toISOString(),
    platform: "workday",
    
    // Raw JSON-LD data for debugging
    _jsonLd: jsonLdData
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