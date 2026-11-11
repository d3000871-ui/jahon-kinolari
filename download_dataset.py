import os
import shutil
import kagglehub

print("Downloading dataset...")
path = kagglehub.dataset_download("sahilk22/trending-movies-analysis-up-to-2026")
print("Path to dataset files:", path)

# List files in the downloaded folder
files = os.listdir(path)
print("Files in dataset:", files)

# Let's copy the files to a local 'data' directory in the project for easy access
target_dir = os.path.join(os.getcwd(), "data")
os.makedirs(target_dir, exist_ok=True)
for f in files:
    src = os.path.join(path, f)
    dst = os.path.join(target_dir, f)
    if os.path.isfile(src):
        shutil.copy2(src, dst)
        print(f"Copied {f} to {dst}")

print("Dataset setup completed successfully!")

