import os

# Define file names and sizes in bytes
files_to_create = {
    "1mb_test.bin": 1024 * 1024,
    "10mb_test.bin": 10 * 1024 * 1024,
    "100mb_test.bin": 100 * 1024 * 1024
}

for filename, size in files_to_create.items():
    print(f"Creating {filename} ({size / (1024*1024)} MB)...")
    with open(filename, "wb") as f:
        # Generate random bytes to ensure the file isn't empty or easily compressed
        f.write(os.urandom(size))

print("All files generated successfully.")