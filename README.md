# Google Indexing Automation Script

## Overview

This Python script automates the process of submitting URLs to Google for indexing, leveraging multiple Google service accounts to handle authentication. By reading URLs and their statuses from a CSV file, the script efficiently manages the indexing or deletion of URLs from Google's index. This tool is particularly useful for SEO professionals and web administrators who need to manage large volumes of URL updates across different domains.

## Features

- **CSV Input Handling**: Reads URLs and their statuses from a CSV file, allowing batch processing of URLs.
- **Multiple Service Accounts**: Utilizes multiple Google service accounts for authentication, ensuring that API usage limits are not exceeded.
- **Submission Limits**: Enforces a limit on the number of URL submissions per service account to comply with API quotas.
- **Logging**: Captures and logs responses and errors to help with debugging and monitoring.
- **Output Files**: Generates separate CSV files for each domain to track submission results and status updates.

## Prerequisites

To use this script, ensure you have the following:

- **Python 3.6 or Higher**: The script requires Python version 3.6 or later.
- **Google API Client Library for Python**: Install via pip to interact with Google APIs.
- **OAuth2Client Library**: Required for managing authentication with Google services.
- **CSV File**: Prepare a CSV file containing the URLs and their corresponding statuses. The CSV should be formatted as follows:

  ```csv
  URL,Status
  https://example.com/page1,URL_UPDATED
  https://example.com/page2,URL_DELETED

## Setup Instructions

### 1. Clone the Repository

Clone the repository to your local machine:

    git clone https://github.com/yourusername/google-indexing-script.git
    cd google-indexing-script

## 2. Install Dependencies
Install the required Python libraries using pip:

    
    pip install oauth2client google-api-python-client

## 3. Create Service Account JSON Key Files
Obtain multiple service account JSON key files from the Google Cloud Console. Place these files in the same directory as your script. Update the JSON_KEY_FILES list in the script to include the filenames of your JSON key files.

## 4. Prepare the Input CSV File
Create a CSV file named urls.csv with the structure as shown in the prerequisites section. Ensure this file is in the same directory as the script.

## License
This project is licensed under the MIT License. For more details, visit the GitHub repository.

## Related Links
For more information on SEO and URL indexing, visit our websites:

<a href="https://thevolar.com/" rel="follow" target="_blank">Volar Agency</a><br>
<a href="https://foxseo.com/">Fox SEO</a>


Feel free to explore these resources for additional insights and services related to search engine optimization and web management.


