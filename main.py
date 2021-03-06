import shutil
from time import strftime
from datetime import date
import os
import sys
import re
import ctypes
import shlex
from stat import S_IWUSR
from glob import glob
from time import sleep
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


class DirCmp2(dircmp):
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
            self.subdirs[x] = DirCmp2(a_x, b_x, self.file, self.ignore, self.hide)

    def report(self):
        if self.left_only or self.right_only or self.diff_files or self.funny_files:
            print(file=self.file)

    def report_full_closure(self):
        self.report()
        for sd in self.subdirs.values():
            sd.report_full_closure()


class TwoDict(dict):
    def __init__(self, iterable):
        super().__init__()
        game_name_dict.clear()
        for pair in iterable:
            if len(pair) == 3:
                name, nickname, loc = pair
                name, nickname, loc = name.strip(), nickname.strip(), loc.strip()
                if name in game_name_dict or nickname in game_name_dict:
                    print_color("다음 이름 또는 별칭에 중복이 있습니다: " + name if name in game_name_dict else nickname, FORE_RED)
                    print_color("locations.txt 파일을 열어 중복을 제거한 뒤 다시 실행해 주세요.", FORE_RED)
                    print_color("프로그램이 3초 후에 종료됩니다...", FORE_GRAPEFRUIT)
                    sleep(3)
                    sys.exit()
                game_name_dict[name] = name
                if name.startswith("!"):
                    game_name_dict[name[1:]] = name
                self.__setitem__(name, loc)
                if nickname:
                    game_name_dict[nickname] = name
            elif len(pair) == 2:
                name, loc = pair
                name, loc = name.strip(), loc.strip()
                if name in game_name_dict:
                    print_color("다음 이름에 중복이 있습니다: " + name, FORE_RED)
                    print_color("locations.txt 파일을 열어 중복을 제거한 뒤 다시 실행해 주세요.", FORE_RED)
                    print_color("프로그램이 3초 후에 종료됩니다...", FORE_GRAPEFRUIT)
                    sleep(3)
                    sys.exit()
                game_name_dict[name] = name
                if name.startswith("!"):
                    game_name_dict[name[1:]] = name
                self.__setitem__(name, loc)


class FileSelectDialog(QtWidgets.QWidget):
    def __init__(self, is_a_file: bool):
        super().__init__()
        self.dialog = QFileDialog()
        if not is_a_file:
            self.dialog.setFileMode(QFileDialog.Directory)

    def get_selected_path(self) -> str:
        return self.dialog.selectedFiles()[0]


def save_logic(game_dict: dict):
    succeeded_games.clear()
    failed_games.clear()
    skipped_games.clear()
    same_time_games.clear()
    identical_games.clear()

    for name, src in game_dict.items():
        if name.startswith('!'):
            skipped_games.append(name[1:])
            print_color(name[1:] + "는 저장하지 않습니다. 해당 게임을 건너뜁니다...\n", FORE_GRAPEFRUIT)
            continue

        print(name + " 저장 중...")

        if (not eval(options['SAVE_IDENTICAL_FILE_TOO'])) and name in last_dsts:
            if os.path.isdir(src):
                with TemporaryFile('w+', encoding='utf-8') as temp_file:
                    try:
                        comp_obj = DirCmp2(last_dsts[name], src, temp_file)
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

    print_color("\n모든 게임의 저장이 완료되었습니다.", FORE_CYAN)
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


def save(_name: str, _src: str) -> bool:
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
            os.chmod(save_dst, S_IWUSR)
            shutil.copy(_src, save_dst)
            last_dsts[_name] = save_dst + _src.split('/')[-1]
        else:
            print_color(_name + "의 동일 시각 저장본이 이미 있습니다. 해당 게임을 건너뜁니다...\n", FORE_YELLOW)
            same_time_games.append(_name)
            return False

    succeeded_games.append(_name)
    print_color(_name + " 저장 완료했습니다.\n", FORE_BLUE)
    return True


def delete(game_names: list):
    for name in game_names:
        if os.path.exists(save_root + game_name_dict[name] + "/"):
            try:
                shutil.rmtree(save_root + game_name_dict[name] + "/", False, delete_error)
            except FileException:
                return
        else:
            print_color(name + "게임의 백업본이 존재하지 않습니다.", FORE_YELLOW)
            return

        print_color(name + "의 백업본 삭제 완료했습니다.", FORE_PINK)


def delete_date(*dates: date or str):
    if len(dates) == 1:
        passed_paths = glob(save_root + '**/' + dates[0].isoformat() + "*/", recursive=True)

        if not passed_paths:
            print_color("해당 날짜의 백업본이 존재하지 않습니다.", FORE_MAGENTA)
            return
        for path in passed_paths:
            try:
                shutil.rmtree(path, False, delete_error)
            except FileException:
                return
        print_color(dates[0].isoformat() + "의 백업본을 모두 삭제했습니다.", FORE_PINK)
    else:
        file_dates = glob(save_root + '**/????-??-?? ??-??/', recursive=True)
        file_date_objects = list(map(lambda x: date(int(x[:4]), int(x[5:7]), int(x[8:])),
                                     (map(lambda y: re.search(PATTERN_DATE, y).group(), file_dates))))
        file_date_dict = dict(zip(file_dates, file_date_objects))
        passed_paths = []
        if isinstance(dates[0], date) and isinstance(dates[1], date):  # date date
            for path in file_date_dict.keys():
                if dates[0] <= file_date_dict[path] <= dates[1]:
                    passed_paths.append(path)
        elif isinstance(dates[0], str):  # ~ date
            for path in file_date_dict.keys():
                if file_date_dict[path] <= dates[1]:
                    passed_paths.append(path)
        else:  # date ~
            for path in file_date_dict.keys():
                if dates[0] <= file_date_dict[path]:
                    passed_paths.append(path)

        if not passed_paths:
            print_color("해당 기간 내 백업본이 존재하지 않습니다.", FORE_MAGENTA)
            return
        for path in passed_paths:
            try:
                shutil.rmtree(path, False, delete_error)
            except FileException:
                pass
        print_color("해당 기간 내 모든 백업본을 삭제했습니다.", FORE_PINK)


def delete_path(names: list):
    with open('locations.txt', 'r+', encoding='utf-8') as loc_file:
        for name in names:
            loc_file.seek(0)
            original = loc_file.read()
            target_string = re.search(r'(\A|\n)[ \t!]*' + game_name_dict[name] + r'.+(\Z|\n)', original).group()
            changed_text = original.replace(target_string[1:] if target_string.startswith('\n') else target_string, '')
            loc_file.seek(0)
            loc_file.write(changed_text)
            loc_file.truncate()
            print_color(name + "의 경로 삭제 완료했습니다.", FORE_BLUE)
    return read_loc_file()


def report_result(message: str, game_list: list, color=FORE_WHITE):
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
    print_color("성공적으로 변경되었습니다.\n", FORE_CYAN)
    return read_option_file()


def set_cmd_color(color: int, handle=ctypes.windll.kernel32.GetStdHandle(-11)):
    ctypes.windll.kernel32.SetConsoleTextAttribute(handle, color)


def print_color(_msg: str, color: int, handle=ctypes.windll.kernel32.GetStdHandle(-11)):
    set_cmd_color(color, handle)
    print(_msg)
    set_cmd_color(FORE_WHITE, handle)


def input_color(_msg: str, color: int, handle=ctypes.windll.kernel32.GetStdHandle(-11)):
    set_cmd_color(color, handle)
    print(_msg, end='')
    set_cmd_color(FORE_WHITE, handle)
    return input()


def delete_error(func, path: str, exc_info: tuple):
    if not os.access(path, os.W_OK):
        os.chmod(path, S_IWUSR)
        func(path)
    else:
        print_color("파일을 지우는 도중 에러가 발생했습니다.", FORE_RED)
        print_color(exc_info[1], FORE_RED)
        raise FileException


def eval_command(**kwargs):
    if kwargs['command'] == 'help':  # help [command]
        if len(kwargs['args']) == 0:  # help
            print_color(SYMBOL_MEANING_EXPLANATION, FORE_GRAY)
            for _command in COMMANDS:
                print_color(COMMAND_SYNTAX[_command], FORE_LIME)
                print_color(COMMAND_EXPLANATION_SIMPLE[_command], FORE_SILVER)
                print()
        else:  # help command
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
        if len(kwargs['args']) == 0:  # save
            if os.path.isdir(save_root):
                save_logic(srcs)
            else:
                print_color("저장 경로가 올바르지 않습니다. (이미 존재하는 폴더여야 합니다.)\n", FORE_RED)
        else:  # save game_name+
            temp_dict = {}
            for name in kwargs['args']:
                if name not in game_name_dict:
                    print_color(name + GAME_NONEXISTENT + "해당 게임을 건너뜁니다...\n", FORE_YELLOW)
                else:
                    temp_dict[game_name_dict[name]] = srcs[game_name_dict[name]]
            save_logic(temp_dict)

    elif kwargs['command'] == 'path':
        if kwargs['args']:
            if kwargs['args'][0] == 'add':  # path add <game_name> [isAFile=0] [nickname]
                with open('locations.txt', 'a', encoding='utf-8') as loc_file:
                    if len(kwargs['args']) == 1:
                        raise TooFewArgumentError
                    elif len(kwargs['args']) == 2:  # path add game_name
                        file_obj = FileSelectDialog(False)
                        if file_obj.dialog.exec_():
                            loc_file.write('\n' + kwargs['args'][1] + '||' + file_obj.get_selected_path())
                        else:
                            return
                    elif len(kwargs['args']) == 3:  # path add game_name isAFile
                        if kwargs['args'][2] == '0':
                            file_obj = FileSelectDialog(False)
                        elif kwargs['args'][2] == '1':
                            file_obj = FileSelectDialog(True)
                        else:
                            raise ArgumentTypeMismatchError("0과 1 중 하나를 입력해 주세요.")

                        if file_obj.dialog.exec_():
                            loc_file.write('\n' + kwargs['args'][1] + '||' + file_obj.get_selected_path())
                        else:
                            return
                    elif len(kwargs['args']) == 4:  # path add game_name isAFile nickname
                        if kwargs['args'][2] == '0':
                            file_obj = FileSelectDialog(False)
                        elif kwargs['args'][2] == '1':
                            file_obj = FileSelectDialog(True)
                        else:
                            raise ArgumentTypeMismatchError("0과 1 중 하나를 입력해 주세요.")

                        if file_obj.dialog.exec_():
                            loc_file.write('\n' + kwargs['args'][1] + '|' +
                                           kwargs['args'][3] + '|' + file_obj.get_selected_path())
                        else:
                            return
                    else:
                        raise TooManyArgumentsError
                print_color(kwargs['args'][1] + ' 추가되었습니다.', FORE_CYAN)
                return read_loc_file()

            elif kwargs['args'][0] == 'edit':  # path edit <game_name|'dst'> ['name'|{'path'}|'nickname'|'toggle']
                if len(kwargs['args']) == 1:
                    raise TooFewArgumentError
                elif len(kwargs['args']) == 2:
                    with open('locations.txt', 'r+', encoding='utf-8') as loc_file:
                        original = loc_file.read()
                        pat = r'(\A|\n)[ \t!]*SaveLocation[^\n\r]+' if kwargs['args'][1] == 'dst' else \
                              r'(\A|\n)[ \t!]*' + game_name_dict[kwargs['args'][1]] + r'[^\n\r]+'
                        target_string = re.search(pat, original).group()[1:] \
                            if re.search(pat, original).group().startswith('\n') else re.search(pat, original).group()
                        target_strings = target_string.split("|")
                        alter_strings = target_strings.copy()
                        if kwargs['args'][1] == 'dst':  # path edit dst
                            file_obj = FileSelectDialog(False)
                            if file_obj.dialog.exec_():
                                alter_strings[1] = file_obj.get_selected_path()
                            else:
                                return
                        else:  # path edit game_name
                            if kwargs['args'][1] not in game_name_dict:
                                print_color(kwargs['args'][1] + GAME_NONEXISTENT, FORE_YELLOW)
                                return
                            file_obj = FileSelectDialog(False if os.path.isdir(srcs[game_name_dict[kwargs['args'][1]]])
                                                        else True)
                            if file_obj.dialog.exec_():
                                alter_strings[2] = file_obj.get_selected_path()
                            else:
                                return
                        loc_file.seek(0)
                        loc_file.write(original.replace("|".join(target_strings), "|".join(alter_strings)))
                        loc_file.truncate()
                    print_color('변경이 완료되었습니다.', FORE_CYAN)
                    return read_loc_file()

                elif len(kwargs['args']) == 3:
                    if kwargs['args'][1] == 'dst':
                        if kwargs['args'][2] == "path":  # path edit dst path
                            return eval_command(command='path', args=['edit', 'dst'])
                        else:
                            raise ArgumentTypeMismatchError('백업 경로는 경로 변경만 가능합니다.')
                    else:
                        if kwargs['args'][1] not in game_name_dict:
                            print_color(kwargs['args'][1] + GAME_NONEXISTENT, FORE_YELLOW)
                            return

                        with open('locations.txt', 'r+', encoding='utf-8') as loc_file:
                            original = loc_file.read()
                            pat = r'(\A|\n)[ \t!]*' + game_name_dict[kwargs['args'][1]] + r'[^\n\r]+'
                            target_string = re.search(pat, original).group()[1:] \
                                if re.search(pat, original).group().startswith('\n') \
                                else re.search(pat, original).group()
                            target_strings = target_string.split("|")
                            alter_strings = target_strings.copy()
                            if kwargs['args'][2] == 'name':  # path edit game_name name
                                alter_strings[0] = input(game_name_dict[kwargs['args'][1]] + '의 새 이름을 입력하세요: ')
                            elif kwargs['args'][2] == 'path':  # path edit game_name path
                                return eval_command(command='path', args=['edit', kwargs['args'][1]])
                            elif kwargs['args'][2] == 'nickname':  # path edit game_name nickname
                                alter_strings[1] = input(game_name_dict[kwargs['args'][1]] + "의 새 별칭을 입력하세요: ")
                            elif kwargs['args'][2] == 'toggle':  # path edit game_name toggle
                                alter_strings[0] = alter_strings[0][1:] if alter_strings[0].startswith("!") \
                                    else "!" + alter_strings[0]
                                print(game_name_dict[kwargs['args'][1]] + "는 이제",
                                      "저장되지 않습니다." if alter_strings[0].startswith('!') else "저장됩니다.")
                            else:
                                raise ArgumentTypeMismatchError('name, path, nickname, toggle 중 하나를 입력해 주세요.')
                            loc_file.seek(0)
                            loc_file.write(original.replace("|".join(target_strings), "|".join(alter_strings)))
                            loc_file.truncate()
                        print_color("변경이 완료되었습니다.", FORE_CYAN)
                        return read_loc_file()

                else:
                    raise TooManyArgumentsError

            elif kwargs['args'][0] == 'show':  # path show [game_name+|'dst']
                if len(kwargs['args']) == 1:  # path show
                    print_color('{0:30}{1:15}{2}\n'.format("NAME", "NICKNAME", "LOCATION"), FORE_GREEN)
                    for name, nickname, src in src_list:
                        print(f'{name:30}{nickname:15}{src}')
                elif len(kwargs['args']) == 2:
                    if kwargs['args'][1] == 'dst':  # path show dst
                        print(f'Save Location: {save_root}')
                    else:  # path show game_name
                        name = kwargs['args'][1]
                        if name in game_name_dict:
                            print(f'{name}: {srcs[game_name_dict[name]]}')
                        else:
                            print_color(name + GAME_NONEXISTENT, FORE_YELLOW)
                else:  # path show game_name+
                    print_color('{0:30}{1}\n'.format("GAME", "LOCATION"), FORE_GREEN)
                    for name in kwargs['args'][1:]:
                        if name in game_name_dict:
                            print(f'{name:30}{srcs[game_name_dict[name]]}')
                        else:
                            print_color(name + GAME_NONEXISTENT, FORE_YELLOW)

            elif kwargs['args'][0] == 'del':  # path del <game_name+>
                if len(kwargs['args']) == 1:
                    raise TooFewArgumentError
                else:  # path del game_name+
                    temp_list = []
                    for name in kwargs['args'][1:]:
                        if name in game_name_dict:
                            temp_list.append(name)
                        else:
                            print_color(name + '이란 이름 혹은 닉네임을 가진 게임이 없습니다.', FORE_YELLOW)
                    return delete_path(temp_list)
            else:
                raise ArgumentTypeMismatchError('add, edit, show, del 중 하나를 입력해 주세요.')

        else:
            raise TooFewArgumentError('add, edit, show, del 중 하나를 추가로 입력해 주세요.')

    elif kwargs['command'] == 'del':  # del <game_name+|date [date]>
        if len(kwargs['args']) == 0:
            raise TooFewArgumentError('전체 삭제는 delall을 이용하세요.')
        elif len(kwargs['args']) == 1:
            date_search = re.search(PATTERN_DATE, kwargs['args'][0])
            if date_search:  # del date
                date_str = date_search.group()
                try:
                    delete_date(date(int(date_str[:4]), int(date_str[5:7]), int(date_str[8:])))
                except ValueError:
                    print_color("올바른 날짜를 입력해 주세요.", FORE_YELLOW)
            else:  # del game_name
                if kwargs['args'][0] in game_name_dict:
                    delete(kwargs['args'])
                else:
                    print_color(kwargs['args'][0] + GAME_NONEXISTENT, FORE_YELLOW)
        elif len(kwargs['args']) == 2:
            date_search1 = re.search(PATTERN_DATE, kwargs['args'][0])
            date_search2 = re.search(PATTERN_DATE, kwargs['args'][1])
            date1_str = date_search1.group() if date_search1 else None
            date2_str = date_search2.group() if date_search2 else None
            if date_search1 and date_search2:  # del date date
                delete_date(date(int(date1_str[:4]), int(date1_str[5:7]), int(date1_str[8:])),
                            date(int(date2_str[:4]), int(date2_str[5:7]), int(date2_str[8:])))
            elif date_search1 and kwargs['args'][1] == "~":
                delete_date(date(int(date1_str[:4]), int(date1_str[5:7]), int(date1_str[8:])), "~")
            elif kwargs['args'][0] == "~" and date_search2:
                delete_date("~", date(int(date2_str[:4]), int(date2_str[5:7]), int(date2_str[8:])))
            else:  # del game_name game_name
                temp_list = []
                for name in kwargs['args']:
                    if name in game_name_dict:
                        temp_list.append(name)
                    else:
                        print_color(name + GAME_NONEXISTENT, FORE_YELLOW)
                delete(temp_list)
        else:  # del game_name+
            temp_list = []
            for name in kwargs['args']:
                if name in game_name_dict:
                    temp_list.append(name)
                else:
                    print_color(name + GAME_NONEXISTENT, FORE_YELLOW)
            delete(temp_list)

    elif kwargs['command'] == 'delall':  # delall
        if len(kwargs['args']) == 0:  # delall
            print_color("※이 명령어는 백업본을 모두 삭제합니다! Y를 입력하시면 진행합니다.", FORE_YELLOW)
            if input() == "Y":
                try:
                    shutil.rmtree(save_root, False, delete_error)
                except FileException:
                    pass
                print_color("모든 백업본의 삭제가 완료되었습니다.", FORE_PINK)
                if not os.path.isdir(save_root):
                    os.makedirs(save_root)
                    os.chmod(save_root, S_IWUSR)

        else:
            raise TooManyArgumentsError

    elif kwargs['command'] == 'option':  # option [showTF=0]
        if len(kwargs['args']) == 0:  # option
            return edit_options()
        elif len(kwargs['args']) == 1:  # option showTF
            if kwargs['args'][0] == '0':
                return edit_options()
            elif kwargs['args'][0] == '1':
                return edit_options(True)
            else:
                raise ArgumentTypeMismatchError('0과 1 중 하나를 입력해 주세요.')
        else:
            raise TooManyArgumentsError

    elif kwargs['command'] == 'exit':  # exit
        if len(kwargs['args']) == 0:  # exit
            sys.exit()
        else:
            raise TooManyArgumentsError

    else:
        print_color('존재하지 않는 명령어입니다. 도움말을 보려면 help를 치세요.\n', FORE_GRAPEFRUIT)


def read_loc_file():
    with open("locations.txt", encoding="utf-8") as gm_loc_file:
        _src_list = list(filter(lambda x: len(x) != 1,
                                map(lambda x: x.strip().replace('\\', '/').split("|") if x[0] != "#" else '_',
                                    gm_loc_file.readlines())))
        _srcs = TwoDict(_src_list)
        _src_list = list(map(lambda x: (x[0].strip(), x[1].strip(), x[2].strip()),
                             list(filter(lambda x: len(x) != 2, _src_list))))
    return _srcs, _src_list


def read_last_file():
    with open("last_saved.txt", 'a+', encoding='utf-8') as last_saved_file:
        last_saved_file.seek(0)
        _last_dsts = dict(filter(lambda x: len(x) != 1,
                                 map(lambda x: x.strip().split("|"),
                                     last_saved_file.readlines())))
    return _last_dsts


def read_option_file():
    with open("options.txt", encoding='utf-8') as _option_file:
        _options = dict(filter(lambda x: len(x) != 1,
                               map(lambda x: x.strip().split(" = ") if x[0] != "#" else '_',
                                   _option_file.readlines())))
    return _options


srcs, src_list = read_loc_file()
last_dsts = read_last_file()
options = read_option_file()

save_root = srcs['SaveLocation'] if srcs['SaveLocation'].endswith('/') else srcs['SaveLocation'] + '/'
del srcs['SaveLocation']

app = QtWidgets.QApplication(sys.argv)

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
                result = eval_command(command=command[0], args=command[1:])
                if len(result) == 2:
                    srcs, src_list = result
                else:
                    options = result
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
            except TypeError:
                pass

else:
    while True:
        answer = input_color(QUERY_MAIN, FORE_LIME)
        if answer.isnumeric():
            answer = int(answer)
            if answer == 0:  # exit
                sys.exit()
                
            elif answer == 1:  # save [game_name+]
                answer_1 = input_color(QUERY_1_SAVE, FORE_IVORY)
                if answer_1 == "1":  # save
                    eval_command(command='save', args=[])
                elif answer_1 == '2':  # save game_name+
                    eval_command(command='save', args=shlex.split(input_color(QUERY_GAME_NAMES, FORE_CYAN)))
                                    
            elif answer == 2:  # path add <game_name> [isAFile=0] [nickname]
                answer_name = input_color("\n게임 이름을 입력하세요: ", FORE_CYAN)
                if answer_name not in game_name_dict:
                    print_color(answer_name + GAME_NONEXISTENT, FORE_YELLOW)
                    continue
                answer_2 = input_color(QUERY_2_PATH_ADD, FORE_IVORY)
                if answer_2 == '1':  # path add game_name
                    eval_command(command='path', args=['add', answer_name])
                elif answer_2 == '2':  # path add game_name 0 nickname
                    eval_command(command='path', args=['add', answer_name, '0',
                                                       input_color("\n닉네임을 입력하세요: ", FORE_CYAN)])
                elif answer_2 == '3':  # path add game_name 1
                    eval_command(command='path', args=['add', answer_name, '1'])
                elif answer_2 == '4':  # path add game_name 1 nickname
                    eval_command(command='path', args=['add', answer_name, '1',
                                                       input_color("\n닉네임을 입력하세요: ", FORE_CYAN)])
                
            elif answer == 3:  # path edit <game_name|"dst"> ["name"|{"path"}|"nickname"|"toggle"]
                answer_name = input_color("\n게임 이름을 입력하세요: ", FORE_CYAN)
                if answer_name not in game_name_dict:
                    print_color(answer_name + GAME_NONEXISTENT, FORE_YELLOW)
                    continue
                answer_3 = input_color(QUERY_3_PATH_EDIT, FORE_IVORY)
                if answer_3 == '1':  # path edit game_name name
                    eval_command(command='path', args=['edit', answer_name, 'name'])
                elif answer_3 == '2':  # path edit game_name
                    eval_command(command='path', args=['edit', answer_name])
                elif answer_3 == '3':  # path edit game_name nickname
                    eval_command(command='path', args=['edit', answer_name, 'nickname'])
                elif answer_3 == '4':  # path edit game_name toggle
                    eval_command(command='path', args=['edit', answer_name, 'toggle'])
                elif answer_3 == '5':  # path edit dst
                    eval_command(command='path', args=['edit', 'dst'])
                
            elif answer == 4:  # path show [game_name+|"dst"]
                answer_4 = input_color(QUERY_4_PATH_SHOW, FORE_IVORY)
                if answer_4 == '1':  # path show
                    eval_command(command='path', args=['show'])
                elif answer_4 == '2':  # path show game_name+
                    eval_command(command='path', args=shlex.split(input_color(QUERY_GAME_NAMES, FORE_CYAN)))
                elif answer_4 == '3':  # path show dst
                    eval_command(command='path', args=['show', 'dst'])
                                
            elif answer == 5:  # path del <game_name+>
                eval_command(command='path', args=['del'] + shlex.split(input_color(QUERY_GAME_NAMES, FORE_CYAN)))
                
            elif answer == 6:  # del <game_name+|date [date]>
                answer_6 = input_color(QUERY_6_DEL, FORE_IVORY)
                if answer_6 == '1':  # del game_name+
                    eval_command(command='del', args=shlex.split(input_color(QUERY_GAME_NAMES, FORE_CYAN)))
                elif answer_6 == '2':  # del date
                    while True:
                        answer_6_2 = re.search(r'^' + PATTERN_DATE + r'$', input("YYYY-MM-DD의 형식으로 입력해 주세요: "))
                        if answer_6_2:
                            eval_command(command='del', args=[answer_6_2.group()])
                            break
                        else:
                            print_color("올바른 날짜를 입력해 주세요.", FORE_GRAPEFRUIT)
                elif answer_6 == '3':  # del date date
                    while True:
                        answer_6_3 = input("YYYY-MM-DD YYYY-MM-DD의 형식으로 입력해 주세요.\n"
                                           "~까지, ~부터를 나타내기 위해 각각 전자와 후자를 ~로 대체할 수 있습니다: ")
                        match_to = re.search(r'^~ ' + PATTERN_DATE + r'$', answer_6_3)
                        match_period = re.search(r'^' + PATTERN_DATE + ' ' + PATTERN_DATE + r'$', answer_6_3)
                        match_from = re.search(r'^' + PATTERN_DATE + r' ~$', answer_6_3)
                        if match_to or match_period or match_from:
                            eval_command(command='del', args=answer_6_3.split())
                            break
                        else:
                            print_color("올바른 기간을 입력해 주세요.", FORE_GRAPEFRUIT)
                                
            elif answer == 7:  # delall
                eval_command(command='delall', args=[])
                
            elif answer == 8:  # option [showTF=0]
                answer_8 = input_color(QUERY_8_OPTION, FORE_IVORY)
                if answer_8 == "1" or answer_8 == "2":  # option showTF
                    eval_command(command='option', args=[str(int(answer_8) - 1)])
                                    
            else:
                print_color("올바른 번호를 입력해 주세요.", FORE_GRAPEFRUIT)
        else:
            print_color("올바른 번호를 입력해 주세요.", FORE_GRAPEFRUIT)
