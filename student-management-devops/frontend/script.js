document.getElementById("studentForm").addEventListener("submit", async function(e) {
  e.preventDefault();

  const data = {
    name: document.getElementById("name").value,
    email: document.getElementById("email").value,
    tech: document.getElementById("tech").value,
    location: document.getElementById("location").value
  };

  await fetch("http://localhost:5000/add_student", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(data)
  });

  alert("Student Added!");
});