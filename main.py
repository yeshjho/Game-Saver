import shutil
from time import strftime
from datetime import date
import os
import sys
import re
import ctypes
import shlex
import stat
import glob
from filecmp import dircmp, cmp
from tempfile import TemporaryFile
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog

from constants import *

succeeded_games = []
failed_games = []
skipped_games = []
same_time_games = []
identical_games = []

game_name_dict = {}


class TooManyArgumentsError(Exception):
    pass


class TooFewArgumentError(Exception):
    pass


class ArgumentTypeMismatchError(Exception):
    pass


class FileException(Exception):
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


class two_dict(dict):
    def __init__(self, iterable):
        super().__init__()
        for pair in iterable:
            if len(pair) == 3:
                name, nickname, loc = pair
                game_name_dict[name.strip()] = name.strip()
                if name.startswith("!"):
                    game_name_dict[name.strip()[1:]] = name.strip()
                self.__setitem__(name.strip(), loc.strip())
                if nickname:
                    game_name_dict[nickname.strip()] = name.strip()
            elif len(pair) == 2:
                name, loc = pair
                game_name_dict[name.strip()] = name.strip()
                if name.startswith("!"):
                    game_name_dict[name.strip()[1:]] = name.strip()
                self.__setitem__(name.strip(), loc.strip())


class FileSelectDialog(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.dialog = QFileDialog()
        self.dialog.setFileMode(QFileDialog.Directory)
        self.dialog.exec_()

    def get_selected_path(self):
        return self.dialog.selectedFiles()[0]


def save_logic(game_dict):
    succeeded_games.clear()
    failed_games.clear()
    skipped_games.clear()
    same_time_games.clear()
    identical_games.clear()

    for name, src in game_dict.items():
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
            os.chmod(save_dst, stat.S_IWUSR)
            shutil.copy(_src, save_dst)
            last_dsts[_name] = save_dst + _src.split('/')[-1]
        else:
            print_color(_name + "의 동일 시각 저장본이 이미 있습니다. 해당 게임을 건너뜁니다...\n", FORE_YELLOW)
            same_time_games.append(_name)
            return False

    succeeded_games.append(_name)
    print_color(_name + " 저장 완료했습니다.\n", FORE_BLUE)
    return True


def delete(game_names):
    for name in game_names:
        if os.path.exists(save_root + game_name_dict[name] + "/"):
            try:
                shutil.rmtree(save_root + game_name_dict[name] + "/", False, delete_error)
            except FileException:
                return
        else:
            print_color(name + "게임의 백업본이 존재하지 않습니다.", FORE_YELLOW)
            return

        print(name + "의 백업본 삭제 완료했습니다.")


def delete_date(*dates):
    if len(dates) == 1:
        for path in glob.glob(save_root + '**/' + dates[0].isoformat() + "*/", recursive=True):
            try:
                shutil.rmtree(path, False, delete_error)
            except FileException:
                return
        print(dates[0].isoformat() + "의 백업본을 모두 삭제했습니다.")
    else:
        if isinstance(dates[0], date) and isinstance(dates[1], date):
            pass
        elif isinstance(dates[0], str):
            pass
        else:
            pass  # TODO: 세이브 루트 내 모든 경로 가져와서 date 인스턴스 만들고 비교 후 삭제 결정


def delete_path(names):
    for name in names:
        with open('locations.txt', 'r+', encoding='utf-8') as loc_file:
            original = loc_file.read()
            pat = r'[ \t!]*' + game_name_dict[name] + r'.+\n'
            target_string = re.search(pat, original).group()
            changed_text = original.replace(target_string, '')
            loc_file.seek(0)
            loc_file.write(changed_text)
            loc_file.truncate()
        del srcs[game_name_dict[name]]
        src_list.remove(list(filter(lambda x: True if x[0] == game_name_dict[name] else False, src_list))[0])
        del game_name_dict[game_name_dict[name]]
        try:
            del game_name_dict["!" + name]
        except KeyError:
            pass
        try:
            del game_name_dict[name]
        except KeyError:
            pass
        print_color(name + "의 경로 삭제 완료했습니다.", FORE_BLUE)


def report_result(message, game_list, color=FORE_WHITE):
    print_color(message, color)
    for _game in sorted(game_list):
        print('\t' + _game)


def edit_options(show_tf=False):
    option_list = []
    count = 0

    for option, value in options.items():
        count += 1
        if show_tf and (value == "0" or value == "1"):
            value = "True" if value == "1" else "False"
        if not show_tf and (value == "True" or value == "False"):
            value = "1" if value == "True" else "0"
        option_list.append(option)
        print_color(f"[{count:2}]  {option:30} : {value}", FORE_GREEN)

    while True:
        answer1 = input("\n변경할 옵션의 번호를 입력해 주세요 (취소하려면 -1을 입력하세요): ")
        if answer1.isdigit() and 0 < int(answer1) <= count:
            while True:
                answer2 = input(option_list[int(answer1) - 1] + "를 무엇으로 변경하시겠습니까? 0/1로 대답해 주세요: ")
                if answer2 == "0":
                    options[option_list[int(answer1) - 1]] = "0"
                    break
                elif answer2 == "1":
                    options[option_list[int(answer1) - 1]] = "1"
                    break
                else:
                    print_color("올바른 값을 입력해 주세요.", FORE_RED)
            print("성공적으로 변경되었습니다.\n")
            break
        elif answer1 == "-1":
            return
        else:
            print_color("올바른 번호를 입력해 주세요.", FORE_RED)

    with open("options.txt", "r+", encoding='utf-8') as _option_file:
        pattern = option_list[int(answer1) - 1] + r" = ([01]|(\w)+)\s*"
        original = _option_file.read()
        target_string = re.search(pattern, original).group()
        alter_text = target_string[:target_string.find('=') + 1] + ' ' + options[option_list[int(answer1) - 1]] + '\n'
        _option_file.seek(0)
        _option_file.write(original.replace(target_string, alter_text))
        _option_file.truncate()


def set_cmd_color(color, handle=ctypes.windll.kernel32.GetStdHandle(-11)):
    ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)


def print_color(_msg, color, handle=ctypes.windll.kernel32.GetStdHandle(-11)):
    set_cmd_color(color, handle)
    print(_msg)
    set_cmd_color(FORE_WHITE, handle)


def delete_error(func, path, exc_info):
    if not os.access(path, os.W_OK):
        os.chmod(path, stat.S_IWUSR)
        func(path)
    else:
        print_color("파일을 지우는 도중 에러가 발생했습니다.", FORE_RED)
        print_color(exc_info[1], FORE_RED)
        raise FileException


def eval_command(**kwargs):
    if kwargs['command'] == 'help':  # help [command]
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

    elif kwargs['command'] == 'save':  # save [game_name+]
        if len(kwargs['args']) == 0:
            if os.path.isdir(save_root):
                save_logic(srcs)
            else:
                print_color("저장 경로가 올바르지 않습니다. (이미 존재하는 폴더여야 합니다.)\n", FORE_RED)
        else:
            temp_dict = {}
            for name in kwargs['args']:
                if name not in game_name_dict:
                    print_color(name + "이란 이름 혹은 닉네임을 가진 게임이 없습니다. 해당 게임을 건너뜁니다...\n", FORE_YELLOW)
                else:
                    temp_dict[game_name_dict[name]] = srcs[game_name_dict[name]]
            save_logic(temp_dict)

    elif kwargs['command'] == 'path':  # TODO: 이미 있는 이름을 추가하려 할 때
        if kwargs['args']:
            if kwargs['args'][0] == 'add':  # path add <game_name> [isAFile=0] [nickname]
                if len(kwargs['args']) == 1:
                    raise TooFewArgumentError
                elif len(kwargs['args']) == 2:
                    pass  # TODO: 게임 이름만 주어짐
                elif len(kwargs['args']) == 3:
                    pass  # TODO: 파일인지의 여부까지 주어짐
                elif len(kwargs['args']) == 4:
                    pass  # TODO: 닉네임까지 주어짐
                else:
                    raise TooManyArgumentsError

            elif kwargs['args'][0] == 'edit':  # path edit <game_name|'dst'> ['name'|{'path'}|'nickname'|'toggle']
                if len(kwargs['args']) == 1:
                    raise TooFewArgumentError
                elif len(kwargs['args']) == 2:
                    if kwargs['args'][1] == 'dst':
                        pass  # TODO: dst가 주어짐
                    else:
                        pass  # TODO: 게임 이름이 주어짐
                elif len(kwargs['args']) == 3:
                    pass  # TODO: 모드가 추가로 주어짐
                else:
                    raise TooManyArgumentsError

            elif kwargs['args'][0] == 'show':  # path show [game_name+|'dst']
                if len(kwargs['args']) == 1:
                    print_color('{0:30}{1:15}{2}\n'.format("NAME", "NICKNAME", "LOCATION"), FORE_GREEN)
                    for name, nickname, src in src_list:
                        print(f'{name:30}{nickname:15}{src}')
                elif len(kwargs['args']) == 2:
                    if kwargs['args'][1] == 'dst':
                        print(f'Save Location: {save_root}')
                    else:
                        name = kwargs['args'][1]
                        if name in game_name_dict:
                            print(f'{name}: {srcs[game_name_dict[name]]}')
                        else:
                            print_color(name + "이란 이름 혹은 닉네임을 가진 게임이 없습니다.", FORE_YELLOW)
                else:
                    print_color('{0:30}{1}\n'.format("GAME", "LOCATION"), FORE_GREEN)
                    for name in kwargs['args'][1:]:
                        if name in game_name_dict:
                            print(f'{name:30}{srcs[game_name_dict[name]]}')
                        else:
                            print_color(name + "이란 이름 혹은 닉네임을 가진 게임이 없습니다.", FORE_YELLOW)

            elif kwargs['args'][0] == 'del':  # path del <game_name+>
                if len(kwargs['args']) == 1:
                    raise TooFewArgumentError
                else:
                    temp_list = []
                    for name in kwargs['args'][1:]:
                        if name in game_name_dict:
                            temp_list.append(name)
                        else:
                            print_color(name + '이란 이름 혹은 닉네임을 가진 게임이 없습니다.', FORE_YELLOW)
                    delete_path(temp_list)
            else:
                raise ArgumentTypeMismatchError('add, edit, show, del 중 하나를 입력해 주세요.')

        else:
            raise TooFewArgumentError('add, edit, show, del 중 하나를 추가로 입력해 주세요.')

    elif kwargs['command'] == 'del':  # del <game_name+|date [date]>
        if len(kwargs['args']) == 0:
            raise TooFewArgumentError('전체 삭제는 delall을 이용하세요.')
        elif len(kwargs['args']) == 1:
            date_search = re.search(PATTERN_DATE, kwargs['args'][0])
            if date_search:
                date_str = date_search.group()
                try:
                    delete_date(date(int(date_str[:4]), int(date_str[5:7]), int(date_str[8:])))
                except ValueError:
                    print_color("올바른 날짜를 입력해 주세요.", FORE_YELLOW)
            else:
                if kwargs['args'][0] in game_name_dict:
                    delete(kwargs['args'])
                else:
                    print_color(kwargs['args'][0] + "이란 이름 혹은 닉네임을 가진 게임이 없습니다.", FORE_YELLOW)
        elif len(kwargs['args']) == 2:
            date_search1 = re.search(PATTERN_DATE, kwargs['args'][0])
            date_search2 = re.search(PATTERN_DATE, kwargs['args'][1])
            date1_str = date_search1.group() if date_search1 else None
            date2_str = date_search2.group() if date_search2 else None
            if date_search1 and date_search2:
                delete_date(date(int(date1_str[:4]), int(date1_str[5:7]), int(date1_str[8:])),
                            date(int(date2_str[:4]), int(date2_str[5:7]), int(date2_str[8:])))
            elif date_search1 and kwargs['args'][1] == "~":
                delete_date(date(int(date1_str[:4]), int(date1_str[5:7]), int(date1_str[8:])), "~")
            elif kwargs['args'][0] == "~" and date_search2:
                delete_date("~", date(int(date2_str[:4]), int(date2_str[5:7]), int(date2_str[8:])))
            else:
                temp_list = []
                for name in kwargs['args']:
                    if name in game_name_dict:
                        temp_list.append(name)
                    else:
                        print_color(name + "이란 이름 혹은 닉네임을 가진 게임이 없습니다.", FORE_YELLOW)
                delete(temp_list)
        else:
            temp_list = []
            for name in kwargs['args']:
                if name in game_name_dict:
                    temp_list.append(name)
                else:
                    print_color(name + "이란 이름 혹은 닉네임을 가진 게임이 없습니다.", FORE_YELLOW)
            delete(temp_list)

    elif kwargs['command'] == 'delall':  # delall
        if len(kwargs['args']) == 0:
            print_color("※이 명령어는 백업본을 모두 삭제합니다! Y를 입력하시면 진행합니다.", FORE_YELLOW)
            if input() == "Y":
                try:
                    shutil.rmtree(save_root, False, delete_error)
                except FileException:
                    pass
                print("모든 백업본의 삭제가 완료되었습니다.")
                if not os.path.isdir(save_root):
                    os.makedirs(save_root)
                    os.chmod(save_root, stat.S_IWUSR)

        else:
            raise TooManyArgumentsError

    elif kwargs['command'] == 'option':  # option [showTF=0]
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

    elif kwargs['command'] == 'exit':  # exit
        if len(kwargs['args']) == 0:
            sys.exit()
        else:
            raise TooManyArgumentsError

    else:
        print_color('존재하지 않는 명령어입니다. 도움말을 보려면 help를 치세요.\n', FORE_GRAPEFRUIT)


with open("locations.txt", encoding="utf-8") as gm_loc_file:
    src_list = list(filter(lambda x: len(x) != 1,
                           map(lambda x: x.strip().replace('\\', '/').split("|") if x[0] != "#" else '_',
                               gm_loc_file.readlines())))
    srcs = two_dict(src_list)
    src_list = list(map(lambda x: (x[0].strip(), x[1].strip(), x[2].strip()),
                        list(filter(lambda x: len(x) != 2, src_list))))

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
        command = shlex.split(input(">>"))
        if command:
            try:
                eval_command(command=command[0], args=command[1:])
            except TooManyArgumentsError as msg:
                print_color('인수가 너무 많습니다.', FORE_RED)
                if str(msg):
                    print_color(str(msg), FORE_RED)
                try:
                    print_color(COMMAND_SYNTAX[command[0]], FORE_RED)
                except KeyError:
                    print_color(COMMAND_SYNTAX[command[0] + ' ' + command[1]], FORE_RED)
                print()
            except TooFewArgumentError as msg:
                print_color('인수가 너무 적습니다.', FORE_RED)
                if str(msg):
                    print_color(str(msg), FORE_RED)
                try:
                    print_color(COMMAND_SYNTAX[command[0]], FORE_RED)
                except KeyError:
                    try:
                        print_color(COMMAND_SYNTAX[command[0] + ' ' + command[1]], FORE_RED)
                    except KeyError and IndexError:
                        pass
                print()
            except ArgumentTypeMismatchError as msg:
                print_color('인수가 적절하지 않습니다.', FORE_RED)
                if str(msg):
                    print_color(str(msg), FORE_RED)
                try:
                    print_color(COMMAND_SYNTAX[command[0]], FORE_RED)
                except KeyError:
                    pass
                print()

else:
    while True:
        break
