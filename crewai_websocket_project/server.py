# server.py
import os
import asyncio
import threading
import queue
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from pydantic import BaseModel

# crewai imports (you already had these)
from crewai.flow.flow import Flow, start, listen, router

os.environ['CREWAI_DISABLE_TELEMETRY'] = 'true'
logging.basicConfig(level=logging.INFO)

# -------------------- Flow + State --------------------
class CalculatorState(BaseModel):
    num_1: int = 0
    num_2: int = 0
    operation: str = ""
    result: float = 0.0


class CalculatorFlow(Flow[CalculatorState]):
    """
    IMPORTANT: this Flow is written sync (no async keywords). It expects
    two callables to be injected:
      - send_user(msg: str) -> None        # fire-and-forget messages (logs)
      - ask_user(prompt: str) -> str       # blocking: put prompt, wait for answer
    The Flow methods use those to drive UI instead of input()/print().
    """

    def __init__(self, send_user, ask_user):
        super().__init__()
        self.send_user = send_user
        self.ask_user = ask_user

    @start()
    def first_number(self):
        self.send_user("Starting the structured flow")
        num1 = self.ask_user("Enter the first number:")
        self.state.num_1 = int(num1)

    @listen(first_number)
    def second_number(self):
        self.send_user("Starting second method")
        num2 = self.ask_user("Enter the second number:")
        self.state.num_2 = int(num2)

    @router(second_number)
    def conditional_operation(self):
        self.send_user("Starting Calculator Operation")
        operation = self.ask_user("Enter the operation (add/subtract/multiply/divide):")
        self.state.operation = operation.lower().strip()
        if operation == "add":
            return "add"
        if operation == "subtract":
            return "subtract"
        if operation == "multiply":
            return "multiply"
        if operation == "divide":
            return "divide"
        return "failed"

    @listen("add")
    def addition(self):
        self.state.result = self.state.num_1 + self.state.num_2
        self.send_user(f"Result: {self.state.result}")

    @listen("subtract")
    def subtraction(self):
        self.state.result = self.state.num_1 - self.state.num_2
        self.send_user(f"Result: {self.state.result}")

    @listen("multiply")
    def multiplication(self):
        self.state.result = self.state.num_1 * self.state.num_2
        self.send_user(f"Result: {self.state.result}")

    @listen("divide")
    def division(self):
        if self.state.num_2 == 0:
            self.send_user("Division by zero!")
        else:
            self.state.result = self.state.num_1 / self.state.num_2
            self.send_user(f"Result: {self.state.result}")


# -------------------- Web app --------------------
app = FastAPI()

# Serve a tiny client from the root for convenience:
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
        // focus the input so user can reply quickly
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

@app.get("/")
async def root():
    return HTMLResponse(CLIENT_HTML)


@app.websocket("/calc")
async def calc_socket(ws: WebSocket):
    await ws.accept()

    # two thread-safe queues for two-way comms
    prompts_q: "queue.Queue[tuple[str, bool]]" = queue.Queue()
    answers_q: "queue.Queue[str]" = queue.Queue()

    # used by the Flow (running in worker thread)
    def send_user(msg: str) -> None:
        # a non-blocking informational message; expects no reply.
        prompts_q.put((msg, False))

    def ask_user(prompt: str) -> str:
        # put a prompt which *expects* a reply, then block until an answer arrives
        prompts_q.put((prompt, True))
        ans = answers_q.get()   # blocking; worker thread will wait here until websocket handler provides answer
        return ans

    # instantiate flow with the injected I/O
    flow = CalculatorFlow(send_user=send_user, ask_user=ask_user)

    # run flow synchronously in a background thread so we don't block the asyncio loop
    def run_flow():
        try:
            flow.kickoff()   # synchronous / blocking call (matches your original usage)
        except Exception as e:
            logging.exception("Flow raised an exception")
            prompts_q.put((f"[flow error] {e}", False))

    worker = threading.Thread(target=run_flow, daemon=True)
    worker.start()

    loop = asyncio.get_event_loop()
    try:
        # main loop: wait for messages/prompts the Flow places on prompts_q
        while True:
            # exit condition: worker finished and no pending prompts
            if not worker.is_alive() and prompts_q.empty():
                break

            # block on prompts_q.get() without blocking asyncio by running it in an executor
            msg, expects_reply = await loop.run_in_executor(None, prompts_q.get)
            # send the message to the client
            try:
                await ws.send_text(msg)
            except WebSocketDisconnect:
                logging.info("client disconnected while sending")
                # if client disconnected, unblock flow if waiting for answer and break
                if expects_reply:
                    answers_q.put("")   # empty answer to unblock blocking get()
                break

            if expects_reply:
                # wait for the client's reply (this awaited receive_text pairs with ask_user)
                try:
                    answer = await ws.receive_text()
                except WebSocketDisconnect:
                    logging.info("client disconnected while waiting for answer")
                    answers_q.put("")   # unblock worker
                    break
                # forward answer to the flow worker
                answers_q.put(answer)

    except WebSocketDisconnect:
        logging.info("client disconnected")
    finally:
        # ensure worker won't hang forever
        if worker.is_alive():
            try:
                answers_q.put("")   # best-effort: unblock any waiting ask_user
            except Exception:
                pass
            worker.join(timeout=1)
        try:
            await ws.close()
        except Exception:
            pass
