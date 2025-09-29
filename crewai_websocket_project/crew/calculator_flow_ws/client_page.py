# client_page.py
CLIENT_HTML = """
<!doctype html>
<html>
  <head>
    <meta charset="utf-8"/>
    <title>Calculator Flow (WebSocket)</title>
    <style>
      body { font-family: Arial; padding: 1rem; }
      #log { border: 1px solid #ddd; padding: .5rem; height: 300px; overflow-y: auto; white-space: pre-wrap; }
      #controls { margin-top: .5rem; }
      input { width: 300px; padding: .4rem; }
      button { padding: .4rem .6rem; }
    </style>
  </head>
  <body>
    <h2>Calculator Flow (WebSocket)</h2>
    <div id="log"></div>
    <div id="controls">
      <input id="answer" placeholder="Type answer and press Enter or Send" />
      <button id="sendBtn">Send</button>
    </div>

    <script>
      const log = document.getElementById('log');
      const input = document.getElementById('answer');
      const sendBtn = document.getElementById('sendBtn');

      function append(msg) {
        log.innerHTML += msg + '\\n';
        log.scrollTop = log.scrollHeight;
      }

      const ws = new WebSocket(`ws://${location.host}/calc`);
      ws.addEventListener('open', () => append('[connected to server]'));
      ws.addEventListener('close', () => append('[disconnected]'));
      ws.addEventListener('message', (ev) => {
        append('SERVER: ' + ev.data);
        input.focus();
      });

      function sendAnswer() {
        const v = input.value;
        if (!v) return;
        ws.send(v);
        append('YOU: ' + v);
        input.value = '';
      }

      sendBtn.addEventListener('click', sendAnswer);
      input.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') sendAnswer();
      });
    </script>
  </body>
</html>
"""
