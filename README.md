> [!CAUTION]
> https://gitlab.com/robalexdev/mta-sts-cache-warming


# MTA-STS cache warming list

A list of domains known to support MTA-STS.

Mail senders that support MTA-STS can use this list to warm their MTA-STS policy cache.

A pre-warmed MTA-STS cache **protects the first email to a domain**, which is not generally protected by MTA-STS (as the cache would otherwise be empty and an attacker-in-the-middle may be able to block MTA-STS lookup attempts).


## Supported software

### Postfix

Use [postfix-mta-sts-resolver](https://github.com/Snawoot/postfix-mta-sts-resolver).
You can warm the cache by running the following command, either as a one-time import or periodically using cron:

    $ curl https://raw.githubusercontent.com/robalexdev/mta-sts-cache-warming/refs/heads/main/mta-sts-hints.txt \
      | /usr/sbin/postmap -q - socketmap:inet:127.0.0.1:8461:postfix

Or use [postfix-tlspol](https://github.com/Zuplu/postfix-tlspol).
Similarly, you can use this command for cache warming:

    $ curl https://raw.githubusercontent.com/robalexdev/mta-sts-cache-warming/refs/heads/main/mta-sts-hints.txt \
      | /usr/sbin/postmap -q - socketmap:inet:127.0.0.1:8642:query

These commands trigger the MTA-STS resolver to check each domain's current MTA-STS policy, caching the result when appropriate.


## Similar work

The web browsers maintain a HSTS preload list, which is distributed with the browser.

Important differences of MTA-STS from HSTS:

* HSTS has a preload directive; MTA-STS does not
* Servers with HSTS often use `max-age` of over a year; MTA-STS `max_age` is often shorter, such as a week
* The HSTS list is a trusted authority; this MTA-STS list is intended to provide hints only


## Inclusion criteria

A domain may be included if:

* It supports MTA-STS
* It uses the `enforce` mode
* The max-age setting is at least one week
  * The [MTA-STS RFC](https://www.rfc-editor.org/rfc/rfc8461#section-3.2) suggests this should be weeks or greater


## Adding a domain

Anyone may add a domain (not just the domain owner).

Please fork this repo and add your domain to the `mta-sts-hints.txt` file.
The file must be sorted, so find the correct location for your domain name.
Create a PR and ensure the automated tests pass.
The repo owner will manually review and merge the request.


## Removing a domain

Anyone may remove a domain (not just the domain owner).

The process mirrors adding a domain (see above).

The domain must no longer show support for MTA-STS over several repeated checks.


## Is this list an authority on MTA-STS policy status?

Unfortunately, with MTA-STS's relatively short caching periods and sporadic updates to this repo, this list will not be fully in-sync with the current MTA-STS status for every domain.
Senders are advised to cache the result of a live MTA-STS check for each domain, using their own systems.


## Contributing

Thanks for the interest in the project!
See [Issues](https://github.com/robalexdev/mta-sts-cache-warming/issues) for suggested tasks.
If you have an idea, open an issue and we'll coordinate on the best way to get your work incorporated.


## Repo design

Uses [postfix-mta-sts-resolver](https://github.com/Snawoot/postfix-mta-sts-resolver) to check if a domain has an MTA-STS policy.
This ensures the MTA-STS checks remain consistent with Postfix's extension.

Based on the process and code of [the public suffix list](https://github.com/publicsuffix/list). 💙

