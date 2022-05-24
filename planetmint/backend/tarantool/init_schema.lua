abci_chains:format({{name='height' , type='integer'},{name='is_synched' , type='boolean'},{name='chain_id',type='string'}})
assets:format({{name='data' , type='any'}, {name='tx_id', type='string'}, {name='asset_id', type='string'}})
blocks:format{{name='app_hash',type='string'},{name='height' , type='integer'},{name='block_id' , type='string'}}
blocks_tx:format{{name='transaction_id', type = 'string'}, {name = 'block_id', type = 'string'}}
elections:format({{name='election_id' , type='string'},{name='height' , type='integer'}, {name='is_concluded' , type='boolean'}})
meta_datas:format({{name='transaction_id' , type='string'}, {name='meta_data' , type='any'}})
pre_commits:format({{name='commit_id', type='string'}, {name='height',type='integer'}, {name='transactions',type=any}})
validators:format({{name='validator_id' , type='string'},{name='height',type='integer'},{name='validators' , type='any'}})
transactions:format({{name='transaction_id' , type='string'}, {name='operation' , type='string'}, {name='version' ,type='string'}, {name='dict_map', type='any'}})
inputs:format({{name='transaction_id' , type='string'}, {name='fulfillment' , type='any'}, {name='owners_before' , type='array'}, {name='fulfills_transaction_id', type = 'string'}, {name='fulfills_output_index', type = 'string'}, {name='input_id', type='string'}, {name='input_index', type='number'}})
outputs:format({{name='transaction_id' , type='string'}, {name='amount' , type='string'}, {name='uri', type='string'}, {name='details_type', type='string'}, {name='details_public_key', type='any'}, {name = 'output_id', type = 'string'}, {name='treshold', type='any'}, {name='subconditions', type='any'}, {name='output_index', type='number'}})
keys:format({{name = 'id', type='string'}, {name = 'transaction_id', type = 'string'} ,{name = 'output_id', type = 'string'}, {name = 'public_key', type = 'string'}, {name = 'key_index', type = 'integer'}})
utxos:format({{name='transaction_id' , type='string'}, {name='output_index' , type='integer'}, {name='utxo_dict', type='string'}})