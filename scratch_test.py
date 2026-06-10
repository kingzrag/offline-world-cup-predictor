import requests
from bs4 import BeautifulSoup

CLUBS = [
    (11, "arsenal-fc"),
    (281, "manchester-city"),
    (985, "manchester-united"),
    (405, "aston-villa"),
    (31, "fc-liverpool"),
    (1010, "afc-bournemouth"),
    (289, "sunderland-afc"),
    (1237, "brighton-amp-hove-albion"),
    (1148, "brentford-fc"),
    (631, "chelsea-fc"),
    (931, "fulham-fc"),
    (762, "newcastle-united"),
    (29, "everton-fc"),
    (399, "leeds-united"),
    (873, "crystal-palace"),
    (703, "nottingham-forest"),
    (148, "tottenham-hotspur"),
    (379, "west-ham-united"),
    (1132, "burnley-fc"),
    (543, "wolverhampton-wanderers")
]

def scan_club(club_id, name):
    url = f"https://www.transfermarkt.com/{name}/sperrenundverletzungen/verein/{club_id}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(response.text, "html.parser")
        tables = soup.find_all("table")
        
        for idx, table in enumerate(tables):
            headers = [th.get_text(strip=True) for th in table.find_all("th")]
            # Check if this table has player/reason/return headers
            if "Reason" in headers and ("Expected return" in headers or "Expected Return" in headers):
                tbody = table.find("tbody")
                if not tbody:
                    tbody = table
                rows = tbody.find_all("tr", recursive=False)
                
                print(f"\nClub: {name} (ID: {club_id}) | Table {idx} | Row Count: {len(rows)}")
                current_section = None
                for r in rows:
                    cells = r.find_all("td", recursive=False)
                    if len(cells) == 1:
                        cell_text = cells[0].get_text(strip=True)
                        current_section = cell_text
                        print(f"  Section: '{current_section}'")
                        continue
                    
                    if not cells:
                        continue
                        
                    player_link = cells[0].find("a", title=True)
                    player_name = player_link.get_text(strip=True) if player_link else "Unknown"
                    reason = cells[2].get_text(strip=True) if len(cells) > 2 else ""
                    since = cells[3].get_text(strip=True) if len(cells) > 3 else ""
                    expected_return = cells[4].get_text(strip=True) if len(cells) > 4 else ""
                    missed = cells[5].get_text(strip=True) if len(cells) > 5 else ""
                    
                    print(f"    [{current_section}] {player_name} | {reason} | Since: {since} | Return: {expected_return} | Missed: {missed}")
    except Exception as e:
        print(f"Error {name}: {e}")

def main():
    for club_id, name in CLUBS:
        scan_club(club_id, name)

if __name__ == "__main__":
    main()
