import logging
import os

import click
import requests

import time

log = logging.getLogger(__name__)


@click.group()
def main():
    logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))


@main.command()
def query():
    headers = {
        'Content-Type': 'application/json',
        'clientName': 'stakingrewards'
    }

    t_start = time.time()

    url = f'https://rest2.unification.io/txs?message.action=record_wrkchain_hash'

    r = requests.get(url, headers=headers)
    resp = r.json()
    pages = int(resp['page_total'])

    log.info(f'Total pages {pages}')

    for i in range(pages):
        q_start = time.time()
        url = f'https://rest2.unification.io/txs?message.action=record_wrkchain_hash&page={i}'
        r = requests.get(url, headers=headers)
        resp = r.json()
        num_txs = len(resp.get('txs', []))
        q_stop = time.time()
        query_diff = q_stop - q_start
        log.info(
            f'Query Completed for page {i} in {query_diff:.2f} seconds and found {num_txs} transactions')

    t_stop = time.time()

    total_diff = t_stop - t_start

    log.info(f'Completed in {total_diff:.2f} seconds')


if __name__ == "__main__":
    main()
