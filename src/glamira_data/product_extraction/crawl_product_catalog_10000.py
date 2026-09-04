#!/usr/bin/env python3
"""
Glamira Product Catalog Crawler
================================
Crawl du lieu san pham tu nhieu storefront (host) khac nhau, dung curl_cffi
de gia lap (impersonate) TLS/HTTP fingerprint cua nhieu trinh duyet khac nhau
nham giam kha nang bi chan boi WAF / anti-bot.

Cau truc thu muc mong doi (co the doi trong class Config):
    ~/glamira-product-extraction/
        output/
            distinct_product_ids.txt        # moi dong 1 product_id
            production_storefront_hosts.txt # moi dong 1 domain, vd: www.glamira.com
            product_catalog_10000_results.csv
            product_catalog_10000_summary.txt

Cach chay:
    pip install curl_cffi beautifulsoup4 --break-system-packages
    python3 glamira_crawler.py
"""

import csv
import json
import random
import re
import threading
import time
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup
from curl_cffi import requests as cf_requests
from curl_cffi.requests.exceptions import RequestException


# --------------------------------------------------------------------------
# Cau hinh
# --------------------------------------------------------------------------

class Config:
    BASE_DIR = Path("/home/DELL/glamira-product-extraction")
    OUTPUT_DIR = BASE_DIR / "output"

    PRODUCT_IDS_FILE = OUTPUT_DIR / "distinct_product_ids.txt"
    HOSTS_FILE = OUTPUT_DIR / "production_storefront_hosts.txt"
    RESULTS_FILE = OUTPUT_DIR / "product_catalog_10000_results.csv"
    SUMMARY_FILE = OUTPUT_DIR / "product_catalog_10000_summary.txt"

    URL_TEMPLATE = "https://{domain}/catalog/product/view/id/{pid}"

    MAX_WORKERS = 20          # so luong dong thoi
    REQUEST_TIMEOUT = 15      # giay
    MAX_RETRIES = 2           # so lan thu lai neu that bai
    RETRY_BACKOFF_BASE = 1.5  # giay, nhan doi moi lan retry
    MIN_DELAY = 0.1           # delay ngau nhien giua cac request (giay)
    MAX_DELAY = 0.4

    # Danh sach trinh duyet de curl_cffi impersonate, se duoc chon ngau nhien
    IMPERSONATE_BROWSERS = [
        "chrome136",
        "chrome133a",
        "chrome131",
        "chrome124",
        "chrome123",
        "chrome120",
        "firefox144",
        "firefox135",
        "firefox133",
        "safari184",
        "safari180",
        "edge101",
    ]

    BASE_HEADERS = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "none",
    }


CSV_FIELDS = [
    "product_id",
    "domain",
    "impersonate",
    "url",
    "http_status",
    "success",
    "name",
    "sku",
    "price",
    "currency",
    "image",
    "category",
    "description",
    "error",
]


# --------------------------------------------------------------------------
# Ho tro: doc file, ghi ket qua thread-safe
# --------------------------------------------------------------------------

def load_lines(path: Path) -> list[str]:
    if not path.exists():
        raise FileNotFoundError(f"Khong tim thay file: {path}")
    with path.open("r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]


def load_done_ids(results_file: Path) -> set[str]:
    """Cho phep resume: doc lai cac product_id da crawl thanh cong tu lan truoc."""
    done = set()
    if results_file.exists():
        with results_file.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get("success") == "True":
                    done.add(row["product_id"])
    return done


class ResultWriter:
    """Ghi CSV theo streaming, an toan giua nhieu thread."""

    def __init__(self, path: Path, fieldnames: list[str], resume: bool):
        self.path = path
        self.fieldnames = fieldnames
        self.lock = threading.Lock()
        write_header = not (resume and path.exists())
        self._fh = path.open("a" if resume else "w", encoding="utf-8", newline="")
        self._writer = csv.DictWriter(self._fh, fieldnames=fieldnames)
        if write_header:
            self._writer.writeheader()
            self._fh.flush()

    def write(self, row: dict):
        with self.lock:
            self._writer.writerow(row)
            self._fh.flush()

    def close(self):
        self._fh.close()


# --------------------------------------------------------------------------
# Trich xuat du lieu tu HTML
# --------------------------------------------------------------------------

def extract_product_data(html: str) -> dict:
    """
    Uu tien doc JSON-LD (schema.org/Product) vi hau het site Magento (nhu
    Glamira) deu nhung san du lieu nay vao <script type="application/ld+json">.
    Fallback sang meta tag / title neu khong co JSON-LD.
    """
    soup = BeautifulSoup(html, "html.parser")
    data = {
        "name": None,
        "sku": None,
        "price": None,
        "currency": None,
        "image": None,
        "category": None,
        "description": None,
    }

    for script in soup.find_all("script", {"type": "application/ld+json"}):
        try:
            payload = json.loads(script.string or "{}")
        except (json.JSONDecodeError, TypeError):
            continue

        candidates = payload if isinstance(payload, list) else [payload]
        for item in candidates:
            if not isinstance(item, dict):
                continue
            item_type = item.get("@type", "")
            if isinstance(item_type, list):
                is_product = "Product" in item_type
            else:
                is_product = item_type == "Product"
            if not is_product:
                continue

            data["name"] = item.get("name")
            data["sku"] = item.get("sku")
            data["description"] = item.get("description")

            image = item.get("image")
            if isinstance(image, list) and image:
                data["image"] = image[0]
            elif isinstance(image, str):
                data["image"] = image

            offers = item.get("offers")
            if isinstance(offers, list) and offers:
                offers = offers[0]
            if isinstance(offers, dict):
                data["price"] = offers.get("price")
                data["currency"] = offers.get("priceCurrency")

            category = item.get("category")
            if category:
                data["category"] = category

    # Fallback neu JSON-LD khong co hoac thieu
    if not data["name"]:
        og_title = soup.find("meta", property="og:title")
        title_tag = soup.find("title")
        data["name"] = (og_title["content"] if og_title else None) or (
            title_tag.text.strip() if title_tag else None
        )

    if not data["image"]:
        og_image = soup.find("meta", property="og:image")
        if og_image:
            data["image"] = og_image.get("content")

    if not data["description"]:
        meta_desc = soup.find("meta", attrs={"name": "description"})
        if meta_desc:
            data["description"] = meta_desc.get("content")

    return data


# --------------------------------------------------------------------------
# Logic crawl 1 san pham, voi retry + rotate host/browser
# --------------------------------------------------------------------------

@dataclass
class CrawlStats:
    lock: threading.Lock = field(default_factory=threading.Lock)
    total: int = 0
    success: int = 0
    failed: int = 0
    by_host: Counter = field(default_factory=Counter)
    by_status: Counter = field(default_factory=Counter)

    def record(self, host: str, success: bool, status):
        with self.lock:
            self.total += 1
            if success:
                self.success += 1
            else:
                self.failed += 1
            self.by_host[host] += 1
            self.by_status[str(status)] += 1


def fetch_product(pid: str, hosts: list[str], stats: CrawlStats) -> dict:
    """
    Thu crawl 1 product_id. Moi lan thu (bao gom retry) se chon ngau nhien
    mot host khac va mot browser impersonate khac, de vua phan tan tai vua
    tang co hoi thanh cong neu 1 host/fingerprint bi chan tam thoi.
    """
    last_error = None
    last_status = None
    last_domain = None
    last_browser = None

    for attempt in range(Config.MAX_RETRIES + 1):
        domain = random.choice(hosts)
        browser = random.choice(Config.IMPERSONATE_BROWSERS)
        url = Config.URL_TEMPLATE.format(domain=domain, pid=pid)
        last_domain, last_browser = domain, browser

        try:
            time.sleep(random.uniform(Config.MIN_DELAY, Config.MAX_DELAY))
            resp = cf_requests.get(
                url,
                impersonate=browser,
                headers=Config.BASE_HEADERS,
                timeout=Config.REQUEST_TIMEOUT,
            )
            last_status = resp.status_code

            if resp.status_code == 200:
                extracted = extract_product_data(resp.text)
                stats.record(domain, True, resp.status_code)
                return {
                    "product_id": pid,
                    "domain": domain,
                    "impersonate": browser,
                    "url": url,
                    "http_status": resp.status_code,
                    "success": True,
                    "error": "",
                    **extracted,
                }

            # 404 = san pham khong ton tai tren host nay, khong dang retry voi cung id
            if resp.status_code == 404:
                last_error = "not_found"
                break

            last_error = f"http_{resp.status_code}"

        except RequestException as exc:
            last_error = f"request_error: {exc}"
        except Exception as exc:  # noqa: BLE001 - muon log moi loi khong luong truoc
            last_error = f"unexpected_error: {exc}"

        if attempt < Config.MAX_RETRIES:
            time.sleep(Config.RETRY_BACKOFF_BASE * (attempt + 1))

    stats.record(last_domain, False, last_status)
    return {
        "product_id": pid,
        "domain": last_domain,
        "impersonate": last_browser,
        "url": Config.URL_TEMPLATE.format(domain=last_domain, pid=pid),
        "http_status": last_status,
        "success": False,
        "error": last_error,
        "name": None,
        "sku": None,
        "price": None,
        "currency": None,
        "image": None,
        "category": None,
        "description": None,
    }


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------

def main():
    print("Dang doc danh sach product_id va host...")
    product_ids = load_lines(Config.PRODUCT_IDS_FILE)
    hosts = load_lines(Config.HOSTS_FILE)
    print(f"  -> {len(product_ids)} product_id, {len(hosts)} host")

    done_ids = load_done_ids(Config.RESULTS_FILE)
    todo_ids = [pid for pid in product_ids if pid not in done_ids]
    if done_ids:
        print(f"  -> Resume: bo qua {len(done_ids)} id da crawl thanh cong truoc do")
    print(f"  -> Se crawl {len(todo_ids)} product_id")

    writer = ResultWriter(Config.RESULTS_FILE, CSV_FIELDS, resume=bool(done_ids))
    stats = CrawlStats()

    start_time = time.time()
    try:
        with ThreadPoolExecutor(max_workers=Config.MAX_WORKERS) as executor:
            futures = {
                executor.submit(fetch_product, pid, hosts, stats): pid
                for pid in todo_ids
            }
            for i, future in enumerate(as_completed(futures), 1):
                row = future.result()
                writer.write(row)
                if i % 100 == 0 or i == len(todo_ids):
                    elapsed = time.time() - start_time
                    rate = i / elapsed if elapsed > 0 else 0
                    print(
                        f"[{i}/{len(todo_ids)}] "
                        f"OK={stats.success} FAIL={stats.failed} "
                        f"({rate:.1f} req/s)"
                    )
    finally:
        writer.close()

    write_summary(stats, len(todo_ids), time.time() - start_time)
    print(f"\nHoan tat. Ket qua: {Config.RESULTS_FILE}")
    print(f"Tong ket: {Config.SUMMARY_FILE}")


def write_summary(stats: CrawlStats, total_attempted: int, elapsed: float):
    lines = [
        "GLAMIRA PRODUCT CATALOG CRAWL - SUMMARY",
        "=" * 50,
        f"Tong so product_id da xu ly trong lan chay nay: {total_attempted}",
        f"Thanh cong: {stats.success}",
        f"That bai: {stats.failed}",
        f"Thoi gian chay: {elapsed:.1f}s",
        "",
        "Ket qua theo host (top 20):",
    ]
    for host, count in stats.by_host.most_common(20):
        lines.append(f"  {host}: {count}")

    lines.append("")
    lines.append("Ket qua theo HTTP status:")
    for status, count in stats.by_status.most_common():
        lines.append(f"  {status}: {count}")

    Config.SUMMARY_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
