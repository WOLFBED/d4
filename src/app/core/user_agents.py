"""
Post-processing tasks for downloaded videos.
"""
import json

import requests
import secrets
import validators
from bs4 import BeautifulSoup








class UserAgents:
    """Handles determination of user agent."""

    def __init__(self):
        pass

    @staticmethod
    def fetch_useragents_json():
        url = "https://www.useragents.me/#most-common-desktop-useragents-json-csv"
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        def extract_json_from_div(div_id: str):
            div = soup.find("div", id=div_id)
            if not div:
                raise ValueError(f"Could not find div with id={div_id}")
            # find the <textarea> under the first col-lg-6 child that has <h3>JSON</h3>
            json_col = div.find("div", class_="col-lg-6")
            if not json_col:
                raise ValueError(f"Could not find JSON column in {div_id}")
            textarea = json_col.find("textarea")
            if not textarea or not textarea.text.strip():
                raise ValueError(f"Could not find JSON textarea in {div_id}")
            return json.loads(textarea.text.strip())

        desktop_json = extract_json_from_div("most-common-desktop-useragents-json-csv")
        mobile_json = extract_json_from_div("most-common-mobile-useragents-json-csv")

        return {"desktop": desktop_json, "mobile": mobile_json}

    def choose_random_user_agent(self, desktop_list, mobile_list):
        """
        Combine the desktop and mobile user-agent lists and return one UA string
        chosen at random using strong randomness.
        """
        if desktop_list is None:
            desktop_list = []
        if mobile_list is None:
            mobile_list = []

        combined_entries = list(desktop_list) + list(mobile_list)
        if not combined_entries:
            raise ValueError("No user-agent entries were provided.")

        ua_strings = [entry["ua"] for entry in combined_entries if "ua" in entry]
        if not ua_strings:
            raise ValueError("No 'ua' field found in the provided user-agent entries.")

        return secrets.choice(ua_strings)

# // ... existing code ...

if __name__ == "__main__":
    # Example usage / manual test code moved outside the class definition
    ua_helper = UserAgents()
    data = ua_helper.fetch_useragents_json()

    print("Desktop User-Agents:")
    print(json.dumps(data["desktop"], indent=2))
    print("\nMobile User-Agents:")
    print(json.dumps(data["mobile"], indent=2))

    ranua = ua_helper.choose_random_user_agent(data["desktop"], data["mobile"])
    print("\nRandom User-Agent:")
    print(ranua)




































# class UserAgents:
#     """Handles determination of user agent."""
#
#     def __init__(self):
#         pass
#
#     def fetch_useragents_json():
#         url = "https://www.useragents.me/#most-common-desktop-useragents-json-csv"
#         response = requests.get(url, timeout=10)
#         response.raise_for_status()
#
#         soup = BeautifulSoup(response.text, "html.parser")
#
#         def extract_json_from_div(div_id: str):
#             div = soup.find("div", id=div_id)
#             if not div:
#                 raise ValueError(f"Could not find div with id={div_id}")
#             # find the <textarea> under the first col-lg-6 child that has <h3>JSON</h3>
#             json_col = div.find("div", class_="col-lg-6")
#             if not json_col:
#                 raise ValueError(f"Could not find JSON column in {div_id}")
#             textarea = json_col.find("textarea")
#             if not textarea or not textarea.text.strip():
#                 raise ValueError(f"Could not find JSON textarea in {div_id}")
#             return json.loads(textarea.text.strip())
#
#         desktop_json = extract_json_from_div("most-common-desktop-useragents-json-csv")
#         mobile_json = extract_json_from_div("most-common-mobile-useragents-json-csv")
#
#         return {"desktop": desktop_json, "mobile": mobile_json}
#
#     # # if __name__ == "__main__":
#     # data = fetch_useragents_json()
#     # print("Desktop User-Agents:")
#     # print(json.dumps(data["desktop"], indent=2))
#     # print("\nMobile User-Agents:")
#     # print(json.dumps(data["mobile"], indent=2))
#
#     def choose_random_user_agent(self, desktop_list, mobile_list):
#         """
#         Combine the desktop and mobile user-agent lists and return one UA string
#         chosen at random using strong randomness.
#
#         Both inputs are expected to be lists of dicts with at least the key "ua".
#         For example: [{"ua": "Mozilla/5.0 ...", ...}, ...]
#
#         :param desktop_list: List of desktop user-agent entries.
#         :param mobile_list: List of mobile user-agent entries.
#         :return: A single user-agent string chosen at random.
#         """
#         if desktop_list is None:
#             desktop_list = []
#         if mobile_list is None:
#             mobile_list = []
#
#         combined_entries = list(desktop_list) + list(mobile_list)
#         if not combined_entries:
#             raise ValueError("No user-agent entries were provided.")
#
#         ua_strings = [entry["ua"] for entry in combined_entries if "ua" in entry]
#         if not ua_strings:
#             raise ValueError("No 'ua' field found in the provided user-agent entries.")
#
#         # Use secrets.choice for strong randomness
#         return secrets.choice(ua_strings)
#
#     # if __name__ == "__main__":
#     # data = fetch_useragents_json()
#     # print("Desktop User-Agents:")
#     # print(json.dumps(data["desktop"], indent=2))
#     # print("\nMobile User-Agents:")
#     # print(json.dumps(data["mobile"], indent=2))
#
#     # Example usage of the new method:
#     data = fetch_useragents_json()
#     ua_helper = UserAgents()
#     ranua = ua_helper.choose_random_user_agent(data["desktop"], data["mobile"])
#
#
#
# #     def get_ua_randomly(self, json_ua_list_file):
# #         """
# #         Selects a random string from a list using strong randomness.
# #         :param strings: List of strings to choose from.
# #         :return: Randomly selected string from the list.
# #         """
# #         # TODO: Add mechanism to ERS to obtain fresh list of user agents from https://www.useragents.me/#most-common-desktop-useragents-json-csv
# #         with open(json_ua_list_file, "r") as f:
# #             data = json.load(f)
# #         ua_list = [item["ua"] for item in data]
# #         if not ua_list:
# #             raise ValueError("The user agent list cannot be empty.")
# #         return secrets.choice(ua_list)
# #
# #     def process_video(self, video_path: Path, options: dict) -> bool:
# #         """
# #         Post-process a downloaded video.
# #
# #         Args:
# #             video_path: Path to the downloaded video
# #             options: Processing options (re-encode, etc.)
# #
# #         Returns:
# #             True if successful, False otherwise
# #         """
# #         # Placeholder for post-processing logic
# #         # Could include:
# #         # - Re-encoding with ffmpeg
# #         # - Format conversion
# #         # - Thumbnail extraction
# #         # - Metadata editing
# #         return True
#
#
#
# username = getpass.getuser()  # Get the username of the user running the current script
# ua_path = f"/home/{username}/zyng/apps/dealer/ua_list.json"
#
#
#
#
# ranua = get_ua_randomly(ua_path)