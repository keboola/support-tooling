import kbc.kbcapi_scripts as kbc

token = ''
config = kbc.get_config_detail(token, 'US', 'keboola.ex-db-pgsql', '1095794158')
print(config)

for row in config['rows']:
    if 'sample_table' not in row['name']:
        continue
    row_id = row['id']
    config = row['configuration']
    config['parameters']['incrementalFetchingColumn'] = 'id'
    config['parameters']['primaryKey'] = ['id']
    kbc.update_config_row(token, 'US', 'keboola.ex-db-pgsql', '1095794158', row_id, row['name'],
                          configuration=config)
