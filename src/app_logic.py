import asyncio

from src.scrapers.processing import processing_functions
from src.scrapers.processing.processing_functions import csv_to_dict, crunchbase_urls

from src.scrapers.scrapfly_scraper.run import run

from src.scrapers.uncorrelated_scraper.uncorrelated_portfolio_company_urls import scrape_uncorrelated, create_output_file
def display_menu():
    menu_options = {
        1: 'Scrape Crunchbase for Uncorrelated portfolio companies information.',
        2: 'Scrape Uncorrelated for portfolio companies.',
        3: 'Placeholder',
        4: 'Exit'
    }

    while True:
        print("\nMenu:")
        for key in menu_options.keys():
            print(f"{key}. {menu_options[key]}")

        try:
            choice = int(input("Enter your choice (1-4): "))
            if choice in menu_options:
                print(f"You selected: {menu_options[choice]}")
                if choice == 4:
                    print("Exiting the menu.")
                    break
                else:
                    handle_choice(choice)
            else:
                print("Invalid choice. Please enter a number between 1 and 4.")
        except ValueError:
            print("Invalid input. Please enter a number between 1 and 4.")


def handle_choice(choice):
    if choice == 1:
        file_path = r"C:\Users\fanti\PycharmProjects\Uncorrelated-Pipeline\src\data\uncorrelated_portfolio_company_urls\2024-5-7-uncorrelated-portfolio-company-urls.csv"
        urls = crunchbase_urls(csv_to_dict(file_path))
        asyncio.run(run(urls))

    elif choice == 2:
        scrape_uncorrelated()

    elif choice == 3:
        create_output_file()


