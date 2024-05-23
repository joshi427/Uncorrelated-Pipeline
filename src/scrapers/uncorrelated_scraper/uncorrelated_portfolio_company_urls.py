import requests
from bs4 import BeautifulSoup

from src.scrapers.uncorrelated_scraper.models import Company

import csv

import os
from pathlib import Path
from datetime import datetime

def create_output_file():
    output_base = Path(__file__).parents[2] / "src" / "data" / "uncorrelated_portfolio_company_urls"
    output_base.mkdir(parents=True, exist_ok=True)
    dated_filename = datetime.now().strftime('%Y-%m+%d') + "-uncorrelated-portfolio-company-urls.csv"
    output_file = output_base / dated_filename
    print(f"File created at: {output_file}")

    return output_file


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

    file_name = create_output_file()
    with open(file_name, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Name', 'URL'])

        for company in companies:
            writer.writerow([company.name, company.url])

    print("Scraping Complete!")

