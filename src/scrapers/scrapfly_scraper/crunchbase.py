"""
This is an example web scraper for crunchbase.com used in scrapfly blog article:
https://scrapfly.io/blog/how-to-scrape-crunchbase/

To run this scraper set env variable $SCRAPFLY_KEY with your scrapfly API key:
$ export $SCRAPFLY_KEY="your key from https://scrapfly.io/dashboard"
"""
from datetime import datetime
import gzip
import json
import os
import jmespath
from src.scrapers.scrapfly_scraper import config

from parsel import Selector
from typing import Dict, Iterator, List, Literal, Tuple, TypedDict

from loguru import logger as log
from scrapfly import ScrapeApiResponse, ScrapeConfig, ScrapflyClient

SCRAPFLY = ScrapflyClient(key=os.environ["SCRAPFLY_KEY"])
BASE_CONFIG = {
    "asp": True,
}


class CompanyData(TypedDict):
    organization: Dict
    employees: List[Dict]


def parse_company(result: ScrapeApiResponse) -> CompanyData:
    # the app cache data can be in one of two places:
    app_state_data = result.selector.css("script#ng-state::text").get()
    if not app_state_data:
        app_state_data = _unescape_angular(result.selector.css("script#client-app-state::text").get() or "")
    app_state_data = json.loads(app_state_data)
    # there are multiple caches:
    cache_keys = list(app_state_data["HttpState"])
    # Organization data can be found in this cache:
    data_cache_key = next(key for key in cache_keys if "entities/organizations/" in key)
    # Some employee/contact data can be found in this key:
    people_cache_key = next(key for key in cache_keys if "/data/searches/contacts" in key)
    organization = app_state_data["HttpState"][data_cache_key]["data"]
    employees = app_state_data["HttpState"][people_cache_key]["data"]
    return {
        "organization": _reduce_organization_dataset(organization),
        "employees": _reduce_employee_dataset(employees),
        "board_members_advisors": _important_people_from_company(organization),
        "import_employees": _get_company_important_employees(organization)
    }


async def scrape_company(url: str) -> CompanyData:
    log.info(f"scraping company: {url}")
    result = await SCRAPFLY.async_scrape(ScrapeConfig(url, **BASE_CONFIG))
    return parse_company(result)


async def scrape_person(url: str) -> Dict:
    log.info(f"scraping person: {url}")
    result = await SCRAPFLY.async_scrape(ScrapeConfig(url, **BASE_CONFIG))
    return parse_person(result)


def parse_person(result: ScrapeApiResponse) -> Dict:
    app_state_data = result.selector.css("script#ng-state::text").get()
    if not app_state_data:
        app_state_data = _unescape_angular(result.selector.css("script#client-app-state::text").get() or "")
    app_state_data = json.loads(app_state_data)
    cache_keys = list(app_state_data["HttpState"])
    dataset_key = next(key for key in cache_keys if "data/entities" in key)
    dataset = app_state_data["HttpState"][dataset_key]["data"]
    return _reduce_person_dataset(dataset)


async def _scrape_sitemap_index() -> List[str]:
    log.info("scraping sitemap index for sitemap urls")
    result = await SCRAPFLY.async_scrape(
        ScrapeConfig("https://www.crunchbase.com/www-sitemaps/sitemap-index.xml", **BASE_CONFIG)
    )
    urls = result.selector.xpath("//sitemap/loc/text()").getall()
    log.info(f"found {len(urls)} sitemaps")
    return urls


def parse_sitemap(result: ScrapeApiResponse) -> Iterator[Tuple[str, datetime]]:
    sel = Selector(text=gzip.decompress(result.content.read()).decode())
    urls = sel.xpath("//url")
    log.info(f"found {len(urls)} in sitemap {result.context['url']}")
    for url_node in urls:
        url = url_node.xpath("loc/text()").get()
        last_modified = datetime.fromisoformat(url_node.xpath("lastmod/text()").get().strip("Z"))
        yield url, last_modified


async def discover_target(target: Literal["organizations", "people"], min_last_modified=None):
    sitemap_urls = await _scrape_sitemap_index()
    urls = [url for url in sitemap_urls if target in url]
    log.info(f"found {len(urls)} matching sitemap urls (from total of {len(sitemap_urls)})")
    for url in urls:
        log.info(f"scraping sitemap: {url}")
        result = await SCRAPFLY.async_scrape(ScrapeConfig(url, **BASE_CONFIG))
        for url, mod_time in parse_sitemap(result):
            if min_last_modified and mod_time < min_last_modified:
                continue  # skip
            yield url


def _reduce_organization_dataset(data: Dict) -> Dict:
    return jmespath.search(
        """{
        id: properties.identifier.permalink,
        name: properties.title,
        logo: properties.identifier.image_id,
        description: cards.overview_description.description,

        linkedin: cards.social_fields.linkedin.value,
        facebook: cards.social_fields.facebook.value,
        twitter: cards.social_fields.twitter.value,

        email: cards.contact_fields.contact_email,
        phone: cards.contact_fields.phone_number,

        website: cards.company_about_fields2.website.value,
        ipo_status: cards.company_about_fields2.ipo_status,
        rank_org_company: cards.company_about_fields2.rank_org_company,

        semrush_global_rank: cards.semrush_summary.semrush_global_rank,
        semrush_visits_latest_month: cards.semrush_summary.semrush_visits_latest_month,
        semrush_id: cards.semrush_summary.identifier.permalink,

        categories: cards.overview_fields_extended.categories[].value,
        legal_name: cards.overview_fields_extended.legal_name,
        operating_status: cards.overview_fields_extended.operating_status,
        last_funding_type: cards.overview_fields_extended.last_funding_type,
        founded_on: cards.overview_fields_extended.founded_on.value,
        location_groups: cards.overview_fields_extended.location_group_identifiers[].value,

        trademarks: cards.ipqwery_summary.ipqwery_num_trademark_registered,
        trademark_popular_class: cards.ipqwery_summary.ipqwery_popular_trademark_class,
        patents: cards.ipqwery_summary.ipqwery_num_patent_granted,
        patent_popular_category: cards.ipqwery_summary.ipqwery_popular_patent_category,

        investments: cards.company_overview_highlights.num_investments,
        investors: cards.company_overview_highlights.num_investors,
        acquisitions: cards.company_overview_highlights.num_acquisitions,
        contacts: cards.company_overview_highlights.num_contacts,
        funding_total_usd: cards.company_overview_highlights.funding_total.value_usd,
        stock_symbol: cards.company_overview_highlights.listed_stock_symbol,
        exits: cards.company_overview_highlights.num_exits,
        similar_orgs: cards.company_overview_highlights.num_org_similarities,
        current_positions: cards.company_overview_highlights.num_current_positions,

        investors_lead: cards.company_financials_highlights.num_lead_investors,
        investments_lead: cards.company_financials_highlights.num_lead_investments,
        funding_rounds: cards.company_financials_highlights.num_funding_rounds,

        event_appearances: cards.event_appearances_headline.num_event_appearances,
        advisors: cards.advisors_headline.num_current_advisor_positions,
        buildwith_tech_used: cards.builtwith_summary.builtwith_num_technologies_used,

        similar: cards.org_similarity_list[].{
            score: score,
            reasons: reasons,
            id: source.permalink
        },
        timeline: cards.overview_timeline.entities[].{
            title: properties.activity_properties.title,
            author: properties.activity_properties.author,
            publisher: properties.activity_properties.publisher,
            url: properties.activity_properties.url.value,
            thumb: properties.activity_properties.thumbnail_url,
            date: properties.activity_date,
            type: properties.entity_def_id
        },
        events: cards.event_appearances_list[].{
            type: appearance_type,
            event_start_date: event_starts_on,
            name: event_identifier.value
        },
        investments: cards.investments_list[].{
            raised_usd: funding_round_money_raised.value_usd,
            name: funding_round_identifier.value,
            organization: organization_identifier.value,
            announced_on: announced_on,
            is_lead_investor: is_lead_investor
        },
        funding_rounds: cards.funding_rounds_list[].{
            announced_on: announced_on,
            raised_usd: money_raised.value_usd,
            investors: num_investors,
            lead_investors: lead_investor_identifiers[].value
        },
        investors: cards.investors_list[].{
            is_lead_investor: is_lead_investor,
            name: investor_identifier.value
        }
    }""",
        data,
    )


def _get_company_important_employees(data: Dict) -> List[Dict]:
    parsed = []
    for person in data.get("cards", {}).get("current_employees_featured_order_field", []):
        parsed.append(
            jmespath.search(
                """{
                name: person_identifier.value,
                linkedin: person_identifier.permalink,
                job_levels: job_type,
                job_departments: identifier.entity_def_id,
                started_on: started_on.value,
                title: title
            }""",
                person,
            )
        )

    return parsed


def _important_people_from_company(data: Dict) -> List[Dict]:
    parsed = []
    for person in data.get("cards", {}).get("current_advisors_image_list", []):
        parsed.append(
            jmespath.search(
                """{
                name: person_identifier.value,
                linkedin: person_identifier.permalink,
                job_levels: job_type,
                job_departments: identifier.entity_def_id
            }""",
                person,
            )
        )

    return parsed


def _reduce_employee_dataset(data: Dict) -> List[Dict]:
    parsed = []
    for person in data["entities"]:
        parsed.append(
            jmespath.search(
                """{
                name: properties.name,    
                linkedin: properties.linkedin,
                job_levels: properties.job_levels,
                job_departments: properties.job_departments
            }""",
                person,
            )
        )

    return parsed


def _reduce_person_dataset(dataset: dict) -> Dict:
    parsed = jmespath.search(
        """{
        name: properties.identifier.value,
        title: properties.title,
        description: properties.short_description,
        type: properties.layout_id,

        gender: cards.overview_fields.gender,
        location_groups: cards.overview_fields.location_group_identifiers[].value,
        location: cards.overview_fields.location_identifiers[].value,
        current_jobs: cards.jobs_summary.num_current_jobs,
        past_jobs: cards.jobs_summary.num_past_jobs,

        education: cards.education_image_list[].{
            school: school_identifier.value,
            completed_on: completed_on.value,
            started_on: started_on.value,
            type: type_name
        },

        timeline: cards.timeline.entities[].{
            title: properties.activity_properties.title,
            author: properties.activity_properties.author,
            publisher: properties.activity_properties.publisher,
            url: properties.activity_properties.url.value,
            thumb: properties.activity_properties.thumbnail_url,
            date: properties.activity_date,
            type: properties.entity_def_id
        },

        investments: cards.investments_list[].{
            raised_usd: funding_round_money_raised.value_usd,
            name: funding_round_identifier.value,
            organization: organization_identifier.value,
            announced_on: announced_on,
            is_lead_investor: is_lead_investor
        },

        exits: cards.exits_image_list[].{
            name: identifier.value,
            short_description: short_description
        }

        investing_overview: cards.investor_overview_headline,
        linkedin: cards.overview_fields2.linkedin.value,
        twitter: cards.overview_fields2.twitter.value,
        facebook: cards.overview_fields2.facebook.value,

        current_advisor_jobs: cards.investor_overview_headline.num_current_advisor_jobs,
        founded_orgs: cards.investor_overview_headline.num_founded_organizations,
        portfolio_orgs: cards.investor_overview_headline.num_portfolio_organizations,
        rank_principal_investor: cards.investor_overview_headline.rank_principal_investor
    }""",
        dataset,
    )
    return parsed


def _unescape_angular(text):
    ANGULAR_ESCAPE = {
        "&a;": "&",
        "&q;": '"',
        "&s;": "'",
        "&l;": "<",
        "&g;": ">",
    }
    for from_, to in ANGULAR_ESCAPE.items():
        text = text.replace(from_, to)

    return text
