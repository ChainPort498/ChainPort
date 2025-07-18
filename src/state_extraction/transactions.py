import requests
from configparser import ConfigParser
import time


config = ConfigParser()
config.read("config.ini")

tx_limit = 0

def set_tx_limit(value):
    global tx_limit
    tx_limit = value


def get_transactions(cont_addr, transactions, endpoint, api_key, end_block):
    page = 1
    seen_hashes = set()
    transactions = []
    print("The tx limit is",tx_limit)
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    while len(transactions) < tx_limit:
        try:
            response = requests.get(endpoint.format(cont_addr, 0, end_block, page, api_key), headers=headers).json()
            if response["status"] == "1":
                
                txs = response["result"]
                if len(txs) == 0:
                    break
                for tx in txs:
                    tx_hash = tx["hash"]
                    if tx_hash not in seen_hashes:
                        seen_hashes.add(tx_hash)
                        transactions.append(tx)
                page += 1
                
                time.sleep(10)
                
                
            else:
                time.sleep(10)
                print(response)
                break
        except requests.exceptions.RequestException as e:
            print("Error occurred:", e)
            break
    print(f"Total transactions downloaded: {len(transactions)}")
    return transactions


def get_internal_transactions(cont_addr, transactions, endpoint, api_key, end_block):
    page = 1
    
    seen_hashes = set()
    transactions = []
    print("The tx limit is",tx_limit)
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
    while len(transactions) < tx_limit:
        try:
            response = requests.get(endpoint.format(cont_addr, 0, end_block, page, api_key), headers=headers).json()
            if response["status"] == "1":
                txs = response["result"]
                if len(txs) == 0:
                    break
                for tx in txs:
                    tx_hash = tx["hash"]
                    if tx_hash not in seen_hashes:
                        seen_hashes.add(tx_hash)
                        transactions.append(tx)
                page += 1
                
                time.sleep(10)
            else:
                print(response)
                time.sleep(10)
                break
        except requests.exceptions.RequestException as e:
            print("Error occurred:", e)
            break
    print(f"Total internal txs downloaded: {len(transactions)}")
    return transactions


