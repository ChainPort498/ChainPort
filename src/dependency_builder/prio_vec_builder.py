from slither.slither import Slither
from slither.utils.function import get_function_id
import subprocess
import copy
import json
from collections import defaultdict, deque
import requests
from configparser import ConfigParser
from src.state_extraction.transactions import get_transactions
from src.state_extraction.transactions import get_internal_transactions
from web3.auto import Web3
from web3.middleware import ExtraDataToPOAMiddleware
from src.ast_parsing.ast_parser import generate_ast
from src.state_extraction.state_extractor import switch_compiler, generate_abi
from slither.core.declarations import Event
from slither.slithir.operations.event_call import EventCall
from slither.core.declarations.function_contract import FunctionContract
from slither.core.variables.state_variable import StateVariable
from openai import AzureOpenAI
import time
import fitz


def rate_func_llm(code,func_names,doc):
    config = ConfigParser()
    config.read("config.ini")
    LLM_ENDPOINT = config.get('openai', 'llm_endpoint')
    MODEL_NAME = config.get('openai', 'model_name')
    DEPLOYMENT_NAME = config.get('openai', 'deployment')
    MAX_TOKENS = config.get('openai', 'max_tokens')
    DEFAULT_TEMP = config.get('openai', 'default_temperature')
    LLM_API_KEY = config.get('openai', 'llm_api_key')
    LLM_API_VERSION = config.get('openai', 'llm_api_version')
    SYSTEM_PROMPT = "You are a smart contract migration analyst. Your role is to analyze smart contract functions and assess their relative importance during a migration. Functions that are more critical — such as those managing assets, controlling access, or serving as public interfaces — must be migrated and reactivated earlier to avoid disruption. Functions with lower importance can be safely deferred."
    API_SLEEP_SECONDS = 5
    client = AzureOpenAI(azure_endpoint=LLM_ENDPOINT,api_key=LLM_API_KEY,api_version=LLM_API_VERSION)
    instruction_prompt = f"""
        You are provided with the **entire Solidity contract code**, along with **inline documentation**. A list of **function names** is also provided. For each named function, assign a **priority score** between **0.0** and **1.0** based solely on the code and documentation.

        ---

        ### 🎯 Why This Score Matters:
        The score determines the migration order within the **SmartShift** framework. High-priority functions must be reactivated early to:
        - Maintain essential business logic
        - Prevent downtime in user-facing operations
        - Preserve control over funds, ownership, and permissions
        - Avoid failure in dependent or interacting functions

        Low-priority functions can be safely deferred without compromising core contract integrity or availability.

        ---

        ### 🧠 How to Score:
        Base your evaluation **only** on the provided Solidity code and inline documentation. Do **not** assume access to other modules or contracts. Consider the following factors:

        1. **Business Logic Importance** – Is the function essential to core behavior (e.g., transfer, execute, mint)?
        2. **State Dependency** – Does it read/write critical state variables (balances, roles, config)?
        3. **External Accessibility** – Is it `public` or `external` (accessible to users or dApps)?
        4. **Security Role** – Does it manage access, ownership, or pausing behavior?
        5. **Control Flow Role** – Is it a fallback, constructor, modifier, or logic trigger?
        6. **Dependency Blocking** – Will other functions fail or stall if this function is unavailable?

        ---

        ### 📄 Solidity Contract Code:
        {code}

        ---

        ### 🔍 Functions to Analyze:
        {func_names}

        ---

        ### 📄 Documentation (if available):
        {doc}
        ---

        ### ✅ Response Format:
        Return a **JSON array**, with one object per function, using this exact format:

        [
        {{
            "function": "<function_name>",
            "priority": <float between 0.0 and 1.0>,
            "reason": "<Concise explanation based only on code and documentation>"
        }},
        ...
        ]

        Strictly respond with a **raw JSON array only**. Do **not** include any explanations, markdown, comments, or surrounding text. **Any deviation is unacceptable.**
    """
    
    messages = [{"role": "system", "content": SYSTEM_PROMPT},{"role": "assistant","content": instruction_prompt}]

    response = client.chat.completions.create(model=DEPLOYMENT_NAME,messages=messages,max_tokens=int(MAX_TOKENS),temperature=int(DEFAULT_TEMP))

    print(f"Sleeping for {API_SLEEP_SECONDS} seconds to respect API rate limits...")
    time.sleep(API_SLEEP_SECONDS)
    print(response.choices[0].message.content)
    response = json.loads(response.choices[0].message.content[response.choices[0].message.content.find('['):response.choices[0].message.content.rfind(']')+1])
    return response


def build_priority_vector(input_dir, cont_name, source_code, compiler_version, transactions, internal_transactions):
    config = ConfigParser()
    config.read("config.ini")
    BLOCK_SCANNER_API_KEY = config.get('etherscan', 'etherscan_api_key')
    BLOCKCHAIN_NODE_LINK = config.get('infura', 'infura_node_link')
    BLOCKCHAIN_NODE_PID = config.get('infura', 'infura_pid')
    TRANSACTION_LINK = config.get('etherscan', 'transaction_link')
    INTERNAL_TRANSACTION_LINK = config.get('etherscan', 'internal_transaction_link')
    w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_NODE_LINK + BLOCKCHAIN_NODE_PID))
    w3.middleware_onion.inject(ExtraDataToPOAMiddleware, layer=0)
    all_transactions = []
    if compiler_version != '':
        switch_compiler(compiler_version)
    else:
        _, compiler_version = generate_ast(source_code)
        switch_compiler(compiler_version)


    
    contract_abi = generate_abi(source_code, cont_name)

    all_transactions = transactions
    all_transactions += internal_transactions
    
    func_call_freq = {}
    
    for tran in all_transactions:
        
        try:
            cont_abi = copy.deepcopy(contract_abi)
            contract = w3.eth.contract(abi=cont_abi)
            transac_input = contract.decode_function_input(tran['input'])
        except Exception as e:
            # print("Warning:", str(e))
            continue
        
        if func_call_freq.get(transac_input[0].fn_name) in func_call_freq.keys():
            func_call_freq[transac_input[0].fn_name] = func_call_freq[transac_input[0].fn_name] +1
        else:
            func_call_freq[transac_input[0].fn_name] = 1

    slither = Slither(input_dir+"/main.sol")
    
    for contract in slither.contracts:
        if contract.name == cont_name:
            for function in contract.functions:
                if function.is_constructor or function.is_constructor_variables:
                    continue
                if function.name not in func_call_freq.keys():
                    func_call_freq[function.name] = 0
                
    doc = fitz.open(input_dir+"/doc.pdf")
    pdf_text = "\n".join(page.get_text() for page in doc)
    llm_priorities = rate_func_llm(source_code,func_call_freq.keys(),pdf_text)
    func_priority = {}
    
    min_item = min(func_call_freq.items(), key=lambda x: x[1])
    max_item = max(func_call_freq.items(), key=lambda x: x[1])
    alpha = 0.5
    for function in func_call_freq.items():
        for llm_assigned_prio in llm_priorities:
            if llm_assigned_prio["function"] == function[0]:
                func_priority[function[0]] = (alpha * ((func_call_freq[function[0]]-min_item[1])/(max_item[1]-min_item[1]))) + ((1-alpha)*llm_assigned_prio["priority"])
    return dict(sorted(func_priority.items(), key=lambda item: item[1], reverse=True)),llm_priorities