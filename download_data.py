from huggingface_hub import snapshot_download

# GSMS-B: BNS/BNSS/BSA QA pairs [citation:3]
snapshot_download(
    repo_id="GSMS-B/Indian-Legal-QA-BNS-BNSS-BSA",
    repo_type="dataset",
    local_dir="./data/raw/gsms-b"
)

# InIRAC: IRAC-structured judgments [citation:4]
snapshot_download(
    repo_id="joyboseroy/inIRAC",
    repo_type="dataset",
    local_dir="./data/raw/inIRAC"
)

# GovIntel: Temporal mapping and knowledge graph [citation:5]
snapshot_download(
    repo_id="aashnasharma/govintel-legal-dataset",
    repo_type="dataset",
    local_dir="./data/raw/govintel"
)

print("Datasets downloaded.")