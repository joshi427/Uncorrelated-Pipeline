"""
To run this script set the env variable $SCRAPFLY_KEY with your scrapfly API key:
$ export $SCRAPFLY_KEY='scp-live-467683007c4948a082bb5459c41a3e91'
"""
from pathlib import Path
import asyncio
import json
import crunchbase
from datetime import datetime

output = Path(__file__).parents[2] / "data" / "scrapfly-results"
output.mkdir(exist_ok=True)


async def run(urls: list):
    crunchbase.BASE_CONFIG["cache"] = True

    print("running Crunchbase scrape and saving scrapfly-results to ./scrapfly-results directory")
    for url in urls:
        company = await crunchbase.scrape_company(url)
        name = company["organization"]['id']
        output.joinpath(f"{datetime.now().strftime('%Y-%m-%d')}-{name}.json").write_text(json.dumps(company, indent=2, ensure_ascii=False))

    # url = "https://www.crunchbase.com/person/danny-hayes-8e1b"
    # person = await crunchbase.scrape_person(url)
    # output.joinpath("person.json").write_text(json.dumps(person, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    urls = ["https://www.crunchbase.com/organization/gradle/people",
            "https://www.crunchbase.com/organization/grafbase/people",
            "https://www.crunchbase.com/organization/keebo/people",
            "https://www.crunchbase.com/organization/redis/people"]
    asyncio.run(run(urls))