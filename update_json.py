import json
import re
import requests
from datetime import datetime

# Fetch the latest release information from GitHub
def fetch_latest_release(repo_url, keyword):
    api_url = f"https://api.github.com/repos/{repo_url}/releases"
    headers = {"Accept": "application/vnd.github+json"}
    response = requests.get(api_url, headers=headers)
    response.raise_for_status()
    releases = response.json()
    for release in releases:
        if keyword in release["name"]:
            return release
    raise ValueError(f"No release found containing the keyword '{keyword}'.")

# Remove HTML and markdown tags from text
def remove_tags(text):
    text = re.sub('<[^<]+?>', '', text)  # Remove HTML tags
    text = re.sub(r'#{1,6}\s?', '', text)  # Remove markdown header tags
    return text

# Extract Catbox download URL from release body
def extract_catbox_url(description):
    catbox_url_prefix = "https://files.catbox.moe/"
    match = re.search(r'### Catbox\s*`([^`]+)`', description)
    if match:
        return catbox_url_prefix + match.group(1)
    return None

# Get the size of the file from the download URL
def get_file_size(url):
    response = requests.head(url)
    response.raise_for_status()
    return int(response.headers.get('Content-Length', 0))

# Update the JSON file with the fetched data
def update_json_file(json_file, latest_release):
    with open(json_file, "r") as file:
        data = json.load(file)

    app = data["apps"][0]

    # Ensure 'versions' key exists in app
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

    # Extract Catbox download URL
    download_url = extract_catbox_url(latest_release["body"])
    size = get_file_size(download_url) if download_url else None

    version_entry = {
        "version": version,
        "date": version_date,
        "localizedDescription": description,
        "downloadURL": download_url,
        "size": size
    }

    # Check if the version entry already exists based on version
    duplicate_entries = [item for item in app["versions"] if item["version"] == version]

    # If duplicate is found, remove it
    if duplicate_entries:
        app["versions"].remove(duplicate_entries[0])

    # Add the version entry (either it's new or it's an update to an existing one)
    app["versions"].insert(0, version_entry)

    # Now handle the latest release data
    app["version"] = version
    app["versionDate"] = version_date
    app["versionDescription"] = description
    app["downloadURL"] = download_url
    app["size"] = size

    # Ensure 'news' key exists in data
    if "news" not in data:
        data["news"] = []

    # Add news entry if there's a new release
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

    # Check if the news entry already exists
    news_entry_exists = any(item["identifier"] == news_identifier for item in data["news"])

    # Add the news entry if it doesn't exist
    if not news_entry_exists:
        data["news"].append(news_entry)

    with open(json_file, "w") as file:
        json.dump(data, file, indent=2)

# Main function


def main():
    repo_url = "Balackburn/YTLitePlus"
    json_file = "apps.json"
    keyword = "YTLitePlus"

    fetched_data_latest = fetch_latest_release(repo_url, keyword)
    update_json_file(json_file, fetched_data_latest)


if __name__ == "__main__":
    main()
