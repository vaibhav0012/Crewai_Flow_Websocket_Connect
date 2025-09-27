import random
from crewai.flow.flow import Flow, listen, router, start
from pydantic import BaseModel
import os

os.environ['CREWAI_DISABLE_TELEMETRY'] = 'true'

class CalculatorState(BaseModel):
    num_1: int = 0
    num_2: int = 0
    operation: str = ""
    result: int = 0

class CalculatorFlow(Flow[CalculatorState]):

    @start()
    def first_number(self):
        print("Starting the structured flow")
        num1 = input("Enter the first number: ")
        self.state.num_1 = int(num1)

    @listen(first_number)
    def second_number(self):
        print("Starting second_method")
        num2 = input("Enter the second number: ")
        self.state.num_2 = int(num2)

    @router(second_number)
    def conditional_operation(self):
        print("Starting Calculator Operation")
        operation = input("Enter the operation: ")
        self.state.operation = operation
        if self.state.operation == "add":
            return "add"
        elif self.state.operation == "subtract":
            return "subtract"
        elif self.state.operation == "multiply":
            return "multiply"
        elif self.state.operation == "divide":
            return "divide"
        else:
            return "failed"

    @listen("add")
    def addition(self):
        print("Adding numbers")
        self.result = self.state.num_1 + self.state.num_2

    @listen("subtract")
    def subtraction(self):
        print("Subtracting numbers")
        self.result = self.state.num_1 - self.state.num_2

    @listen("multiply")
    def multiplication(self):
        print("Multiplying numbers")
        self.result = self.state.num_1 * self.state.num_2

    @listen("divide")
    def division(self):
        print("Dividing numbers")
        self.result = self.state.num_1 / self.state.num_2


flow = CalculatorFlow()
flow.plot("my_calculator_plot")
flow.kickoff()