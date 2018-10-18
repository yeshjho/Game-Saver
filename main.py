import shutil
from time import strftime
import os
import sys
import re
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


class TooManyArgumentsError(Exception):
    pass


class TooFewArgumentError(Exception):
    pass


class ArgumentTypeMismatchError(Exception):
    pass


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


def save_logic(game_dict):
    for name, src in game_dict.items():
        name = name.strip()
        src = src.strip()

        if name.startswith('!'):
            skipped_games.append(name[:1])
            print_color(name[1:] + "는 저장하지 않습니다. 해당 게임을 건너뜁니다...\n", FORE_GRAPEFRUIT)
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
                            print_color(name + "는 최신 저장본과 동일합니다. 해당 게임을 건너뜁니다...\n", FORE_IVORY)
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
                        print_color(name + "는 최신 저장본과 동일합니다. 해당 게임을 건너뜁니다...\n", FORE_IVORY)
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
            report_result("\n사용자에 의해 건너뛴 게임들:", skipped_games, FORE_GRAPEFRUIT)
        if same_time_games:
            report_result("\n동일 시각 저장본이 존재해 건너뛴 게임들:", same_time_games, FORE_YELLOW)
        if identical_games:
            report_result("\n최신 저장본과 동일해 건너뛴 게임들:", identical_games, FORE_IVORY)


def save(_name, _src):
    save_dst = save_root + _name + "/" + strftime("%Y-%m-%d %H-%M" + '/')
    try:
        shutil.copytree(_src, save_dst)
        if os.path.isdir(_src):
            last_dsts[_name] = save_dst
        else:
            last_dsts[_name] = save_dst + _src.split('/')[-1]
    except FileExistsError:
        print_color(_name + "의 동일 시각 저장본이 이미 있습니다. 해당 게임을 건너뜁니다...\n", FORE_YELLOW)
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
            print_color(_name + "의 동일 시각 저장본이 이미 있습니다. 해당 게임을 건너뜁니다...\n", FORE_YELLOW)
            same_time_games.append(_name)
            return False

    succeeded_games.append(_name)
    print_color(_name + " 저장 완료했습니다.\n", FORE_BLUE)
    return True


def delete(game_dict):
    pass


def report_result(message, game_list, color=FORE_WHITE):
    print_color(message, color)
    for _game in sorted(game_list):
        print('\t' + _game)


def edit_options(showTF=False):
    option_list = []
    count = 0

    for option, value in options.items():
        count += 1
        if showTF and value in "01":
            value = "True" if value == "1" else "False"
        option_list.append(value)
        print(f"{number:3}  {option:30}  {value}")

    while True:
        answer = eval(input("변경할 옵션의 번호를 입력해 주세요: "))
        if isinstance(answer, int) and 0 < answer <= count:
            while True:
                answer2 = eval(input(option_list[answer - 1] + "를 무엇으로 변경하시겠습니까? 0/1로 대답해 주세요: "))
                if answer2 == "0":
                    options[option_list[answer - 1]] = "0"
                    break
                elif answer2 == "1":
                    options[option_list[answer - 1]] = "1"
                    break
                else:
                    print("올바른 값을 입력해 주세요.")
            print("성공적으로 변경되었습니다.")
            break
        else:
            print("올바른 번호를 입력해 주세요.")

    with open("option.txt", "r+", encoding='utf-8') as option_file:
        pattern = option_list[answer - 1] + r" = ([01]|(\w)+)\s*"
        original = option_file.read()
        target_string = re.search(pattern, original).group()
        changed = original.replace(target_string, target_string[:target_string.find('=') + 1] + ' ' + options[option_list[answer - 1]] + '\n')
        option_file.write(changed)


def set_cmd_color(color, handle=ctypes.windll.kernel32.GetStdHandle(-11)):
    ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)


def print_color(_msg, color, handle=ctypes.windll.kernel32.GetStdHandle(-11)):
    set_cmd_color(color, handle)
    print(_msg)
    set_cmd_color(FORE_WHITE, handle)


def eval_command(**kwargs):
    if kwargs['command'] == 'help': # help [command]
        if len(kwargs['args']) == 0:
            print_color(SYMBOL_MEANING_EXPLANATION, FORE_GRAY)
            for _command in COMMANDS:
                print_color(COMMAND_SYNTAX[_command], FORE_LIME)
                print_color(COMMAND_EXPLANATION_SIMPLE[_command], FORE_SILVER)
                print()
        else:
            if kwargs['args'] == ['path']:
                print_color('add, edit, show, del 중 한 가지 모드를 추가로 입력해 주세요.\n', FORE_YELLOW)
            else:
                try:
                    print_color(COMMAND_SYNTAX[' '.join(kwargs['args'])], FORE_LIME)
                    print_color(COMMAND_EXPLANATION_DETAILED[' '.join(kwargs['args'])], FORE_SILVER)
                    print()
                except KeyError:
                    print_color('존재하지 않는 명령어입니다.\n', FORE_YELLOW)

    elif kwargs['command'] == 'save': # save [game_name+]
        if len(kwargs['args']) == 0:
            if os.path.isdir(save_root):
                save_logic(srcs)
            else:
                print_color("저장 경로가 올바르지 않습니다. (이미 존재하는 폴더여야 합니다.)\n", FORE_RED)
        else:
            pass

    elif kwargs['command'] == 'path':
        if kwargs['args']:
            if kwargs['args'][0] == 'add': # path add <game_name> [isAFile = 0] [nickname]
                if len(kwargs['args']) == 1:
                    raise TooFewArgumentError
                elif len(kwargs['args']) == 2:
                    pass
                elif len(kwargs['args']) == 3:
                    pass
                elif len(kwargs['args']) == 4:
                    pass
                else:
                    raise TooManyArgumentsError
            elif kwargs['args'][0] == 'edit': # path edit <game_name|'dst'> ['name'|{'path'}|'nickname'|'toggle']
                if len(kwargs['args']) == 1:
                    raise TooFewArgumentError
                elif len(kwargs['args']) == 2:
                    pass
                elif len(kwargs['args']) == 3:
                    pass
                else:
                    raise TooManyArgumentsError
            elif kwargs['args'][0] == 'show': # path show [game_name+|'dst']
                if len(kwargs['args']) == 1:
                    pass
                elif len(kwargs['args']) == 2:
                    pass
                else:
                    pass
            elif kwargs['args'][0] == 'del': # path del <game_name+>
                if len(kwargs['args']) == 1:
                    raise TooFewArgumentError
                else:
                    pass
            else:
                raise ArgumentTypeMismatchError('add, edit, show, del 중 하나를 입력해 주세요.')
        else:
            raise TooFewArgumentError('add, edit, show, del 중 하나를 추가로 입력해 주세요.')

    elif kwargs['command'] == 'del': # del <game_name+|date [date]> [trackHistory=0]
        if len(kwargs['args']) == 0:
            raise TooFewArgumentError
        elif len(kwargs['args']) == 1:
            pass
        elif len(kwargs['args']) == 2:
            pass
        elif len(kwargs['args']) == 3:
            pass
        else:
            pass

    elif kwargs['command'] == 'delall': # delall [trackHistory=0]
        if len(kwargs['args']) == 0:
            pass
        elif len(kwargs['args']) == 1:
            pass
        else:
            raise TooManyArgumentsError

    elif kwargs['command'] == 'option': # option [showTF=0]
        if len(kwargs['args']) == 0:
            edit_options()
        elif len(kwargs['args']) == 1:
            if kwargs['args'][0] == '0':
                edit_options()
            elif kwargs['args'][0] == '1':
                edit_options(True)
            else:
                raise ArgumentTypeMismatchError('0과 1 중 하나를 입력해 주세요.')
        else:
            raise TooManyArgumentsError

    elif kwargs['command'] == 'exit': # exit
        if len(kwargs['args']) == 0:
            sys.exit()
        else:
            raise TooManyArgumentsError

    else:
        print_color('존재하지 않는 명령어입니다. 도움말을 보려면 help를 치세요.\n', FORE_YELLOW)


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


set_cmd_color(FORE_WHITE)
print_color('제작자: yeshjho\n', FORE_CYAN)

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
        command = input(">>").split()  # TODO: not splitting spaces inside ""
        if command:
            try:
                eval_command(command=command[0], args=command[1:])
            except TooManyArgumentsError as msg:
                print_color('인수가 너무 많습니다.', FORE_RED)
                if str(msg):
                    print_color(str(msg), FORE_RED)
                print_color(COMMAND_SYNTAX[command[0]], FORE_RED)
                print()
            except TooFewArgumentError as msg:
                print_color('인수가 너무 적습니다.', FORE_RED)
                if str(msg):
                    print_color(str(msg), FORE_RED)
                print_color(COMMAND_SYNTAX[command[0]], FORE_RED)
                print()
            except ArgumentTypeMismatchError as msg:
                print_color('인수가 적절하지 않습니다.', FORE_RED)
                if str(msg):
                    print_color(str(msg), FORE_RED)
                print_color(COMMAND_SYNTAX[command[0]], FORE_RED)
                print()

else:
    while True:
        break
