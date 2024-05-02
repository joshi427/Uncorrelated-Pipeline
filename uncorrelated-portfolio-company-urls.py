import requests
from bs4 import BeautifulSoup

def scrape_uncorrelated():
    url = 'https://uncorrelated.com'
    response = requests.get(url)

    if response.status_code != 200:
        print("Failed to retrieve the website")
        return

    soup = BeautifulSoup(response.text, 'html.parser')
    portfolio_company_names = soup.find_all('div', class_='name')

    for div in portfolio_company_names:
        print(div.text.strip())

scrape_uncorrelated()

