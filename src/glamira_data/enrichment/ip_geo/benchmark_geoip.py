from pathlib import Path
from time import perf_counter
from ipaddress import ip_address

import geoip2.database
from geoip2.errors import AddressNotFoundError


INPUT_PATH = Path.home() / "glamira-ip-geo" / "unique_ips.txt"
DB_PATH = Path.home() / "glamira-ip-geo" / "db" / "GeoLite2-City.mmdb"

SAMPLE_SIZE = 10_000


def main() -> None:
    processed = 0
    eligible = 0

    invalid = 0
    non_global = 0
    address_not_found = 0

    country_found = 0
    region_found = 0
    city_found = 0

    start = perf_counter()

    with geoip2.database.Reader(DB_PATH) as reader:
        with INPUT_PATH.open("r", encoding="utf-8") as file:
            for line in file:
                if processed >= SAMPLE_SIZE:
                    break

                value = line.strip()
                processed += 1

                try:
                    parsed_ip = ip_address(value)
                except ValueError:
                    invalid += 1
                    continue

                # Exclude addresses that are not globally routable.
                if not parsed_ip.is_global:
                    non_global += 1
                    continue

                eligible += 1

                try:
                    response = reader.city(value)
                except AddressNotFoundError:
                    address_not_found += 1
                    continue

                if response.country.iso_code:
                    country_found += 1

                if response.subdivisions.most_specific.iso_code:
                    region_found += 1

                if response.city.name:
                    city_found += 1

    elapsed = perf_counter() - start

    def coverage(found: int) -> float:
        if eligible == 0:
            return 0.0
        return found / eligible * 100

    print("========== GEOIP BENCHMARK ==========")
    print(f"sample_size: {processed:,}")
    print(f"eligible_public_ips: {eligible:,}")
    print(f"invalid: {invalid:,}")
    print(f"non_global: {non_global:,}")
    print(f"address_not_found: {address_not_found:,}")

    print()
    print(f"country_found: {country_found:,}")
    print(f"region_found: {region_found:,}")
    print(f"city_found: {city_found:,}")

    print()
    print(f"country_coverage_pct: {coverage(country_found):.2f}")
    print(f"region_coverage_pct: {coverage(region_found):.2f}")
    print(f"city_coverage_pct: {coverage(city_found):.2f}")

    print()
    print(f"elapsed_seconds: {elapsed:.2f}")

    if eligible:
        print(f"lookups_per_second: {eligible / elapsed:,.0f}")


if __name__ == "__main__":
    main()
