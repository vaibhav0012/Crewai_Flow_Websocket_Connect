# server.py
import asyncio
import logging
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

    answers_q: asyncio.Queue[str] = asyncio.Queue()

    # async helpers for the Flow
    async def send_user(msg: str):
        await ws.send_text(msg)

    async def ask_user(prompt: str) -> str:
        await ws.send_text(prompt)
        # wait for user reply from queue
        return await answers_q.get()

    # background task to read all messages from the browser
    async def reader():
        try:
            while True:
                msg = await ws.receive_text()
                await answers_q.put(msg)
        except WebSocketDisconnect:
            # Put a sentinel to unblock ask_user if the client disconnects
            await answers_q.put("__DISCONNECT__")

    reader_task = asyncio.create_task(reader())

    flow = CalculatorFlow(send_user=send_user, ask_user=ask_user)

    try:
        # run the flow completely asynchronously
        await flow.kickoff_async()
    finally:
        reader_task.cancel()
        await ws.close()
