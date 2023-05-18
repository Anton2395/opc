from service import create_connection, get_connection


conn_db, cursor_db = create_connection()
for i in get_connection(cursor=cursor_db):
    print('-------------------')
    print(i['driver'])
    for j in i['area']:
        for u in j['value_list']:
            print(u)
    print('-------------------')
conn_db.close()
