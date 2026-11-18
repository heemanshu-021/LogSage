"""
Execute notebooks/02_anomaly_detection.ipynb and save outputs inplace.
"""
import nbformat
from nbclient import NotebookClient
from pathlib import Path

nb_path = Path("notebooks/02_anomaly_detection.ipynb")
print(f"Loading {nb_path}...")
with open(nb_path, "r", encoding="utf-8") as f:
    nb = nbformat.read(f, as_version=4)

client = NotebookClient(nb, timeout=600, kernel_name="python3", resources={"metadata": {"path": "notebooks/"}})
print("Executing notebook cells...")
client.execute()

with open(nb_path, "w", encoding="utf-8") as f:
    nbformat.write(nb, f)

print(f"Notebook {nb_path} executed successfully with all outputs saved!")
