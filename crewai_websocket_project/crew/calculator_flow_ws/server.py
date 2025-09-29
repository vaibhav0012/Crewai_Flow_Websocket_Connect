# server.py
import asyncio
import logging
import threading
import queue
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse

from flow_logic import CalculatorFlow
from client_page import CLIENT_HTML

logging.basicConfig(level=logging.INFO)
app = FastAPI()

@app.get("/")
async def root():
    return HTMLResponse(CLIENT_HTML)

@app.websocket("/calc")
async def calc_socket(ws: WebSocket):
    await ws.accept()

    prompts_q: "queue.Queue[tuple[str,bool]]" = queue.Queue()
    answers_q: "queue.Queue[str]" = queue.Queue()

    def send_user(msg: str) -> None:
        prompts_q.put((msg, False))

    def ask_user(prompt: str) -> str:
        prompts_q.put((prompt, True))
        return answers_q.get()   # blocks in worker thread

    flow = CalculatorFlow(send_user=send_user, ask_user=ask_user)

    def run_flow():
        try:
            flow.kickoff()   # synchronous kickoff
        except Exception as e:
            logging.exception("Flow raised exception")
            prompts_q.put((f"[flow error] {e}", False))

    worker = threading.Thread(target=run_flow, daemon=True)
    worker.start()

    loop = asyncio.get_event_loop()
    try:
        while True:
            if not worker.is_alive() and prompts_q.empty():
                break
            msg, expects_reply = await loop.run_in_executor(None, prompts_q.get)
            try:
                await ws.send_text(msg)
            except WebSocketDisconnect:
                if expects_reply:
                    answers_q.put("")
                break

            if expects_reply:
                try:
                    answer = await ws.receive_text()
                except WebSocketDisconnect:
                    answers_q.put("")
                    break
                answers_q.put(answer)
    finally:
        if worker.is_alive():
            answers_q.put("")  # unblock if waiting
            worker.join(timeout=1)
        await ws.close()
