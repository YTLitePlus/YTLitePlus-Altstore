import json
import re
import requests

# Fetch all release information from GitHub
def fetch_all_releases(repo_url, keyword):
    api_url = f"https://api.github.com/repos/{repo_url}/releases"
    headers = {"Accept": "application/vnd.github+json"}
    response = requests.get(api_url, headers=headers)
    releases = response.json()
    sorted_releases = sorted(releases, key=lambda x: x["published_at"], reverse=True)

    return [release for release in sorted_releases if keyword in release["name"]]

# Update the JSON file with the fetched data
def remove_tags(text):
    text = re.sub('<[^<]+?>', '', text)  # Remove HTML tags
    text = re.sub(r'#{1,6}\s?', '', text)  # Remove markdown header tags
    return text

def update_json_file(json_file, fetched_data):
    with open(json_file, "r") as file:
        data = json.load(file)

    app = data["apps"][0]
    
    # Ensure 'versions' key exists in app
    if "versions" not in app:
        app["versions"] = []

    for release in fetched_data:
        full_version = release["tag_name"].lstrip('v')
        tag = release["tag_name"]
        version = re.search(r"(\d+\.\d+\.\d+)", full_version).group(1)
        versionDate = release["published_at"]

        description = release["body"]
        keyword = "YTLitePlus Release Information"
        if keyword in description:
            description = description.split(keyword, 1)[1].strip()

        description = remove_tags(description)
        description = re.sub(r'\*{2}', '', description)
        description = re.sub(r'-', '•', description)
        description = re.sub(r'`', '"', description)

        downloadURL = release["assets"][0]["browser_download_url"]
        size = release["assets"][0]["size"]

        version_entry = {
            "version": version,
            "date": versionDate,
            "localizedDescription": description,
            "downloadURL": downloadURL,
            "size": size
        }

        # Check if the version entry already exists
        version_entry_exists = any(item["version"] == version for item in app["versions"])

        # Add the version entry if it doesn't exist
        if not version_entry_exists:
            app["versions"].append(version_entry)

    with open(json_file, "w") as file:
        json.dump(data, file, indent=2)

# Main function
def main():
    repo_url = "Balackburn/YTLitePlus"
    json_file = "apps.json"
    keyword = "YTLitePlus"

    fetched_data = fetch_all_releases(repo_url, keyword)
    update_json_file(json_file, fetched_data)

if __name__ == "__main__":
    main()