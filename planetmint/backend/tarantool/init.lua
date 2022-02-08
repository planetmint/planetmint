box.cfg{listen=3301}

transactions = box.schema.space.create('transactions',{engine='memtx' , is_sync=false,if_not_exists = true})
transactions:format({{name='transaction_id' , type='string'},{name='operation' , type='string'}, {name='version' ,type='string'}})
transactions:create_index('id_search' , {type = 'hash' , parts={'transaction_id'},if_not_exists=true})

inputs = box.schema.space.create('inputs',{engine='memtx' , is_sync=false,if_not_exists = true})
inputs:format({{name='transaction_id' , type='string'},{name='fullfilment' , type='string'},{name='owners_before' , type='array'}, {name='fulfills_transaction_id', type = 'string'}, {name='fulfills_output_index', type = 'string'}})
inputs:create_index('spent_search' , {type = 'hash' , parts={'fulfills_transaction_id', 'fulfills_output_index'},if_not_exists=true})

outputs = box.schema.space.create('outputs',{engine='memtx' , is_sync=false,if_not_exists = true})
outputs:format({{name='transaction_id' , type='string'}, {name='amount' , type='string'}, {name='uri', type='string'}, {name='details_type', type='string'}, {name='details_public_key', type='string'}, {name = 'public_keys', type = 'array'}})
outputs:create_index('id_search' ,{type='hash' , parts={'transaction_id'},if_not_exists=true})
outputs:create_index('keys_search' ,{type='rtree' , parts={'public_keys'},if_not_exists=true})

keys = box.schema.space.create('keys',{engine='memtx' , is_sync=false,if_not_exists = true})
keys:format({{name='transaction_id' , type='string'}, {name='public_keys' , type='array'}, {name = 'output_id', type = 'string'}})
keys:create_index('id_search' ,{type='hash' , parts={'transaction_id', 'output_id'},if_not_exists=true})
keys:create_index('keys_search', {type='rtree', parts={'public_keys'},if_not_exists=true})