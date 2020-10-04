import json
import logging
import os
import time
from datetime import datetime
from pathlib import Path

import click

import requests

log = logging.getLogger(__name__)

BASE_URL = 'https://rest2.unification.io'

REGISTRATION_COST = 10000
TIMESTAMP_COST = 1

MAX_PAGES = 3478


# https://rest2.unification.io/txs?message.action=record_wrkchain_hash&page=5
# https://rest.unification.io/staking/validators?limit=100

def root_path() -> Path:
    current_script = Path(os.path.abspath(__file__))
    data_dir = current_script.parent.parent.parent / 'data'
    return data_dir


def write_page(the_type, d, n):
    target = root_path() / the_type / f'page{n}.json'
    target.write_text(json.dumps(d, indent=2, separators=(',', ': ')))


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
        if timestamps is None:
            log.warning(f"Registered Beacon with not timestamps")
            continue
        for stamp in timestamps:
            beacon_submissions.append(
                (datetime.utcfromtimestamp(int(stamp['submit_time'])),
                 stamp['hash'], TIMESTAMP_COST))

    wrkchain_submissions = []
    for n, br in enumerate(wrkchain_registrations):
        timestamps = d['app_state']['wrkchain']['registered_wrkchains'][n][
            'blocks']
        if timestamps is None:
            log.warning(f"Registered WRKChain with not timestamps")
            continue
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
    plt.title('Instantaneous rewards')

    log.info('Saving image')
    fig1 = plt.gcf()
    fig1.set_size_inches(18.5, 10.5)
    fig1.savefig('instantaneous.png', dpi=200)
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
    fig1 = plt.gcf()
    fig1.set_size_inches(18.5, 10.5)
    fig1.savefig('accumulated.png', dpi=200)
    plt.show()


def calc(daily):
    validator_power = 1.88 / 100
    std_commission = 10 / 100
    validator_earns = daily * validator_power
    commission_charged = validator_earns * std_commission
    delegators_earns = validator_earns - commission_charged

    total_stake = 56473787  # TODO: Fetch me
    principal = 1000
    thousand_fund = principal / (total_stake * validator_power)

    daily_earning = delegators_earns * thousand_fund
    daily_interest_rate = daily_earning / principal
    monthly = daily_earning * 30
    annual_earnings = daily_earning * 365

    monthly_compound = principal * ((1 + daily_interest_rate) ** 30)
    annual_earnings_comp = principal * ((1 + daily_interest_rate) ** 365)

    rate = (annual_earnings / principal) * 100
    compounding_rate = ((annual_earnings_comp - principal) / principal) * 100

    print(f"A validator that has {validator_power * 100:.2f}% power will "
          f"earn {validator_earns:.2f} FUND of the daily distribution of "
          f"{daily:.2f} FUND.")
    print(f"If the validator charges {std_commission * 100:.2f}% commission, "
          f"the validator will take {commission_charged:.2f} FUND as "
          f"commission.")
    print(f"The remaining {delegators_earns:.2f} FUND is distributed to "
          f"delegators.")
    print(f"Staking {principal} FUND of the total "
          f"{total_stake * validator_power:.2f} FUND that the validator "
          f"stakes, means")
    print(f"The daily earnings is {daily_earning:.2f} FUND representing a "
          f"daily interest rate of {daily_interest_rate * 100:.4f}%")
    print(f"The monthly earning is {monthly:.2f} FUND")
    print(f"Monthly amount compounded daily is {monthly_compound:.2f} FUND")
    print(f"The annual earnings is {annual_earnings:.2f} FUND and the earnings "
          f"compounded is {annual_earnings_comp:.2f} FUND")
    print(f"APY rate is {rate:.2f} % or the compound rate "
          f"{compounding_rate:.2f} %")


@main.command()
def report():
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
    log.info(f'{sample_duration} days {y1} with delta {delta} is {per_day} '
             f'FUND per day')

    calc(per_day)

    plot_instantaneous_rewards(mergedlist)
    plot_accumulated_rewards(accumulation_list)


if __name__ == "__main__":
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))
    main()