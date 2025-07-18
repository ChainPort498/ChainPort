import json
import os
import numpy as np
import matplotlib.pyplot as plt

plt.rcParams['font.family'] = 'Arial'

# Directory where the JSON files are stored
FOLDER = "./Data"
TRANSACTION_VOLUMES = [1000 * i for i in range(1, 11)]  # 1000 to 10000

def load_batch_data(contract_folder, volume):
    """Load the JSON data for a given transaction volume."""
    filename = f"batch_{volume}.json"
    with open(os.path.join(FOLDER, contract_folder, filename), "r") as f:
        return json.load(f)

def compute_time(batches):
    batch_no = 1
    avg_time = 0
    total_funcs = 0
    for batch in batches:
        num_of_funcs = len(batch["selectors"])
        total_funcs += num_of_funcs
        avg_time += (batch_no * 184) * num_of_funcs
        batch_no += 1
    return (batch_no - 1) * 184, avg_time / total_funcs

def evaluate_volume(volume):
    chainport_averages = []
    traditional_averages = []
    for contract_folder in os.listdir(FOLDER):
        if contract_folder == ".DS_Store":
            continue
        data = load_batch_data(contract_folder, volume)
        avg_traditional, avg_chainport = compute_time(data)
        chainport_averages.append(avg_chainport)
        traditional_averages.append(avg_traditional)

    final_avg_chainport = np.mean(chainport_averages)
    final_avg_traditional = np.mean(traditional_averages)
    return final_avg_chainport, final_avg_traditional

# Collect data
chainport_scores = []
traditional_scores = []

for volume in TRANSACTION_VOLUMES:
    chain_port, traditional = evaluate_volume(volume)
    chainport_scores.append(chain_port)
    traditional_scores.append(traditional)

for cp, trad in zip(chainport_scores, traditional_scores):
    print(f"ChainPort: {cp}, Traditional: {trad}")

reductions = [(t - c) / t * 100 for c, t in zip(chainport_scores, traditional_scores)]
avg_reduction = np.mean(reductions)
print("Avg_reduction",avg_reduction)
speedups = [t / c for t, c in zip(traditional_scores, chainport_scores)]
avg_speedup = np.mean(speedups)
min_speedup = np.min(speedups)
max_speedup = np.max(speedups)

print("avg_speedup",avg_speedup)
print("max_speedup",max_speedup)
print
# Plotting line graph
plt.figure(figsize=(8, 5))
plt.plot(TRANSACTION_VOLUMES, chainport_scores, marker='o', label='ChainPort', color='#606060')
plt.plot(TRANSACTION_VOLUMES, traditional_scores, marker='s', label='Traditional', color='black', linestyle='--')

plt.xlabel('Transaction Volume', fontsize=14)
plt.ylabel('Avg. Function Reactivation Time (s)', fontsize=14)
#plt.title('Execution Time per Function vs Transaction Volume', fontsize=13)
plt.xticks(TRANSACTION_VOLUMES, fontsize=10,  fontweight = 'bold')
plt.yticks(fontsize=10,  fontweight = 'bold')
plt.grid(True, linestyle='--', alpha=0.6)
plt.legend(prop={'weight': 'bold'}, fontsize=10)
plt.tight_layout()
plt.savefig("time_comparison_line.pdf")
plt.show()
