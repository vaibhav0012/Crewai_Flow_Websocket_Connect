# flow_logic.py
import os
from pydantic import BaseModel
from crewai.flow.flow import Flow, start, listen, router

os.environ['CREWAI_DISABLE_TELEMETRY'] = 'true'

class CalculatorState(BaseModel):
    num_1: int = 0
    num_2: int = 0
    operation: str = ""
    result: float = 0.0


class CalculatorFlow(Flow[CalculatorState]):
    """
    Async Flow.
    Expects two async callables injected at construction:
      send_user(msg: str) -> Awaitable[None]
      ask_user(prompt: str) -> Awaitable[str]
    """

    def __init__(self, send_user, ask_user):
        super().__init__()
        self.send_user = send_user
        self.ask_user = ask_user

    @start()
    async def first_number(self):
        await self.send_user("Starting the structured flow")
        num1 = await self.ask_user("Enter the first number:")
        self.state.num_1 = int(num1)

    @listen(first_number)
    async def second_number(self):
        await self.send_user("Starting second method")
        num2 = await self.ask_user("Enter the second number:")
        self.state.num_2 = int(num2)

    @router(second_number)
    async def conditional_operation(self):
        await self.send_user("Starting Calculator Operation")
        op = await self.ask_user("Enter the operation (add/subtract/multiply/divide):")
        op = op.lower().strip()
        self.state.operation = op
        return op if op in {"add", "subtract", "multiply", "divide"} else "failed"

    @listen("add")
    async def addition(self):
        self.state.result = self.state.num_1 + self.state.num_2
        await self.send_user(f"Result: {self.state.result}")

    @listen("subtract")
    async def subtraction(self):
        self.state.result = self.state.num_1 - self.state.num_2
        await self.send_user(f"Result: {self.state.result}")

    @listen("multiply")
    async def multiplication(self):
        self.state.result = self.state.num_1 * self.state.num_2
        await self.send_user(f"Result: {self.state.result}")

    @listen("divide")
    async def division(self):
        if self.state.num_2 == 0:
            await self.send_user("Division by zero!")
        else:
            self.state.result = self.state.num_1 / self.state.num_2
            await self.send_user(f"Result: {self.state.result}")
