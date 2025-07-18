import json
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import ScalarFormatter

plt.rcParams['font.family'] = 'Arial'
# Directory where the JSON files are stored
FOLDER = "./Data"
TRANSACTION_VOLUMES = [1000 * i for i in range(1, 11)]  # 1000 to 10000

def load_dependency_data(contract_folder,volume):
    """Load the JSON data for a given transaction volume."""
    filename = f"fun_data_dep_{volume}.json"
    with open(os.path.join(FOLDER, contract_folder, filename), "r") as f:
        return json.load(f)

def compute_chainport_avg_bytes(data):
    """Compute the average bytes per function for ChainPort from dependency data."""
    total_bytes = 0
    num_functions = len(data)

    for func, vars_info in data.items():
        func_bytes = 0
        seen_vars = []
        for var, slots in vars_info.items():
            if var not in seen_vars:
                func_bytes += slots*32
                seen_vars.append(var)
        total_bytes += func_bytes

    return total_bytes / num_functions if num_functions > 0 else 0

def compute_traditional_bytes(data):
    """Compute the bytes required per function under the traditional model."""
    unique_vars = set()
    total_slots = 0
    for vars_info in data.values():
        for var, slots in vars_info.items():
            if var not in unique_vars:
                unique_vars.add(var)
                total_slots+=slots
    return total_slots * 32  # Total bytes per function in traditional model

def evaluate_contract(contract_folder):
    """Evaluate one contract across all transaction volumes."""
    chainport_averages = []
    traditional_averages = []

    for volume in TRANSACTION_VOLUMES:
        data = load_dependency_data(contract_folder,volume)
        avg_chainport = compute_chainport_avg_bytes(data)
        chainport_averages.append(avg_chainport)
        avg_traditional = compute_traditional_bytes(data)
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
percent_reductions = [(t - c) / t * 100 if t != 0 else 0 for t, c in zip(traditional_scores, chainport_scores)]

# Summary statistics
avg_reduction = np.mean(reductions)
avg_percent_reduction = np.mean(percent_reductions)
min_percent_reduction = np.min(percent_reductions)
max_percent_reduction = np.max(percent_reductions)
std_percent_reduction = np.std(percent_reductions)

# Print results
print(f"Avg reduction (bytes): {avg_reduction:.2f}")
print(f"Avg percentage reduction: {avg_percent_reduction:.2f}%")
print(f"Min percentage reduction: {min_percent_reduction:.2f}%")
print(f"Max percentage reduction: {max_percent_reduction:.2f}%")
print(f"Std dev of percentage reduction: {std_percent_reduction:.2f}%")

fig, ax = plt.subplots(figsize=(8, 5))

bars1 = ax.bar(x - width/2, chainport_scores, width, label='ChainPort', color='#606060')
bars2 = ax.bar(x + width/2, traditional_scores, width, label='Traditional', edgecolor='black', hatch='//', color='white')

# Add labels
ax.set_ylabel('Avg. Bytes per Function', fontsize=14)
ax.set_xticks(x)
ax.set_xticklabels(contracts, fontsize=11, fontweight = 'bold')
ax.legend(prop={'weight': 'bold'}, fontsize=15)

for label in ax.get_yticklabels():
    label.set_fontweight('bold')
    label.set_fontsize(11)
# Add values on top
"""
for bar in bars1 + bars2:
    height = bar.get_height()
    ax.text(bar.get_x() + bar.get_width()/2., height + 1, f'{int(height)}', ha='center', va='bottom', fontsize=9)
"""
formatter = ScalarFormatter(useMathText=True)
formatter.set_scientific(True)
formatter.set_powerlimits((4, 4))  # Forces 10^4
ax.yaxis.set_major_formatter(formatter)
ax.ticklabel_format(style='sci', axis='y', scilimits=(4, 4))
ax.yaxis.offsetText.set_fontweight('bold')

plt.tight_layout()
plt.savefig("bytes_comparison.pdf")
plt.show()

