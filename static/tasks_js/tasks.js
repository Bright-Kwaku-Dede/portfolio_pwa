// DOM Elements
const taskForm = document.getElementById("task-form");
const tasksContainer = document.getElementById("tasks-container");
const loading = document.getElementById("loading");
const noTasks = document.getElementById("no-tasks");
const filterBtns = document.querySelectorAll(".filter-btn");

// State
let allTasks = [];
let currentFilter = "all";

// Event Listeners
document.addEventListener("DOMContentLoaded", () => {
  loadTasks();
  loadStats();
});

taskForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  await addTask();
});

filterBtns.forEach((btn) => {
  btn.addEventListener("click", () => {
    filterBtns.forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    currentFilter = btn.dataset.filter;
    displayTasks();
  });
});

// Load Tasks
async function loadTasks() {
  loading.style.display = "block";
  tasksContainer.innerHTML = "";
  noTasks.style.display = "none";

  try {
    const response = await fetch("/api/tasks");
    const data = await response.json();

    if (data.success) {
      allTasks = data.tasks;
      displayTasks();
    }
  } catch (error) {
    console.error("Error loading tasks:", error);
  } finally {
    loading.style.display = "none";
  }
}

// Display Tasks
function displayTasks() {
  tasksContainer.innerHTML = "";

  // Filter tasks
  let filteredTasks = allTasks;
  if (currentFilter === "completed") {
    filteredTasks = allTasks.filter((task) => task.completed === 1);
  } else if (currentFilter === "pending") {
    filteredTasks = allTasks.filter((task) => task.completed === 0);
  }

  if (filteredTasks.length === 0) {
    noTasks.style.display = "block";
    return;
  }

  noTasks.style.display = "none";

  filteredTasks.forEach((task) => {
    const taskCard = createTaskCard(task);
    tasksContainer.appendChild(taskCard);
  });
}

// Create Task Card
function createTaskCard(task) {
  const card = document.createElement("div");
  card.className = `task-card ${task.completed ? "completed" : ""}`;

  const dueDate = task.due_date
    ? new Date(task.due_date + "T00:00:00").toLocaleDateString()
    : "No due date";

  card.innerHTML = `
        <div class="task-header">
            <div class="task-title">${escapeHtml(task.title)}</div>
            <div class="task-actions">
                <button class="task-btn complete" onclick="toggleComplete(${task.id}, ${task.completed})" title="${task.completed ? "Mark as incomplete" : "Mark as complete"}">
                    ${task.completed ? "↩️" : "✅"}
                </button>
                <button class="task-btn delete" onclick="deleteTask(${task.id})" title="Delete task">
                    🗑️
                </button>
            </div>
        </div>
        
        ${task.description ? `<div class="task-description">${escapeHtml(task.description)}</div>` : ""}
        
        <div class="task-meta">
            <span class="task-badge badge-category">${escapeHtml(task.category)}</span>
            <span class="task-badge badge-priority ${task.priority.toLowerCase()}">${escapeHtml(task.priority)}</span>
            <span class="task-due-date">📅 ${dueDate}</span>
        </div>
    `;

  return card;
}

// Add Task
async function addTask() {
  const title = document.getElementById("task-title").value.trim();
  const description = document.getElementById("task-description").value.trim();
  const category = document.getElementById("task-category").value;
  const priority = document.getElementById("task-priority").value;
  const dueDate = document.getElementById("task-due-date").value;

  if (!title) {
    alert("Please enter a task title");
    return;
  }

  try {
    const response = await fetch("/api/tasks", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        title,
        description,
        category,
        priority,
        due_date: dueDate,
      }),
    });

    const data = await response.json();

    if (data.success) {
      taskForm.reset();
      await loadTasks();
      await loadStats();
    } else {
      alert("Failed to add task: " + data.error);
    }
  } catch (error) {
    console.error("Error adding task:", error);
    alert("Error adding task. Please try again.");
  }
}

// Toggle Complete
async function toggleComplete(taskId, currentStatus) {
  try {
    const response = await fetch(`/api/tasks/${taskId}`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        completed: !currentStatus,
      }),
    });

    const data = await response.json();

    if (data.success) {
      await loadTasks();
      await loadStats();
    }
  } catch (error) {
    console.error("Error updating task:", error);
  }
}

// Delete Task
async function deleteTask(taskId) {
  if (!confirm("Are you sure you want to delete this task?")) {
    return;
  }

  try {
    const response = await fetch(`/api/tasks/${taskId}`, {
      method: "DELETE",
    });

    const data = await response.json();

    if (data.success) {
      await loadTasks();
      await loadStats();
    }
  } catch (error) {
    console.error("Error deleting task:", error);
  }
}

// Load Statistics
async function loadStats() {
  try {
    const response = await fetch("/api/tasks/stats");
    const data = await response.json();

    if (data.success) {
      document.getElementById("total-tasks").textContent = data.stats.total;
      document.getElementById("completed-tasks").textContent =
        data.stats.completed;
      document.getElementById("pending-tasks").textContent = data.stats.pending;
    }
  } catch (error) {
    console.error("Error loading stats:", error);
  }
}

// Escape HTML to prevent XSS
function escapeHtml(text) {
  const div = document.createElement("div");
  div.textContent = text;
  return div.innerHTML;
}
