box.cfg{listen = 3303}

abci_chains = box.schema.create_space('abci_chains', { if_not_exists = true })
abci_chains:format({
    { name = 'id', type = 'string' },
    { name = 'height', type = 'unsigned' },
    { name = 'is_synced', type = 'boolean' }
})
abci_chains:create_index('id', { parts = {'id'}})
abci_chains:create_index('height', { parts = {'height'}})


-- Transactions
transactions = box.schema.create_space('transactions', { if_not_exists = true })
transactions:format({
    { name = 'id', type = 'string' },
    { name = 'operation', type = 'string' },
    { name = 'version', type = 'string' },
    { name = 'metadata', type = 'string' },
    { name = 'assets', type = 'array' },
    { name = 'inputs', type = 'array', is_nullable = true },
    { name = 'scripts', type = 'map', is_nullable = true }
})
transactions:create_index('id', { parts = {{ field = 'id', type = 'string' }}})
transactions:create_index('transactions_by_asset', { parts = {
    { field = 'assets[*].id', type = 'string', is_nullable = true },
    { field = 'assets[*].data', type = 'string', is_nullable = true }
}})
transactions:create_index('spending_transaction_by_id_and_output_index', { parts = {
    { field = 'inputs[*].fulfills["transaction_id"]', type = 'string' },
    { field = 'inputs[*].fulfills["output_index"]', type = 'unsigned' }
}})


-- Outputs
outputs = box.schema.create_space('outputs', { if_not_exists = true })
outputs:format({
    { name = 'id', type = 'string' },
    { name = 'amount' , type='unsigned' },
    { name = 'public_keys', type='array' },
    { name = 'condition', type = 'map' },
    { name = 'output_index', type='number' },
    { name = 'transaction_id' , foreign_key = { space = 'transactions', field = 'id' }}
})
outputs:create_index('id', { parts = {{ field = 'id', type = 'string' }}})
outputs:create_index('transaction_id', { parts = {{ field = 'id', type = 'string' }}})
outputs:create_index('public_keys', { unique = false, parts = {{field = 'public_keys[*]', type  = 'string' }}})


-- Precommits
pre_commits = box.schema.create_space('pre_commits', { if_not_exists = true })
pre_commits:format({
    { name = 'id', type = 'string' },
    { name = 'height', type = 'unsigned' },
    { name = 'transaction_ids', type = 'array'}
})
pre_commits:create_index('id', { parts = {{ field = 'id', type = 'string' }}})
pre_commits:create_index('height', { parts = {{ field = 'height', type = 'unsigned' }}})


-- Blocks
blocks = box.schema.create_space('blocks', { if_not_exists = true })
blocks:format({
    { name = 'id', type = 'string' },
    { name = 'app_hash', type = 'string' },
    { name = 'height', type = 'unsigned' },
    { name = 'transaction_ids', type = 'array' }
})
blocks:create_index('id', { parts = {{ field = 'id', type = 'string' }}})
blocks:create_index('height', { parts = {{ field = 'height', type = 'unsigned' }}})
blocks:create_index('block_by_transaction_id', { parts = {{ field = 'transaction_ids[*]', type = 'string' }}})


-- UTXO
utxos = box.schema.create_space('utxos', { if_not_exists = true })
utxos:format({
    { name = 'id', type = 'string' },
    { name = 'transaction_id', foreign_key = { space = 'transactions', field = 'id' } },
    { name = 'output_index', type = 'unsigned' },
    { name = 'utxo', type = 'map' }
})
utxos:create_index('id', { parts = {{ field = 'id', type = 'string' }}})
utxos:create_index('utxo_by_transaction_id_and_output_index', { parts = {
    { field = 'transaction_id', type = 'string' },
    { field = 'output_index', type = 'unsigned' }
}})


-- Elections
elections = box.schema.create_space('elections', { if_not_exists = true })
elections:format({
    { name = 'id', type = 'string' },
    { name = 'height', type = 'unsigned' },
    { name = 'is_concluded', type = 'boolean' }
})
elections:create_index('id', { parts = {{ field = 'id', type = 'string' }}})
elections:create_index('height', { parts = {{ field = 'height', type = 'unsigned' }}})


-- Validators
validator_sets = box.schema.create_space('validator_sets', { if_not_exists = true })
validator_sets:format({
    { name = 'id', type = 'string' },
    { name = 'height', type = 'unsigned' },
    { name = 'set', type = 'array' }
})
validator_sets:create_index('id', { parts = {{ field = 'id', type = 'string' }}})