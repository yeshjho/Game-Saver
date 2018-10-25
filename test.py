from main import input_color, print_color
from constants import *
import winreg
import requests
import re
from lxml import html
import sys
from PyQt5 import QtGui


class SteamGameListGetter:
    def __init__(self, auto_id=True):
        if not auto_id or not self.get_steam_id():
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
            return False
        try_path = steam_path + '/config/loginusers.vdf'
        try:
            with open(try_path, encoding='utf-8') as user_file:
                steam_id = eval(user_file.readlines()[2].strip())
                self.steam_id = steam_id
                return True
        except OSError or IndexError:
            return False

    def try_connect(self):
        try:
            self.connection = requests.get(self.url, self.headers)
            self.connection.raise_for_status()
            return True
        except requests.exceptions.RequestException:
            print_color('스팀 서버로부터 응답을 받지 못했습니다.', FORE_RED)
            return False

    def get_games(self, extra=False, raw=False):
        if not self.try_connect():
            return False

        content = str(self.connection.content, encoding='utf-8')
        if '<title>Steam Community :: Error</title>' in content:
            print_color('해당 아이디가 존재하지 않습니다.', FORE_RED)
            return False
        if '<div class="profile_private_info">' in content:
            print_color('해당 아이디의 프로필이 비공개여서 불러올 수 없습니다.', FORE_RED)
            return False

        if raw:
            return content

        index_start = content.find(self.start_tag) + len(self.start_tag)
        index_end = content.find(self.end_tag)
        try:
            game_list = eval(content[index_start:index_end].replace('true', 'True').replace('false', 'False'))
            if extra:
                return game_list
            else:
                return list(map(lambda x: (x['appid'], x['name']), game_list))
        except NameError or TypeError:
            print_color('페이지로부터 게임 목록을 불러오는 데 실패했습니다.', FORE_RED)
            return False


def get_save_loc(game_list: list):
    for app_id, app_name in game_list:
        try:
            connection = requests.get('https://store.steampowered.com/app/' + str(app_id))
            connection.raise_for_status()
            content = str(connection.content, encoding='utf-8')

            is_dlc = True if 'This content requires the base game' in content or 'This DLC may contain' in content \
                else False
            if not is_dlc:
                name = re.sub(r"[A-Za-z]+('[A-Za-z]+)?",
                              lambda mo: mo.group(0)[0].upper() + mo.group(0)[1:].lower(), app_name)
                name = name.replace("'", '%27').replace('™', '')
                print()
                print(app_id, name)
                connection = requests.get('https://pcgamingwiki.com/w/index.php?search=' + app_name.replace('™', ''))
                connection.raise_for_status()
                content = str(connection.content, encoding='utf-8')
                try:
                    pat = r'location">Save game data location[\S\s]+(Windows|Steam)[\S\s]+</td>'
                    phase_0 = re.search(pat, content).group()
                    pat = r'(Windows|Steam)</th>\n\t<td class="template-infotable-monospace">.+</td>'
                    phase_1 = re.search(pat, phase_0).group()
                    pat = r'<.+?>'
                    for i in re.findall(pat, phase_1):
                        phase_1 = phase_1.replace(i, '')
                    if "Windows" in phase_1:
                        print(phase_1.replace('Windows', '').strip().replace('&lt;', '<').replace('&gt;', '>'))
                    elif "Steam" in phase_1:
                        print(phase_1.replace("Steam", '').strip().replace('&lt;', '<').replace('&gt;', '>'))
                    else:
                        print("something went wrong")
                except AttributeError:
                    try:
                        pat = r'Page title matches</span>[\s\S]+data-serp-pos="0"'
                        second = re.search(pat, content).group()
                        pat = r'a href=".+?"'
                        third = 'https://pcgamingwiki.com' + re.search(pat, second).group()[8:-1]
                        connection = requests.get(third)
                        connection.raise_for_status()
                        content = str(connection.content, encoding='utf-8')
                        pat = r'location">Save game data location[\S\s]+(Windows|Steam)[\S\s]+</td>'
                        phase_0 = re.search(pat, content).group()
                        pat = r'(Windows|Steam)</th>\n\t<td class="template-infotable-monospace">.+</td>'
                        phase_1 = re.search(pat, phase_0).group()
                        pat = r'<.+?>'
                        for i in re.findall(pat, phase_1):
                            phase_1 = phase_1.replace(i, '')
                        if "Windows" in phase_1:
                            print(phase_1.replace('Windows', '').strip().replace('&lt;', '<').replace('&gt;', '>'))
                        elif "Steam" in phase_1:
                            print(phase_1.replace("Steam", '').strip().replace('&lt;', '<').replace('&gt;', '>'))
                        else:
                            print("something went wrong")
                    except AttributeError:
                        print("NO GAME/NO SAVE FILE")
        except requests.exceptions.RequestException:
            print('FAIL')


a = SteamGameListGetter()
games = a.get_games()
get_save_loc(games)
"""
for i in a.get_games(True):
    del i['logo']
    for j in i:
        print(j)
        print('\t' + str(i[j]))
    print()
"""
# TODO DOING THIS TO GET DATA FROM STEAMDB.INFO WHERE USES JAVASCRIPT TO RENDER ITS CONTENT(STEAM STORE AIN'T ACCURATE)
"""
import sys  
from PyQt4.QtGui import *  
from PyQt4.QtCore import *  
from PyQt4.QtWebKit import *  
from lxml import html 

#Take this class for granted.Just use result of rendering.
class Render(QWebPage):  
  def __init__(self, url):  
    self.app = QApplication(sys.argv)  
    QWebPage.__init__(self)  
    self.loadFinished.connect(self._loadFinished)  
    self.mainFrame().load(QUrl(url))  
    self.app.exec_()  

  def _loadFinished(self, result):  
    self.frame = self.mainFrame()  
    self.app.quit()  

url = 'http://pycoders.com/archive/'  
r = Render(url)  
result = r.frame.toHtml()
# This step is important.Converting QString to Ascii for lxml to process

# The following returns an lxml element tree
archive_links = html.fromstring(str(result.toAscii()))
print archive_links

# The following returns an array containing the URLs
raw_links = archive_links.xpath('//div[@class="campaign"]/a/@href')
print raw_links
                

"""