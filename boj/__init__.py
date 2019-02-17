"""
module boj

a module for logging in, submitting, getting stats from BOJ
"""

import argparse
import configparser
import getpass
import logging
import logging.handlers
import os
import pickle
import re
import requests

from bs4 import BeautifulSoup as bs
from colorama import init, Fore, Back, Style
from xdg import (XDG_CONFIG_HOME, XDG_DATA_HOME)

init()

__version__ = '1.1.3'

data_dir = XDG_DATA_HOME + '/boj-tool'
config_dir = XDG_CONFIG_HOME + '/boj-tool'
boj_url = 'https://www.acmicpc.net'
cookiefile_path = data_dir + '/cookiefile'
configfile_path = config_dir + '/config'
sess = requests.Session()

logger = logging.getLogger('boj-tool')
streamHandler = logging.StreamHandler()
logger.addHandler(streamHandler)
config = configparser.ConfigParser()


def initialize():
    """
    function initialize -- initialize boj-tool

    This function loads cookie/config from cookifile/config file if the file
    exists.
    """
    if not os.path.exists(data_dir):
        logger.debug('Creating directory for cookiefile...')
        os.makedirs(data_dir)
        logger.debug('Created directory for cookiefile')
    if os.path.isfile(configfile_path):
        logger.debug('Config file found')
        config.read(configfile_path)


def auth_user(username, password):
    """
    function auth_user -- authenticate user to BOJ

    params:
    username: str -- the user's name to log in
    password: str -- the password used in authentication
    """
    data = {'login_user_id': username,
            'login_password': password,
            'auto_login': 'on'}
    logger.info('Authenticating...')
    logger.debug('Username: {0}, Password: {1}'.format(username,
                                                       '*' * len(password)))
    sess.post(boj_url + '/signin', data=data)


def check_login():
    """
    function check_login -- checks if the user is logged in

    returns True if logged in, and False if not logged in.
    """
    soup = bs(sess.get(boj_url).text, 'html.parser')
    return soup.find('a', {'class': 'username'}) is not None


def save_cookie(session):
    """
    function save_cookie -- saves cookie to cookiefile

    this function saves cookiefile to data_dir, which is
    $XDG_DATA_HOME/boj-tool.

    params:
    session: request.Session -- the session object to extract cookie from
    """
    with open(cookiefile_path, 'wb') as f:
        logger.debug('Saving cookie to {0}...'.format(cookiefile_path))
        pickle.dump(session.cookies, f)
        logger.info('Saved cookie to {0}'.format(cookiefile_path))


def load_cookie():
    """
    function load_cookie -- loads cookie to cookiefile

    This function loads cookiefile to global session object if cookiefile is
    found. If not, the function calls login and asks user username and
    password.
    """
    if os.path.isfile(data_dir + '/cookiefile'):
        logger.debug('Cookiefile found. Loading...')
        with open(data_dir + '/cookiefile', 'rb') as f:
            sess.cookies.update(pickle.load(f))
        logger.info('Loaded cookiefile')
    else:
        logger.error('Cookiefile not found. Logging in...')
        login()


def login():
    """
    function login -- logs user to BOJ

    This function asks user username and password and calls auth_user. After
    authenticating, it checks if the login was successful and saves cookie to
    cookiefile.
    """
    username = input('Username: ')
    password = getpass.getpass()
    auth_user(username, password)
    save_cookie(sess)
    if check_login():
        logger.info('Logged in')
    else:
        logger.error('Login failed')
        logger.debug('Removing cookiefile...')
        os.remove(cookiefile_path)
        logger.info('Removed cookiefile')


def get_compiler(lang, default):
    """
    function get_compiler -- gets compiler version from config

    This function reads user-specified compiler from config file. If the
    compiler was not found, it fall backs to the default specified.

    params:
    lang: str -- the language to look up in the config file
    default: str -- the value to return if compiler was not found
    """
    if 'Compiler' in config[lang]:
        return config[lang]['Compiler']
    return default


def get_version(lang, default):
    """
    function get_version -- gets language version from config

    This function reads user-specified version of a language from config file.
    If the version was not found, it fall backs to the default specified.

    params:
    lang: str -- the language to look up in the config file
    default: str -- the value to return if version was not found
    """
    if 'Version' in config[lang]:
        return config[lang]['Version']
    return default


def get_lang_code(ext):
    """
    function get_lang_code -- gets language code from specified extension

    Instead of recognizing language from user-submitted code, BOJ uses
    'language code' to know which language the user coded. This function gets
    the language code from specified file extension.

    param:
    ext: str -- the file extension to recognize language from
    """
    if ext in ['.cc', '.cpp', '.c++']:
        if 'C++' not in config:
            return 88 # default is C++14
        compiler = get_compiler('C++', default='g++')
        version = get_version('C++', default='C++14')
        if compiler.lower() == 'g++':
            if '11' in version:
                return 49
            elif '14' in version:
                return 88
            elif '17' in version:
                return 84
            else:
                logger.error('Invalid C++ version: {0}'.format(version))
        elif compiler.lower() == 'clang':
            if '11' in version:
                return 66
            elif '14' in version:
                return 67
            elif '17' in version:
                return 85
            else:
                logger.error('Invalid C++ version: {0}'.format(version))
        else:
            logger.error('Invalid C++ compiler: {0}'.format(compiler))
    elif ext == '.c':
        if 'C' not in config:
            return 75 # default is C11
        compiler = get_compiler('C', default='gcc')
        version = get_version('C', default='C11')
        if compiler.lower() == 'gcc':
            if '11' in version:
                return 75
            elif version == 'C':
                return 0
            else:
                logger.error('Invalid C version: {0}'.format(version))
        elif compiler.lower() == 'clang':
            if '11' in version:
                return 77
            elif version == 'C':
                return 59
            else:
                logger.error('Invalid C version: {0}'.format(version))
        else:
            logger.error('Invalid C compiler: {0}'.format(compiler))
    elif ext == '.py':
        if 'Python' not in config:
            return 28 # default is CPython 3
        compiler = get_compiler('Python', default='CPython')
        version = get_version('Python', default='3')
        if compiler.lower() == 'cpython':
            if '2' in version:
                return 6
            elif '3' in version:
                return 28
            else:
                logger.error('Invalid Python version: {0}'.format(version))
        elif compiler.lower() == 'pypy':
            if '2' in version:
                return 32
            elif '3' in version:
                return 73
            else:
                logger.error('Invalid Python version: {0}'.format(version))
        else:
            logger.error('Invalid Python interpreter: {0}'.format(compiler))
    elif ext == '.java':
        if 'Java' not in config:
            return 3 # default is Java (oracle)
        compiler = get_compiler('Java', default='Oracle')
        if compiler.lower() == 'oracle':
            return 3
        elif compiler.lower() == 'openjdk':
            return 91
        else:
            logger.error('Invalid Java compiler: {0}'.format(compiler))
    elif ext == '.txt':
        return 58
    elif ext == '.js':
        return 17
    elif ext == '.aheui':
        return 83
    return 88 # fallback


def submit(number, filename):
    """
    function submit -- submits code to BOJ

    This function submits code to BOJ.

    params:
    number: int -- the problem number
    filename: str -- the filename to submit
    """
    load_cookie()
    logger.debug('Problem number is {0}, filename is {1}'.format(number,
                                                                 filename))
    soup = bs(sess.get(boj_url + '/submit/' + str(number)).text, 'html.parser')
    key = soup.find('input', {'name': 'csrf_key'})['value']
    file_ext = os.path.splitext(filename)[1]
    language_code = get_lang_code(file_ext)
    code = ''
    with open(filename, 'r') as f:
        code = f.read()

    data = {
        'problem_id': number,
        'source': code,
        'language': language_code,
        'code_open': 'open',
        'csrf_key': key
    }
    sess.post(boj_url + '/submit/' + str(number), data=data)


def get_username():
    """
    function get_username -- gets username from site's HTML

    This function gets username from the site's HTML.
    """
    soup = bs(sess.get(boj_url).text, 'html.parser')
    return soup.find('a', {'class': 'username'}).get_text()


def convert_msg(msg, mem=None, rtime=None):
    """
    function convert_msg -- converts message to short formats

    This function converts message from BOJ site to short format.

    params:
    msg: str -- the message to convert
    """
    if '채점 준비 중' in msg:
        msg = Fore.YELLOW + 'Preparing...' + Style.RESET_ALL
        return msg
    elif '채점 중' in msg:
        msg = msg.replace('채점 중', Fore.YELLOW + 'Judging...')
        msg += Style.RESET_ALL
        return msg
    elif re.match(r'^\d+점$', msg) is not None:
        msg = Fore.YELLOW + 'Partial ({0})'.format(re.match(r'\d+', msg)[0])
        return msg + Style.RESET_ALL
    conversion_table = {
        '맞았습니다!!': Fore.GREEN + 'AC (%sKB, %sms)' % (mem, rtime),
        '출력 형식이 잘못되었습니다': Fore.RED + 'PE',
        '틀렸습니다': Fore.RED + 'WA',
        '시간 초과': Fore.RED + 'TLE',
        '메모리 초과': Fore.RED + 'MLE',
        '출력 초과': Fore.RED + 'PLE',
        '런타임 에러': Fore.BLUE + 'RTE',
        '컴파일 에러': Fore.BLUE + 'Compile Error',
        '기다리는 중': Fore.YELLOW + 'Waiting...'
    }
    return conversion_table[msg] + Style.RESET_ALL


def check_finished(text):
    """
    function check_finished -- determines if the judging was complete from
    site's text

    This function determines if the judging was complete from given text.

    params:
    text: str -- the text from BOJ site
    """
    if re.fullmatch(r'^\d+점$', text):
        return True
    result = {
        '맞았습니다!!',
        '출력 형식이 잘못되었습니다', '틀렸습니다', '시간 초과',
        '메모리 초과', '출력 초과', '런타임 에러', '컴파일 에러'
    }
    return text in result


def print_result(number):
    """
    function print_result -- prints submission results

    This function prints submission result from problem number

    params:
    number: int -- the problem number to print result
    """
    done = False
    while not done:
        logger.debug('Getting username from HTML...')
        username = get_username()
        logger.debug('Username is {0}'.format(username))
        result_url = boj_url + "/status?from_mine=1&problem_id=" + str(number) +\
                    "&user_id=" + username
        soup = bs(sess.get(result_url).text, 'html.parser')
        text = soup.find('span',
                         {'class': 'result-text'}).find('span').string.strip()
        mem = soup.find('td', {'class': 'memory'}).text
        rtime = soup.find('td', {'class': 'time'}).text
        print('\r' + ' ' * 20, end='')
        print('\r{0}'.format(convert_msg(text, mem, rtime)), end='')
        done = check_finished(text)
    print()


def stats(username):
    """
    function stats -- print user's stats read from BOJ

    This function prints the user's stats read from BOJ.

    params:
    username: str -- user's name
    """
    load_cookie()
    if username is None:
        username = get_username()
    print('Stats of user {0}'.format(username))
    print()
    soup = bs(sess.get(boj_url + '/user/' + username).text, 'html.parser')
    table_tr_elems = soup.find('table', {'id': 'statics'}).tbody.findAll('tr')
    conversion_table = {
        '랭킹': Fore.BLUE + 'Rank:\t\t' + Style.RESET_ALL,
        '푼 문제': Fore.GREEN + 'Solved:\t\t' + Style.RESET_ALL,
        '제출': Fore.YELLOW + 'Submissions:\t' + Style.RESET_ALL,
        '맞았습니다': Fore.GREEN + 'AC count:\t' + Style.RESET_ALL,
        '출력 형식': Fore.RED + 'PE count:\t' + Style.RESET_ALL,
        '틀렸습니다': Fore.RED + 'WA count:\t' + Style.RESET_ALL,
        '시간 초과': Fore.RED + 'TLE count:\t' + Style.RESET_ALL,
        '컴파일 에러': Fore.RED + 'Compile errors:\t' + Style.RESET_ALL,
        '메모리 초과': Fore.RED + 'MLE count:\t' + Style.RESET_ALL,
        '출력 초과': Fore.RED + 'PLE count:\t' + Style.RESET_ALL,
        '런타임 에러': Fore.RED + 'RTE count:\t' + Style.RESET_ALL,
        '학교/회사': 'Organization:\t',
        '대회 우승': Fore.GREEN + 'First place:\t' + Style.RESET_ALL,
        '대회 준우승': Fore.CYAN + 'Second place:\t' + Style.RESET_ALL,
    }
    for tr_elem in table_tr_elems:
        if tr_elem.th.get_text() in conversion_table:
            print(conversion_table[tr_elem.th.get_text()], end='')
            print(', '.join(
                [s for s in re.split(r'\t|\n', tr_elem.td.get_text().strip())
                 if s != '']))


def version():
    """
    function version -- prints version

    This function prints version number.
    """
    print('boj-tool: a CLI tool for BOJ')
    print('v' + __version__)


def main():
    """
    function main -- main function
    """
    parser = argparse.ArgumentParser(description='boj-tool: a CLI tool for BOJ')
    parser.add_argument('-v', '--verbose', help='set log level to INFO',
                        action='store_true')
    parser.add_argument('-d', '--debug', help='set log level to DEBUG',
                        action='store_true')
    subparsers = parser.add_subparsers(dest='subparser')
    login_parser = subparsers.add_parser('login')
    submit_parser = subparsers.add_parser('submit')
    submit_parser.add_argument('number', type=int, help='the problem number')
    submit_parser.add_argument('filename', help='filename to submit')
    stat_parser = subparsers.add_parser('stats')
    stat_parser.add_argument('-u', '--user', type=str,
                             help='the user to show stats')
    version_parser = subparsers.add_parser('version')
    args = parser.parse_args()

    initialize()
    if args.verbose:
        logger.setLevel(logging.INFO)
    elif args.debug:
        logger.setLevel(logging.DEBUG)

    if args.subparser == 'login':
        login()
    elif args.subparser == 'submit':
        submit(args.number, args.filename)
        print_result(args.number)
    elif args.subparser == 'stats':
        stats(args.user)
    elif args.subparser == 'version':
        version()


if __name__ == '__main__':
    main()
