import dns.asyncresolver
import dns.exception
import dns.rdatatype
import dns.resolver


async def check_mx(domain: str, timeout: float = 5.0) -> tuple[bool, list[str]]:
    """Check MX records for domain. Returns (has_mx, record_list)."""
    resolver = dns.asyncresolver.Resolver()
    resolver.lifetime = timeout

    try:
        answers = await resolver.resolve(domain, dns.rdatatype.MX)
        records = sorted(
            [(rdata.preference, str(rdata.exchange).rstrip(".")) for rdata in answers],
            key=lambda r: r[0],
        )
        mx_hosts = [host for _, host in records]
        return bool(mx_hosts), mx_hosts
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
        return False, []
    except dns.exception.DNSException:
        # Timeout or other DNS failure — can't confirm, but don't hard-fail
        return False, []
