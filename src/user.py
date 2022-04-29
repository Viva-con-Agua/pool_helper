import pymysql, pymysql.cursors, os
from dotenv import load_dotenv

userModel = {
    'id': '',
    'first_name': '',
    'last_name': '',
    'full_name': '',
    'display_name': '',
    'country': '',
    'privacy_policy': '',
    'confirmed': '',
}

class User:

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
    
    def getUser(self):
        sql = ('select * from User as u ' 
                'left join Profile as p on u.id = p.user_id ' 
                'left join Supporter as s on s.profile_id = p.id '
                'left join Address as a on a.supporter_id = s.id'
                )
        with self.connection.cursor() as cursor:
            cursor.execute(sql)
            result = cursor.fetchall()
        return result

    def migrate(self):
        user = self.getUser()
        for i in user:
            print(i)


    def process(self, argv):
        if len(argv) < 2:
            print("no param")
        if argv[2] == "migrate":
            self.migrate()
