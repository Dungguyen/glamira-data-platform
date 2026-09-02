from ipaddress import ip_address
from pathlib import Path


INPUT_PATH = Path.home() / "glamira-ip-geo" / "unique_ips.txt"


def main() -> None:
    total = 0
    valid = 0
    invalid = 0
    ipv4 = 0
    ipv6 = 0
    private = 0
    loopback = 0

    examples_invalid = []

    with INPUT_PATH.open("r", encoding="utf-8") as file:
        for line in file:
            value = line.strip()
            total += 1

            try:
                parsed = ip_address(value)
                valid += 1

                if parsed.version == 4:
                    ipv4 += 1
                else:
                    ipv6 += 1

                if parsed.is_private:
                    private += 1

                if parsed.is_loopback:
                    loopback += 1

            except ValueError:
                invalid += 1

                if len(examples_invalid) < 10:
                    examples_invalid.append(value)

    print("========== IP VALIDATION ==========")
    print(f"total: {total:,}")
    print(f"valid: {valid:,}")
    print(f"invalid: {invalid:,}")
    print(f"ipv4: {ipv4:,}")
    print(f"ipv6: {ipv6:,}")
    print(f"private: {private:,}")
    print(f"loopback: {loopback:,}")

    if examples_invalid:
        print("\ninvalid_examples:")
        for value in examples_invalid:
            print(value)


if __name__ == "__main__":
    main()
