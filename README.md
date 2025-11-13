# **Google Indexing Automation Script**

## **Overview**

This Python script automates the process of submitting URLs to the **Google Indexing API**. It ensures high-volume submission capability by leveraging multiple Google service accounts and automatically checking the HTTP status of each URL to determine the correct API action (URL\_UPDATED or URL\_DELETED).

This tool is designed for web administrators and SEO professionals who need to manage bulk indexing requests efficiently.

---

## **Features**

* **Plain Text URL List:** Reads a simple list of URLs from a plain text file (urls.txt).  
* **Automatic Status Check:** Performs an HTTP status check (HEAD request) on each URL to determine the appropriate Indexing API action.  
* **Multiple Service Accounts:** Supports using multiple Google service accounts to ensure high-volume submission capabilities without hitting API limits.  
* **Submission Quotas:** Enforces a limit (**200 URLs**) per service account before automatically switching to the next account.  
* **Output and Logging:** Generates comprehensive log files and separate CSV output files for each domain to track submission results, HTTP status codes, and actions taken.

---

## **Dependencies**

The script relies on the following Python packages, listed in the requirements.txt file:

google-api-python-client  
google-auth-oauthlib  
requests

---

## **Prerequisites**

To use this script, ensure you have the following:

1. **Python 3.6 or Higher** installed.  
2. **Multiple Google service account JSON key files** (e.g., indexing.json, indexing2.json, etc.).  
3. The **Google Indexing API** must be enabled in your Google Cloud Project.  
4. The domains you wish to index must be verified in Google Search Console for **each** service account's client email.

---

## **Setup and Operation**

### **Step 1: Clone the Repository**

Clone the repository to your local machine:

```Bash  
git clone https://github.com/yourusername/google-indexing-script.git  
cd google-indexing-script
```
### **Step 2: Install Dependencies**

Use the provided requirements.txt file to install all necessary Python libraries:

```Bash  
pip install -r requirements.txt
```
### **Step 3: Configure Service Accounts**

1. Place all your service account JSON key files (e.g., indexing.json, indexing2.json, etc.) into the main script directory.  
2. Verify the list of JSON file names in the JSON_KEY_FILES variable within the main.py script matches your files.

```Bash  
JSON_KEY_FILES = [
    "indexing.json",
    "indexing2.json",
    "indexing3.json",
    "indexing4.json",
    "indexing5.json"
]
```

### **Step 4: Prepare the Input File**

Create a plain text file named **urls.txt** in the script directory. It must contain one complete URL per line.

***urls.txt*** format example  
```
https://strongrootspreschool.com/  
https://strongrootspreschool.com/blog  
https://strongrootspreschool.com/deleted-page
```
### **Step 5: Run the Script**

Execute the script from your terminal:

```Bash  
python main.py
```
The script will begin checking URLs and submitting requests, automatically switching service accounts after every **200 URLs**.

### **Output Files**

Upon completion, the script generates:

* A comprehensive log file named like indexing\_YYYYMMDD\_HHMMSS.log.  
* Domain-specific CSV report files (e.g., strongrootspreschool.com\_2025-10-22\_1.csv) detailing the status code and action taken for each URL.

---

## **Status Code Logic**

The script checks the HTTP status code for each URL before attempting an Indexing API submission. The corresponding action is determined as follows:

| HTTP Status Code | Indexing API Action | CSV Status Logged | Script Action |
| :---- | :---- | :---- | :---- |
| **200–299 (OK)** | URL_UPDATED | URL_UPDATED | Submits a request to update the URL. |
| **400–499 (Client Errors)** | URL_DELETED | URL_DELETED | Submits a request to remove the URL from the index. |
| **0 (Network Error)** | N/A | UNREACHABLE | Skips submission (URL is unreachable). |
| **Other (e.g., 3xx, 5xx)** | N/A | URL_SKIPPED | Skips submission (status code suggests non-indexing issue or is a temporary redirect). |

---

## **License**

This project is licensed under the MIT License.

---

## **Related Links**

For more information on SEO and URL indexing, visit our websites:

[**Volar Agency**](https://thevolar.com)
