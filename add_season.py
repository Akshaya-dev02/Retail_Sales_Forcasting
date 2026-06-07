import pandas as pd
from pathlib import Path

BASE_DIR = Path(__file__).parent
INPUT_FILE = BASE_DIR / "sales_project.xlsx"
OUTPUT_FILE = BASE_DIR / "sales_with_season.xlsx"


def get_season(month):
    if month in [12, 1, 2]:
        return "Winter"
    elif month in [3, 4, 5]:
        return "Summer"
    elif month in [6, 7, 8, 9]:
        return "Rainy"
    else:
        return "Autumn"


def add_season_column(df):
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["Season"] = df["Date"].dt.month.apply(get_season)
    return df


def load_sales_data():
    if OUTPUT_FILE.exists():
        df = pd.read_excel(OUTPUT_FILE)
        df["Date"] = pd.to_datetime(df["Date"])
        return df

    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Data file not found. Add 'sales_project.xlsx' to:\n  {BASE_DIR}"
        )

    df = add_season_column(pd.read_excel(INPUT_FILE))
    df.to_excel(OUTPUT_FILE, index=False)
    return df


if __name__ == "__main__":
    df = load_sales_data()
    print("File ready: sales_with_season.xlsx")
    print(df.head())
