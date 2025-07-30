// Service worker for Chrome extension
// Handles background tasks and message passing

chrome.runtime.onInstalled.addListener(() => {
  console.log('Visa Sponsorship Checker extension installed');
});

// Handle messages between content script and popup
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  // Forward messages from content script to popup
  if (message.type === "analysis_result") {
    // This will be handled by the popup.js listener
    return true;
  }
});