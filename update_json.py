import json
import re
import requests
import os
from datetime import datetime

def fetch_latest_release(repo_url, keyword):
    api_url = f"https://api.github.com/repos/{repo_url}/releases"
    headers = {
        "Accept": "application/vnd.github+json",
    }
    try:
        response = requests.get(api_url, headers=headers)
        response.raise_for_status()
        releases = response.json()
        for release in releases:
            if keyword in release["name"]:
                return release
        raise ValueError(f"No release found containing the keyword '{keyword}'.")
    except requests.RequestException as e:
        print(f"Error fetching releases: {e}")
        raise

def remove_tags(text):
    text = re.sub('<[^<]+?>', '', text)
    text = re.sub(r'#{1,6}\s?', '', text)
    return text

def extract_catbox_url(description):
    catbox_url_prefix = "https://files.catbox.moe/"
    match = re.search(r'### Catbox\s*`([^`]+)`', description)
    if match:
        return catbox_url_prefix + match.group(1)
    return None

def get_file_size(url):
    try:
        response = requests.head(url)
        response.raise_for_status()
        return int(response.headers.get('Content-Length', 0))
    except requests.RequestException as e:
        print(f"Error getting file size: {e}")
        return 111020044

def update_json_file(json_file, latest_release):
    try:
        with open(json_file, "r") as file:
            data = json.load(file)
    except json.JSONDecodeError as e:
        print(f"Error reading JSON file: {e}")
        raise

    app = data["apps"][0]
    if "versions" not in app:
        app["versions"] = []

    full_version = latest_release["tag_name"].lstrip('v')
    tag = latest_release["tag_name"]
    version = re.search(r"(\d+\.\d+\.\d+)", full_version).group(1)
    version_date = latest_release["published_at"]
    date_obj = datetime.strptime(version_date, "%Y-%m-%dT%H:%M:%SZ")
    version_date = date_obj.strftime("%Y-%m-%d")

    description = latest_release["body"]
    keyword = "YTLitePlus Release Information"
    if keyword in description:
        description = description.split(keyword, 1)[1].strip()

    description = remove_tags(description)
    description = re.sub(r'\*{2}', '', description)
    description = re.sub(r'-', '•', description)
    description = re.sub(r'`', '"', description)

    download_url = extract_catbox_url(latest_release["body"])
    size = get_file_size(download_url) if download_url else None

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
        "date": latest_release["published_at"],
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
    repo_url = "YTLitePlus/YTLitePlus"
    json_file = "apps.json"
    keyword = "YTLitePlus"

    try:
        fetched_data_latest = fetch_latest_release(repo_url, keyword)
        update_json_file(json_file, fetched_data_latest)
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main()