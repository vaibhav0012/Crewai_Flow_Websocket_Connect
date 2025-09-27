import os
import asyncio
import threading
import queue
import logging
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from calculator_flow import CalculatorFlow

logging.basicConfig(level=logging.INFO)

app = FastAPI()

@app.websocket("/calc")
async def calc_socket(ws: WebSocket):
    await ws.accept()
    prompts_q = queue.Queue()
    answers_q = queue.Queue()

    def send_user(msg: str) -> None:
        prompts_q.put((msg, False))

    def ask_user(prompt: str) -> str:
        prompts_q.put((prompt, True))
        ans = answers_q.get()
        return ans

    flow = CalculatorFlow(send_user=send_user, ask_user=ask_user)

    def run_flow():
        try:
            flow.kickoff()
        except Exception as e:
            logging.exception("Flow raised an exception")
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
                logging.info("client disconnected while sending")
                if expects_reply:
                    answers_q.put("")
                break
            if expects_reply:
                try:
                    answer = await ws.receive_text()
                except WebSocketDisconnect:
                    logging.info("client disconnected while waiting for answer")
                    answers_q.put("")
                    break
                answers_q.put(answer)
    except WebSocketDisconnect:
        logging.info("client disconnected")
    finally:
        if worker.is_alive():
            try:
                answers_q.put("")
            except Exception:
                pass
            worker.join(timeout=1)
        try:
            await ws.close()
        except Exception:
            pass
