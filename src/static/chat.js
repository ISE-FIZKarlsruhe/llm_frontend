document.addEventListener("DOMContentLoaded", function () {
  var chatElement = document.getElementById("chat");

  chatElement.addEventListener("click", function (event) {
    event.preventDefault();

    let response = document.getElementById("response");
    response.innerHTML = "waiting...";
    let system = document.getElementById("system");
    let prompt = document.getElementById("prompt");

    payload = {
      messages: [
        { role: "system", content: system.value },
        { role: "user", content: prompt.value },
      ],
    };

    if (system.value && prompt.value) {
      fetch("/v1/chat/completions", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: "Bearer " + document.TOKEN,
        },
        body: JSON.stringify(payload),
        credentials: "omit",
      })
        .then((response) => response.json())
        .then((data) => {
          response.innerHTML = data.choices[0].message.content;
          response.innerHTML = "";
          let result = data.choices[0].message.content;
          let lines = result.split("\n");
          lines.forEach((line) => {
            let paragraph = document.createElement("p");
            paragraph.textContent = line;
            response.appendChild(paragraph);
          });
        })
        .catch((error) => {
          console.error(error);
        });
    }
  });
});
