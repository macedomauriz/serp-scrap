import requests
from bs4 import BeautifulSoup
import collections
import functools
import operator
from urllib.parse import urlparse
from tqdm import tqdm
import os

preferred_domain = os.environ.get("PREFERRED_DOMAIN")
geography = os.environ.get("GEOGRAPHY").split(",")
synonyms = os.environ.get("SYNONIMS").split(",")


def track(query, site, geo):
    # Define the URL to scrape (replace with your target URL)
    url = f"https://www.google.com/search?q={query}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.36"
    }

    try:
        # Make search
        response = requests.get(url, headers=headers)
    except requests.exceptions.RequestException as e:
        raise SystemExit(e)

    # Parse the HTML content of the page using BeautifulSoup
    soup = BeautifulSoup(response.text, "html.parser")

    # Find and make a list of every anchor tag
    links = soup.find_all("a")

    # Set a list for all domain results
    total_serp = []

    # Loop through the anchor list
    for link in links:
        # Append in the single_serp list every link with a h3 inside
        # WARNING: Google DOM changes might break this
        if link.h3 is not None:
            a = link.get("href")

            if "http" in a:
                domain = urlparse("http" + a.split("http")[1]).netloc
                total_serp.append(domain)

    for index, result in enumerate(total_serp):
        if result.find(site) != -1:
            return [total_serp[:5], {geo: index + 1}]

    return [total_serp, {geo: 0}]


while True:
    site = input(
        f"\nWhich site search results you'd like to track \
[blank: {preferred_domain}]. Enter 'q' to quit: "
    )

    if len(site) == 0:
        site = preferred_domain

    if site == "q":
        break

    print(f"\nPosition track for: {site}\n")

    # Set list to store dictionaries with {geo: position}
    city_results = []

    # Set list to store raw position numbers
    raw_results = []

    # Set list to store domain results in each query
    raw_domains_results = []

    for geo in tqdm(
        geography, ncols=80, bar_format="{l_bar}{bar}", ascii="︲▇", desc="Searching: "
    ):
        for synonym in synonyms:
            # print(f"track args: {synonym} {geo}, {site}, {geo}")
            tracked = track(f"{synonym} {geo}", site, geo)

            raw_domains_results.append(tracked[0])

            city_results.append(tracked[1])
            raw_results.append(tracked[1].values())

    ordered_city_results = dict(
        functools.reduce(operator.add, map(collections.Counter, city_results))
    )

    ordered_raw_results = [item for sublist in raw_results for item in sublist]

    unordered_domains_results = [
        item for sublist in raw_domains_results for item in sublist
    ]

    # Set a dictionary to add domain results
    ordered_domain_results = {}

    for domain in list(set(unordered_domains_results)):
        value = unordered_domains_results.count(domain)
        ordered_domain_results[domain] = value

    def domain_appearances():
        print(f"\nPositions for all queries: {ordered_raw_results}\n")

        print("Position by cities:")
        for key, value in sorted(
            ordered_city_results.items(), key=lambda item: item[1]
        ):
            print(f"{key.title()}: {value} ({value/len(synonyms)})")

        print(
            f"Total: {sum(ordered_raw_results)} ({sum(ordered_raw_results)/(len(synonyms)*len(geography))})"
        )

        print("\nTop 5 domain appearances count:")
        for key, value in sorted(
            ordered_domain_results.items(), key=lambda item: item[1], reverse=True
        ):
            print(f"{key}: {value}")

        print("\nDone!")

    domain_appearances()
