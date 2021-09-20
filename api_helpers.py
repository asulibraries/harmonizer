import json
import requests as r
import aiohttp
import asyncio
from asyncio_throttle import Throttler
import urllib.parse
from mongodb import get_tokens


async def async_grab_colls(uri, client, throttler):
    async with throttler:
        try:
            resp = None
            headers = {"accept": "application/json"}
            async with client.get(uri, headers=headers) as session:
                if session.status != 200:
                    resp = await session.json()
                    session.raise_for_status()
                resp = await session.json()
                if uri.startswith("https://keep.lib.asu.edu"):
                    return {"keep": resp["search_results"]}
                elif uri.startswith("https://prism.lib.asu.edu"):
                    return {"prism": resp["search_results"]}
        except Exception as e:
            print(f"Error on {uri}: {e}")


async def async_colls_worker(uris_list):
    output = []
    throttler = Throttler(rate_limit=25)
    async with aiohttp.ClientSession() as client:
        awaitables = [async_grab_colls(uri, client, throttler) for uri in uris_list]
        results = await asyncio.gather(*awaitables)
    return results


def get_colls():
    final_results = {}
    uris_to_go = [
        "https://prism.lib.asu.edu/api/collections",
        "https://keep.lib.asu.edu/api/collections",
    ]
    results = asyncio.run(async_colls_worker(uris_to_go))
    for coll in results:
        for key, value in coll.items():
            for entry in value:
                entry["field_title"] = (
                    (urllib.parse.unquote(entry["field_title"]))
                    .strip()
                    .replace("&#039;", "'")
                    .replace("&quot;", '"')
                )
            final_results[key] = value
    return final_results


def retrieve_coll_meta(repo_name, col_id):
    splitsville = col_id.split("||")
    raw_json = r.get(
        f"http://10.192.17.250:8983/solr/{repo_name.upper()}/select?q=itm_field_ancestors:{splitsville[0]}&rows=1000&fl=itm_field_linked_agent_tid,sm_all_subjects"
    )
    temp = []
    for obj in raw_json.json()["response"]["docs"]:
        if len(obj) == 0:
            pass
        else:
            if "sm_all_subjects" in obj:
                for itm_id in obj["sm_all_subjects"]:
                    if itm_id not in temp:
                        temp.append(itm_id)
            if "itm_field_linked_agent_tid" in obj:
                for itm_id in obj["itm_field_linked_agent_tid"]:
                    if itm_id not in temp:
                        temp.append(itm_id)
    if len(temp) > 0:
        return temp
    else:
        return None


def retrieve_item_meta(repo_name, item_id):
    raw_json = r.get(
        f"http://10.192.17.250:8983/solr/{repo_name.upper()}/select?q=its_nid:{item_id}"
    )
    temp = []
    if len(raw_json.json()["response"]["docs"]) == 0:
        return None, "no records"
    elif len(raw_json.json()["response"]["docs"]) > 1:
        return None, "more than 1 record"
    else:
        if len(raw_json.json()["response"]["docs"][0]) == 0:
            return None, "no metadata"
        else:
            temp = {"title": None, "headings": []}

            if "sm_all_subjects" in (raw_json.json()["response"]["docs"][0]):
                for itm_id in raw_json.json()["response"]["docs"][0]["sm_all_subjects"]:
                    if itm_id not in temp["headings"]:
                        temp["headings"].append(int(itm_id))

            if "itm_field_linked_agent_tid" in (raw_json.json()["response"]["docs"][0]):
                for itm_id in raw_json.json()["response"]["docs"][0][
                    "itm_field_linked_agent_tid"
                ]:
                    if itm_id not in temp["headings"]:
                        temp["headings"].append(int(itm_id))

            if "tm_X3b_en_complex_title" in (raw_json.json()["response"]["docs"][0]):
                temp["title"] = raw_json.json()["response"]["docs"][0][
                    "tm_X3b_en_complex_title"
                ][0]

            if len(temp["headings"]) > 0:
                return temp, "sucess"
            else:
                return None, "no metadata"


def retrieve_term_meta(repo_name, term_id):
    raw = r.get(f"https://{repo_name}.lib.asu.edu/taxonomy/term/{term_id}?_format=json")
    if raw.status_code == 200:
        return True, raw.json()
    else:
        return False, raw.json()


def send_term_updates(orig_term_data, data_package):
    new_term_field_authority_link = {
        "uri": data_package["uri"],
        "title": data_package["term_name"],
        "options": [],
        "source": data_package["source"],
    }

    orig_term_data["name"][0]["value"] = data_package["term_name"]

    if "field_authority_link" in orig_term_data:
        if len(orig_term_data["field_authority_link"]) == 1:
            if (
                orig_term_data["field_authority_link"][0]["source"]
                == data_package["source"]
            ):
                orig_term_data["field_authority_link"][
                    0
                ] = new_term_field_authority_link
            else:
                (orig_term_data["field_authority_link"]).append(
                    new_term_field_authority_link
                )
        elif len(orig_term_data["field_authority_link"]) > 1:
            (orig_term_data["field_authority_link"]).append(
                new_term_field_authority_link
            )
        else:
            (orig_term_data["field_authority_link"]).append(
                new_term_field_authority_link
            )
    else:
        orig_term_data["field_authority_link"] = []
        (orig_term_data["field_authority_link"]).append(new_term_field_authority_link)

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {data_package['token']}",
    }
    patch = r.patch(
        f"https://{data_package['repo_name']}.lib.asu.edu/taxonomy/term/{data_package['term_id']}?_format=json",
        headers=headers,
        data=json.dumps(orig_term_data),
    )
    if patch.status_code != 200:
        return False, patch.status_code
    else:
        return True, 200


def cookie_monster(req, response):
    existing_cookie = req.cookies.get("harmonizer")
    if not existing_cookie:
        tokens = get_tokens()
        response.set_cookie(
            "harmonizer_keep",
            tokens["keep"],
            max_age=14400,
            samesite="None",
            secure=True,
        )
        response.set_cookie(
            "harmonizer_prism",
            tokens["prism"],
            max_age=14400,
            samesite="None",
            secure=True,
        )
        return response
    else:
        return response
