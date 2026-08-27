from pathlib import Path

from bson import BSON, decode_file_iter

SOURCE = Path("data/raw/summary.bson")
OUTPUT = Path("data/samples/summary_50000.bson")

SAMPLE_SIZE = 50_000

def create_sample() -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)

    count = 0

    with SOURCE.open("rb") as source_file, OUTPUT.open("wb") as output_file:
        for document in decode_file_iter(source_file):
            output_file.write(BSON.encode(document))

            count += 1

            if count >= SAMPLE_SIZE:
                break

    print(f"Created sample: {OUTPUT}")
    print(f"Documents: {count:,}")
    print(f"Size: {OUTPUT.stat().st_size / (1024 ** 2):.2f} MiB")

if __name__ == "__main__":
    create_sample()