import MySQLdb
import psycopg2
import pymssql
import pandas as pd
from pymongo import MongoClient
from urllib.parse import quote_plus
from config import config

mysql_config = config.get('MYSQL_DB')
con= MySQLdb.connect(**mysql_config) #return Connection object
query = """SELECT * FROM northwind.Territories;"""
cursor = con.cursor() #Connection.cursor() return Cursor object
try: 
    cursor.execute(query)
    # cursor.fetchone() # return tuple
    # cursor.fetchmany(5) # return tuple of tuple
    data = cursor.fetchall() # return tuple of tuple
    con.commit()
except Exception as e:
    print('Error: ', e)
    con.rollback()
data = pd.DataFrame(data)
print(data[:5])

#postgres
connection_config = config.get('PG_DB')
connection = psycopg2.connect(**connection_config)
cursor = connection.cursor()
query = """SELECT * FROM public.categories"""
try: 
    cursor.execute(query)
    # cursor.fetchone() #return  tuple
    data = cursor.fetchmany(5) #return list of tuples
    # cursor.fetchall() #return list of tuples
except Exception as error:
    connection.rollback()
    print('Error: ', error)
data = pd.DataFrame(data)
print(data[:5])

#MYSQL
con_config = {'host': 'localhost', 'port': 1433, 'user': 'sa', 'password': 'Buixuantoan@916263', 'database': 'Northwind'}
con = pymssql.connect(**con_config)
cursor = con.cursor()
query = """SELECT * FROM dbo.Categories"""
try:
    cursor.execute(query)
    data = cursor.fetchmany()
except Exception as e:
    print('Exception: ', e)
    con.rollback()

data = pd.DataFrame(data)
print(data[:5])

#mongdb
import pandas as pd
con_config = {'user': 'root', 'password': 'Buixuantoan@916263', 'host': 'localhost', 'port': '27018'}
con_config['user'] = quote_plus(con_config.get('user'))
con_config['password'] = quote_plus(con_config.get('password')) 
user, password, host, port = 'root', 'Buixuantoan@916263', 'localhost', 27018
con_uri = 'mongodb://{user}:{password}@{host}:{port}/?authMechanism=DEFAULT'.format(**con_config)
client = MongoClient(con_uri)
database = client['sample_airbnb'] #create database if not exist
collection = database['listingsAndReviews'] #create collection if not exist
docs = collection.find({'description': {"$regex": "^Fantastic"}})
for doc in docs:
    print(doc)

#summary on config in python project
    # store config data in config.py
    # from config import config
    # config.get('key').get('key')
