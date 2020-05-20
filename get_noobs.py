
# this script takes 1 league of legends summoner name as a command line argument as input,
# and outputs 1 row of match data to "data.csv"

from bs4 import BeautifulSoup
import requests
import io
import csv
import sys

user = sys.argv[1]
headers = requests.utils.default_headers()
url = "https://na.op.gg/summoner/userName=" + user
req = requests.get(url, headers)
user_soup = BeautifulSoup(req.content, 'html.parser')

win = 0

# get entire html
games = user_soup.find_all("div", class_="GameItemWrap")
teams = []

# search through this player's last 10 games for a ranked solo queue game
for gm in games:
	# put the teams into a list if found: [blue, red]
	if "Ranked Solo" in gm.find("div", class_="GameType").string:
		teams = gm.find_all("div", class_="FollowPlayers Names")
		# assuming we are on the blue team, flip later if not...
		if "Defeat" in gm.find("div", class_="GameResult").string:
			win = 0
		if "Victory" in gm.find("div", class_="GameResult").string:
			win = 1
		print("found a ranked game for this player")
		break

if not teams:
	# no ranked games found for this asshole, need to find another player from this game
	print("KMS")
	
#construct string to query all player data at once
url = "https://na.op.gg/multi/query="
summoners = [] # fill this up
champions = []

summoner_strings = []
champion_strings = []
for team in teams:
	summoners = team.find_all("div", class_="SummonerName")
	champions = team.find_all("div", class_="ChampionImage")
	
	for x in range(0, 10):
		champion_strings.append(champions[x].select('div')[1].get_text(strip=True))
		str = summoners[x].find("a").string
		summoner_strings.append(str)
		url += str + "%2C"
		
		#determine here if win should be flipped or not
		#if user is on red team, flip bit
		if x > 4 and user in summoner_strings[-1]:
			win = 1 if win == 0 else 0

headers = requests.utils.default_headers()
req = requests.get(url, headers)
player_soup = BeautifulSoup(req.content, 'html.parser')

# use new url to get player stats
all_rows = player_soup.find("div", class_="MultiSearchTable")
player_rows = all_rows.find_all("div", class_="MultiSearchResultRow tabWrap")

# fill out some DICTS
playerDicts = [{}]*10

for row in player_rows:
	idx = summoner_strings.index(row.find("span", class_="SummonerName").string)
	
	# html sections
	tier_rank = row.find("div", class_="TierRank")
	champ_stat_tables = row.find("div", class_="MostChampionStats tabItems").select('div')[0].find_all("tbody", class_="Content")
	
	# sorry bad name, it's pretty much the same as the champ_stat_tables above^
	ccc = []
	for csr in champ_stat_tables:
		ccc.append(csr.find_all("tr", class_="Row"))
		
	# get stats here
	win_ratio_overall = tier_rank.find("div", class_="WinRatio")
	win_ratio_overall = 0 if not win_ratio_overall else win_ratio_overall.string.strip('(%)')
	champ_win_ratio = 0
	
	# see if the player's champion is in their top 10 most played
	for champ_rows in ccc:
		for champ_row in champ_rows:
			champ_name = champ_row.find("div", class_="ChampionName").string
			champ_wr = champ_row.find("td", class_="WinRatio Cell").select('span')[0].get_text(strip=True)
			
			if champion_strings[idx] == champ_name:
				champ_win_ratio = champ_wr.strip('(%)')
				break
	
	playerDicts[idx] = { 'champ': champion_strings[idx], 'champ_win_ratio': champ_win_ratio, 'win_ratio_overall': win_ratio_overall }

with open('data.csv', 'a+', newline='') as csvfile:
	writer = csv.writer(csvfile, delimiter=',')
	stuff = []
	for player in playerDicts:
		stuff.append(player.get('champ'))
		stuff.append(player.get('champ_win_ratio'))
		stuff.append(player.get('win_ratio_overall'))
	stuff.append(win)
	writer.writerow(stuff)
