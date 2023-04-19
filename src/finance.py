from .utils import Utils
from typing import List, Optional
from pydantic import BaseModel, validator
from tqdm import tqdm
from pprint import pprint
import csv
import pandas as pd

class TakingDatabase(BaseModel):
    id: int
    public_id: str
    received: int
    description: str
    category: str
    comment: str
    reason_for_payment: str
    receipt: bool
    author: str
    created: int
    updated: int

class SourceDatabase(BaseModel):
    id: int
    public_id: str
    taking_id:int
    category: str
    description: Optional[str] = ""
    amount: float
    currency: str
    type_of_source: str
    type_location: Optional[str] = ""
    type_contact_person: Optional[str] =""
    type_email: Optional[str] = ""
    type_address: Optional[str] = ""
    receipt: Optional[bool] = False
    norms: str

class Taking(BaseModel):
    id: int
    public_id: str
    received: int
    description: str
    category: str
    comment: str
    reason_for_payment: str
    receipt: bool
    author: str
    created: int
    updated: int
    sources: List[SourceDatabase]    

class TakingCSVEntry(BaseModel):
    taking_id: str
    t_public_id: str
    received: str
    received: int
    description: str
    category: str
    comment: str
    reason_for_payment: str
    receipt: bool
    author: str
    created: int
    updated: int
    source_id: int
    s_public_id: str
    s_category: str
    s_description: Optional[str] = ""
    amount: float
    currency: str
    type_of_source: str
    type_location: Optional[str] = ""
    type_contact_person: Optional[str] =""
    type_email: Optional[str] = ""
    type_address: Optional[str] = ""
    s_receipt: Optional[bool] = False
    norms: str

class DepositCSVEntry(BaseModel):
    taking_id: str
    t_public_id: str
    received: str
    received: int
    description: str
    category: str
    comment: str
    reason_for_payment: str
    receipt: bool
    author: str
    t_created: int
    t_updated: int
    amount: int
    currency: str
    du_created: int
    deposit_id: int
    d_public_id: str
    full_amount: int
    crew: str
    crew_name: str
    supporter: str
    supporter_name: str
    date_of_deposit: int





class FinanceHandler:

    def __init__(self):
        self.utils = Utils()
        self.conn = self.utils.connect_stream()
        self.storage = self.utils.get_env_string("STORAGE")

    def get_taking(self):
        sql_taking = ('select * from Taking')
        sql_source = ('select * from Source where taking_id = %s')
        with self.conn.cursor() as cursor:
            cursor.execute(sql_taking)
            sql_result = cursor.fetchall()
        result = []
        for i in tqdm (range(len(sql_result)), desc="Create Takings form Database...", ncols=75):
            element = sql_result[i]
            taking_database = TakingDatabase(**element)
            with self.conn.cursor() as cursor:
                cursor.execute(sql_source, taking_database.id)
                sql_result2 = cursor.fetchall()
            
            sources = []
            for source in sql_result2:
                source = SourceDatabase(**source)
                sources.append(source)
            taking = Taking(**taking_database.dict(), sources=sources)
            result.append(taking)
        return result

    def get_source_taking(self):
        sql_taking = ('select ' 
            't.id as taking_id, t.public_id as t_public_id, received, t.description as description, t.category as category, comment, '
            'reason_for_payment, t.receipt as receipt, '
            'author, created, updated, s.id as source_id, s.public_id as s_public_id, s.category as s_category, '
            's.description as s_description, amount, currency, type_of_source, type_location, type_contact_person, '
            'type_email, type_address, s.receipt as s_receipt, norms '
            'from Taking as t left join Source as s on s.taking_id = t.id where t.comment != "Migration from Pool1"')
        with self.conn.cursor() as cursor:
            cursor.execute(sql_taking)
            sql_result = cursor.fetchall()
        result = []
        for e in sql_result:
            taking = TakingCSVEntry(**e)
            result.append(taking)
        data_file = open(self.storage + '/source_taking_'+ self.utils.today()+'.csv', 'w')
        csv_writer = csv.writer(data_file)
        count = 0
        for emp in result:
            if count == 0:
                header = emp.dict().keys()
                csv_writer.writerow(header)
                count += 1
            csv_writer.writerow(emp.dict().values())
        data_file.close()
         
    
    def get_deposit_taking(self):
        sql_deposit = ('select ' 
            't.id as taking_id, t.public_id as t_public_id, received, t.description as description, t.category as category, comment, '
            'reason_for_payment, t.receipt as receipt, '
            'author, t.created as t_created, t.updated as t_updated, ' 
            'amount, du.currency as currency, du.created as du_created, deposit_id, d.public_id as d_public_id, '
            'full_amount, crew, crew_name, supporter, supporter_name, date_of_deposit '
            'from Deposit as d '
            'left join Deposit_Unit as du on du.deposit_id = d.id '
            'left join Taking as t on t.id = du.taking_id '
            'where t.comment != "Migration from Pool1"')
        with self.conn.cursor() as cursor:
            cursor.execute(sql_deposit)
            sql_result = cursor.fetchall()
        result = []
        for e in sql_result:
            taking = DepositCSVEntry(**e)
            result.append(taking)
        path = self.storage + '/deposit_taking_'+self.utils.today()
        data_file = open(path + '.csv', 'w')
        csv_writer = csv.writer(data_file)
        count = 0
        for emp in result:
            if count == 0:
                header = emp.dict().keys()
                csv_writer.writerow(header)
                count += 1
            csv_writer.writerow(emp.dict().values())
        data_file.close()

    def process(self, argv):
        func = argv[2]
        if func == "get":
            model = argv[3]
            if model == "taking":
                self.get_taking()
            elif model == "source":
                self.get_source_taking()
            elif model == "deposit":
                self.get_deposit_taking()
