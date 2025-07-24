document.getElementById("extractBtn").addEventListener("click", () => {
  document.getElementById("status").innerText = "Extracting...";

  chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
    chrome.scripting.executeScript({
      target: { tabId: tabs[0].id },
      function: extractEverythingFromJobPostingPage,
    });
  });
});

function extractEverythingFromJobPostingPage() {
  const div = document.querySelector('[data-automation-id="jobPostingPage"]');
  const text = div ? div.innerText + "\n\n---RAW HTML---\n\n" : "No such div found";

  fetch("http://127.0.0.1:8000/save", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text }),
  })
    .then((res) => res.json())
    .then((data) => {
      alert("Success: " + data.status);
    })
    .catch((err) => alert("Error: " + err));
}

