

import copy
from typing import List
from pydantic import BaseModel

from tqdm import tqdm

from .result import Result
from .utils import Utils


class Newsletter(BaseModel):
    email: str
    newsletter: str


class NewsletterHandler:

    def __init__(self) -> None:
        self.utils = Utils()
        self.pool1 = self.utils.connect_pool1()

    def all(self) -> List:
        sql = ( 'select user_email, meta_value from wp_users as u '
        'left join wp_usermeta as m on u.ID = m.user_id '
        'where m.meta_key = "mail_switch"')
        with self.pool1.cursor() as cursor:
            cursor.execute(sql)
            sql_result = cursor.fetchall()
        result = []
        for e in sql_result:
            result.append(Newsletter(email=e["user_email"], newsletter=e["meta_value"]))
        return result

    def export(self, list):
        result = Result()
        for i in tqdm (range(len(list)), desc="Export Newsletter to IDjango...", ncols=75):
            response = self.utils.idjango_post('/v1/pool/newsletter/mail/', list[i].dict())
            result.add(response)
        result.print()

    def process(self, argv):
        if len(argv) < 2:
            print("no param")
        if argv[2] == "select":
            result = self.all()
            self.utils.print_list(result)
        elif argv[2] == "export":
            result = self.all()
            self.export(result)