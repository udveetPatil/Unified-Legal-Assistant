from datasets import load_dataset

dataset = load_dataset("nisaar/Articles_Constitution_3300_Instruction_Set")
dataset.save_to_disk("data/raw/constitution_qa/dataset")
print(dataset)

import requests

# Get the repo tree from GitHub API
url = "https://api.github.com/repos/ShreyGanatra/GrahakNyay/git/trees/main?recursive=1"
response = requests.get(url)
data = response.json()

# Print all JSON files in the repo
for item in data.get("tree", []):
    if item["path"].endswith(".json"):
        print(item["path"])