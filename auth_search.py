import json
import requests as r
import aiohttp
import asyncio
from asyncio_throttle import Throttler
import xmltodict
import urllib.parse
from fuzzywuzzy import fuzz
from time import perf_counter


async def lc_data(uri, client, throttler):
    async with throttler:
        try:
            resp = None
            if uri.startswith(
                "http://id.loc.gov/authorities/subjects/suggest/"
            ) or uri.startswith("http://id.loc.gov/authorities/names/suggest/"):
                headers = {"accept": "application/json"}
                async with client.get(uri, headers=headers) as session:
                    if session.status != 200:
                        resp = await session.json()
                        session.raise_for_status()
                    resp = await session.json()
                    if len(resp[1]) > 0:
                        temp = []
                        for authority in resp[1]:
                            index = resp[1].index(authority)
                            new_uri = resp[3][index].replace("http://", "https://")
                            temp.append({"heading": authority, "uri": new_uri})
                        return temp
                    else:
                        return []
            elif uri.startswith(
                "http://id.loc.gov/authorities/subjects/didyoumean/"
            ) or uri.startswith("http://id.loc.gov/authorities/names/didyoumean/"):
                headers = {"accept": "application/xml"}
                async with client.get(uri, headers=headers) as session:
                    if session.status != 200:
                        resp = await session.json()
                        session.raise_for_status()
                    resp = await session.text()
                    jsonified_xml = xmltodict.parse(resp, dict_constructor=dict)
                    if int(jsonified_xml["idservice:service"]["@search-hits"]) > 0:
                        return [
                            {
                                "heading": jsonified_xml["idservice:service"][
                                    "idservice:term"
                                ]["#text"],
                                "uri": jsonified_xml["idservice:service"][
                                    "idservice:term"
                                ]["@uri"],
                            }
                        ]
                    else:
                        return []
        except Exception as e:
            print(f"Error on {uri}: {e}")


async def lc_data_worker(uris_list):
    output = []
    throttler = Throttler(rate_limit=25)
    async with aiohttp.ClientSession() as client:
        awaitables = [lc_data(uri, client, throttler) for uri in uris_list]
        results = await asyncio.gather(*awaitables)
    return results


def design_lc_uris(query):
    parsed_term = urllib.parse.quote(query)
    return [
        f"http://id.loc.gov/authorities/subjects/didyoumean/?label={parsed_term}",
        f"http://id.loc.gov/authorities/names/didyoumean/?label={parsed_term}",
        f"http://id.loc.gov/authorities/subjects/suggest/?q={parsed_term}",
        f"http://id.loc.gov/authorities/names/suggest/?q={parsed_term}",
        f"http://id.loc.gov/authorities/subjects/label/{parsed_term}",
        f"http://id.loc.gov/authorities/names/label/{parsed_term}",
    ]


async def enrich_lc_data(data_package, client, throttler):
    async with throttler:
        try:
            resp = None
            headers = {"accept": "application/json"}
            async with client.get(
                data_package["uri"] + ".json", headers=headers
            ) as session:
                if session.status != 200:
                    resp = await session.json()
                    session.raise_for_status()
                resp = await session.json()
                data_package["citations"] = []
                match_uri = data_package["uri"].replace("https://", "http://")
                for json_block in resp:
                    if (
                        json_block["@type"][0]
                        == "http://www.loc.gov/mads/rdf/v1#Source"
                    ):
                        if (
                            "http://www.loc.gov/mads/rdf/v1#citationSource"
                            in json_block
                        ):
                            source = json_block[
                                "http://www.loc.gov/mads/rdf/v1#citationSource"
                            ][0]["@value"]
                        else:
                            source = "No source;"
                        if "http://www.loc.gov/mads/rdf/v1#citationNote" in json_block:
                            note = json_block[
                                "http://www.loc.gov/mads/rdf/v1#citationNote"
                            ][0]["@value"]
                        else:
                            note = "[no citation note]"
                        data_package["citations"].append(f"{source} {note}")
                    elif json_block["@id"] == match_uri:
                        for auth_kind in json_block["@type"]:
                            if (
                                auth_kind != "http://www.loc.gov/mads/rdf/v1#Authority"
                                and auth_kind
                                != "http://www.w3.org/2004/02/skos/core#Concept"
                            ):
                                data_package["type"] = (auth_kind.split("#"))[-1]
                    else:
                        pass
                return data_package
        except Exception as e:
            print(f"Error on {uri}: {e}")


async def enrich_lc_data_worker(uris_list):
    output = []
    throttler = Throttler(rate_limit=25)
    async with aiohttp.ClientSession() as client:
        awaitables = [
            enrich_lc_data(data_package, client, throttler)
            for data_package in uris_list
        ]
        results = await asyncio.gather(*awaitables)
    return results


def grab_lc(search_term):
    t1 = perf_counter()
    uris_to_go = design_lc_uris(search_term)
    results = asyncio.run(lc_data_worker(uris_to_go))
    flattened = []
    for sublist in results:
        if sublist is not None:
            for item in sublist:
                flattened.append(item)
    deduped = []
    for item in flattened:
        if item not in deduped:
            item["fuzzy"] = fuzz.token_sort_ratio(item["heading"], search_term)
            deduped.append(item)
    enriched = asyncio.run(enrich_lc_data_worker(deduped))
    sorted_enriched = sorted(enriched, key=lambda k: k["fuzzy"], reverse=True)
    t2 = perf_counter()
    print(t2 - t1)
    if len(sorted_enriched) > 0:
        return sorted_enriched
    else:
        return None
