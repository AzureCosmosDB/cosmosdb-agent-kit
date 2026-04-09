const REPO_ISSUE_URL = "https://github.com/AzureCosmosDB/cosmosdb-agent-kit/issues/new";

function revealOnScroll() {
  const revealNodes = document.querySelectorAll(".reveal");
  const observer = new IntersectionObserver(
    (entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) {
          entry.target.classList.add("visible");

          const staggerItems = entry.target.querySelectorAll(".stagger-item");
          staggerItems.forEach((item, index) => {
            window.setTimeout(() => item.classList.add("visible"), 90 * index);
          });

          observer.unobserve(entry.target);
        }
      }
    },
    { threshold: 0.14 }
  );

  revealNodes.forEach((node) => observer.observe(node));
}

function getField(form, name) {
  return form.elements.namedItem(name)?.value?.trim() || "";
}

function buildIssueBody(form) {
  const today = new Date().toISOString().slice(0, 10);

  return [
    "## Agent Kit Survey Response",
    "",
    `Date: ${today}`,
    `Role: ${getField(form, "role")}`,
    `Usage Frequency: ${getField(form, "frequency")}`,
    "",
    "### Ratings",
    `- Usefulness: ${getField(form, "usefulness")}/5`,
    `- Rule clarity: ${getField(form, "clarity")}/5`,
    `- Scenario coverage: ${getField(form, "coverage")}/5`,
    `- Example quality: ${getField(form, "examples")}/5`,
    "",
    "### Most valuable",
    getField(form, "valuable"),
    "",
    "### Pain points",
    getField(form, "pain"),
    "",
    "### Requested additions",
    getField(form, "wishlist"),
    "",
    "### Optional contact",
    getField(form, "contact") || "(not provided)",
  ].join("\n");
}

function openPrefilledIssue(form) {
  const role = getField(form, "role") || "Unspecified role";
  const title = `Survey: ${role} feedback`;
  const body = buildIssueBody(form);

  const params = new URLSearchParams({
    title,
    labels: "feedback,survey",
    body,
  });

  const target = `${REPO_ISSUE_URL}?${params.toString()}`;
  window.open(target, "_blank", "noopener,noreferrer");
}

function validateRange(value) {
  const n = Number(value);
  return Number.isInteger(n) && n >= 1 && n <= 5;
}

function bindSurvey() {
  const form = document.getElementById("feedback-form");
  const status = document.getElementById("form-status");

  if (!form || !status) {
    return;
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();

    const requiredNames = ["role", "frequency", "valuable", "pain", "wishlist"];
    const scoreNames = ["usefulness", "clarity", "coverage", "examples"];

    const missing = requiredNames.find((name) => getField(form, name) === "");
    if (missing) {
      status.textContent = "Please complete all required fields before submitting.";
      status.className = "error";
      return;
    }

    const invalidScore = scoreNames.find((name) => !validateRange(getField(form, name)));
    if (invalidScore) {
      status.textContent = "Ratings must be whole numbers from 1 to 5.";
      status.className = "error";
      return;
    }

    openPrefilledIssue(form);
    status.textContent = "Survey opened in GitHub. Submit the issue there to send feedback.";
    status.className = "success";
    form.reset();
  });
}

revealOnScroll();
bindSurvey();
