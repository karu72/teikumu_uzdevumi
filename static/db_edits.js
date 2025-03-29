document.addEventListener("DOMContentLoaded", function () {

    document.getElementById("add-sentence-form").addEventListener("submit", function (event) {
        event.preventDefault();

        let difficulty = document.getElementById("difficulty").value;
        let words = document.getElementById("sentence").value.trim().split(" ");
        let word_index = parseInt(document.getElementById("word_index").value, 10);
        let examples = document.getElementById("examples").value.split(",").map(e => e.trim());

        fetch("/add_sentence", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ difficulty, words, word_index, examples })
        })
        .then(response => response.json())
        .then(data => {
            alert(data.message);
        });
    });
});
