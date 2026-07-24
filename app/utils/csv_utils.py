import csv
import io

def csv_string_to_json(csv_string: str):
    csv_file = io.StringIO(csv_string)
    reader = csv.DictReader(csv_file)

    data = []
    for row in reader:
        data.append(row)
    
    if not data:
        raise ValueError("CSV file is empty or has no data rows")

    return data