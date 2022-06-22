

import copy
from ossaudiodev import control_labels
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
        self.drops = self.utils.connect_drops()

    def all(self) -> List:
        sql_user = ("select email from Profile where confirmed = 1")
        with self.drops.cursor() as cursor:
            cursor.execute(sql_user)
            sql_user_result = cursor.fetchall()
        
        sql_newsletter = ( 'select user_email, meta_value from wp_users as u '
        'left join wp_usermeta as m on u.ID = m.user_id '
        'where m.meta_key = "mail_switch" && u.user_email = %s')
        sql_result = []
        for i in tqdm (range(len(sql_user_result)), desc="Select Newsletter from Database...", ncols=75):
            if sql_user_result[i] == None:
                continue
            with self.pool1.cursor() as cursor:
                cursor.execute(sql_newsletter, sql_user_result[i]['email'])
                sql_result.append(cursor.fetchone())
        result = []
        for e in sql_result:
            if e == None:
                continue
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