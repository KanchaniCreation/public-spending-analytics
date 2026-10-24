
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt

# Project folder
BASE_DIR = Path(__file__).resolve().parent.parent

# Folders
DATA_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "outputs" / "graphs"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("\nPUBLIC SPENDING ANALYTICS")
print("=" * 40)

# Find cleaned CSV files
csv_files = sorted(DATA_DIR.glob("*_cleaned.csv"))

if not csv_files:
    print("No cleaned CSV files found!")
else:
    for file in csv_files:
        print(f"\nAnalyzing: {file.name}")

        df = pd.read_csv(file, low_memory=False)

        print("Total rows:", len(df))
        print("Total columns:", len(df.columns))

        # Missing values report
        missing = df.isnull().sum()
        missing = missing[missing > 0]

        print("\nColumns with missing values:")
        print(missing if not missing.empty else "No missing values")

        # Select numerical columns
        numeric_df = df.select_dtypes(include="number")

        # Plot numerical columns with varying values
        if not numeric_df.empty:
            columns = [
                col for col in numeric_df.columns
                if numeric_df[col].nunique() > 1
            ]

            if columns:
                selected_columns = columns[:5]

                numeric_df[selected_columns].hist(
                    figsize=(12, 8),
                    bins=20
                )

                plt.suptitle(f"Data Distribution: {file.stem}")
                plt.tight_layout()

                graph_file = OUTPUT_DIR / f"{file.stem}_distribution.png"

                plt.savefig(graph_file)
                plt.close()

                print("Graph saved:", graph_file)
                
# COMPARATIVE ANALYSIS

print("\nCOMPARATIVE ANALYSIS")
print("=" * 40)

comparison_results = []

for file in sorted(DATA_DIR.glob("*_cleaned.csv")):
    df = pd.read_csv(file, low_memory=False)

    numeric_df = df.select_dtypes(include="number")

    if numeric_df.empty:
        continue

    result = {
        "Dataset": file.name,
        "Total Rows": len(df),
        "Total Columns": len(df.columns),
        "Numeric Columns": len(numeric_df.columns),
        "Missing Values": int(df.isnull().sum().sum()),
        "Duplicate Rows": int(df.duplicated().sum())
    }

    comparison_results.append(result)

comparison_df = pd.DataFrame(comparison_results)

report_file = OUTPUT_DIR / "comparative_analysis.csv"
comparison_df.to_csv(report_file, index=False)

print(comparison_df.to_string(index=False))
print("\nComparative report saved:", report_file)


print("\nDATA ANALYSIS COMPLETED!")
