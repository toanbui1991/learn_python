<<<<<<< HEAD
from decouple import config
import MySQLdb
import pandas as pd
import os

mysql_config = {'host': config('MYSQL_HOST'), 'port': int(config('MYSQL_PORT')), 'user': config('MYSQL_USER'), 'password': config('MYSQL_PASSWORD')}
print(mysql_config)
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
=======
from decouple import config
import MySQLdb
import pandas as pd
import os

mysql_config = {'host': config('MYSQL_HOST'), 'port': int(config('MYSQL_PORT')), 'user': config('MYSQL_USER'), 'password': config('MYSQL_PASSWORD')}
print(mysql_config)
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
>>>>>>> 83f62a4723ede795ba2a52293b61bce757c2d1b4
print(data)