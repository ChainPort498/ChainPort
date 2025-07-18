import re
from web3 import Web3
from hexbytes import HexBytes
"""
def get_relevant_selectors(func_to_selector,last_slot_index_of_state_var,start_index,size,original_dependency_matrix,cur_dependency_status):
    selectors = []
    for item in last_slot_index_of_state_var.keys():
        if last_slot_index_of_state_var[item] >= start_index and last_slot_index_of_state_var[item] <= start_index+size-1:
            for func,deps in original_dependency_matrix.items():
                for dep in deps:
                    if dep.name == item:
                        cur_dependency_status[func] = cur_dependency_status[func]-1
                        if cur_dependency_status[func] == 0:
                            selectors.append(func_to_selector[func])
    return selectors
                            

def generateBatch(slots,func_to_selector,last_slot_index_of_state_var,start_index,original_dependency_matrix,cur_dependency_status):
    
    high = len(slots)-start_index
    low = 1

    while(low <= high):
        mid = (low + high) // 2
        keys = [slot[0] for slot in slots[start_index:start_index+mid]]
        values = [slot[1] for slot in slots[start_index:start_index+mid]]
        selectors = get_relevant_selectors(func_to_selector,last_slot_index_of_state_var,start_index,mid,original_dependency_matrix,cur_dependency_status)  
"""


def estimate_gas(contract_address, contract_abi, keys, values, selectors, ganache_url="http://127.0.0.1:8545"):
    web3 = Web3(Web3.HTTPProvider(ganache_url))
    if not web3.is_connected():
        raise ConnectionError("Unable to connect to Ganache at " + ganache_url)
    account = web3.eth.accounts[0]

    contract = web3.eth.contract(address=contract_address, abi=contract_abi)
    
    try:
        gas_estimate = contract.functions.applyStateAndReactivate(keys, values, selectors).estimate_gas({
            'from': account
        })
        return gas_estimate
    except Exception as e:
        raise RuntimeError(f"Gas estimation failed: {e}")


def generate_shards(contract_state):
    shards = {}
    for var in contract_state:
        if len(var) < 5:  # Check if var has at least 5 elements
            print(f"Warning: Variable {var} has insufficient elements, skipping...")
            continue
        if re.split(r'[:.]', var[0])[0] not in shards.keys():
            shards[re.split(r'[:.]', var[0])[0]] = []
        shards[re.split(r'[:.]', var[0])[0]].append(var[4])
    return shards

def get_func_activation_index(prio_vec,dep_matrix,shards):
    slots = []
    last_slot_index_of_state_var = {}
    for function in prio_vec.keys():
        dpendencies = dep_matrix[function]
        for dep in dpendencies:
            if dep.name not in shards.keys():
                print("Not in shard", dep.name)
                dep_matrix[function].remove(dep)
                continue
            shard = shards[dep.name]
            max_index = -1
            for slot in shard:
                if slot in slots:
                    if max_index <= slots.index(slot):
                        max_index = slots.index(slot) 
                else:
                    slots.append(slot)
                    if max_index <= len(slots)-1:
                        max_index = len(slots)-1
            last_slot_index_of_state_var[dep.name] = max_index
    

    for var in shards.keys():
        if var not in last_slot_index_of_state_var.keys():
            shard = shards[var]
            max_index = -1
            for slot in shard:
                if slot in slots:
                    if max_index <= slots.index(slot):
                        max_index = slots.index(slot) 
                else:
                    slots.append(slot)
                    if max_index <= len(slots)-1:
                        max_index = len(slots)-1
            last_slot_index_of_state_var[var] = max_index
    
    func_activation_index = {}
    for func,deps in dep_matrix.items():
        max = 0
        for dep in deps:
            if dep.name not in last_slot_index_of_state_var.keys():
                continue
            if max < last_slot_index_of_state_var[dep.name]:
                max = last_slot_index_of_state_var[dep.name]
        func_activation_index[func] = max
    
    func_activation_index = dict(sorted(func_activation_index.items(), key=lambda item: item[1]))

    return slots,func_activation_index

def generate_batch(storage,contract_state,prio_vec,dep_matrix,selectors,thershold,contract_address,abi):
    shards = generate_shards(contract_state)
    slots,func_activation_index = get_func_activation_index(prio_vec,dep_matrix,shards)
    start_index = 0
    batches = []
    while start_index < len(slots):
        high = len(slots)-start_index
        low = 1

        while(low <= high):
            mid = (low + high) // 2
            cur_slots = []
            vals = []
            for i in range(start_index, start_index + mid):
                slot = Web3.to_bytes(hexstr=slots[i]).rjust(32, b'\x00')
                cur_slots.append(slot)
                vals.append(storage[int(slots[i], 16)])

            selectors_to_be_activated = []
            
            for func,index in func_activation_index.items():
                if index >= start_index and index <= start_index+mid-1:
                    selectors_to_be_activated.append(HexBytes(selectors[func]))
            estimate = estimate_gas(contract_address,abi,cur_slots,vals,selectors_to_be_activated)

            if estimate < thershold:
                best = (cur_slots,vals,selectors_to_be_activated,mid,estimate)
                low = mid+1
            else:
                high = mid-1

        batches.append(best)
        start_index = start_index+best[3]
    return batches,shards,func_activation_index


            
            

        
