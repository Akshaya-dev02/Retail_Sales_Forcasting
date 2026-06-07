import pandas as pd
from pathlib import Path

df = pd.read_excel(Path(__file__).parent / "sales_project.xlsx")
print(df.columns)

