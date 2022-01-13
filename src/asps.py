import pymysql, pymysql.cursors, os, getopt, sys, csv
from pymysql import connections
from dotenv import load_dotenv
import time
import datetime
class Asps:
    def __init__(self):
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
    
    # crew, Name, email, pillar
    def set_list(self, file):
        with open(file) as csv_file:
            csv_reader= csv.reader(csv_file, delimiter=';')
            line_count = 0
            for row in csv_reader:
                if row[0] == None:
                    break
                if line_count == 0:
                    line_count += 1
                else:
                    try:
                        self.set(row[2], row[0], row[3])
                    except Exception as e:
                        print(e)
                    line_count += 1
            print(line_count)

    def all(self, crew):
        if crew != None:
            crew = 'and c.name = "' + crew + '"'
        else:
            crew = ""
        with self.connection.cursor() as cursor:
            sql = 'select p.email, s.full_name, c.name, sc.role, sc.pillar from Profile as p left join Supporter as s on p.id = s.profile_id left join Supporter_Crew as sc on sc.supporter_id = s.id left join Crew as c on c.id = sc.crew_id where sc.role = "VolunteerManager" ' + crew
            cursor.execute(sql)
            result = cursor.fetchall()
            print(result)


    def get(self, email=None, crew=None):
        if email != None and crew != None:
            where = 'where p.email = ' + '"' + email +'"' + ' and c.name = ' + '"'+crew+'"'
        elif email != None:
            where = 'where p.email = ' + '"' + email + '"'
        elif crew != None:
            where = 'where c.name = ' + '"'+crew+'"'
        else:
            print("error")
            exit(1)

        with self.connection.cursor() as cursor:
            sql = ('select p.email, s.full_name, c.name, sc.role, sc.pillar, sc.updated, sc.created '
                'from Profile as p '
                'left join Supporter as s on p.id = s.profile_id '
                'left join Supporter_Crew as sc on sc.supporter_id = s.id '
                'left join Crew as c on c.id = sc.crew_id ' + where )
            cursor.execute(sql)
            result = cursor.fetchall()
            print(result)
    


    def set(self, email, crew, pillar):
        presentDate = datetime.datetime.now()
        unix_timestamp = datetime.datetime.timestamp(presentDate)*1000
        with self.connection.cursor() as cursor:
            sql = ('select s.id from Profile as p left join Supporter as s on s.profile_id = p.id '
                    'where LOWER(email) = %s')
            cursor.execute(sql, (email.lower(),))
            result = cursor.fetchone()
            if result != None:
                s_id = result["id"]
            else:
                raise Exception(email + " -- No Profile with given email ")
            sql = ('select c.id from Crew as c where c.name = %s')
            cursor.execute(sql, (crew,))
            result = cursor.fetchone()
            if result != None:
                c_id = result["id"]
            else:
                raise Exception("No Crew with given crew " + crew)

        with self.connection.cursor() as cursor:
            # Create a new record
            sql = ("insert into Supporter_Crew " 
                    "(`supporter_id`, `crew_id`, `role`, `pillar`, `updated`, `created`, `active`, `nvm_date` )"
                    " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)")
            cursor.execute(sql, (s_id, c_id, "VolunteerManager", pillar, unix_timestamp, unix_timestamp, None, None,  ))

        # connection is not autocommit by default. So you must commit to save
        # your changes.
        self.connection.commit()
    
    
    
    def delete_for_crew(self, crew):
        with self.connection.cursor() as cursor:
            sql = ('select p.email, s.full_name, c.name, sc.role, sc.pillar '
                    'from Profile as p '
                    'left join Supporter as s on p.id = s.profile_id '
                    'left join Supporter_Crew as sc on sc.supporter_id = s.id '
                    'left join Crew as c on c.id = sc.crew_id '
                    'where sc.role = "VolunteerManager" and c.name = %s')
            cursor.execute(sql, (crew,))
            result = cursor.fetchall()
            email_list = []
            for e in result:
                email_list.append(e["email"])
            email_list = list(set(email_list))
            for email in email_list:
                self.deleteOrUpdate(email)



    def deleteOrUpdate(self, email):
        if email != None:
            where = 'where LOWER(p.email) = ' + '"' + email + '"'
        else:
            print("error")
            exit(1)

        with self.connection.cursor() as cursor:
            sql = ('select p.email, s.full_name, c.name, sc.role, sc.pillar, sc.updated, sc.created '
                'from Profile as p '
                'left join Supporter as s on p.id = s.profile_id '
                'left join Supporter_Crew as sc on sc.supporter_id = s.id '
                'left join Crew as c on c.id = sc.crew_id ' + where )
            cursor.execute(sql)
            result = cursor.fetchall()
        if len(result) == 1:
            self.update(email)
        else:
            self.delete(email)


    def update(self, email):
        print("update " + email)
        if email != None:
            where = 'where LOWER(p.email) = ' + '"' + email + '" and sc.role = "VolunteerManager"'
        else:
            print("error")
            exit(1)
        with self.connection.cursor() as cursor:
            sql = ('update Supporter_Crew as sc '
                    'left join Supporter as s on sc.supporter_id = s.id '
                    'left join Profile as p on s.profile_id = p.id '
                    'left join Crew as c on c.id = sc.crew_id ' 
                    'set sc.pillar = NULL, sc.role = NULL '
                    + where
                )
            cursor.execute(sql)
        self.connection.commit()

    def delete(self, email):
        print("delete " + email)
        if email != None:
            where = 'where LOWER(p.email) = ' + '"' + email + '" and sc.role = "VolunteerManager"'
        else:
            print("error")
            exit(1)
        with self.connection.cursor() as cursor:
            sql = ('delete sc '
                    'from Supporter_Crew as sc '
                    'left join Supporter as s on sc.supporter_id = s.id '
                    'left join Profile as p on s.profile_id = p.id '
                    'left join Crew as c on c.id = sc.crew_id ' 
                    + where
                )
            cursor.execute(sql)
        self.connection.commit()
