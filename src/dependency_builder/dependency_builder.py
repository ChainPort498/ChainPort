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
from slither.slithir.operations.internal_call import InternalCall
from slither.slithir.operations.solidity_call import SolidityCall
from collections import defaultdict



def print_dependency_matrix(dependency_matrix):
    for func, deps in dependency_matrix.items():
        print(f"\n🔹 Function: {func}")
        if not deps:
            print("   └── No dependencies")
        else:
            for dep in deps:
                if hasattr(dep, 'name'):
                    print(f"   └── {type(dep).__name__}: {dep.name}")
                else:
                    print(f"   └── {type(dep).__name__}")

    

def find_dependency(func, visited, adj_list):
    if visited.get(func.name, False):
        return []

    visited[func.name] = True
    dependencies = [] 
    
    for dpendency in adj_list[func.name]:
        if isinstance(dpendency,StateVariable):
            dependencies.append(dpendency)
        else:
            dependencies = dependencies + find_dependency(dpendency,visited,adj_list)    

    return dependencies



def build_dependency_matrix(input_dir, cont_name):
    slither = Slither(input_dir+"/main.sol")
    adj_list = defaultdict(list)
    for contract in slither.contracts:
        if contract.name == cont_name:
            for function in contract.functions:
                if function.is_constructor or function.is_constructor_variables:
                    continue
                if function.name not in adj_list.keys():
                    adj_list[function.name] = []
                adj_list[function.name].extend(function.state_variables_read + function.state_variables_written)
                for call in function.all_internal_calls():
                    if  isinstance(call,InternalCall):
                        adj_list[function.name].append(call.function)
                    
    dependency_matrix = {}
    
    for contract in slither.contracts:
        if contract.name == cont_name:
            for function in contract.functions:
                if function.is_constructor or function.is_constructor_variables:
                    continue
                visited = {}
                dependency_matrix[function.name] = find_dependency(function,visited,adj_list)
    
    print_dependency_matrix(dependency_matrix)
    
    return dependency_matrix