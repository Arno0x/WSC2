<div id="${prefix}Input" style="display: none"></div>
<div id="${prefix}Output" style="display: none"></div>
<button id="${prefix}Button" style="display: none" type="button" onClick="sendResult()">sendResult</button>
<script>

var ws = new WebSocket('${wsCallbackURL}:${port}/ws');

ws.onmessage = function(event) {
	document.getElementById("${prefix}Input").innerText = event.data;
};

function sendResult() {
	var data = document.getElementById("${prefix}Output").innerText;
	ws.send(data);
}
</script>
</body>
