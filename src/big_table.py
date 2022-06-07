# BigTable Module

import datetime
from google.cloud import bigtable
from google.cloud.bigtable import column_family
from google.cloud.bigtable import row_filters

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


# # 讀取現在所有的 Column Families
# def read_column_families(table):
#     column_families = list(table.list_column_families().keys())
#     return column_families


# 讀取現在所有的 Columns
def read_all_columns(table) -> dict:
    default_columns = read_vote(table, "default_columns")
    columns = dict()
    for cf, cols in default_columns:
        cols = [col.decode("utf-8") for col in cols.keys()]
        columns[cf] = cols if cf not in columns else columns[cf] + cols
    return columns


# 把某人的一筆投票記錄寫入資料庫
def write_one_vote(table, account_id: str, column_family_id: str, column_id: str, candidate_id: str):
    column = column_id.encode()
    row_key = account_id.encode()
    candidate_id = candidate_id.encode()
    row = table.direct_row(row_key)
    row.set_cell(
        column_family_id, column, candidate_id, timestamp=datetime.datetime.utcnow()
    )
    print("write")
    table.mutate_rows([row])


# 從資料庫讀取某人在某投票項目的紀錄
def read_vote(table, account_id: str, column_family_id: str = None, column_id: str = None):
    # Create a filter to only retrieve the most recent version of the cell for each column accross entire row.
    row_filter = row_filters.CellsColumnLimitFilter(1)
    row_key = account_id.encode()
    row = table.read_row(row_key, row_filter)
    if not column_family_id or not column_id:
        print(row)
        return row.cells.items()
    else:
        column = column_id.encode()
        cell = row.cells[column_family_id][column][0]
        return cell.value.decode("utf-8")


# 從資料庫讀取某個投票項目的所有投票紀錄總計
def read_all_votes(table, column_family_id: str, column_id: str):
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