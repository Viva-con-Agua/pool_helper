import uuid
from pydantic import BaseModel
from .result import Result
from tqdm import tqdm
from .utils import Utils

class UserCrew(BaseModel):
    user_id: str
    crew_id: str

class UserCrewHandler:

    def __init__(self) -> None:
        self.utils = Utils()
        self.drops = self.utils.connect_drops()

    def all(self):
        sql = ('select distinct c.publicId, u.public_id ' 
            'from  User as u ' 
            'left join Profile as p on p.user_id = u.id '
            'left join Supporter as s on s.profile_id = p.id '
            'left join Supporter_Crew as sc on sc.supporter_id = s.id '
            'left join Crew as c on c.id = sc.crew_id '
            'where p.confirmed = 1')
        with self.drops.cursor() as cursor:
            cursor.execute(sql)
            sql_result = cursor.fetchall()
        result = []
        for x in sql_result:
            if x['publicId'] == None:
                continue
            user_id = str(uuid.UUID(bytes=x['public_id']))
            crew_id = str(uuid.UUID(bytes=x['publicId']))
            result.append(
                UserCrew(
                    user_id=user_id,
                    crew_id=crew_id,
                )
            )
        return result

    def fix_active(self):
        sql = ('select distinct(sc1.supporter_id) '
               'from Supporter_Crew as sc1 '
               'WHERE sc1.active = "active" '
               'AND exists (SELECT 1 FROM Supporter_Crew as sc2 WHERE sc2.supporter_id = sc1.supporter_id and sc2.active IS NULL)')
        with self.drops.cursor() as cursor:
            cursor.execute(sql)
            sql_result = cursor.fetchall()

        result = ('update Supporter_Crew set active="active" where supporter_id in (%s) ')
        with self.drops.cursor() as cursor:
            cursor.execute(result, ', '.join(str(_['supporter_id']) for _ in sql_result))
        self.drops.commit()
        return ', '.join(str(_['supporter_id']) for _ in sql_result)

    def fix_nvm(self):
        sql = ('select DISTINCT(sc1.supporter_id), sc1.nvm_date '
               'from Supporter_Crew as sc1 '
               'where sc1.nvm_date IS NOT NULL '
               'AND exists (SELECT 1 FROM Supporter_Crew as sc2 WHERE sc2.supporter_id = sc1.supporter_id and sc2.nvm_date IS NULL)')
        with self.drops.cursor() as cursor:
            cursor.execute(sql)
            sql_result = cursor.fetchall()

        for x in sql_result:
            sql = "update Supporter_Crew set nvm_date = %i where supporter_id = %i" % (x['nvm_date'], x['supporter_id'])
            with self.drops.cursor() as cursor:
                cursor.execute(sql)
            self.drops.commit()

        return ', '.join(str(_['supporter_id']) for _ in sql_result)

    def export(self, list):
        result = Result()
        for i in tqdm (range(len(list)), desc="Export UserCrew to IDjango...", ncols=75):
            response = self.utils.idjango_post('/v1/pool/crew/', list[i].dict())
            result.add(response)
        result.print() 
    
    def process(self, argv):
        if argv[2] == 'all':
            result = self.all()
            print(result)
        if argv[2] == 'export':
            result = self.all()
            self.export(result)
        if argv[2] == 'fix_active':
            result = self.fix_active()
            print(result)
        if argv[2] == 'fix_nvm':
            result = self.fix_nvm()
            print(result)
