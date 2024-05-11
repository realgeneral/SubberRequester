import json
import re

import aiohttp
import requests
from fake_useragent import UserAgent

from app.logs import logging

def get_headers(token, user_agent):
    headers = {
        'authority': 'www.subber.xyz',
        'accept': '*/*',
        'accept-language': 'de-DE,de;q=0.9',
        'authorization': f'Bearer {token}',
        'user-agent': user_agent,
        'sec-fetch-dest': 'empty',
        'sec-fetch-mode': 'cors',
        'sec-fetch-site': 'same-origin',
    }
    return headers

async def fetch_and_parse_data(token):
    cookies = {
        'token': token,
    }

    # Generating a random user-agent using fake_useragent library
    user_agent = UserAgent().random
    headers = get_headers(token, user_agent)

    async with aiohttp.ClientSession() as session:
        async with session.get('https://www.subber.xyz/api/me', cookies=cookies, headers=headers) as response:
            logging.info(f"status code - {response.status}")
            if response.status == 200:

                data = await response.json()
                logging.info(f"data - {data}")

                return {
                    "id": data.get("id"),
                    "username": data.get("username"),
                    "community_roles": data.get("community_roles", [])
                }
            else:
                return {"error": f"Failed to fetch data, status code: {response.status}"}


async def send_collab_request(token, base_url, profile):
    cookies = {
        'token': token,
    }

    # Generating a random user-agent using fake_useragent library
    user_agent = UserAgent().random
    headers = get_headers(token, user_agent)

    async with aiohttp.ClientSession() as session:
        async with session.get('https://www.subber.xyz/', cookies=cookies, headers=headers) as response:
            if response.status == 200:
                text = await response.text()

                match = re.search(r'"buildId":"(.*?)"', text)
                build_id = match.group(1)
            else:
                return {"error": f"Failed to fetch buildId, status code: {response.status}"}

    parts = base_url.split('/')  # Splitting the URL by '/'
    segment = parts[3]  # The segment 'moonsters' is expected to be at this position
    logging.info(f"parts - {parts}")
    logging.info(f"segment - {segment}")

    # Constructing the new URL
    new_url = f"https://www.subber.xyz/_next/data/{build_id}/{segment}/allowlist.json?slug={segment}"
    logging.info(f"new_url - {new_url}")


    user_agent = UserAgent().random
    headers = get_headers(token, user_agent)

    async with aiohttp.ClientSession() as session:
        async with session.get(new_url,cookies=cookies, headers=headers) as response:
            if response.status == 200:
                data = await response.json()
                if "__N_REDIRECT" in data["pageProps"]:
                    redirect = data["pageProps"]["__N_REDIRECT"]
                    redirect_url = f"https://www.subber.xyz/_next/data/{build_id}{redirect}.json?slug={segment}"
                    async with session.get(redirect_url, cookies=cookies, headers=headers) as redirect_response:
                        if redirect_response.status == 200:
                            red_data = await redirect_response.json()
                            allowlist_id = red_data["pageProps"]["allowlist"]["id"]
                            logging.info(f"allowlist_id 1- {allowlist_id}")

                        else:
                            return {"error": f"Failed to fetch allowlist_id, status code: {redirect_response.status}"}
                else:
                    if "allowlist" in data["pageProps"]:
                        allowlist_id = data["pageProps"]["allowlist"]["id"]
                        logging.info(f"allowlist_id 2- {allowlist_id}")
                    if "allowlists" in data["pageProps"]:
                        allowlist_id = data["pageProps"]["allowlists"][0]["id"]
                        logging.info(f"allowlist_id 2- {allowlist_id}")
            else:
                return {"error": f"Failed to fetch allowlist_id, status code: {response.status}"}

    if allowlist_id is None or allowlist_id == "":
        return {"error": f"Failed to fetch allowlist_id"}
    else:
        allowlist_entries = []
        contact = profile.get("username", "Unknown")
        contact_user_id = profile.get("id", "Unknown")
        community_roles = profile.get("community_roles", [])

        logging.info(f"contact - {contact}")
        logging.info(f"contact_user_id - {contact_user_id}")

        for role in community_roles:
            allowlist_entries.append({
                "allowlist_id": allowlist_id,
                "community_id": role["community_id"],
                "contact_user_id": contact_user_id,
                "contact": contact,
                "giveaway_data": ""
            })

        allowlist_entries_json = json.dumps(allowlist_entries)

        logging.info(f"allowlist_entries_json - {allowlist_entries_json}")
        logging.info(f"1")
        user_agent = UserAgent().random

        logging.info(f"2")

        headers = {
            'authority': 'www.subber.xyz',
            'accept': '*/*',
            'accept-language': 'de-DE,de;q=0.9',
            'authorization': f'Bearer {token}',
            'content-type': 'text/plain;charset=UTF-8',
            'origin': 'https://www.subber.xyz',
            'user-agent': user_agent,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post('https://www.subber.xyz/api/collabRequest', cookies=cookies, headers=headers,
                                         data=allowlist_entries_json) as response:
                if response.status == 200:
                    return "OK"
                else:
                    return {"error": f"Failed to send request, status code: {response.status}"}
