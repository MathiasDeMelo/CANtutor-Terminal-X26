// ============================================================
// app.js – all the page behaviour lives here.
// STEP 1: uses FAKE data so we can build without the backend.
// ============================================================

// ---------- 1. Fake response (same shape as POST /api/plan) ----------
const FAKE_PLAN = {
  pathway: "computing",
  roadmap: {
    "10": [],
    "11": [
      { code: "ICS3U", name: "Introduction to Computer Science", why: "Core programming course. Needed for ICS4U." },
      { code: "MCR3U", name: "Functions", why: "Builds the math skills university CS programs expect." }
    ],
    "12": [
      { code: "ICS4U", name: "Computer Science", why: "Most university CS programs recommend it." },
      { code: "MHF4U", name: "Advanced Functions", why: "Required by almost every university CS program." },
      { code: "MCV4U", name: "Calculus and Vectors", why: "Required by many engineering and CS programs." }
    ]
  },
  eligible_now: ["ICS3U"],
  warnings: [
    { course: "MCR3U", missing: ["MPM2D"],
      message: "You need Grade 10 Principles of Math (MPM2D) before you can take Functions (MCR3U)." }
  ],
  explanation: "You're on track for computing! Your next step is ICS3U. To keep university math options open, you'll need MPM2D first so you can take MCR3U.",
  spoken_summary: "You're on track for computing. Take ICS3U next. You're missing MPM2D, which you need before Functions."
};

// ---------- 2. Grab the page elements we'll use ----------
const form = document.getElementById("plan-form");
const button = document.getElementById("plan-btn");
const statusBox = document.getElementById("status");
const explanationBox = document.getElementById("explanation");
const warningsBox = document.getElementById("warnings");

// ---------- 3. Read the form into the request object ----------
function readForm() {
  // Find every ticked "completed" checkbox and keep its value (e.g. "ICS2O")
  const ticked = document.querySelectorAll('input[name="completed"]:checked');
  const completed = Array.from(ticked).map(box => box.value);

  return {
    grade: Number(document.getElementById("grade").value),
    completed: completed,
    interests: document.getElementById("interests").value.trim(),
    pathway: document.getElementById("pathway").value
  };
}

// ---------- 4. Get a plan (FAKE for now) ----------
// Returns a Promise, just like fetch() will. In step 2 we replace
// the inside of this function with a real fetch("/api/plan").
function getPlan(request) {
  console.log("Would send to /api/plan:", request);
  return new Promise(resolve => {
    setTimeout(() => resolve(FAKE_PLAN), 800); // pretend the server takes 0.8s
  });
}

// ---------- 5. Small helpers ----------
// Makes text safe to put inside HTML (so "<" in AI text can't break the page)
function esc(text) {
  const div = document.createElement("div");
  div.textContent = text ?? "";
  return div.innerHTML;
}

// Show a message in the status bar. type = "loading" or "error". Empty text hides it.
function showStatus(text, type) {
  statusBox.textContent = text;
  statusBox.className = "status " + (type || "");
  if (!text) statusBox.classList.add("hidden");
}

// ---------- 6. Draw the plan on the page ----------
function renderPlan(plan) {
  // Explanation text from the AI
  explanationBox.textContent = plan.explanation || "";

  // Make a quick lookup: course code -> its warning (if any)
  const warningFor = {};
  (plan.warnings || []).forEach(w => { warningFor[w.course] = w; });

  // Warnings list (red box), in plain language
  if (plan.warnings && plan.warnings.length > 0) {
    warningsBox.innerHTML =
      '<div class="panel warn-box"><h3>⚠️ Missing prerequisites</h3><ul>' +
      plan.warnings.map(w => "<li>" + esc(w.message) + "</li>").join("") +
      "</ul></div>";
  } else {
    warningsBox.innerHTML = "";
  }

  // One column per grade
  ["10", "11", "12"].forEach(grade => {
    const column = document.getElementById("col-" + grade);
    const courses = (plan.roadmap && plan.roadmap[grade]) || [];

    if (courses.length === 0) {
      column.innerHTML = '<p class="empty">No courses planned</p>';
      return;
    }

    column.innerHTML = courses.map(course => {
      const warning = warningFor[course.code];
      const eligible = (plan.eligible_now || []).includes(course.code);

      // Pick a colour/label for the card
      let cssClass = "card";
      let tag = "";
      if (warning) {
        cssClass += " blocked";
        tag = '<span class="tag tag-red">Missing: ' + esc(warning.missing.join(", ")) + "</span>";
      } else if (eligible) {
        cssClass += " ready";
        tag = '<span class="tag tag-green">✓ You can take this now</span>';
      }

      return (
        '<div class="' + cssClass + '">' +
          '<div class="code">' + esc(course.code) + "</div>" +
          '<div class="name">' + esc(course.name) + "</div>" +
          '<div class="why">' + esc(course.why) + "</div>" +
          tag +
        "</div>"
      );
    }).join("");
  });
}

// ---------- 7. When the button is pressed ----------
form.addEventListener("submit", async (event) => {
  event.preventDefault();            // stop the browser reloading the page
  button.disabled = true;
  button.textContent = "Thinking…";
  showStatus("Building your plan…", "loading");

  try {
    const plan = await getPlan(readForm());
    renderPlan(plan);
    showStatus("");                  // hide status bar
  } catch (err) {
    console.error(err);
    // Friendly message – the old roadmap stays on screen, never a blank page
    showStatus("Sorry, the planner isn't responding right now. Please try again in a moment.", "error");
  } finally {
    button.disabled = false;
    button.textContent = "Get my plan";
  }
});
