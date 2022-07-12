import os, pymysql, pymysql.cursors
from dotenv import load_dotenv

class Confirm:

    def __init__(self) -> None:
        load_dotenv()
        password=os.getenv('DROPS_PASSWORD')
        port_string= os.getenv("DROPS_PORT")
        if port_string != None:
            port = int(port_string)
        else:
            port = 3306
        if password == None:
            print("set")
            exit(1)
        self.connection = pymysql.connect(
                host=os.getenv('DROPS_HOST'),
                port=port,
                user=os.getenv('DROPS_USER'),
                password=password,
                database="drops",
                cursorclass=pymysql.cursors.DictCursor
                )

    def confirm(self, email):
        sql = "update Profile set confirmed = 1 where email = %s"
        with self.connection.cursor() as cursor:
            cursor.execute(sql, email)
        self.connection.commit()

    def process(self, argv):
        if len(argv) < 2:
            print("no param")

