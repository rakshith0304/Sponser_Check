function extractEverythingFromJobPostingPage() {
  const container = document.querySelector('[data-automation-id="jobPostingPage"]');
  if (!container) {
    return { text: "❌ jobPostingPage not found", html: "" };
  }

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
  const rawHTML = container.innerHTML;

  return {
    text: textContent,
    html: rawHTML
  };
}