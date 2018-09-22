import shutil
from time import strftime
import os
import sys
from filecmp import dircmp, cmp
from tempfile import TemporaryFile
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog
import ctypes

from constants import *

succeeded_games = []
failed_games = []
skipped_games = []
same_time_games = []
identical_games = []


class dircmp2(dircmp):
    def __init__(self, a, b, f, ignore=None, hide=None):
        super().__init__(a, b, ignore, hide)
        self.result = []
        self.file = f
        self.subdirs = {}

    def phase4(self):
        self.subdirs = {}
        for x in self.common_dirs:
            a_x = os.path.join(self.left, x)
            b_x = os.path.join(self.right, x)
            self.subdirs[x] = dircmp2(a_x, b_x, self.file, self.ignore, self.hide)

    def report(self):
        if self.left_only or self.right_only or self.diff_files or self.funny_files:
            print(file=self.file)

    def report_full_closure(self):
        self.report()
        for sd in self.subdirs.values():
            sd.report_full_closure()


class FileSelectDialog(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.dialog = QFileDialog()
        self.dialog.setFileMode(QFileDialog.Directory)
        self.dialog.exec_()

    def get_selected_path(self):
        return self.dialog.selectedFiles()[0]


def save_logic():
    for name, src in srcs.items():
        name = name.strip()
        src = src.strip()

        if name.startswith('!'):
            skipped_games.append(name[:1])
            print_color(name[1:] + "는 저장하지 않습니다. 해당 게임을 건너뜁니다...\n", FORE_ORANGEb)
            continue

        print(name + " 저장 중...")

        if (not eval(options['SAVE_IDENTICAL_FILE_TOO'])) and name in last_dsts:
            if os.path.isdir(src):
                with TemporaryFile('w+', encoding='utf-8') as temp_file:
                    try:
                        comp_obj = dircmp2(last_dsts[name], src, temp_file)
                        comp_obj.report_full_closure()
                        temp_file.seek(0)
                        is_identical = False if temp_file.read() else True
                        if is_identical:
                            identical_games.append(name)
                            print_color(name + "는 최신 저장본과 동일합니다. 해당 게임을 건너뜁니다...\n", FORE_YELLOWb)
                            continue
                        else:
                            if not save(name, src):
                                continue
                    except FileNotFoundError:
                        del last_dsts[name]
                        if not save(name, src):
                            continue
            else:
                try:
                    is_identical = cmp(last_dsts[name], src)
                    if is_identical:
                        identical_games.append(name)
                        print_color(name + "는 최신 저장본과 동일합니다. 해당 게임을 건너뜁니다...\n", FORE_YELLOWb)
                        continue
                    else:
                        if not save(name, src):
                            continue
                except FileNotFoundError:
                    del last_dsts[name]
                    if not save(name, src):
                        continue
        else:
            if not save(name, src):
                continue

    print("\n모든 게임의 저장이 완료되었습니다.")
    if succeeded_games:
        report_result("\n새로 저장한 게임들:", succeeded_games, FORE_BLUE)

        with open('last_saved.txt', 'w', encoding='utf-8') as _last_saved_file:
            for _key in last_dsts:
                print(_key + '|' + last_dsts[_key], file=_last_saved_file)
    if failed_games:
        report_result("\n저장에 실패한 게임들:", failed_games, FORE_RED)
    if eval(options['VERBOSE_REPORT']):
        if skipped_games:
            report_result("\n사용자에 의해 건너뛴 게임들:", skipped_games, FORE_ORANGEb)
        if same_time_games:
            report_result("\n동일 시각 저장본이 존재해 건너뛴 게임들:", same_time_games, FORE_BROWN)
        if identical_games:
            report_result("\n최신 저장본과 동일해 건너뛴 게임들:", identical_games, FORE_YELLOWb)


def save(_name, _src):
    save_dst = save_root + _name + "/" + strftime("%Y-%m-%d %H-%M" + '/')
    try:
        shutil.copytree(_src, save_dst)
        if os.path.isdir(_src):
            last_dsts[_name] = save_dst
        else:
            last_dsts[_name] = save_dst + _src.split('/')[-1]
    except FileExistsError:
        print_color(_name + "의 동일 시각 저장본이 이미 있습니다. 해당 게임을 건너뜁니다...\n", FORE_BROWN)
        same_time_games.append(_name)
        return False
    except FileNotFoundError:
        print_color(_name + "의 " + _src + " 경로가 올바르지 않거나 파일이 존재하지 않습니다. 저장에 실패했습니다.\n", FORE_RED)
        failed_games.append(_name)
        return False
    except NotADirectoryError:
        if not os.path.exists(save_dst):
            os.makedirs(save_dst)
            shutil.copy(_src, save_dst)
            last_dsts[_name] = save_dst + _src.split('/')[-1]
        else:
            print_color(_name + "의 동일 시각 저장본이 이미 있습니다. 해당 게임을 건너뜁니다...\n", FORE_BROWN)
            same_time_games.append(_name)
            return False

    succeeded_games.append(_name)
    print_color(_name + " 저장 완료했습니다.\n", FORE_BLUE)
    return True


def report_result(message, game_list, color=FORE_WHITEb):
    print_color(message, color)
    for _game in sorted(game_list):
        print('\t' + _game)


def set_cmd_color(color, handle=ctypes.windll.kernel32.GetStdHandle(-11)):
    ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)


def print_color(msg, color, handle=ctypes.windll.kernel32.GetStdHandle(-11)):
    set_cmd_color(color, handle)
    print(msg)
    set_cmd_color(FORE_WHITEb)


def eval_command(**kwargs):
    if kwargs['command'] == 'help':
        if kwargs['args']:
            pass
        else:
            print('''~사용한 기호들의 의미~

[]\t선택적으로 입력
<>\t필수적으로 입력
|\t또는 (하나 선택)
+\t한 개 이상
"###"\t### 그대로 입력
=, {}\t기본값


help [command]
도움말을 봅니다.\ncommand가 주어지면 해당 명령어에 관한 자세한 설명을 봅니다.

save [game_name+]
게임 파일들을 백업합니다.

path add <game_name> [isAFile=0] [nickname]
세이브 파일 경로를 추가합니다.

path edit <game_name|"dst"> ["name"|{"path"}|"nickname"|"toggle"]
세이브 파일 경로를 수정합니다.

path show [game_name+|"dst"]
세이브 파일 경로를 보여줍니다.

path del <game_name+>
저장된 세이브 파일 경로를 삭제합니다.

del <game_name|date [date]> [trackHistory=0]
저장된 백업본을 삭제합니다.

delall [trackHistory=0]
이때까지의 모든 백업본을 삭제합니다.

option [showTF=0]
옵션 값을 보고 수정합니다.

exit
프로그램을 종료합니다.
''')

    elif kwargs['command'] == 'save':
        if kwargs['args']:
            pass
        else:
            if os.path.isdir(save_root):
                save_logic()
            else:
                print_color("저장 경로가 올바르지 않습니다. (이미 존재하는 폴더여야 합니다.)", FORE_RED)

    elif kwargs['command'] == 'path':
        if kwargs['args']:
            pass
        else:
            pass

    elif kwargs['command'] == 'del':
        if kwargs['args']:
            pass
        else:
            pass

    elif kwargs['command'] == 'delall':
        if kwargs['args']:
            pass
        else:
            pass

    elif kwargs['command'] == 'option':
        if kwargs['args']:
            pass
        else:
            pass

    elif kwargs['command'] == 'exit':
        if kwargs['args']:
            pass
        else:
            # TODO: save files
            sys.exit()

    else:
        print('존재하지 않는 명령어입니다. 도움말을 보려면 help를 치세요.')


with open("locations.txt", encoding="utf-8") as gm_loc_file:
    srcs = dict(filter(lambda x: len(x) != 1,
                       map(lambda x: x.strip().replace('\\', '/').split("|") if x[0] != "#" else '_',
                           gm_loc_file.readlines())))  # TODO: nickname system

with open("last_saved.txt", 'a+', encoding='utf-8') as last_saved_file:
    last_saved_file.seek(0)
    last_dsts = dict(filter(lambda x: len(x) != 1,
                            map(lambda x: x.strip().split("|"),
                                last_saved_file.readlines())))

with open("options.txt", encoding='utf-8') as option_file:
    options = dict(filter(lambda x: len(x) != 1,
                          map(lambda x: x.strip().split(" = ") if x[0] != "#" else '_',
                              option_file.readlines())))

save_root = srcs['SaveLocation'] if srcs['SaveLocation'].endswith('/') else srcs['SaveLocation'] + '/'
del srcs['SaveLocation']

if __name__ == "__main__":
    set_cmd_color(FORE_WHITEb)

    if options['USE_COMMAND'] == '-1':
        answer = input("명령어로 프로그램을 조작하시겠습니까? 이 옵션은 나중에 변경할 수 있습니다. ([y]/n): ").lower()
        while answer != 'y' and answer != 'n' and answer != '':
            answer = input("y/n 중 하나를 입력해 주세요: ")
        options['USE_COMMAND'] = '1' if answer == 'y' or answer == '' else '0'
        with open('options.txt', 'r+', encoding='utf-8') as option_file:
            contain = option_file.read().replace('-1', options['USE_COMMAND'])
            option_file.seek(0)
            option_file.write(contain)
            option_file.truncate()

    if eval(options['USE_COMMAND']):
        print('도움말을 보려면 help를 치세요.\n')
        while True:
            command = input(">>").split()  # TODO: not splitting spaces inside ''
            if command:
                eval_command(command=command[0], args=command[1:])

    else:
        while True:
            break
