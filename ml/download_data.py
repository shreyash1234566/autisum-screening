"""
download_data.py
Downloads UCI ASD datasets (Thabtah et al. 2018, CC BY 4.0) into ml/data/
Run once before training: python ml/download_data.py
"""
import urllib.request, os, zipfile, shutil
from pathlib import Path

DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)

DATASETS = {
    # UCI Children dataset (292 instances, age 4-11)
    "autism_children.csv": (
        "https://archive.ics.uci.edu/ml/machine-learning-databases/00419/"
        "Autism-Child-Data.arff"
    ),
    # UCI Adult dataset (704 instances)
    "autism_adult.csv": (
        "https://archive.ics.uci.edu/ml/machine-learning-databases/00426/"
        "Autism-Adult-Data.arff"
    ),
}

def arff_to_csv(arff_path: str, csv_path: str):
    """Convert ARFF format to CSV."""
    with open(arff_path) as f:
        lines = f.readlines()

    header = []
    data_lines = []
    in_data = False
    for line in lines:
        line = line.strip()
        if line.lower() == "@data":
            in_data = True
            continue
        if not in_data and line.lower().startswith("@attribute"):
            parts = line.split()
            header.append(parts[1])
        elif in_data and line and not line.startswith("%"):
            data_lines.append(line)

    with open(csv_path, "w") as f:
        f.write(",".join(header) + "\n")
        for row in data_lines:
            f.write(row + "\n")

    print(f"  Converted → {csv_path} ({len(data_lines)} rows)")

print(f"Downloading UCI ASD datasets to {DATA_DIR}/")
for filename, url in DATASETS.items():
    dest = DATA_DIR / filename
    arff_tmp = DATA_DIR / (filename.replace(".csv", ".arff"))
    try:
        print(f"  Downloading {url} ...")
        urllib.request.urlretrieve(url, arff_tmp)
        arff_to_csv(str(arff_tmp), str(dest))
        arff_tmp.unlink()
    except Exception as e:
        print(f"  FAILED: {e}")
        print(f"  Manual download: {url}")

print("\nFor toddler dataset:")
print("  1. Visit kaggle.com/fabdelja/autism-screening-for-toddlers")
print("  2. Download autism-screening-for-toddlers.csv")
print(f"  3. Place in {DATA_DIR}/autism_toddlers.csv")
print("\nFor Indian data (AMI dataset):")
print("  Email: Trapti Shrivastava (arxiv.org/abs/2404.02181)")
print("  Request dataset for research use")
print(f"  Place received CSV in {DATA_DIR}/autism_indian_ami.csv")
print("\nThen run: python ml/train_model.py")
