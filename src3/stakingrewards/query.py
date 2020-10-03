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

REGISTRATION_COST = 10000
TIMESTAMP_COST = 1


def root_path() -> Path:
    current_script = Path(os.path.abspath(__file__))
    data_dir = current_script.parent.parent.parent / 'data'
    return data_dir


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


def load_data():
    target = root_path() / 'genesis' / f'genesis.json'
    contents = target.read_text()
    d = json.loads(contents)

    # Beacon registration dates are missing from the Genesis export,
    # so get them from the API. WRKChain registrations exist, but get them from
    # the API for symmetry
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

    return beacon_registrations, wrkchain_registrations, \
           beacon_submissions, wrkchain_submissions


def plot_instantaneous_rewards(mergedlist):
    import matplotlib.pyplot as plt
    timestamps = [x[0] for x in mergedlist]
    fund = [x[2] for x in mergedlist]
    plt.scatter(timestamps, fund)

    plt.xlabel('Date')
    plt.ylabel('FUND entered')

    # giving a title to my graph
    plt.title('Instantaneous rewards')

    # function to show the plot
    plt.savefig('instantaneous.pdf', format='pdf', dpi=1200)
    plt.show()


def plot_accumulated_rewards(accumulation_list):
    import matplotlib.pyplot as plt
    timestamps = [x[0] for x in accumulation_list]
    fund = [x[2] for x in accumulation_list]

    plt.scatter(timestamps, fund)
    plt.xlabel('Date')
    plt.ylabel('FUND entered')
    plt.title('Accumulated rewards')

    log.info('Saving image')
    plt.savefig('accumulated.pdf', format='pdf', dpi=1200)
    plt.show()


@main.command()
def pry():
    log.info('Loading data')
    beacon_registrations, wrkchain_registrations, beacon_submissions, \
    wrkchain_submissions = load_data()

    log.info('Plotting data')
    mergedlist = beacon_registrations + wrkchain_registrations + \
                 beacon_submissions + wrkchain_submissions
    mergedlist = sorted(mergedlist, key=lambda x: x[0])

    y1 = datetime.strptime('2020-09-01', "%Y-%m-%d")

    accumulation_list = []
    acc = 0
    x1 = None
    for dt, submission_hash, value in mergedlist:
        if dt > y1 and x1 is None:
            x1 = acc
        acc = acc + value
        accumulation_list.append((dt, submission_hash, acc))

    first = accumulation_list[0][0]
    last = accumulation_list[-1][0]
    x2 = acc
    y2 = last
    log.info(f'First item: {first}')
    log.info(f'Last item: {last}')

    duration = abs((last - first).days)
    log.info(f'Duration: {duration}')

    sample_duration = abs((y2 - y1).days)
    delta = x2 - x1
    per_day = delta / sample_duration
    log.info(f'{x1} {y1} {x2} {y1}')
    log.info(f'{sample_duration} days {y1} with delta {delta} is {per_day} FUND per day')


    # plot_instantaneous_rewards(mergedlist)
    # plot_accumulated_rewards(accumulation_list)


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
    main()
