# ChainPort

**ChainPort** is a secure and gas-efficient framework for migrating Ethereum smart contracts with minimal downtime. It restores contract state in phases by analyzing function–state dependencies, prioritizing critical functionality, and enforcing strict access control and batch sequencing.

## 📁 Project Structure

    ├── src/
    │   ├── ast_parsing/           # Parses Solidity ASTs
    │   ├── dependency_builder/    # Builds dependency matrix and priority scores
    │   ├── batch_generator/       # Plans gas-bounded migration batches
    │   ├── key_approx_analysis/   # Analyzes slot-level storage layout
    │   └── state_extraction/      # Extracts state and transaction data
    ├── Data.zip                   # Processed contract state and analysis outputs
    ├── config.ini                 # Experiment configuration
    ├── data_analysis_byte.py      # Evaluates storage overhead
    ├── data_analysis_gas.py       # Evaluates gas efficiency
    ├── data_analysis_time.py      # Evaluates reactivation latency
