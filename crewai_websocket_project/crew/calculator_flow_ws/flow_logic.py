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
    Flow is synchronous. It expects two injected callables:
      send_user(msg: str) -> None
      ask_user(prompt: str) -> str
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
