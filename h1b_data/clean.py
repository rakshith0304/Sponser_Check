import pandas as pd
import os

def combine_and_clean_h1b(data_folder: str, output_file: str):
    """
    Combine and clean multiple yearly H1B CSVs.
    - Reads 2021.csv, 2022.csv, 2023.csv from `data_folder`
    - Cleans each file
    - Keeps only Employer and H1B_Total
    - Aggregates duplicates by Employer
    - Saves one combined CSV
    """
    years = ["2021", "2022", "2023"]
    all_data = []

    for year in years:
        file_path = os.path.join(data_folder, f"{year}.csv")
        if not os.path.exists(file_path):
            print(f"⚠️ File not found: {file_path}")
            continue

        df = pd.read_csv(file_path)

        # Ensure Employer exists
        if "Employer" not in df.columns:
            raise ValueError(f"{file_path} missing 'Employer' column")

        # Clean Employer names
        df["Employer"] = df["Employer"].astype(str).str.strip()

        # Ensure required columns exist
        cols_needed = ["Initial Approval", "Initial Denial", "Continuing Approval", "Continuing Denial"]
        missing = [c for c in cols_needed if c not in df.columns]
        if missing:
            raise ValueError(f"{file_path} missing columns: {missing}")

        # Create H1B_Total column
        df["H1B_Total"] = df[cols_needed].sum(axis=1)

        # Keep only Employer + H1B_Total
        df = df[["Employer", "H1B_Total"]]

        all_data.append(df)

    # Combine all years
    combined = pd.concat(all_data, ignore_index=True)

    # Group by Employer and sum across years
    combined_cleaned = combined.groupby("Employer", as_index=False)["H1B_Total"].sum()

    # Save cleaned file
    combined_cleaned.to_csv(output_file, index=False)

    print(f"✅ Combined & cleaned CSV saved to: {output_file}")
    print(f"Rows before: {len(combined)}, after cleaning: {len(combined_cleaned)}")


# Example usage
if __name__ == "__main__":
    combine_and_clean_h1b(".", "cleaned_h1b.csv")
