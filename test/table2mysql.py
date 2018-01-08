import pymysql
import pandas as pd

conn = pymysql.connect(
    host='127.0.0.1',
    user='lxgui',
    passwd='123',
    db='jx3',
    charset="utf8",
)

cur = conn.cursor()
cur.execute("USE jx3")

sql = "INSERT INTO `jx_account` \
           (`region`, `server`, `menpai`, `tixing`, `waiguan`, \
           `price`, `detail`, `contact_information`, `create_time`)\
           VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"

df = pd.read_csv('test_data.csv')
for each in df.index:
    eachline_list = [str(each) for each in df.loc[each]]
    region, server, menpai, tixing, waiguan, price = eachline_list[:6]
    contact_information = 'qq:12345678 ## test'
    detail = eachline_list[-2]
    create_time = eachline_list[-3]
    cur.execute(sql, (region, server, menpai,
                      tixing, waiguan, price,
                      detail, contact_information, create_time))
    conn.commit()

cur.close()
conn.close()
    
    


