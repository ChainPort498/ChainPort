import json
import os
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Arial'
# Directory where the JSON files are stored
FOLDER = "./Data"
TRANSACTION_VOLUMES = [1000 * i for i in range(1, 11)]  # 1000 to 10000

def load_batch_data(contract_folder,volume):
    """Load the JSON data for a given transaction volume."""
    filename = f"batch_{volume}.json"
    with open(os.path.join(FOLDER, contract_folder, filename), "r") as f:
        return json.load(f)

def compute_gas_usage(batches):
    total_gas = 0
    avg_gas = 0
    total_funcs = 0
    for batch in batches:
        num_of_funcs = len(batch["selectors"])
        total_funcs += num_of_funcs
        gas_used = batch["estimate"]
        total_gas += gas_used
        avg_gas += total_gas*num_of_funcs
    return total_gas, avg_gas/total_funcs


def evaluate_contract(contract_folder):
    """Evaluate one contract across all transaction volumes."""
    chainport_averages = []
    traditional_averages = []

    for volume in TRANSACTION_VOLUMES:
        data = load_batch_data(contract_folder,volume)
        avg_traditional, avg_chainport = compute_gas_usage(data)
        chainport_averages.append(avg_chainport)
        traditional_averages.append(avg_traditional)

    final_avg_chainport = np.mean(chainport_averages)
    final_avg_traditional = np.mean(traditional_averages)

   

    return final_avg_chainport, final_avg_traditional


contracts = ['SC1', 'SC2', 'SC3', 'SC4', 'SC5', 'SC6', 'SC7', 'SC8', 'SC9', 'SC10']
chainport_scores = []
traditional_scores = []

x = np.arange(len(contracts))
width = 0.35

for contract_folder in os.listdir(FOLDER):
    if contract_folder == ".DS_Store":
        continue
    chain_port,traditional = evaluate_contract(contract_folder)
    chainport_scores.append(chain_port)
    traditional_scores.append(traditional)

reductions = [t - c for t, c in zip(traditional_scores, chainport_scores)]
percent_reductions = [(t - c) / t * 100 for t, c in zip(traditional_scores, chainport_scores)]

avg_chainport = np.mean(chainport_scores)
avg_traditional = np.mean(traditional_scores)
avg_reduction = np.mean(reductions)
avg_percent_reduction = np.mean(percent_reductions)

min_percent_reduction = np.min(percent_reductions)
max_percent_reduction = np.max(percent_reductions)
std_percent_reduction = np.std(percent_reductions)

print(f"Avg ChainPort Gas per Function: {avg_chainport:.2f}")
print(f"Avg Traditional Gas per Function: {avg_traditional:.2f}")
print(f"Avg Reduction: {avg_reduction:.2f}")
print(f"Avg % Reduction: {avg_percent_reduction:.2f}%")
print(f"Min % Reduction: {min_percent_reduction:.2f}%")
print(f"Max % Reduction: {max_percent_reduction:.2f}%")
print(f"Std Dev of % Reduction: {std_percent_reduction:.2f}%")

fig, ax = plt.subplots(figsize=(8, 5))

bars1 = ax.bar(x - width/2, chainport_scores, width, label='ChainPort', color='#606060')
bars2 = ax.bar(x + width/2, traditional_scores, width, label='Traditional', edgecolor='black', hatch='//', color='white')

# Add labels
ax.set_ylabel('Avg. Gas per Function', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(contracts, fontsize=11, fontweight='bold')

for label in ax.get_yticklabels():
    label.set_fontweight('bold')
    label.set_fontsize(11)

# Add values on top
"""
for bar in bars1 + bars2:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 1, f'{int(height)}', ha='center', va='bottom', fontsize=9)
"""
ax.legend(prop={'weight': 'bold'}, fontsize=15)
plt.tight_layout()
plt.savefig("gas_comparison.pdf")
plt.show()

