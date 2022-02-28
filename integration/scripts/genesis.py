#!/usr/bin/env python3
import json
import os

# TODO: CHANGE ME/OTHER VARIABLES
def edit_genesis() -> None:
    ME = os.getenv('ME')
    OTHER = os.getenv('OTHER')

    if ME == 'planetmint_1':
        file_name = '{}_genesis.json'.format(ME)
        other_file_name = '{}_genesis.json'.format(OTHER)

        file = open(os.path.join('/shared', file_name))
        other_file = open(os.path.join('/shared', other_file_name))

        genesis = json.load(file)
        other_genesis = json.load(other_file)

        genesis['validators'] = genesis['validators'] + other_genesis['validators']

        file.close()
        other_file.close()

        with open(os.path.join('/shared', 'genesis.json'), 'w') as f:
            json.dump(genesis, f, indent=True)

    return None

if __name__ == '__main__':
    edit_genesis()
