
from pathlib import Path
import pandas as pd

# Step 1: Project folder ka path
BASE_DIR = Path(__file__).resolve().parent

# Step 2: CSV files ka correct folder
DATA_DIR = BASE_DIR / "data" / "raw" / "udise_2023_2024"

# Step 3: Saari CSV files find karo
csv_files = sorted(DATA_DIR.glob("*.csv"))

print("\nPUBLIC SPENDING ANALYTICS")
print("=" * 50)

# Step 4: Check karo ki CSV files mili hain ya nahi
if not csv_files:
    print("No CSV files found.")
    print("Please check the folder:", DATA_DIR)

else:
    # Step 5: Har CSV file ko read karo
    for file in csv_files:
        print("\n" + "=" * 50)
        print("FILE:", file.name)
        print("=" * 50)

        try:
            df = pd.read_csv(file, low_memory=False)

            # Total rows aur columns
            print("\nTotal records:", len(df))
            print("Total columns:", len(df.columns))

            # Column names
            print("\nColumn names:")
            print(df.columns.tolist())

            # Data types
            print("\nData types:")
            print(df.dtypes)

            # Missing values
            print("\nMissing values per column:")
            print(df.isnull().sum())

            # Duplicate rows
            print("\nDuplicate rows:", df.duplicated().sum())

            # Statistical summary
            print("\nStatistical summary:")
            print(df.describe())

            # Processed folder mein report save karo
            output_dir = BASE_DIR / "data" / "processed"
            output_dir.mkdir(parents=True, exist_ok=True)

            report_file = output_dir / f"{file.stem}_summary.txt"

            with open(report_file, "w", encoding="utf-8") as report:
                report.write(f"FILE: {file.name}\n")
                report.write(f"Total records: {len(df)}\n")
                report.write(f"Total columns: {len(df.columns)}\n")
                report.write(f"Duplicate rows: {df.duplicated().sum()}\n")

                report.write("\nCOLUMN NAMES:\n")
                report.write(str(df.columns.tolist()))

                report.write("\n\nDATA TYPES:\n")
                report.write(df.dtypes.to_string())

                report.write("\n\nMISSING VALUES:\n")
                report.write(df.isnull().sum().to_string())

                report.write("\n\nSTATISTICAL SUMMARY:\n")
                report.write(df.describe().to_string())

            print("\nReport saved:", report_file.name)

        except Exception as error:
            print("Error processing file:", file.name)
            print(error)

print("\nDATA PROFILING COMPLETED!")