## Import packages
import os
import yaml
import datetime

import big_table
import utils

from flask import Flask, request, render_template, url_for, redirect
from flask_login import LoginManager, UserMixin, login_user, current_user, login_required, logout_user 

from google.cloud import bigtable
from google.cloud.bigtable import column_family
from google.cloud.bigtable import row_filters


##############################################################################

## Read Config File
with open("./config/config.yml", "r") as stream:
    try:
        config = yaml.safe_load(stream)
    except yaml.YAMLError as exc:
        print(exc)


## Set Bigtable & Other Config
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./config/gcp_key.json"

PROJECT_ID = config["project_id"]
INSTANCE_ID = config["instance_id"]

TABLE_ID = config["table_id"]

PORT_NUM = int(config["port_num"])
SECRET_KEY = config["secret_key"]


## Connect to Bigtable
# admin=True -> Because it will create a table
CLIENT = bigtable.Client(project=PROJECT_ID, admin=True)
INSTANCE = CLIENT.instance(INSTANCE_ID)
TABLE = INSTANCE.table(TABLE_ID)


## Initialize Flask APP
app = Flask(__name__)
app.secret_key = SECRET_KEY


## Login Management
login_manager = LoginManager()
login_manager.init_app(app)

##############################################################################


# Users
rows = TABLE.read_rows(filter_=row_filters.StripValueTransformerFilter(True))
users = [row.row_key.decode('utf-8') for row in rows]
# {user_id: user_info} pairs
users = {user.split("#")[-1]: user for user in users}
  
  
class User(UserMixin):
    pass  
  
  
# 檢查 user 登入狀態
@login_manager.user_loader  
def user_loader(id):   
    if id not in users.values():  
        return  
    user = User()  
    user.id = id
    return user   


## Routing
@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    if request.method == 'POST':
        person_id = request.form.get('person_id')
        health_id = request.form.get('health_id')
        id = f"{person_id}#{health_id}".encode('utf-8')
        ## Hash
        hash_result = utils.hash(id)
        #######
        if hash_result in users: 
            print("登入成功") 
            #  實作 User 類別  
            user = User()
            #  設置 id (這裡的 id 有包括年份與投票區)
            user.id = users[hash_result]
            #  這邊，透過 login_user 來記錄 user_id  
            login_user(user)
            #  登入成功，轉址  
            return redirect(url_for('vote')) 
        else:
            print("登入失敗") 
            print(hash_result)
            return render_template('index.html')  


@app.route("/vote", methods=['GET', 'POST'])
@login_required
def vote():
    #  current_user確實的取得了登錄狀態
    if current_user.is_active:  
        print(current_user.id)
    # 取得所有欄位名稱
    column_names = big_table.read_all_columns(TABLE)
    # 取得使用者帳號與區域
    account_id = current_user.id
    # 取得該使用者所屬的城市與行政區
    city, district = current_user.id.split("#")[1], current_user.id.split("#")[2]
    # print(f"該使用者所屬地區: {city} / {district}")
    # 取得該使用者可以投票的項目
    available_voting_items = dict()
    for column_family, columns in column_names.items():
        if column_family == "Status":
            continue
        if "#" not in columns[0]:
            available_voting_items[column_family] = columns
        else:
            for column in columns:
                # print(column)
                if column.split("#")[0] in [city, district]:
                    available_voting_items[column_family] = [column.split("#")[1]] if \
                        column_family not in available_voting_items else available_voting_items[column_family] + [column.split("#")[1]]
    print(available_voting_items)
    if request.method == 'GET':
        try:
            big_table.read_vote(TABLE, account_id, "Status", "Voted")
            print(big_table.read_vote(TABLE, account_id, "Status", "Voted"))
            # 登出
            logout_user()
            return render_template('fail.html')
        except:
            return render_template('vote.html', result=available_voting_items)
    if request.method == 'POST':
        voting_result = []
        for column_family in available_voting_items:
            candidate_id = request.form.get(column_family)
            voting_result.append([column_family, candidate_id])
            if candidate_id and candidate_id != "null":
                if candidate_id in column_names[column_family]:
                    big_table.write_one_vote(TABLE, account_id, column_family, candidate_id, "1")
                    continue
                for place in [city, district]:
                    column = f"{place}#{candidate_id}"
                    if column in column_names[column_family]:
                        big_table.write_one_vote(TABLE, account_id, column_family, column, "1")
        # 記錄使用者投完票了
        big_table.write_one_vote(TABLE, account_id, "Status", "Voted", "1")
        # 登出
        logout_user()
        return render_template('success.html', voting_result=voting_result)
    


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT_NUM)
    # usa_dict={'California':['Los_angles','San_francisco','San_diego'],'Texas':['Houston','San_Antonio','Dallas'] , 'Alaska':['Sitka','Juneau','Wrangell']}
    # for i in range(0, 10):
    #     j = i % len(usa_dict)
    #     j = list(usa_dict.keys())[j]
    #     k = i % len(usa_dict[j])
    #     id = f"{i}#{i}".encode('utf-8')
    #     account_id = f"2022#{j}#{usa_dict[j][k]}#{utils.hash(id)}"
    #     big_table.write_one_vote(TABLE, account_id, "Mayor", "Alaska#Iris", "")