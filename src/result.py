

from requests import request
import requests


class Result:

    def __init__(self) -> None:
        self.success = 0
        self.failed = 0
        self.errors = []

    def add(self, response: requests.Response, success_code=201):
        if response.status_code != success_code: 
            self.failed = self.failed + 1
            self.errors.append(response.text)
        else:
            self.success = self.success + 1
        
    def print(self):
        print("Successfully: ", self.success)
        print("Failed: ", self.failed)
        print("Errors: ")
        for entry in self.errors:
            print(entry)