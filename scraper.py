#!/usr/bin/env python3

import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup

OUTAGES_URL = 'https://www.bchydro.com/power-outages/app/outage-list.html'


def process_region(region_el, status_type):
    region_code = region_el.attrs["region-code"]
    region_id = region_el.attrs["region-id"]

    try:
        customers_affected_14d = int(region_el.select_one(".municipality-filter .col-1").findAll("div")[1].select_one("b").get_text().strip())
    except:
        customers_affected_14d = -1

    outages_el = region_el.select("tbody tr")

    outages = [process_outage(outage, status_type) for outage in outages_el]

    return {
        "region_code": region_code,
        "region_id": region_id,
        "customers_affected_14d": customers_affected_14d,
        "outages": outages
    }


def process_outage(outage_el, status_type):
    try:
        municipality_code = " ".join(outage_el.attrs["class"]).strip()
    except:
        municipality_code = ""

    try:
        municipality = outage_el.select_one(".municip").get_text().strip()
    except:
        municipality = ""

    try:
        off_since = parse_date(outage_el.select_one(".off-since").get_text().strip())
    except:
        off_since = ""

    try:
        status = outage_el.select_one(".status").get_text().strip()
    except:
        status = ""

    try:
        area = outage_el.select_one(".area").get_text().strip()
    except:
        area = ""

    try:
        customers_affected = outage_el.select_one(".cust-aff").get_text().strip()
    except:
        customers_affected = ""

    try:
        cause = outage_el.select_one(".cause").get_text().strip()
    except:
        cause = ""

    try:
        last_updated = outage_el.select_one(".last-updated").get_text().strip()
    except:
        last_updated = ""

    last_updated = parse_date(last_updated)
    outage = {
        "municipality_code": municipality_code,
        "municipality": municipality,
        "area": area,
        "customers_affected": customers_affected,
        "cause": cause,
        "last_updated": last_updated,
        "start": off_since
    }

    if status_type == "restored" or status_type == "planned":
        outage["end"] = parse_date(status)
    elif status_type == "current":
        outage["status"] = status

    return outage


def parse_date(time_str):
    time_str = time_str.replace("a.m.", "AM")
    time_str = time_str.replace("p.m.", "PM")

    try:
        time_formatted = datetime.strptime(time_str, "%b %d %I:%M %p")
        time_formatted = time_formatted.replace(year=datetime.now().year)
    except:
        return ""

    return time_formatted.__str__()


def main():
    r = requests.get(OUTAGES_URL)

    if r.status_code != 200:
        exit(1)

    soup = BeautifulSoup(r.text, 'html.parser')

    restored_outages_regions = soup.select_one("#restored").select(".outage-list-details")
    current_outages_regions = soup.select_one("#current").select(".outage-list-details")
    planned_outages_regions = soup.select_one("#planned").select(".outage-list-details")

    restored_outages = [process_region(region, "restored") for region in restored_outages_regions]
    current_outages = [process_region(region, "current") for region in current_outages_regions]
    planned_outages = [process_region(region, "planned") for region in planned_outages_regions]

    output = {
        "restored": {region["region_code"]: region for region in restored_outages},
        "current": {region["region_code"]: region for region in current_outages},
        "planned": {region["region_code"]: region for region in planned_outages}
    }

    with open("bchydro_outages.json", "w") as outfile:
        json.dump(output, outfile, indent=2, sort_keys=True)


if __name__ == "__main__":
    main()
