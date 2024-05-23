import csv
import os
from pathlib import Path
from datetime import datetime
import json

def csv_to_dict(file_path):
    with open(file_path, mode='r', newline='') as file:
        reader = csv.DictReader(file)

        csv_dict = {header: [] for header in reader.fieldnames}

        for row in reader:
            for header in reader.fieldnames:
                csv_dict[header].append(row[header])

    return csv_dict


def crunchbase_urls(companies: dict) -> list:
    return [f"https://www.crunchbase.com/organization/{company}/people" for company in companies["Name"]]

def create_important_employees_output_file():
    output_base = Path(__file__).parents[2] / "data" / "uncorrelated_portfolio_company_employees"
    output_base.mkdir(parents=True, exist_ok=True)
    dated_filename = f"{datetime.now().strftime('%Y-%m-%d')}-uncorrelated-portfolio-company-employees.csv"
    output_file = output_base / dated_filename
    print(f"File created at: {output_file}")
    print(output_base)
    return output_file
# take json with important employees and save them to csv
def json_important_employees_csv(json_file_path):
    file_name = create_important_employees_output_file()
    with open(json_file_path, 'r') as file:
        data = json.load(file)
    important_people = data.get('import_employees', [])
    company_name = data.get('organization', [])['id']
    for person in important_people:
        person["company"] = company_name
    # Write to the CSV file
    output_file = create_important_employees_output_file()
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['name', 'linkedin', "title", "company"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for person in important_people:
            row = {field: person.get(field, '') for field in fieldnames}
            writer.writerow(row)

    print(f"Important people information written to: {output_file}")

# tests
# file_path = r"C:\Users\fanti\PycharmProjects\Uncorrelated-Pipeline\src\data\2024-5-7-uncorrelated-portfolio-company-urls.csv"
# print(csv_to_dict(file_path))
# print(crunchbase_urls(csv_to_dict(file_path)))

file_path = r"C:\Users\fanti\PycharmProjects\Uncorrelated-Pipeline\src\data\scrapfly_results\uncorrelated_portfolio_company_information\2024-05-uncorrelated-portfolio-company-information\2024-05-22-activestate.json"
json_important_employees_csv(file_path)
