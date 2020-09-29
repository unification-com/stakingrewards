import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

import click
import matplotlib.pyplot as plt
import requests

log = logging.getLogger(__name__)

BASE_URL = 'https://rest2.unification.io'

REGISTRATION_COST = 1000
TIMESTAMP_COST = 1


def root_path() -> Path:
    current_script = Path(os.path.abspath(__file__))
    data_dir = current_script.parent.parent.parent / 'data'
    return data_dir


def write_d(d):
    target = root_path() / f'cache.json'
    target.write_text(json.dumps(d, indent=2, separators=(',', ': ')))


def write_page(the_type, d, n):
    target = root_path() / the_type / f'page{n}.json'
    target.write_text(json.dumps(d, indent=2, separators=(',', ': ')))


def read_d():
    target = root_path() / f'cache.json'
    if target.exists():
        contents = target.read_text()
        d = json.loads(contents)
    else:
        d = {}
    return d


def get_headers():
    return {
        'Content-Type': 'application/json',
        'clientName': 'stakingrewards'
    }


def get_page(the_type, n):
    """
    the_type, could be: register_beacon, record_wrkchain_hash

    """
    target = root_path() / the_type / f'page{n}.json'
    if target.exists():
        contents = target.read_text()
        d = json.loads(contents)
        return d, 0
    else:
        q_start = time.time()
        url = f'{BASE_URL}/txs?message.action={the_type}&page={n}'
        log.info(url)
        r = requests.get(url, headers=get_headers())
        resp = r.json()
        q_stop = time.time()
        query_diff = q_stop - q_start
        target.write_text(r.text)
        return resp, query_diff


def num_pages():
    url = f'{BASE_URL}/txs?message.action=record_wrkchain_hash&page={1}'
    log.info(url)
    r = requests.get(url, headers=get_headers())
    resp = r.json()
    return resp['page_total']


def parse_page(data):
    page_total = data['page_total']
    txs = data['txs']
    return page_total


def read_date(ts):
    return datetime.strptime(ts, "%Y-%m-%dT%H:%M:%SZ")


@click.group()
def main():
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


def get_beacon_registrations():
    """
    # Beacon registration dates are missing from the Genesis export
    """
    beacon_registrations, qtime = get_page('register_beacon', 1)
    for tx in beacon_registrations['txs']:
        yield read_date(tx['timestamp']), tx['txhash'], REGISTRATION_COST


def get_wrkchain_registrations():
    wrkchain_registrations, qtime = get_page('register_wrkchain', 1)
    for tx in wrkchain_registrations['txs']:
        yield read_date(tx['timestamp']), tx['txhash'], REGISTRATION_COST


@main.command()
def pry():
    target = root_path() / 'genesis' / f'genesis.json'
    contents = target.read_text()
    d = json.loads(contents)

    beacon_registrations = list(get_beacon_registrations())
    wrkchain_registrations = list(get_wrkchain_registrations())

    beacon_submissions = []
    for n, br in enumerate(beacon_registrations):
        timestamps = d['app_state']['beacon']['registered_beacons'][n][
            'timestamps']
        for stamp in timestamps:
            beacon_submissions.append(
                (datetime.utcfromtimestamp(int(stamp['submit_time'])),
                 stamp['hash'], TIMESTAMP_COST))

    wrkchain_submissions = []
    for n, br in enumerate(wrkchain_registrations):
        timestamps = d['app_state']['wrkchain']['registered_wrkchains'][n][
            'blocks']
        for stamp in timestamps:
            wrkchain_submissions.append(
                (datetime.utcfromtimestamp(int(stamp['sub_time'])),
                 stamp['blockhash'], TIMESTAMP_COST))

    mergedlist = beacon_registrations + wrkchain_registrations + \
                 beacon_submissions + wrkchain_submissions
    mergedlist = sorted(mergedlist, key=lambda x: x[0])

    # accumulate
    new_list = []
    acc = 0
    for dt, hash, value in mergedlist:
        acc = acc + value
        new_list.append((dt, acc))

    timestamps = [x[0] for x in new_list]
    fund = [x[1] for x in new_list]

    plt.scatter(timestamps, fund)

    # naming the x axis
    plt.xlabel('timestamp')
    # naming the y axis
    plt.ylabel('FUND spent')

    # giving a title to my graph
    plt.title('Accumulated rewards')

    # function to show the plot
    plt.show()


if __name__ == "__main__":
    main()
