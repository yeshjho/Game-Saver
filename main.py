import shutil
from time import strftime
import os
from filecmp import dircmp, cmp
from tempfile import TemporaryFile
from PyQt5 import QtWidgets
from PyQt5.QtWidgets import QFileDialog


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
    for name, src in zip(srcs.keys(), srcs.values()):
        name = name.strip()
        src = src.strip()

        if name.startswith('!'):
            skipped_games.append(name[:1])
            print(name[1:] + "는 저장하지 않습니다. 해당 게임을 건너뜁니다...\n")
            continue

        print(name + " 저장 중...")

        if (not eval(options['SAVE_IDENTICAL_FILE_TOO'])) and name in last_dsts:
            is_identical = False
            if os.path.isdir(src):
                with TemporaryFile('w+', encoding='utf-8') as temp_file:
                    try:
                        comp_obj = dircmp2(last_dsts[name], src, temp_file)
                        comp_obj.report_full_closure()
                        temp_file.seek(0)
                        is_identical = False if temp_file.read() else True
                        if is_identical:
                            identical_games.append(name)
                            print(name + "는 최신 저장본과 동일합니다. 해당 게임을 건너뜁니다...\n")
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
                        print(name + "는 최신 저장본과 동일합니다. 해당 게임을 건너뜁니다...\n")
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
        report_result("\n새로 저장한 게임들:", succeeded_games)

        with open('last_saved.txt', 'w', encoding='utf-8') as _last_saved_file:
            for _key in last_dsts:
                print(_key + '|' + last_dsts[_key], file=_last_saved_file)
    if failed_games:
        report_result("\n저장에 실패한 게임들:", failed_games)
    if eval(options['VERBOSE_REPORT']):
        if skipped_games:
            report_result("\n사용자에 의해 건너뛴 게임들:", skipped_games)
        if same_time_games:
            report_result("\n동일 시각 저장본이 존재해 건너뛴 게임들:", same_time_games)
        if identical_games:
            report_result("\n최신 저장본과 동일해 건너뛴 게임들:", identical_games)


def save(_name, _src):
    save_dst = save_root + _name + "/" + strftime("%Y-%m-%d %H-%M" + '/')
    try:
        shutil.copytree(_src, save_dst)
        if os.path.isdir(_src):
            last_dsts[_name] = save_dst
        else:
            last_dsts[_name] = save_dst + _src.split('/')[-1]
    except FileExistsError:
        print(_name + "의 동일 시각 저장본이 이미 있습니다. 해당 게임을 건너뜁니다...\n")
        same_time_games.append(_name)
        return False
    except FileNotFoundError:
        print(_name + "의 " + _src + " 경로가 올바르지 않거나 파일이 존재하지 않습니다. 저장에 실패했습니다.\n")
        failed_games.append(_name)
        return False
    except NotADirectoryError:
        if not os.path.exists(save_dst):
            os.makedirs(save_dst)
            shutil.copy(_src, save_dst)
            last_dsts[_name] = save_dst + _src.split('/')[-1]
        else:
            print(_name + "의 동일 시각 저장본이 이미 있습니다. 해당 게임을 건너뜁니다...\n")
            same_time_games.append(_name)
            return False

    succeeded_games.append(_name)
    print(_name + " 저장 완료했습니다.\n")
    return True


def report_result(message, game_list):
    print(message)
    for _game in sorted(game_list):
        print('\t' + _game)


with open("locations.txt", 'a+', encoding="utf-8") as gm_loc_file:
    gm_loc_file.seek(0)
    srcs = dict(filter(lambda x: len(x) != 1,
                       map(lambda x: x.strip().replace('\\', '/').split("|") if x[0] != "#" else '_',
                           gm_loc_file.readlines())))

with open("last_saved.txt", 'a+', encoding='utf-8') as last_saved_file:
    last_saved_file.seek(0)
    last_dsts = dict(filter(lambda x: len(x) != 1,
                            map(lambda x: x.strip().split("|"),
                                last_saved_file.readlines())))

with open("options.txt", 'a+', encoding='utf-8') as option_file:
    option_file.seek(0)
    options = dict(filter(lambda x: len(x) != 1,
                          map(lambda x: x.strip().split(" = ") if x[0] != "#" else '_',
                              option_file.readlines())))

save_root = srcs['SaveLocation'] if srcs['SaveLocation'].endswith('/') else srcs['SaveLocation'] + '/'
del srcs['SaveLocation']

if __name__ == "__main__":
    if options['USE_COMMAND'] == '-1':
        answer = input("명령어로 프로그램을 조작하시겠습니까? 이 옵션은 나중에 변경할 수 있습니다. (Y/N): ")
        while answer != 'Y' and answer != 'N':
            answer = input("Y/N 중 하나를 입력해 주세요: ")
        options['USER_COMMAND'] = '1' if answer == 'Y' else '0'
        with open('options.txt', 'r+', encoding='utf-8') as option_file:
            contain = option_file.read().replace('-1', options['USER_COMMAND'])
            option_file.seek(0)
            option_file.write(contain)

    if eval(options['USER_COMMAND']):
        while True:
            break
    else:
        while True:
            break

    '''
    if os.path.isdir(save_root):
        save_logic()
    else:
        print("저장 경로가 올바르지 않습니다. (이미 존재하는 폴더여야 합니다.)")
    '''

input("\n종료하려면 엔터 키를 누르세요.")
