box.cfg{listen = 3303}

box.once("bootstrap", function()
    box.schema.user.grant('guest','read,write,execute,create,drop','universe')
end)


function init()
    -- ABCI chains
    abci_chains = box.schema.create_space('abci_chains', { if_not_exists = true })
    abci_chains:format({
        { name = 'id', type = 'string' },
        { name = 'height', type = 'unsigned' },
        { name = 'is_synced', type = 'boolean' }
    })
    abci_chains:create_index('id', { 
        if_not_exists = true, 
        parts = {{ field = 'id', type = 'string' }}
    })
    abci_chains:create_index('height', { 
        if_not_exists = true,
        unique = false,
        parts = {{ field = 'height', type = 'unsigned' }}
    })


    -- Transactions
    transactions = box.schema.create_space('transactions', { if_not_exists = true })
    transactions:format({
        { name = 'id', type = 'string' },
        { name = 'operation', type = 'string' },
        { name = 'version', type = 'string' },
        { name = 'metadata', type = 'string', is_nullable = true },
        { name = 'assets', type = 'array' },
        { name = 'inputs', type = 'array' },
        { name = 'scripts', type = 'map', is_nullable = true }
    })
    transactions:create_index('id', { 
        if_not_exists = true,
        parts = {{ field = 'id', type = 'string' }}
    })
    transactions:create_index('transactions_by_asset_id', { 
        if_not_exists = true,
        unique = false,
        parts = {
            { field = 'assets[*].id', type = 'string', is_nullable = true }
        }
    })
    transactions:create_index('transactions_by_asset_cid', {
        if_not_exists = true,
        unique = false,
        parts = {
            { field = 'assets[*].data', type = 'string', is_nullable = true }
        }
    })
    transactions:create_index('transactions_by_metadata_cid', {
        if_not_exists = true,
        unique = false,
        parts = {{ field = 'metadata', type = 'string' }}
    })
    transactions:create_index('spending_transaction_by_id_and_output_index', { 
        if_not_exists = true,
        parts = {
            { field = 'inputs[*].fulfills["transaction_id"]', type = 'string', is_nullable = true },
            { field = 'inputs[*].fulfills["output_index"]', type = 'unsigned', is_nullable = true }
    }})
    transactions:create_index('transactions_by_id_and_operation', {
        if_not_exists = true,
        parts = {
            { field = 'id', type = 'string' },
            { field = 'operation', type = 'string' },
            { field = 'assets[*].id', type = 'string', is_nullable = true }
        }
    })

    -- Governance
    governance = box.schema.create_space('governance', { if_not_exists = true })
    governance:format({
        { name = 'id', type = 'string' },
        { name = 'operation', type = 'string' },
        { name = 'version', type = 'string' },
        { name = 'metadata', type = 'string', is_nullable = true },
        { name = 'assets', type = 'array' },
        { name = 'inputs', type = 'array' },
        { name = 'scripts', type = 'map', is_nullable = true }
    })
    governance:create_index('id', {
        if_not_exists = true,
        parts = {{ field = 'id', type = 'string' }}
    })
    governance:create_index('governance_by_asset_id', { 
        if_not_exists = true,
        unique = false,
        parts = {
            { field = 'assets[*].id', type = 'string', is_nullable = true }
        }
    })
    governance:create_index('spending_governance_by_id_and_output_index', { 
        if_not_exists = true,
        parts = {
            { field = 'inputs[*].fulfills["transaction_id"]', type = 'string', is_nullable = true },
            { field = 'inputs[*].fulfills["output_index"]', type = 'unsigned', is_nullable = true }
    }})

    -- Outputs
    outputs = box.schema.create_space('outputs', { if_not_exists = true })
    outputs:format({
        { name = 'id', type = 'string' },
        { name = 'amount' , type = 'unsigned' },
        { name = 'public_keys', type = 'array' },
        { name = 'condition', type = 'map' },
        { name = 'output_index', type = 'number' },
        { name = 'transaction_id' , type = 'string' }
    })
    outputs:create_index('id', {
        if_not_exists = true, 
        parts = {{ field = 'id', type = 'string' }}
    })
    outputs:create_index('transaction_id', { 
        if_not_exists = true,
        unique = false,
        parts = {{ field = 'transaction_id', type = 'string' }}
    })
    outputs:create_index('public_keys', { 
        if_not_exists = true,
        unique = false,
        parts = {{field = 'public_keys[*]', type  = 'string' }}
    })


    -- Precommits
    pre_commits = box.schema.create_space('pre_commits', { if_not_exists = true })
    pre_commits:format({
        { name = 'id', type = 'string' },
        { name = 'height', type = 'unsigned' },
        { name = 'transaction_ids', type = 'array'}
    })
    pre_commits:create_index('id', { 
        if_not_exists = true,
        parts = {{ field = 'id', type = 'string' }}
    })
    pre_commits:create_index('height', { 
        if_not_exists = true,
        parts = {{ field = 'height', type = 'unsigned' }}
    })


    -- Blocks
    blocks = box.schema.create_space('blocks', { if_not_exists = true })
    blocks:format({
        { name = 'id', type = 'string' },
        { name = 'app_hash', type = 'string' },
        { name = 'height', type = 'unsigned' },
        { name = 'transaction_ids', type = 'array' }
    })
    blocks:create_index('id', { 
        if_not_exists = true,
        parts = {{ field = 'id', type = 'string' }}
    })
    blocks:create_index('height', { 
        if_not_exists = true,
        parts = {{ field = 'height', type = 'unsigned' }}
    })
    blocks:create_index('block_by_transaction_id', { 
        if_not_exists = true,
        parts = {{ field = 'transaction_ids[*]', type = 'string' }}
    })


    -- UTXO
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


    -- Elections
    elections = box.schema.create_space('elections', { if_not_exists = true })
    elections:format({
        { name = 'id', type = 'string' },
        { name = 'height', type = 'unsigned' },
        { name = 'is_concluded', type = 'boolean' }
    })
    elections:create_index('id', { 
        if_not_exists = true,
        parts = {{ field = 'id', type = 'string' }}
    })
    elections:create_index('height', { 
        if_not_exists = true,
        unique = false,
        parts = {{ field = 'height', type = 'unsigned' }}
    })


    -- Validators
    validator_sets = box.schema.create_space('validator_sets', { if_not_exists = true })
    validator_sets:format({
        { name = 'id', type = 'string' },
        { name = 'height', type = 'unsigned' },
        { name = 'set', type = 'array' }
    })
    validator_sets:create_index('id', { 
        if_not_exists = true,
        parts = {{ field = 'id', type = 'string' }}
    })
    validator_sets:create_index('height', { 
        if_not_exists = true,
        parts = {{ field = 'height', type = 'unsigned' }}
    })
end

function drop()
    if pcall(function() 
        box.space.abci_chains:drop()
        box.space.blocks:drop()
        box.space.elections:drop()
        box.space.pre_commits:drop()
        box.space.utxos:drop()
        box.space.validator_sets:drop()
        box.space.transactions:drop()
        box.space.outputs:drop()
        box.space.governance:drop()
    end) then
        print("Error: specified space not found")
    end
end

function indexed_pattern_search(space_name, field_no, pattern)
    if (box.space[space_name] == nil) then
        print("Error: Failed to find the specified space")
        return nil
    end
    local index_no = -1
    for i=0,box.schema.INDEX_MAX,1 do
        if (box.space[space_name].index[i] == nil) then break end
        if (box.space[space_name].index[i].type == "TREE"
            and box.space[space_name].index[i].parts[1].fieldno == field_no
            and (box.space[space_name].index[i].parts[1].type == "scalar"
            or box.space[space_name].index[i].parts[1].type == "string")) then
        index_no = i
        break
        end
    end
    if (index_no == -1) then
        print("Error: Failed to find an appropriate index")
        return nil
    end
    local index_search_key = ""
    local index_search_key_length = 0
    local last_character = ""
    local c = ""
    local c2 = ""
    for i=1,string.len(pattern),1 do
        c = string.sub(pattern, i, i)
        if (last_character ~= "%") then
        if (c == '^' or c == "$" or c == "(" or c == ")" or c == "."
                        or c == "[" or c == "]" or c == "*" or c == "+"
                        or c == "-" or c == "?") then
            break
        end
        if (c == "%") then
            c2 = string.sub(pattern, i + 1, i + 1)
            if (string.match(c2, "%p") == nil) then break end
            index_search_key = index_search_key .. c2
        else
            index_search_key = index_search_key .. c
        end
        end
        last_character = c
    end
    index_search_key_length = string.len(index_search_key)
    local result_set = {}
    local number_of_tuples_in_result_set = 0
    local previous_tuple_field = ""
    while true do
        local number_of_tuples_since_last_yield = 0
        local is_time_for_a_yield = false
        for _,tuple in box.space[space_name].index[index_no]:
        pairs(index_search_key,{iterator = box.index.GE}) do
        if (string.sub(tuple[field_no], 1, index_search_key_length)
        > index_search_key) then
            break
        end
        number_of_tuples_since_last_yield = number_of_tuples_since_last_yield + 1
        if (number_of_tuples_since_last_yield >= 10
            and tuple[field_no] ~= previous_tuple_field) then
            index_search_key = tuple[field_no]
            is_time_for_a_yield = true
            break
            end
        previous_tuple_field = tuple[field_no]
        if (string.match(tuple[field_no], pattern) ~= nil) then
            number_of_tuples_in_result_set = number_of_tuples_in_result_set + 1
            result_set[number_of_tuples_in_result_set] = tuple
        end
        end
        if (is_time_for_a_yield ~= true) then
        break
        end
        require('fiber').yield()
    end
    return result_set
end

function delete_output( id )
    box.space.outputs:delete(id)
end
