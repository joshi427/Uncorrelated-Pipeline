"""
To run this script set the env variable $SCRAPFLY_KEY with your scrapfly API key:
$ export $SCRAPFLY_KEY='scp-live-467683007c4948a082bb5459c41a3e91'
"""
from pathlib import Path
import asyncio
import json
from src.scrapers.scrapfly_scraper import crunchbase
from src.scrapers.processing.processing_functions import crunchbase_urls,csv_to_dict
from datetime import datetime


output = Path(__file__).parents[2] / "data" / "scrapfly_results" / "uncorrelated_portfolio_company_information"
output.mkdir(exist_ok=True)

def create_output_directory():
    output_base = Path(__file__).parents[2] / "data" / "scrapfly_results" / "uncorrelated_portfolio_company_information"
    dated_folder_name = datetime.now().strftime('%Y-%m') + "-uncorrelated-portfolio-company-information"
    output = output_base / dated_folder_name
    output.mkdir(parents=True, exist_ok=True)
    print(f"Output directory created at: {output}")

async def run(urls: list):
    crunchbase.BASE_CONFIG["cache"] = True

    print("running Crunchbase scrape and saving scrapfly_results to ./scrapfly_results directory")
    for url in urls:
        try:
            company = await crunchbase.scrape_company(url)
            name = company["organization"]['id']
            output.joinpath(f"{datetime.now().strftime('%Y-%m-%d')}-{name}.json").write_text(json.dumps(company, indent=2, ensure_ascii=False))
        except:
            print(f"{url} has no crunchbase page.")
    # url = "https://www.crunchbase.com/person/danny-hayes-8e1b"
    # person = await crunchbase.scrape_person(url)
    # output.joinpath("person.json").write_text(json.dumps(person, indent=2, ensure_ascii=False))

create_output_directory()
if __name__ == "__main__":
    file_path = r"C:\Users\fanti\PycharmProjects\Uncorrelated-Pipeline\src\data\2024-5-7-uncorrelated-portfolio-company-urls.csv"
    urls = crunchbase_urls(csv_to_dict(file_path))
    asyncio.run(run(urls))