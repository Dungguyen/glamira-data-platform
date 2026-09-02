from __future__ import annotations

import csv
from ipaddress import ip_address
from pathlib import Path
from time import perf_counter

import geoip2.database
from geoip2.errors import AddressNotFoundError


BASE_DIR = Path.home() / "glamira-ip-geo"

INPUT_PATH = BASE_DIR / "unique_ips.txt"
DB_PATH = BASE_DIR / "db" / "GeoLite2-City.mmdb"

OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_CSV = OUTPUT_DIR / "ip_geolocation.csv"
SUMMARY_PATH = OUTPUT_DIR / "geoip_summary.txt"

PROGRESS_EVERY = 100_000


def safe_text(value: object | None) -> str:
    if value is None:
        return ""
    return str(value)


def pct(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return numerator / denominator * 100


def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    total = 0
    valid = 0
    invalid = 0
    non_global = 0

    eligible_public_ips = 0
    lookup_found = 0
    address_not_found = 0

    country_found = 0
    region_found = 0
    city_found = 0

    ipv4 = 0
    ipv6 = 0

    start = perf_counter()

    fieldnames = [
        "ip",
        "ip_version",
        "ip_country_code",
        "ip_country_name",
        "ip_region_code",
        "ip_region_name",
        "ip_city",
        "latitude",
        "longitude",
        "accuracy_radius_km",
        "geo_status",
    ]

    with geoip2.database.Reader(DB_PATH) as reader:
        with INPUT_PATH.open("r", encoding="utf-8") as input_file, \
             OUTPUT_CSV.open("w", encoding="utf-8", newline="", buffering=1024 * 1024) as output_file:

            writer = csv.DictWriter(
                output_file,
                fieldnames=fieldnames,
            )

            writer.writeheader()

            for line in input_file:
                value = line.strip()

                if not value:
                    continue

                total += 1

                row = {
                    "ip": value,
                    "ip_version": "",
                    "ip_country_code": "",
                    "ip_country_name": "",
                    "ip_region_code": "",
                    "ip_region_name": "",
                    "ip_city": "",
                    "latitude": "",
                    "longitude": "",
                    "accuracy_radius_km": "",
                    "geo_status": "",
                }

                try:
                    parsed_ip = ip_address(value)

                except ValueError:
                    invalid += 1
                    row["geo_status"] = "INVALID"
                    writer.writerow(row)
                    continue

                valid += 1

                row["ip_version"] = parsed_ip.version

                if parsed_ip.version == 4:
                    ipv4 += 1
                else:
                    ipv6 += 1

                if not parsed_ip.is_global:
                    non_global += 1
                    row["geo_status"] = "NON_GLOBAL"
                    writer.writerow(row)
                    continue

                eligible_public_ips += 1

                try:
                    response = reader.city(value)

                except AddressNotFoundError:
                    address_not_found += 1
                    row["geo_status"] = "ADDRESS_NOT_FOUND"
                    writer.writerow(row)
                    continue

                lookup_found += 1
                row["geo_status"] = "FOUND"

                country_code = response.country.iso_code
                country_name = response.country.name

                region = response.subdivisions.most_specific

                region_code = region.iso_code
                region_name = region.name

                city_name = response.city.name

                latitude = response.location.latitude
                longitude = response.location.longitude
                accuracy_radius = response.location.accuracy_radius

                if country_code:
                    country_found += 1

                if region_code or region_name:
                    region_found += 1

                if city_name:
                    city_found += 1

                row.update(
                    {
                        "ip_country_code": safe_text(country_code),
                        "ip_country_name": safe_text(country_name),
                        "ip_region_code": safe_text(region_code),
                        "ip_region_name": safe_text(region_name),
                        "ip_city": safe_text(city_name),
                        "latitude": safe_text(latitude),
                        "longitude": safe_text(longitude),
                        "accuracy_radius_km": safe_text(accuracy_radius),
                    }
                )

                writer.writerow(row)

                if total % PROGRESS_EVERY == 0:
                    elapsed = perf_counter() - start

                    print(
                        f"processed={total:,} "
                        f"eligible={eligible_public_ips:,} "
                        f"found={lookup_found:,} "
                        f"elapsed={elapsed / 60:.2f} min"
                    )

    elapsed = perf_counter() - start

    summary = f"""
========== GEOIP FULL ENRICHMENT ==========

total_unique_source_values: {total:,}

valid_ips: {valid:,}
invalid_ips: {invalid:,}

ipv4: {ipv4:,}
ipv6: {ipv6:,}

non_global: {non_global:,}
eligible_public_ips: {eligible_public_ips:,}

lookup_found: {lookup_found:,}
address_not_found: {address_not_found:,}

country_found: {country_found:,}
region_found: {region_found:,}
city_found: {city_found:,}

lookup_success_pct: {pct(lookup_found, eligible_public_ips):.2f}
country_coverage_pct: {pct(country_found, eligible_public_ips):.2f}
region_coverage_pct: {pct(region_found, eligible_public_ips):.2f}
city_coverage_pct: {pct(city_found, eligible_public_ips):.2f}

elapsed_seconds: {elapsed:.2f}
elapsed_minutes: {elapsed / 60:.2f}

lookups_per_second: {
    eligible_public_ips / elapsed if elapsed else 0
:,.0f}

output_csv: {OUTPUT_CSV}
""".strip()

    SUMMARY_PATH.write_text(
        summary + "\n",
        encoding="utf-8",
    )

    print()
    print(summary)


if __name__ == "__main__":
    main()
