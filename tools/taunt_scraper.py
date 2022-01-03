import json
import os
from typing import List, Dict, Union

import requests  # type: ignore
from bs4 import BeautifulSoup  # type: ignore


def main() -> None:
    wiki_url: str = "https://ageofempires.fandom.com/wiki/Taunts"

    try:
        resp: requests.Response = requests.get(wiki_url)
        resp.raise_for_status()
        html_doc: str = resp.text
    except requests.RequestException:
        raise

    soup = BeautifulSoup(html_doc, "html.parser")
    header = soup.select("#Full_list_of_taunts")
    taunts_table = header[0].find_next("table")
    de_taunts_table = taunts_table.find_next("table")

    taunts: List[Dict[str, Union[str, int]]] = []
    for table in [taunts_table, de_taunts_table]:
        rows = table.find_all("tr")
        for row in rows:
            column = row.find_all("td")
            if not column:
                continue

            new_row: Dict[str, Union[str, int]] = {
                "num": int(column[0].text.strip()),
                "text": column[1].text.strip(),
                "url": column[2].find("span").get("data-src"),
            }
            new_row["file"] = f"{new_row['num']:03}.ogg"
            taunts.append(new_row)

    taunts_folder = "../data/taunts"
    os.makedirs(taunts_folder, exist_ok=True)
    for taunt in taunts:
        try:
            resp = requests.get(taunt["url"])
            resp.raise_for_status()
        except requests.RequestException:
            print(f"Failed to fetch {taunt}")
            continue

        with open(f"{taunts_folder}/{taunt['file']}", "wb") as taunt_fd:
            taunt_fd.write(resp.content)

    with open(f"{taunts_folder}/manifest.json", "w") as manifest_fd:
        json.dump(taunts, manifest_fd, indent=2)


if __name__ == "__main__":
    main()
