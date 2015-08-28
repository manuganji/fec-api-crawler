import requests
import json
import os
import operator
import functools

API_KEY = <API_KEY>  # get it from https://api.data.gov/signup/
API_ENDPOINT = "https://api.open.fec.gov/v1"
PAGE_COUNT = 100

def fetch_data(endpoint, api_key, page=1):
    request_params = {
        "sort_hide_null": "false",
        "page": page,
        "api_key": api_key,
        "per_page": PAGE_COUNT,
    }
    request_headers = {
        "Accept":"application/json"
    }
    resp = requests.get(API_ENDPOINT+endpoint,
        params=request_params,
        headers=request_headers
    )
    return resp.json()

def write_page_to_disk(directory, page, json_object):

    if not os.path.exists(directory):
        os.makedirs(directory)

    filename = directory + "/" + str(page) + ".json"

    with open(filename, "w") as f:
        f.write(json.dumps(json_object))

get_results = operator.itemgetter("results")
get_pagination = operator.itemgetter("pagination")
get_count = operator.itemgetter("count")
get_pages = operator.itemgetter("pages")
get_per_page = operator.itemgetter("per_page")

def assert_page_count(json_object):
    achieved_page_count = get_per_page(get_pagination(json_object))
    assert (achieved_page_count >= PAGE_COUNT), "Not desired per page"

def get_last_retrieved_page(directory):

    if not os.path.exists(directory):
        return 0

    files = os.listdir(directory)

    if len(files) == 0:
        return 0
    else:
        return max([int(file.replace(".json","")) for file in files])

def download_for_endpoint(endpoint_name, endpoint_url, api_key=API_KEY):
    print("Fetching data from {0} endpoint".format(endpoint_name))
    endpoint_fetch_data = functools.partial(fetch_data, endpoint_url, api_key)
    write_to_endpoint = functools.partial(write_page_to_disk, endpoint_name)

    last_page = get_last_retrieved_page(endpoint_name)
    max_pages = last_page + 10 # assuming that max_pages will be 10 pages later from now
    page_indx = last_page + 1

    while(page_indx <= max_pages):
        write_to_page = functools.partial(write_to_endpoint, page_indx)

        try:
            json_obj = endpoint_fetch_data(page_indx)
        except Exception as e:
            print("Looks like we may have run out of API_LIMIT for this hour. Or we might have reached the end of pagination.")
            print(e)

        # assert_page_count(json_obj)
        max_pages = get_pages(get_pagination(json_obj))
        log = "Fetched page: {0} of {1} pages"
        print(log.format(page_indx, max_pages))
        write_to_page(get_results(json_obj))
        page_indx = page_indx + 1

    print("""
    *******************************
    We've successfully fetched all the docs for {0} endpoint.
    You should find them in {0} directory.
    *******************************
    """.format(endpoint_name))
