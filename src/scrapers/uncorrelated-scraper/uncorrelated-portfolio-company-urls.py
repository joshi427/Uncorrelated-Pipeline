import requests
from bs4 import BeautifulSoup

from src.models import Company

import csv

def scrape_uncorrelated():
    url = 'https://uncorrelated.com'
    response = requests.get(url)

    soup = BeautifulSoup(response.text, 'html.parser')
    portfolio_company_names = soup.find_all('div', class_='name')

    companies = [Company(div.text.replace(' ', '-').lower()) for div in portfolio_company_names]
    for company in companies:
        if "." in company.name:  # companies like hack.vc don't need a .com
            company.url = company.name
        else:
            company.url = f"{company.name}.com"

    file_name = "../../data/2024-5-7-uncorrelated-portfolio-company-urls.csv"
    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'URL'])

        for company in companies:
            writer.writerow([company.name, company.url])

scrape_uncorrelated()
