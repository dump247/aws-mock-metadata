<html>
<head>
    <title>Local Metadata Service</title>

<style>
body {
    font-family: sans-serif;
}

table.session td {
    line-height: 1.5em;
}

table.session td:first-child {
    text-align: right;
    white-space: nowrap;
    font-weight: bold;
    padding-right: 10px;
    background-color: lightgrey;
}

table.session td:last-child {
    font-family: monospace;
}
</style>

</head>
<body>
    <h2>Session</h2>
<p>Profile: <strong>{{profile_name}}</strong></p>
%if session:
    <table class="session">
    <tbody>
        <tr><td>Access Key</td><td>{{session.access_key}}</td></tr>
        <tr><td>Secret Key</td><td id="secret_key">******* <button onclick="reveal(this.parentNode)">Reveal</button></td></tr>
        <tr><td>Session Token</td><td id="session_token">******* <button onclick="reveal(this.parentNode)">Reveal</button></td></tr>
        <tr><td>Expiration</td><td id="expiration"></td></tr>
    </tbody>
    </table>

    <button onclick="clearSession()">Clear</button>

    <script>
var secret_key = "{{session.secret_key}}";
var session_token = "{{session.session_token}}";
var expiration = new Date("{{session.expiration}}");

document.getElementById("expiration").innerHTML = expiration;

function reveal(node) {
    node.innerHTML = window[node.id];
}

function clearSession() {
    var request = new XMLHttpRequest();
    request.open('DELETE', '/manage/session', false);
    request.send(null);
    location.reload();
}
    </script>
%else:
    <p>No session available</p>
%end

<div>
<h3>Create New Session</h3>
<form>
Token: <input type="text" width="8" id="token"/> <button onclick="newSession()" type="submit">Create</button>
</form>
</div>

<script>
function newSession() {
    var request = new XMLHttpRequest();
    request.open('POST', '/manage/session', false);
    request.send('token=' + encodeURIComponent(document.getElementById('token').value));
    location.reload();
}

function changeProfile(name) {
    var request = new XMLHttpRequest();
    request.open('POST', '/manage/session', false);
    request.send('profile=' + encodeURIComponent(name));
    location.reload();
}
</script>

<h1>Profiles</h1>

<table>
<thead>
    <tr>
        <th></th>
        <th>Name</th>
        <th>Access Key</th>
        <th>Token Duration</th>
        <th>Role ARN</th>
        <th>Region</th>
    </tr>
</thead>
<tbody>
%for name, profile in profiles.items():
<tr>
    <td><input onclick="changeProfile('{{name}}')" type="radio" name="profile" value="{{name}}"{{" checked" if name == profile_name else ""}}></td>
    <td>{{name}}</td>
    <td>{{profile.access_key}}</td>
    <td>{{profile.token_duration}}</td>
    <td>{{profile.role_arn}}</td>
    <td>{{profile.region}}</td>
</tr>
%end
</tbody>
</table>

</body>
</html>
