
import uuid
from pydantic import BaseModel
from .result import Result
from tqdm import tqdm
from .utils import Utils , Modified

class Profile(BaseModel):
    id: str
    gender: str
    phone: str
    birthdate: int
    user_id: str
    modified: Modified

class ProfileHandler:

    def __init__(self) -> None:
        self.utils = Utils()
        self.drops = self.utils.connect_drops()

    
    def all(self):
        sql = ('select s.sex, s.mobile_phone, s.birthday, u.public_id, u.created, u.updated '
                'from User as u '
                'left join Profile as p on u.id = p.user_id ' 
                'left join Supporter as s on p.id = s.profile_id '
                'where p.confirmed = 1')
        with self.drops.cursor() as cursor:
            cursor.execute(sql)
            sql_result = cursor.fetchall()
        result = []
        for x in sql_result:
            user_id = str(uuid.UUID(bytes=x['public_id']))
            modified=Modified(created=int(x['created']/1000), updated=int(x['updated']/1000))
            birthdate = 0
            if x['birthday'] != None:
                birthdate=int(x['birthday']/1000)
            result.append(
                Profile(
                    id='',
                    gender=x['sex'],
                    phone=x['mobile_phone'],
                    birthdate=birthdate,
                    user_id=user_id,
                    modified=modified
                )
            )
        return result

    def export(self, list: list[Profile]):
        result = Result()
        for i in tqdm (range(len(list)), desc="Export Profile to IDjango...", ncols=75):
            response = self.utils.idjango_post('/v1/pool/profile/', list[i].dict())
            result.add(response)
        result.print()

    def process(self, argv):
        if argv[2] == 'all':
            result = self.all()
            print(result)
        if argv[2] == 'export':
            result = self.all()
            self.export(result)