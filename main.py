"""
Google Search Console URL Indexing via API
Fixed version with proper error handling and closure resolution
"""

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import logging
import csv
import datetime
from urllib.parse import urlparse
import requests
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry
import os
from functools import partial
from typing import Dict, Optional, Any
import time

# Configuration
INPUT_FILE = "urls.txt"
JSON_KEY_FILES = [
    "indexing.json",
    "indexing2.json",
    "indexing3.json",
    "indexing4.json",
    "indexing5.json"
]
SCOPES = ["https://www.googleapis.com/auth/indexing"]
URL_LIMIT_PER_ACCOUNT = 200
REQUEST_TIMEOUT = 30  # seconds

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(f"indexing_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class URLIndexer:
    """Handles Google Indexing API operations with proper error handling"""

    def __init__(self):
        self.date_str = datetime.datetime.now().strftime("%Y-%m-%d")
        self.file_handlers: Dict[str, Dict[str, Any]] = {}
        self.session = self._create_session()
        self.unique_domains = set()
        self._initialize_domains()

    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        retry = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        return session

    def _initialize_domains(self):
        """Extract unique domains from input file"""
        try:
            with open(INPUT_FILE, "r", encoding="utf-8") as file:
                for line in file:
                    url = line.strip()
                    if url:  # Skip empty lines
                        try:
                            domain = urlparse(url).netloc
                            if domain:
                                self.unique_domains.add(domain)
                        except Exception as e:
                            logger.error(f"Error parsing URL {url}: {e}")

            # Initialize file handlers for each domain
            for domain in self.unique_domains:
                self.file_handlers[domain] = {
                    "csv_file": None,
                    "csv_writer": None,
                    "file_index": 0
                }

            logger.info(f"Found {len(self.unique_domains)} unique domains")

        except FileNotFoundError:
            logger.error(f"Input file '{INPUT_FILE}' not found")
            raise
        except Exception as e:
            logger.error(f"Error initializing domains: {e}")
            raise

    def _adjust_notify_time(self, notify_time: str) -> str:
        """Adjust notification time to proper format"""
        if '.' in notify_time:
            parts = notify_time.split('.')
            if len(parts) > 1 and len(parts[1]) > 6:
                # Truncate microseconds to 6 digits
                notify_time = f"{parts[0]}.{parts[1][:6]}Z"
        return notify_time

    def _insert_event(
            self,
            request_id: str,
            response: Dict,
            exception: Optional[Exception],
            domain: str,
            url: str,
            status_code: int,
            service_account: str,
            action_type: str
    ):
        """
        Callback function to handle API response and write to CSV

        Args:
            request_id: Request identifier
            response: API response
            exception: Exception if request failed
            domain: Domain name
            url: URL being processed
            status_code: HTTP status code
            service_account: Service account name
            action_type: "URL_UPDATED" or "URL_DELETED"
        """
        if exception is not None:
            logger.error(f"API error for {url}: {exception}")
            csv_writer = self.file_handlers.get(domain, {}).get("csv_writer")
            if csv_writer:
                csv_writer.writerow([
                    url,
                    status_code,
                    "API_ERROR",
                    "N/A",
                    datetime.datetime.now().strftime("%Y-%m-%d"),
                    service_account
                ])
                self._flush_csv(domain)
            return

        logger.info(f"API success for {url}: {response}")

        csv_writer = self.file_handlers.get(domain, {}).get("csv_writer")
        if csv_writer is None:
            logger.warning(f"No CSV writer found for domain {domain}")
            return

        try:
            # Use the action_type passed in, not from response
            status = action_type
            notify_time_readable = "N/A"

            # Try to extract notification time if available
            url_metadata = response.get("urlNotificationMetadata", {})
            notify_time = ""

            # Check for both possible fields
            if "latestUpdate" in url_metadata:
                notify_time = url_metadata["latestUpdate"].get("notifyTime", "")
            elif "latestRemove" in url_metadata:
                notify_time = url_metadata["latestRemove"].get("notifyTime", "")

            if notify_time:
                try:
                    notify_time = self._adjust_notify_time(notify_time)
                    # Remove 'Z' and parse
                    dt = datetime.datetime.fromisoformat(notify_time.rstrip('Z'))
                    notify_time_readable = dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, AttributeError) as e:
                    logger.warning(f"Could not parse notify_time '{notify_time}': {e}")

            date_now = datetime.datetime.now().strftime("%Y-%m-%d")

            # Write to CSV
            csv_writer.writerow([
                url,
                status_code,
                status,
                notify_time_readable,
                date_now,
                service_account
            ])

            # Flush immediately to prevent data loss
            self._flush_csv(domain)

        except Exception as e:
            logger.error(f"Error processing response for {url}: {e}", exc_info=True)

    def _flush_csv(self, domain: str):
        """Flush CSV file to disk"""
        csv_file = self.file_handlers.get(domain, {}).get("csv_file")
        if csv_file and not csv_file.closed:
            try:
                csv_file.flush()
                os.fsync(csv_file.fileno())
            except Exception as e:
                logger.error(f"Error flushing CSV for domain {domain}: {e}")

    def _get_csv_writer(self, domain: str) -> Optional[csv.writer]:
        """Get or create CSV writer for domain"""
        handler = self.file_handlers.get(domain)
        if not handler:
            logger.error(f"No handler found for domain {domain}")
            return None

        # Check if we need to create a new file
        if handler["csv_writer"] is None or (
                handler["csv_file"] and handler["csv_file"].closed
        ):
            handler["file_index"] += 1
            csv_filename = f"{domain}_{self.date_str}_{handler['file_index']}.csv"

            # Ensure unique filename
            while os.path.exists(csv_filename):
                handler["file_index"] += 1
                csv_filename = f"{domain}_{self.date_str}_{handler['file_index']}.csv"

            try:
                csv_file = open(csv_filename, "a", newline="", encoding="utf-8")
                csv_writer = csv.writer(csv_file)

                # Write header
                csv_writer.writerow([
                    "URL",
                    "Status Code",
                    "Status",
                    "Notify Date",
                    "Date",
                    "Service Account"
                ])

                handler["csv_file"] = csv_file
                handler["csv_writer"] = csv_writer

                logger.info(f"Created CSV file: {csv_filename}")

            except (PermissionError, IOError) as e:
                logger.error(f"Error creating CSV file for domain {domain}: {e}")
                handler["csv_file"] = None
                handler["csv_writer"] = None
                return None

        return handler["csv_writer"]

    def _check_url_status(self, url: str) -> int:
        """Check URL status with proper error handling"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = self.session.get(
                url,
                headers=headers,
                allow_redirects=True,
                timeout=REQUEST_TIMEOUT
            )
            return response.status_code
        except requests.RequestException as e:
            logger.error(f"Error checking URL {url}: {e}")
            return 0  # Return 0 for network errors

    def _load_credentials(self, json_file: str) -> Optional[service_account.Credentials]:
        """Load service account credentials"""
        try:
            if not os.path.exists(json_file):
                logger.error(f"Credentials file not found: {json_file}")
                return None

            credentials = service_account.Credentials.from_service_account_file(
                json_file,
                scopes=SCOPES
            )
            logger.info(f"Loaded credentials from {json_file}")
            return credentials

        except Exception as e:
            logger.error(f"Error loading credentials from {json_file}: {e}")
            return None

    def submit_urls(self):
        """Main function to submit URLs to Google Indexing API"""
        url_processed = 0
        credentials_index = 0
        total_urls = 0
        successful_submissions = 0
        failed_submissions = 0

        # Load initial credentials
        credentials = self._load_credentials(JSON_KEY_FILES[credentials_index])
        if not credentials:
            logger.error("Failed to load initial credentials")
            return

        try:
            service = build('indexing', 'v3', credentials=credentials)
        except Exception as e:
            logger.error(f"Error building API service: {e}")
            return

        # Load URLs
        try:
            with open(INPUT_FILE, "r", encoding="utf-8") as file:
                urls = [line.strip() for line in file if line.strip()]
            total_urls = len(urls)
            logger.info(f"Processing {total_urls} URLs")
        except Exception as e:
            logger.error(f"Error reading input file: {e}")
            return

        # Process each URL
        for idx, url in enumerate(urls, 1):
            # Check if we need to switch accounts
            if url_processed >= URL_LIMIT_PER_ACCOUNT:
                credentials_index += 1
                if credentials_index >= len(JSON_KEY_FILES):
                    logger.warning("All service accounts exhausted")
                    break

                credentials = self._load_credentials(JSON_KEY_FILES[credentials_index])
                if not credentials:
                    logger.error("Failed to load next credentials, stopping")
                    break

                try:
                    service = build('indexing', 'v3', credentials=credentials)
                    url_processed = 0
                    logger.info(f"Switched to service account: {JSON_KEY_FILES[credentials_index]}")
                except Exception as e:
                    logger.error(f"Error building API service: {e}")
                    break

            # Extract domain and service account name
            try:
                domain = urlparse(url).netloc
                if not domain:
                    logger.warning(f"Invalid URL, skipping: {url}")
                    continue
            except Exception as e:
                logger.error(f"Error parsing URL {url}: {e}")
                continue

            service_account = JSON_KEY_FILES[credentials_index].replace(".json", "")

            # Get CSV writer
            csv_writer = self._get_csv_writer(domain)
            if csv_writer is None:
                logger.error(f"Could not get CSV writer for {domain}, skipping {url}")
                failed_submissions += 1
                continue

            # Check URL status
            logger.info(f"[{idx}/{total_urls}] Checking URL: {url}")
            status_code = self._check_url_status(url)

            if status_code == 0:
                logger.warning(f"Could not reach URL: {url}")
                csv_writer.writerow([
                    url,
                    0,
                    "UNREACHABLE",
                    "N/A",
                    datetime.datetime.now().strftime("%Y-%m-%d"),
                    service_account
                ])
                self._flush_csv(domain)
                failed_submissions += 1
                continue

            # Determine action based on status code
            try:
                if 200 <= status_code <= 299:
                    action_type = "URL_UPDATED"
                    logger.info(f"Status {status_code} - Submitting URL_UPDATED for: {url}")

                    # Use partial to capture current values
                    callback = partial(
                        self._insert_event,
                        domain=domain,
                        url=url,
                        status_code=status_code,
                        service_account=service_account,
                        action_type=action_type
                    )

                    batch = service.new_batch_http_request(callback=callback)
                    batch.add(service.urlNotifications().publish(
                        body={"url": url, "type": "URL_UPDATED"}
                    ))
                    batch.execute()
                    successful_submissions += 1

                elif 400 <= status_code <= 499:
                    action_type = "URL_DELETED"
                    logger.info(f"Status {status_code} - Submitting URL_DELETED for: {url}")

                    callback = partial(
                        self._insert_event,
                        domain=domain,
                        url=url,
                        status_code=status_code,
                        service_account=service_account,
                        action_type=action_type
                    )

                    batch = service.new_batch_http_request(callback=callback)
                    batch.add(service.urlNotifications().publish(
                        body={"url": url, "type": "URL_DELETED"}
                    ))
                    batch.execute()
                    successful_submissions += 1

                else:
                    logger.info(f"Skipping URL due to status {status_code}: {url}")
                    csv_writer.writerow([
                        url,
                        status_code,
                        "URL_SKIPPED",
                        "N/A",
                        datetime.datetime.now().strftime("%Y-%m-%d"),
                        service_account
                    ])
                    self._flush_csv(domain)
                    failed_submissions += 1

                url_processed += 1

                # Small delay to avoid rate limiting
                time.sleep(0.1)

            except HttpError as e:
                logger.error(f"Google API error for {url}: {e}")
                csv_writer.writerow([
                    url,
                    status_code,
                    "API_ERROR",
                    "N/A",
                    datetime.datetime.now().strftime("%Y-%m-%d"),
                    service_account
                ])
                self._flush_csv(domain)
                failed_submissions += 1

            except Exception as e:
                logger.error(f"Unexpected error processing {url}: {e}", exc_info=True)
                csv_writer.writerow([
                    url,
                    status_code,
                    "ERROR",
                    "N/A",
                    datetime.datetime.now().strftime("%Y-%m-%d"),
                    service_account
                ])
                self._flush_csv(domain)
                failed_submissions += 1

        # Print summary
        logger.info("=" * 60)
        logger.info("PROCESSING COMPLETE")
        logger.info(f"Total URLs: {total_urls}")
        logger.info(f"Successful submissions: {successful_submissions}")
        logger.info(f"Failed/Skipped: {failed_submissions}")
        logger.info("=" * 60)

    def cleanup(self):
        """Close all open CSV files"""
        logger.info("Cleaning up resources...")
        for domain, handler in self.file_handlers.items():
            if handler["csv_file"] and not handler["csv_file"].closed:
                try:
                    handler["csv_file"].close()
                    logger.info(f"Closed CSV file for domain: {domain}")
                except Exception as e:
                    logger.error(f"Error closing CSV for domain {domain}: {e}")


def main():
    """Main entry point"""
    indexer = None
    try:
        logger.info("Starting Google Indexing API submission")
        indexer = URLIndexer()
        indexer.submit_urls()
    except KeyboardInterrupt:
        logger.warning("Process interrupted by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
    finally:
        if indexer:
            indexer.cleanup()
        logger.info("Script finished")


if __name__ == "__main__":
    main()