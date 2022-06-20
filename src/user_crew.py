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

    def export(self, list: list[UserCrew]):
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