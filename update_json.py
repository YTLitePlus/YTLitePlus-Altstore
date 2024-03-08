import json
import re
import requests

# Fetch all release information from GitHub


def fetch_all_releases(repo_url, keyword):
    api_url = f"https://api.github.com/repos/{repo_url}/releases"
    headers = {"Accept": "application/vnd.github+json"}
    response = requests.get(api_url, headers=headers)
    releases = response.json()
    sorted_releases = sorted(
        releases, key=lambda x: x["published_at"], reverse=False)

    return [release for release in sorted_releases if keyword in release["name"]]

# Fetch the latest release information from GitHub


def fetch_latest_release(repo_url, keyword):
    api_url = f"https://api.github.com/repos/{repo_url}/releases"
    headers = {"Accept": "application/vnd.github+json"}
    response = requests.get(api_url, headers=headers)
    releases = response.json()
    sorted_releases = sorted(
        releases, key=lambda x: x["published_at"], reverse=True)

    for release in sorted_releases:
        if keyword in release["name"]:
            return release

    raise ValueError(f"No release found containing the keyword '{keyword}'.")

# Update the JSON file with the fetched data


def remove_tags(text):
    text = re.sub('<[^<]+?>', '', text)  # Remove HTML tags
    text = re.sub(r'#{1,6}\s?', '', text)  # Remove markdown header tags
    return text


def update_json_file(json_file, fetched_data_all, fetched_data_latest):
    with open(json_file, "r") as file:
        data = json.load(file)

    app = data["apps"][0]

    # Ensure 'versions' key exists in app
    if "versions" not in app:
        app["versions"] = []

    for release in fetched_data_all:
        full_version = release["tag_name"].lstrip('v')
        tag = release["tag_name"]
        version = re.search(r"(\d+\.\d+\.\d+)", full_version).group(1)
        import datetime

        versionDate = release["published_at"]
        date_obj = datetime.datetime.strptime(versionDate, "%Y-%m-%dT%H:%M:%SZ")
        versionDate = date_obj.strftime("%Y-%m-%d")

        print(versionDate)

        description = release["body"]
        keyword = "YTLitePlus Release Information"
        if keyword in description:
            description = description.split(keyword, 1)[1].strip()

        description = remove_tags(description)
        description = re.sub(r'\*{2}', '', description)
        description = re.sub(r'-', '•', description)
        description = re.sub(r'`', '"', description)

        downloadURL = release["assets"][0]["browser_download_url"] if release["assets"] else None
        size = release["assets"][0]["size"] if release["assets"] else None

        version_entry = {
            "version": version,
            "date": versionDate,
            "localizedDescription": description,
            "downloadURL": downloadURL,
            "size": size
        }

        # Check if the version entry already exists based on version
        duplicate_entries = [item for item in app["versions"] if item["version"] == version]

        # If duplicate is found, remove it
        if duplicate_entries:
            app["versions"].remove(duplicate_entries[0])

        # Add the version entry (either it's new or it's an update to an existing one)
        app["versions"].insert(0, version_entry)

    # Now handle the latest release data (from the second script)
    full_version = fetched_data_latest["tag_name"].lstrip('v')
    tag = fetched_data_latest["tag_name"]
    version = re.search(r"(\d+\.\d+\.\d+)", full_version).group(1)
    app["version"] = version
    app["versionDate"] = fetched_data_latest["published_at"]

    description = fetched_data_latest["body"]
    keyword = "YTLitePlus Release Information"
    if keyword in description:
        description = description.split(keyword, 1)[1].strip()

    description = remove_tags(description)
    description = re.sub(r'\*{2}', '', description)
    description = re.sub(r'-', '•', description)
    description = re.sub(r'`', '"', description)

    app["versionDescription"] = description
    app["downloadURL"] = fetched_data_latest["assets"][0]["browser_download_url"] if fetched_data_latest["assets"] else None
    app["size"] = fetched_data_latest["assets"][0]["size"] if fetched_data_latest["assets"] else None

    # Ensure 'news' key exists in data
    if "news" not in data:
        data["news"] = []

    # Add news entry if there's a new release
    news_identifier = f"release-{full_version}"
    import datetime
    published_at = datetime.datetime.strptime(fetched_data_latest["published_at"], "%Y-%m-%dT%H:%M:%SZ") 
    date_string = published_at.strftime("%d/%m/%y")
    news_entry = {
        "appID": "com.google.ios.youtube",
        "caption": f"Update of YTLitePlus just got released!",
        "date": fetched_data_latest["published_at"],
        "identifier": news_identifier,
        "imageURL": "https://raw.githubusercontent.com/Balackburn/YTLitePlusAltstore/main/screenshots/news/new_release.png",
        "notify": True,
        "tintColor": "000000",
        "title": f"{full_version} - YTLitePlus  {date_string}",
        "url": f"https://github.com/Balackburn/YTLitePlus/releases/tag/{tag}"
    }

    # Check if the news entry already exists
    news_entry_exists = any(item["identifier"] ==
                            news_identifier for item in data["news"])

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

    fetched_data_all = fetch_all_releases(repo_url, keyword)
    fetched_data_latest = fetch_latest_release(repo_url, keyword)
    update_json_file(json_file, fetched_data_all, fetched_data_latest)


if __name__ == "__main__":
    main()
