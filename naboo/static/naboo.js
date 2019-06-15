
function onChange(event) {
    let input = event.target;

    let d = document.createElement("div");
    var reader = new FileReader();
    reader.onload = function () {
        var text = reader.result;
        d.innerText = text;
        console.log(reader.result.substring(0, 200));
    };
    reader.readAsText(input.files[0]);
    document.body.appendChild(d);
    input.clear()
}

