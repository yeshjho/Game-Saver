from main import input_color, print_color
from constants import *
import winreg
import requests


class SteamGameListGetter:
    def __init__(self):
        if not self.get_steam_id():
            self.steam_id = input_color(QUERY_STEAM_ID, FORE_CYAN)

        self.headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) '
                                      'AppleWebKit/537.36 (KHTML, like Gecko) Chrome/39.0.2171.95 Safari/537.36'}
        self.connection = None
        self.start_tag = 'var rgGames = '
        self.end_tag = ';\r\n\t\tvar rgChangingGames'

        if self.steam_id.startswith('http'):
            self.url = self.steam_id + '/games/?tab=all'
        elif self.steam_id.isnumeric():
            self.url = 'http://steamcommunity.com/profiles/' + self.steam_id + '/games/?tab=all'
        else:
            self.url = 'http://steamcommunity.com/id/' + self.steam_id + '/games/?tab=all'

    def get_steam_id(self):
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Software\\Valve\\Steam")
            steam_path = winreg.QueryValueEx(key, 'SteamPath')[0]
        except OSError:
            print("w")
            return False
        try_path = steam_path + '/config/loginusers.vdf'
        try:
            with open(try_path, encoding='utf-8') as user_file:
                steam_id = eval(user_file.readlines()[2].strip())
                self.steam_id = steam_id
                return True
        except OSError or IndexError:
            print("x")
            return False

    def try_connect(self):
        try:
            self.connection = requests.get(self.url, self.headers)
            self.connection.raise_for_status()
            return True
        except requests.exceptions.RequestException:
            print_color('스팀 서버로부터 응답을 받지 못했습니다.', FORE_RED)
            return False

    def get_games(self, is_raw=False):
        if not self.try_connect():
            return False

        content = str(self.connection.content, encoding='utf-8')
        if '<title>Steam Community :: Error</title>' in content:
            print_color('해당 아이디가 존재하지 않습니다.', FORE_RED)
            return False
        if '<div class="profile_private_info">' in content:
            print_color('해당 아이디의 프로필이 비공개여서 불러올 수 없습니다.', FORE_RED)
            return False

        index_start = content.find(self.start_tag) + len(self.start_tag)
        index_end = content.find(self.end_tag)
        try:
            game_list = eval(content[index_start:index_end].replace('true', 'True').replace('false', 'False'))
            if is_raw:
                return game_list
            else:
                return list(map(lambda x: (x['appid'], x['name']), game_list))
        except NameError or TypeError:
            print_color('페이지로부터 게임 목록을 불러오는 데 실패했습니다.', FORE_RED)
            return False


a = SteamGameListGetter()
for i in a.get_games(True):
    del i['logo']
    for j in i:
        print(j)
        print('\t' + str(i[j]))
    print()
