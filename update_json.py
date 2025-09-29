import json
import re
import requests
import os
import sys
from datetime import datetime

def get_file_metadata(url):
    try:
        response = requests.head(url, headers={"User-Agent": "Github-Actions"}, timeout=10)
        response.raise_for_status()
        return int(response.headers.get('Content-Length')), datetime.strptime(response.headers.get('Last-Modified'), "%a, %d %b %Y %H:%M:%S %Z")
    except requests.RequestException as e:
        print(f"Error requesting file size and creation date: {e}")
        raise
    except TypeError as e:
        print(f"Error while retrieving size and creation date from server response: {e}")
        raise

def update_json_file(json_file, download_url, ytliteplus_version, version):
    size, date_obj = get_file_metadata(download_url)

    try:
        with open(json_file, "r") as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        print(f"Error reading JSON file: {e}")
        raise

    app = data["apps"][0]
    if "versions" not in app:
        app["versions"] = []

    full_version = version.lstrip('v')
    tag = version
    version = re.search(r"(\d+\.\d+\.\d+)", full_version).group(1)
    version_date = date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

    description = f"Current YouTube IPA: {version}\r\nCurrent YTLite Version: {ytliteplus_version}"

    version_entry = {
        "version": version,
        "date": version_date,
        "localizedDescription": description,
        "downloadURL": download_url,
        "size": size
    }

    duplicate_entries = [item for item in app["versions"] if item["version"] == version]
    if duplicate_entries:
        app["versions"].remove(duplicate_entries[0])

    app["versions"].insert(0, version_entry)

    app.update({
        "version": version,
        "versionDate": version_date,
        "versionDescription": description,
        "downloadURL": download_url,
        "size": size
    })

    if "news" not in data:
        data["news"] = []

    news_identifier = f"release-{full_version}"
    date_string = date_obj.strftime("%d/%m/%y")
    news_entry = {
        "appID": "com.google.ios.youtube",
        "caption": f"Update of YTLitePlus just got released!",
        "date": version_date,
        "identifier": news_identifier,
        "imageURL": "https://raw.githubusercontent.com/YTLitePlus/YTLitePlus-Altstore/main/screenshots/news/new_release.png",
        "notify": True,
        "tintColor": "000000",
        "title": f"{full_version} - YTLitePlus  {date_string}",
        "url": f"https://github.com/Balackburn/YTLitePlus/releases/tag/{tag}"
    }

    news_entry_exists = any(item["identifier"] == news_identifier for item in data["news"])
    if not news_entry_exists:
        data["news"].append(news_entry)

    try:
        with open(json_file, "w") as file:
            json.dump(data, file, indent=2)
        print("JSON file updated successfully.")
    except IOError as e:
        print(f"Error writing to JSON file: {e}")
        raise

def main():
    if len(sys.argv) < 4:
        raise TypeError(f"Not enough arguments:\n{os.path.basename(__file__)} <download_url> <yt_version> <ytliteplus_version>")
    download_url = sys.argv[1]
    ytliteplus_version = sys.argv[2]
    yt_version = sys.argv[3]

    json_file = "apps.json"

    try:
        update_json_file(json_file, download_url, ytliteplus_version, yt_version)
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()