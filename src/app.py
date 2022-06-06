import datetime
from flask import Flask, render_template
from google.cloud import bigtable
from google.cloud.bigtable import column_family
from google.cloud.bigtable import row_filters

app = Flask(__name__)

# [START bigtable_hw_connect]

# The client must be created with admin=True because it will create a table
# client = bigtable.Client(project=project_id, admin=True)
# instance = client.instance(instance_id)
# table = instance.table(table_id)

# [END bigtable_hw_connect]

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/vote/")
def vote():
    return render_template('vote.html')

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
    app.run(host="0.0.0.0", port=80)