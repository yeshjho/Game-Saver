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


COMMANDS = ('help', 'save', 'path add', 'path edit', 'path show', 'path del', 'get', 'del', 'delall', 'option', 'exit')

COMMAND_SYNTAX = {'help': 'help [command]',
                  'save': 'save [game_name+]',
                  'path add': 'path add <game_name> [isAFile=0] [nickname]',
                  'path edit': 'path edit <game_name|"dst"> ["name"|{"path"}|"nickname"|"toggle"]',
                  'path show': 'path show [game_name+|"dst"]',
                  'path del': 'path del <game_name+>',
                  'get': 'get <"steam"> [getOnline=0]',
                  'del': 'del <game_name+|date [date]>',
                  'delall': 'delall',
                  'option': 'option [showTF=0]',
                  'exit': 'exit'}

COMMAND_EXPLANATION_SIMPLE = {'help': '도움말을 봅니다.\n'
                                      'command가 주어지면 해당 명령어에 관한 자세한 설명을 봅니다.',
                              'save': '게임 파일들을 백업합니다.',
                              'path add': '세이브 파일 경로를 추가합니다.',
                              'path edit': '세이브 파일 경로를 수정합니다.',
                              'path show': '세이브 파일 경로를 보여줍니다.',
                              'path del': '저장된 세이브 파일 경로를 삭제합니다.',
                              'get': '세이브 파일 경로를 감지해 저장합니다.',
                              'del': '저장된 백업본을 삭제합니다.',
                              'delall': '이때까지의 모든 백업본을 삭제합니다.',
                              'option': '옵션 값을 보고 수정합니다.',
                              'exit': '프로그램을 종료합니다.'}

COMMAND_EXPLANATION_DETAILED = {'help': '도움말을 봅니다.\n'
                                        'command가 주어지면 해당 명령어에 관한 자세한 설명을 봅니다.',
                                'save': '게임 파일들을 저장합니다.\n'
                                        'game_name이 한 개 이상 주어지면 해당 이름 또는 별칭의 게임들만 저장합니다.',
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
                                'get': '현재 컴퓨터에 저장돼 있는 게임을 감지해 경로를 자동으로 저장합니다.\n'
                                       '이 작업은 인터넷 연결을 필요로 합니다.\n'
                                       '첫 번째 옵션에 해당되는 게임이 아니면 감지하지 못합니다.\n'
                                       'steam=스팀\n',
                                'del': '저장된 백업본을 삭제합니다.\n'
                                       'game_name이 주어지면 해당 이름 또는 별칭을 가진 게임들의 백업본만 삭제합니다.\n'
                                       'date가 1개 주어지면 해당 날짜의 백업본을 삭제합니다.\n'
                                       'date가 2개 주어지면 해당 날짜 사이의 모든 백업본을 삭제합니다.\n'
                                       'date는 YYYY-MM-DD의 형태로 작성합니다.\n'
                                       '"~ date"의 형태는 ~까지를, "date ~"의 형태는 ~부터를 표현할 수 있습니다.',
                                'delall': '현재 백업 파일이 저장되는 경로에 있는 모든 백업본을 삭제합니다.',
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

게임 이름 또는 별칭에 공백이 들어간다면 명령어에 입력할 때 따옴표("")로 묶어주세요.

'''

PATTERN_DATE = r'[123456789][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]'

QUERY_MAIN = """
1. 게임 저장
2. 세이브 파일 경로 추가
3. 세이브 파일 경로 수정
4. 세이브 파일 경로 확인
5. 세이브 파일 경로 삭제
6. 저장된 백업본 삭제
7. 저장된 백업본 모두 삭제
8. 옵션 확인 및 변경
9. 세이브 파일 경로 감지

0: 프로그램 종료
>>> """

QUERY_1_SAVE = """
1. 모든 게임 저장
2. 게임 지정 저장

다른 모든 문자: 돌아가기
>>> """

QUERY_2_PATH_ADD = """
1. 폴더 지정
2. 폴더 지정 및 닉네임 지정
3. 파일 지정
4. 파일 지정 및 닉네임 지정

다른 모든 문자: 돌아가기
>>> """

QUERY_3_PATH_EDIT = """
1. 게임 이름 변경
2. 게임 세이브 파일 경로 변경
3. 게임 별칭 변경
4. 게임 저장 여부 변경
5. 백업본 저장 경로 변경

다른 모든 문자: 돌아가기
>>> """

QUERY_4_PATH_SHOW = """
1. 모든 경로 확인
2. 게임 지정 확인
3. 백업본 저장 경로 확인

다른 모든 문자: 돌아가기
>>> """

QUERY_6_DEL = """
1. 게임 지정 삭제
2. 날짜 지정 삭제
3. 기간 지정 삭제

다른 모든 문자: 돌아가기
>>> """

QUERY_8_OPTION = """
1. 0/1 형태로 출력
2. False/True 형태로 출력

다른 모든 문자: 돌아가기
>>> """

QUERY_9_GET = """
1. 스팀 게임

다른 모든 문자: 돌아가기
>>> """

QUERY_GAME_NAMES = '게임 이름 또는 별칭을 입력하세요. 공백으로 구분하며, 게임 이름에 공백이 포함되면 ""로 감싸주세요.\n>>> '

GAME_NONEXISTENT = "이란 이름 혹은 별칭을 가진 게임이 없습니다."

QUERY_STEAM_ID = """
다음 중 하나를 입력해 주세요.
1. 스팀 프로필 주소 전체
2. 사용자 지정 URL에서 설정한 ID
3. 스팀 프로필 주소 끝에 있는 숫자
>>> """
