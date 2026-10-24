
from pathlib import Path
import pandas as pd

# Project directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Raw data directory
DATA_DIR = BASE_DIR / "data" / "raw" / "udise_2023_2024"

# Cleaned data directory
OUTPUT_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Find CSV files
csv_files = sorted(DATA_DIR.glob("*.csv"))

if not csv_files:
    print("No CSV files found!")
else:
    for file in csv_files:
        print(f"\nCleaning: {file.name}")

        try:
            df = pd.read_csv(file, low_memory=False)

            # Remove duplicate rows
            df = df.drop_duplicates()

            # Remove extra spaces from column names
            df.columns = df.columns.str.strip()

            # Save cleaned data
            output_file = OUTPUT_DIR / f"{file.stem}_cleaned.csv"
            df.to_csv(output_file, index=False)

            print("Rows after cleaning:", len(df))
            print("Columns:", len(df.columns))
            print("Saved:", output_file.name)

        except Exception as error:
            print("Error:", error)

print("\nDATA CLEANING COMPLETED!")
