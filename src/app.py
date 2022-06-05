import datetime
from flask import Flask, render_template
from google.cloud import bigtable
from google.cloud.bigtable import column_family
from google.cloud.bigtable import row_filters

app = Flask(__name__)

# [START bigtable_hw_connect]

# The client must be created with admin=True because it will create a table
client = bigtable.Client(project=project_id, admin=True)
instance = client.instance(instance_id)
table = instance.table(table_id)

# [END bigtable_hw_connect]

@app.route("/")
def index():
    return render_template('index.html')

@app.route("/vote/")
def vote():
    return render_template('vote.html')

# 把某人的一筆投票記錄寫入資料庫
def write_one_vote_to_bigtable(account_id, column_id, candidate_id):
    print("Writing some greetings to the table.")
    greetings = ["Hello World!", "Hello Cloud Bigtable!", "Hello Python!"]
    rows = []
    column = "greeting".encode()
    for i, value in enumerate(greetings):
        row_key = "greeting{}".format(i).encode()
        row = table.direct_row(row_key)
        row.set_cell(
            column_family_id, column, value, timestamp=datetime.datetime.utcnow()
        )
        rows.append(row)
    table.mutate_rows(rows)

# 從資料庫讀取某人在某投票項目的紀錄
def read_one_vote_from_bigtable(account_id, column_id):
    # Create a filter to only retrieve the most recent version of the cell for each column accross entire row.
    row_filter = row_filters.CellsColumnLimitFilter(1)
    print("Getting a single greeting by row key.")
    key = "greeting0".encode()
    row = table.read_row(key, row_filter)
    cell = row.cells[column_family_id][column][0]
    print(cell.value.decode("utf-8"))

# 從資料庫讀取某個投票項目的所有投票紀錄總計
def read_all_votes_from_bigtable(column_id):
    # Create a filter to only retrieve the most recent version of the cell for each column accross entire row.
    row_filter = row_filters.CellsColumnLimitFilter(1)
    print("Scanning for all greetings:")
    partial_rows = table.read_rows(filter_=row_filter)
    for row in partial_rows:
        cell = row.cells[column_family_id][column][0]
        print(cell.value.decode("utf-8"))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)