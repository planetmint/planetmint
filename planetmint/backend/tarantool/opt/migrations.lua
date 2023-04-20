local functions = require('functions')
local migrations = {}

migrations.update_utxo_13042023 = {}

migrations.update_utxo_13042023.up = function()
    if utxos.index.public_keys == nil then
        box.space.utxos:drop()
        utxos = box.schema.create_space('utxos', { if_not_exists = true })
        utxos:format({
            { name = 'id', type = 'string' },
            { name = 'amount' , type = 'unsigned' },
            { name = 'public_keys', type = 'array' },
            { name = 'condition', type = 'map' },
            { name = 'output_index', type = 'number' },
            { name = 'transaction_id' , type = 'string' }
        })
        utxos:create_index('id', { 
            if_not_exists = true,
            parts = {{ field = 'id', type = 'string' }}
        })
        utxos:create_index('utxos_by_transaction_id', {
            if_not_exists = true,
            unique = false,
            parts = {{ field = 'transaction_id', type = 'string' }}
        })
        utxos:create_index('utxo_by_transaction_id_and_output_index', { 
            if_not_exists = true,
            parts = {
                { field = 'transaction_id', type = 'string' },
                { field = 'output_index', type = 'unsigned' }
            }
        })
        utxos:create_index('public_keys', { 
            if_not_exists = true,
            unique = false,
            parts = {{field = 'public_keys[*]', type  = 'string' }}
        })
    end

    outputs = box.space.outputs
    functions.atomic(1000, outputs:pairs(), function(output)
        utxos:insert{output[0], output[1], output[2], output[3], output[4], output[5]}
    end)
    functions.atomic(1000, utxos:pairs(), function(utxo) 
        spending_transaction = transactions.index.spending_transaction_by_id_and_output_index:select{utxo[5], utxo[4]}
        if table.getn(spending_transaction) > 0 then
            utxos:delete(utxo[0])
        end
    end)
end

migrations.update_utxo_13042023.down = function()
    box.space.utxos:drop()
    utxos = box.schema.create_space('utxos', { if_not_exists = true })
    utxos:format({
        { name = 'id', type = 'string' },
        { name = 'transaction_id', type = 'string' },
        { name = 'output_index', type = 'unsigned' },
        { name = 'utxo', type = 'map' }
    })
    utxos:create_index('id', { 
        if_not_exists = true,
        parts = {{ field = 'id', type = 'string' }}
    })
    utxos:create_index('utxos_by_transaction_id', {
        if_not_exists = true,
        unique = false,
        parts = {{ field = 'transaction_id', type = 'string' }}
    })
    utxos:create_index('utxo_by_transaction_id_and_output_index', { 
        if_not_exists = true,
        parts = {
            { field = 'transaction_id', type = 'string' },
            { field = 'output_index', type = 'unsigned' }
    }})
end

return migrations