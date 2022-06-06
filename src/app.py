## Import packages
import os
import yaml
import hashlib
import datetime

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

# User
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
 
  
# @app.route('/logout')  
# def logout():  
#     """  
#  logout\_user會將所有的相關session資訊給pop掉 
#  """ 
#     logout_user()  
#     return 'Logged out'  


## Routing
@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'GET':
        return render_template('index.html')
    if request.method == 'POST':
        person_id = request.form.get('person_id')
        health_id = request.form.get('health_id')
        id = f"{person_id}#{health_id}".encode('utf-8')
        print(id)
        ## Hash Function
        hash = hashlib.sha256()
        hash.update(id)
        hash_result = hash.hexdigest()
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
    account_id = current_user.id.split("#")[-1]
    column_family_id = "election"
    column_id = "taipei_mayor"
    if request.method == 'GET':
        return render_template('vote.html')
    if request.method == 'POST':
        candidate_id = request.form.get('selection')
        write_one_vote_to_bigtable(TABLE, account_id, column_family_id, column_id, candidate_id)
        return render_template('index.html')
    

# # 把某人的一筆投票記錄寫入資料庫
# def write_one_vote_to_bigtable(account_id: str, column_id: str, candidate_id: str):
#     greetings = ["Hello World!", "Hello Cloud Bigtable!", "Hello Python!"]
#     rows = []
#     column = column_id.encode()
#     for i, value in enumerate(greetings):
#         row_key = f"greeting{i}".encode()
#         row = table.direct_row(row_key)
#         row.set_cell(
#             column_family_id, column, value, timestamp=datetime.datetime.utcnow()
#         )
#         rows.append(row)
#     table.mutate_rows(rows)

# 把某人的一筆投票記錄寫入資料庫
def write_one_vote_to_bigtable(table, account_id: str, column_family_id: str, column_id: str, candidate_id: str):
    column = column_id.encode()
    row_key = account_id.encode()
    row = table.direct_row(row_key)
    row.set_cell(
        column_family_id, column, candidate_id, timestamp=datetime.datetime.utcnow()
    )
    table.mutate_rows([row])


# 從資料庫讀取某人在某投票項目的紀錄
def read_one_vote_from_bigtable(table, account_id: str, column_family_id: str, column_id: str):
    # Create a filter to only retrieve the most recent version of the cell for each column accross entire row.
    row_filter = row_filters.CellsColumnLimitFilter(1)
    column = column_id.encode()
    row_key = account_id.encode()
    row = table.read_row(row_key, row_filter)
    cell = row.cells[column_family_id][column][0]
    return cell.value.decode("utf-8")


# 從資料庫讀取某個投票項目的所有投票紀錄總計
def read_all_votes_from_bigtable(table, column_family_id: str, column_id: str):
    # Create a filter to only retrieve the most recent version of the cell for each column accross entire row.
    result = []
    row_filter = row_filters.CellsColumnLimitFilter(1)
    column = column_id.encode()
    partial_rows = table.read_rows(filter_=row_filter)
    for row in partial_rows:
        cell = row.cells[column_family_id][column][0]
        value = cell.value.decode("utf-8")
        result.append(value)
    return result


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=PORT_NUM)