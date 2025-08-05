#!/usr/bin/env python

import asyncio
import click
import dns.name
import re
import sys
import time


from postfix_mta_sts_resolver.resolver import STSFetchResult as FR
from postfix_mta_sts_resolver.resolver import STSResolver as Resolver

ONE_WEEK_IN_SECONDS = 7*24*60*60


def read_domains(hint_filename: str) -> set[str]:
    """Read domains from a file into a set

    >>> sorted(read_domains('test_hint_01.dat'))
    ['example.com', 'example.net']

    >>> read_domains('test_out_of_order.dat')
    Traceback (most recent call last):
      ...
    Exception: Domain list must be sorted

    >>> read_domains('test_duplicates.dat')
    Traceback (most recent call last):
      ...
    Exception: Domain list must not have duplicates
    """
    domains = []

    with open(hint_filename) as f:
        for line in f:
            line = line.strip()
            if line != "":
                domains.append(line)

    # Make sure all entries are sorted and distinct
    sorted_domains = sorted(domains)
    if domains != sorted_domains:
        raise Exception("Domain list must be sorted")

    set_domains = set(domains)
    if len(domains) != len(set_domains):
        raise Exception("Domain list must not have duplicates")

    return set_domains


def check(domain: str) -> bool:
    """Check MTA-STS support

    >>> check("example.com")
      Domain: example.com
      No valid policy found
    False
    >>> check("EXAMPLE.com")
      Domain: EXAMPLE.com
      Please normalize EXAMPLE.com as example.com
    False
    >>> check("點看.com")
      Domain: 點看.com
      Please normalize 點看.com as xn--c1yn36f.com
    False
    >>> check("microsoft.com")
      Domain: microsoft.com
    True
    >>> check("yahoo.com")
      Domain: yahoo.com
      Policy not in enforce mode (testing)
    False
    """

    print(f"  Domain: {domain}")

    # Keep entries in canonical format
    normalized = str(dns.name.from_text(domain).canonicalize())
    # without the trailing dot
    normalized = normalized[0:len(normalized)-1]
    if normalized != domain:
        print(f"  Please normalize {domain} as {normalized}")
        return False

    # Retry for intermittent failures
    for _ in range(5):
        mtasts_found = asyncio.run(do_check(domain))
        if mtasts_found:
            return True
        print(f"  Retrying {domain}...")
        time.sleep(10)

    # persistent lookup failure
    return False


async def do_check(domain: str) -> bool:
    resolver = Resolver(loop=None)
    result, policy = await resolver.resolve(domain)
    if result != FR.VALID:
        print("  No valid policy found")
        return False
    max_age = policy[1]['max_age']
    mode = policy[1]['mode']
    if mode != 'enforce':
        print(f"  Policy not in enforce mode ({mode})")
        return False
    if max_age < ONE_WEEK_IN_SECONDS:
        print(f"  max_age must be at least {ONE_WEEK_IN_SECONDS} to be included")
        return False
    return True


def hint_diff(current_filename: str, pull_request_filename: str):
    """Compare two hint files

    >>> added, removed = hint_diff("test_hint_01.dat", "test_hint_02.dat")
    >>> sorted(added)
    ['example.co.uk', 'example.gov']
    >>> sorted(removed)
    ['example.net']
    """
    current_domains = read_domains(current_filename)
    pull_request_domains = read_domains(pull_request_filename)

    removed = current_domains.difference(pull_request_domains)
    added = pull_request_domains.difference(current_domains)

    return (added, removed)


def check_files(current_filename: str, pull_request_filename: str) -> int:
    """
    Run checks on the changes in the PR

    No changes:
    >>> check_files("test_hint_01.dat", "test_hint_01.dat")
    0

    Adding while removing:
    >>> check_files("test_hint_01.dat", "test_hint_02.dat")
      Please do not add and remove entries in the same PR
    1

    Adding a domain that supports MTA-STS
    >>> check_files("test_hint_01.dat", "test_hint_04.dat")
      Domain: microsoft.com
    0

    Remove a domain that no longer supports MTA-STS
    >>> check_files("test_hint_01.dat", "test_hint_03.dat")
      Domain: example.net
      No valid policy found
    0
    """
    added, removed = hint_diff(current_filename, pull_request_filename)

    if added and removed:
        print("  Please do not add and remove entries in the same PR")
        return 1

    # Entries must meet inclusion criteria
    add_results = [ check(domain) for domain in added ]
    if not all(add_results):
        return 1

    # Entries that meet inclusion criteria cannot be removed
    # (without overriding this check)
    remove_results = [ check(domain) for domain in removed ]
    if any(remove_results):
        return 1

    return 0


@click.command()
@click.argument("current_filename")
@click.argument("pull_request_filename")
def main(current_filename: str, pull_request_filename: str):
    """This script compares two hint files and checks for MTA-STS support

    It can be tested using doctests by running `python -m doctest check.py`
    """
    sys.exit(check_files(current_filename, pull_request_filename))


if __name__ == "__main__":
    main()

