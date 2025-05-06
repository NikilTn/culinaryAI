import pandas as pd

# Replace 'RecipeNLG.csv' with the actual path to your CSV file if needed.
file_path = "full_dataset.csv"



# Read only the first 5 rows of the CSV file.
df = pd.read_csv(file_path, nrows=5)

# Convert the DataFrame to a JSON string (list of records format).
json_data = df.to_json(orient='records')

# Print out the JSON data.
print(json_data)

