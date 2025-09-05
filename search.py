import json
import requests
import yaml
import logging
import csv
import itertools
import discord
from discord import SyncWebhook

# linkedin_search_results = gather_urls(dork_filters=' site:linkedin.com/in/')
# website_search_results = gather_urls(queries=['instreamset:(url):ouicroissant'])
# facebook_search_results = gather_urls(queries=['"Jamie Thompson" site:facebook.com/people/'])
# flakebook_search_results = gather_urls(queries=['"flakebook" site:github.com'])

file_path = "queries.yml"
CSV_FILE = "sent_urls.csv"
WEBHOOK_URL = "<DISCORD WEBHOOK URL>"
BING_API_KEY = "<BING API KEY>"
GOOGLE_API_KEY = "<GOOGLE API KEY>"
cx_map = {
    "stackoverflow": "e4c5372e43db9422f",
    "linkedin": "e6a6a2883a91a43fe",
    "facebook": "b6a56331e574f4799",
    "web": "83ce408580d404f1e",
    "social": "3166580f5630a42cc"
}
rev_cx_map = {
    'e4c5372e43db9422f': 'StackOverflow',
    'e6a6a2883a91a43fe': 'Linkedin',
    'b6a56331e574f4799': 'Facebook',
    '83ce408580d404f1e': 'Web',
    '3166580f5630a42cc': 'Social Medias'
}

EMBED_ICONS = {
    "google": {
        "color": 369970,
        "icon_url": "https://cdn4.iconfinder.com/data/icons/logos-brands-7/512/google_logo-google_icongoogle-512.png"
    },
    "bing": {
        "color": 1995919,
        "icon_url": "https://seeklogo.com/images/B/bing-logo-708D786F19-seeklogo.com.png"
    }
}


def send_webhook(query: str, urls: list, search_engine: str, cx: str | None):
    formatted_urls = "\n- ".join(["- " + urls[0]] + urls[1:])
    description = f'Query: `{query}`\nㅤ\n{formatted_urls}'

    if search_engine == "google":
        description = f'Query: `{query}`\nCX: `{rev_cx_map[cx]}`\nㅤ\n{formatted_urls}'

    embed = discord.Embed(
        title="ㅤ",
        description=description,
        color=EMBED_ICONS[search_engine]["color"]
    )
    embed.set_author(
        name=search_engine.title(),
        icon_url=EMBED_ICONS[search_engine]["icon_url"]
    )

    webhook = SyncWebhook.from_url(WEBHOOK_URL)
    webhook.send(embed=embed)


def append_to_csv(data):
    with open(CSV_FILE, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(data)


def get_sent_urls():
    with open(CSV_FILE, mode='r', newline='') as file:
        reader = csv.reader(file)
        data = list(reader)  # Convert the reader object to a list

    flattened_data = list(itertools.chain(*data))
    return flattened_data


def make_request(url, params, headers=None):
    try:
        response = requests.get(url, params=params, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        logging.error(f"Request error: {e}")
        return None


def search_google(query, num_results, cx: str):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": GOOGLE_API_KEY,
        "cx": cx,  # Default to WEB if cx not provided
    }

    response_data = make_request(url, params)
    if "items" in response_data:
        return response_data["items"]

    return None


def search_bing(query, num_results, cx=None):
    url = "https://api.bing.microsoft.com/v7.0/search"
    params = {
        'q': query,
        'mkt': 'en-US',
        'count': num_results,
    }
    headers = {
        'Ocp-Apim-Subscription-Key': BING_API_KEY
    }

    response_data = make_request(url, params, headers)
    if response_data and "webPages" in response_data and "value" in response_data["webPages"]:
        return response_data["webPages"]["value"]
    else:
        logging.error(f"Bing Search API returned no results for query: {query}")
        return None


def extract_urls(search_results):
    urls = []

    if search_results:
        sent_urls = get_sent_urls()

        for result in search_results:
            url = result.get("url") or result.get("link")
            if url and url not in sent_urls:
                urls.append(url)

        if urls:
            append_to_csv(urls)

    else:
        logging.warning(f"No new results found for query")

    return urls


def formatted_search_results(queries, search_engine="google", num_results=30, cx=None):
    search_engine_map = {
        "google": search_google,
        "bing": search_bing
    }

    engine_func = search_engine_map.get(search_engine)
    if not engine_func:
        raise ValueError(f"Unsupported search engine: {search_engine}")

    data = []

    for i, query in enumerate(queries):
        _cx = cx[i] if cx else None

        custom_search_engine = _cx
        search_results = engine_func(query, num_results, custom_search_engine)
        urls = extract_urls(search_results)
	# make it so it sends an embed per query if there are results
        data.append({
            "query": query,
            "urls": urls
        })

        if urls:
            send_webhook(query, urls, search_engine, _cx)

    return data


def fetch_bing_results(queries):
    bing_queries = [query["search_string"] for query in queries["bing"]]
    bing_urls = formatted_search_results(queries=bing_queries, search_engine="bing")
    return bing_urls


def fetch_google_results(queries):
    google_queries = [query["search_string"] for query in queries["google"]]
    google_cxs = [cx_map[query["cx"]] for query in queries["google"]]
    google_urls = formatted_search_results(queries=google_queries, search_engine="google", cx=google_cxs)
    return google_urls


def main():
    with open(file_path, 'r') as file:
        queries = yaml.safe_load(file)

    bing_urls = fetch_bing_results(queries)
    print(json.dumps(bing_urls, indent=4))

    google_urls = fetch_google_results(queries)
    print(json.dumps(google_urls, indent=4, default=str))


if __name__ == "__main__":
    main()
