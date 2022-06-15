

import copy
from typing import List

from tqdm import tqdm

from .result import Result
from .utils import Utils


newsletter = {
    "email": "",
    "newsletter": ""
}

class Newsletter:

    def __init__(self) -> None:
        self.utils = Utils()
        self.pool1 = self.utils.connect_pool1()

    def select_all(self) -> List:
        sql = ( 'select user_email, meta_value from wp_users as u '
        'left join wp_usermeta as m on u.ID = m.user_id '
        'where m.meta_key = "mail_switch" && m.meta_value != "none"')
        with self.pool1.cursor() as cursor:
            cursor.execute(sql)
            sql_result = cursor.fetchall()
        result = []
        for entry in sql_result:
            n = copy.deepcopy(newsletter)
            n["email"] = entry["user_email"].lower()
            n["newsletter"] = entry["meta_value"]
            result.append(n)
        return result

    def export_all(self):
        data = self.select_all()
        result = Result()
        for i in tqdm (range(len(data)), desc="Export Newsletter to IDjango...", ncols=75):
            response = self.utils.idjango_post('/v1/pool/newsletter/', data[i])
            result.add(response)
        result.print()

    def process(self, argv):
        if len(argv) < 2:
            print("no param")
        if argv[2] == "select":
            result = self.select_all()
            self.utils.print_list(result)
        elif argv[2] == "export":
            self.export_all()