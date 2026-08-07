from disposable_email_domains import blocklist

# Hand-maintained additions for disposable services that show up after the
# pinned disposable-email-domains package version was released. Add to this
# set directly when a new one is spotted -- no need to wait for an upstream
# package update.
EXTRA_BLOCKED_DOMAINS: set[str] = set()


def is_disposable_email_domain(email: str) -> bool:
    domain = email.rsplit("@", 1)[-1].strip().lower()
    return domain in blocklist or domain in EXTRA_BLOCKED_DOMAINS
