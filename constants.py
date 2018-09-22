BLACK = 0

FORE_BLUE = 1
FORE_GREEN = 2
FORE_CYAN = 3
FORE_RED = 4
FORE_MAGENTA = 5
FORE_YELLOW = 6
FORE_SILVER = 7
FORE_GRAY = 8
FORE_PURPLE = 9
FORE_LIME = 10
FORE_SKY = 11
FORE_GRAPEFRUIT = 12
FORE_PINK = 13
FORE_IVORY = 14
FORE_WHITE = 15

BACK_BLUE = 1 * 16
BACK_GREEN = 2 * 16
BACK_CYAN = 3 * 16
BACK_RED = 4 * 16
BACK_MAGENTA = 5 * 16
BACK_YELLOW = 6 * 16
BACK_SILVER = 7 * 16
BACK_GRAY = 8 * 16
BACK_PURPLE = 9 * 16
BACK_LIME = 10 * 16
BACK_SKY = 11 * 16
BACK_GRAPEFRUIT = 12 * 16
BACK_PINK = 13 * 16
BACK_IVORY = 14 * 16
BACK_WHITE = 15 * 16


COMMANDS = ('help', 'save', 'path add', 'path edit', 'path show', 'path del', 'del', 'delall', 'option', 'exit')

COMMAND_SYNTAX = {'help': 'help [command]',
                  'save': 'save [game_name+]',
                  'path add': 'path add <game_name> [isAFile=0] [nickname]',
                  'path edit': 'path edit <game_name|"dst"> ["name"|{"path"}|"nickname"|"toggle"]',
                  'path show': 'path show [game_name+|"dst"]',
                  'path del': 'path del <game_name+>',
                  'del': 'del <game_name|date [date]> [trackHistory=0]',
                  'delall': 'delall [trackHistory=0]',
                  'option': 'option [showTF=0]',
                  'exit': 'exit'}

COMMAND_EXPLANATION_SIMPLE = {'help': '도움말을 봅니다.\n'
                                      'command가 주어지면 해당 명령어에 관한 자세한 설명을 봅니다.',
                              'save': '게임 파일들을 백업합니다.',
                              'path add': '세이브 파일 경로를 추가합니다.',
                              'path edit': '세이브 파일 경로를 수정합니다.',
                              'path show': '세이브 파일 경로를 보여줍니다.',
                              'path del': '저장된 세이브 파일 경로를 삭제합니다.',
                              'del': '저장된 백업본을 삭제합니다.',
                              'delall': '이때까지의 모든 백업본을 삭제합니다.',
                              'option': '옵션 값을 보고 수정합니다.',
                              'exit': '프로그램을 종료합니다.'}

COMMAND_EXPLANATION_DETAILED = {'help': '도움말을 봅니다.\n'
                                        'command가 주어지면 해당 명령어에 관한 자세한 설명을 봅니다.',
                                'save': '게임 파일들을 저장합니다.\n'
                                        'game_name이 한 개 이상 주어지면 해당 이름의 게임들만 저장합니다.',
                                'path add': 'game_name의 이름을 가진 게임의 세이브 파일 경로를 추가합니다.\n'
                                            'isAFile은 세이브 파일의 경로가 폴더인지 파일인지를 구분합니다.\n'
                                            'nickname이 주어지면 별칭 또한 저장합니다.',
                                'path edit': 'game_name의 이름 또는 별칭을 가진 게임의 세이브 파일 경로를 수정합니다.\n'
                                             'dst가 주어지면 백업 경로를 수정합니다.\n'
                                             'game_name이 주어지면 옵션이 올 수 있습니다. 옵션이 주어지면 각각 경로 대신 이름, 경로, 별칭, 저장 여부를 '
                                             '수정합니다.',
                                'path show': '모든 게임들의 세이브 파일 경로를 보여줍니다.\n'
                                             'game_name이 주어지면 해당 게임들의 경로만 보여줍니다.\n'
                                             'dst가 주어지면 백업 경로를 보여줍니다.',
                                'path del': 'game_name의 이름 또는 별칭을 가진 게임들의 저장된 세이브 파일 경로를 삭제합니다.',
                                'del': '저장된 백업본을 삭제합니다.\n'
                                       'game_name이 주어지면 해당 이름 또는 별칭을 가진 게임들의 백업본만 삭제합니다.\n'
                                       'date가 1개 주어지면 해당 날짜의 백업본을 삭제합니다.\n'
                                       'date가 2개 주어지면 해당 날짜 사이의 모든 백업본을 삭제합니다.\n'
                                       'date는 YYYY.MM.DD의 형태로 작성합니다.\n'
                                       'trackHistory가 1이면 백업 경로가 바뀐 적이 있어도 이전 경로의 백업본까지 추적해 삭제합니다.',
                                'delall': '이때까지의 모든 백업본을 삭제합니다.\n'
                                          'trackHistory가 1이면 백업 경로가 바뀐 적이 있어도 이전 경로의 백업본까지 추적해 삭제합니다.',
                                'option': '옵션 값을 보고 수정합니다.\n'
                                          'showTF가 1이면 1/0 대신 True/False 형식으로 표시합니다.',
                                'exit': '프로그램을 종료합니다.'}

SYMBOL_MEANING_EXPLANATION = '''~사용한 기호들의 의미~

[]\t선택적으로 입력
<>\t필수적으로 입력
|\t또는 (하나 선택)
+\t한 개 이상
"###"\t###를 그대로 입력
=, {}\t기본값

'''
