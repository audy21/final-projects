import pandas as pd
import numpy as np

np.random.seed(42)
data = {
"name": ["Andi", "Budi", "Citra", "Dewi", "Andi", "Eko", None, "Fani", "Gita", "Budi", "Hani", "Joko"],
"age": [25, np.nan, 30, np.nan, 25, 22, 28, np.nan, 35, 27, np.nan, 40],
"occupation": ["Engineer", "Designer", "Manager", "Analyst", "Engineer", "Developer", "Tester", "Designer", None, "Designer", "Manager", None]
}

df = pd.DataFrame(data)
df.to_csv("dirty_data.csv", index=False)
print("Data kotor baru berhasil dibuat.")