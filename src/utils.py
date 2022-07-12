from getopt import getopt
import os, requests
from pydantic import BaseModel
from typing import List
from dotenv import load_dotenv
import pymysql


class Modified(BaseModel):
    created: int
    updated: int

class Utils:


    def __init__(self) -> None:
        load_dotenv()
        self.IDJANGO_API_KEY = self.get_env_string("IDJANGO_API_KEY")
        self.IDJANGO_API_URL = self.get_env_string("IDJANGO_API_URL", "http://localhost:8000")
        
    

    def get_env_string(self, value: str, default="") -> str:
        var = os.getenv(value)
        if var == None:
            return default
        return var

    def get_env_int(self, value: str, default: int=0) -> int:
        var = os.getenv(value)
        if var == None:
            return default
        return var

    def idjango_post(self, path, json) -> requests.Response:
        headers = {'Content-Type': 'application/json', "Authorization": "Api-Key " + self.IDJANGO_API_KEY}
        return requests.post(self.IDJANGO_API_URL + path, headers=headers, json=json)

    def connect_drops(self) -> pymysql.Connection:
        return pymysql.connect(
                host=self.get_env_string('DROPS_HOST'),
                port=self.get_env_int('DROPS_PORT', 3306),
                user=self.get_env_string('DROPS_USER', "drops"),
                password=self.get_env_string('DROPS_PASSWORD', "drops"),
                database="drops",
                cursorclass=pymysql.cursors.DictCursor
                )
        
    def connect_pool1(self) -> pymysql.Connection:
        return pymysql.connect(
                host=self.get_env_string('POOL1_HOST'),
                port=self.get_env_int('POOL1_PORT', 3306),
                user=self.get_env_string('POOL1_USER'),
                password=self.get_env_string('POOL1_PASSWORD', "root"),
                database="db175370026",
                cursorclass=pymysql.cursors.DictCursor
                )

    

    def print_list(self, p_list):
        for entry in p_list:
            print(entry)


    def get_options(self, options: str, long_option: str, argv: List[str]):
        try:
            a, _ = getopt(argv, options, long_option)
            return a
        except getopt.error as err:
            print(str(err))
