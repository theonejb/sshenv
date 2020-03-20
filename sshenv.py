#!/usr/bin/env python

import sys
import os
import pathlib
import argparse


def get_ssh_home():
    home = pathlib.Path.home()
    default_ssh_home = home / '.ssh'

    ssh_home_config = os.environ.get('SSH_HOME')
    if ssh_home_config is not None:
        ssh_home = pathlib.Path(ssh_home_config)
    else:
        ssh_home = default_ssh_home

    return ssh_home


def is_valid_env_dir(dir_path):
    sshenv_config_file = dir_path / '.sshenv'

    return sshenv_config_file.exists() and sshenv_config_file.is_file()


def get_valid_env_dirs(ssh_home):
    available_dirs = []

    for child in ssh_home.iterdir():
        if child.is_dir() and is_valid_env_dir(child):
            available_dirs.append(child)

    return available_dirs


def get_envs(ssh_home):
    env_dirs = get_valid_env_dirs(ssh_home)

    return [{
        'id': i+1,
        'path': p,
        'name': p.name,
    } for i, p in enumerate(env_dirs)]


def get_config_path(ssh_home):
    return ssh_home / '.sshenv'


def can_modify_current_config(ssh_home):
    config_path = get_config_path(ssh_home)

    if not config_path.exists():
        return True, None

    if not config_path.is_file():
        return False, f'The config file {config_path} is not a file.'

    if not config_path.is_symlink():
        return False, f'The config file {config_path} is not a symlink.'

    true_config_path = config_path.resolve()
    if ssh_home not in true_config_path.parents:
        return False, f'The config file is a symlink to {true_config_path} which is not under the SSH home.'

    return True, None


def get_active_env(ssh_home, envs):
    config_path = get_config_path(ssh_home)
    true_config_path = config_path.resolve()

    for env in envs:
        if env['path'] == true_config_path.parent:
            return env

    return None


def get_all_symlinked_files_for_env(ssh_home, env):
    symlinked_files = []

    for path in ssh_home.iterdir():
        if not path.is_file():
            continue

        if not path.is_symlink():
            continue

        true_path = path.resolve()
        if true_path.parent == env['path']:
            symlinked_files.append(path)

    return symlinked_files


def get_all_files_to_symlink(env):
    files = []

    for path in env['path'].iterdir():
        if path.is_file():
            files.append(path)

    return files


def deactivate_env(ssh_home, env_to_deactivate):
    symlinked_files = get_all_symlinked_files_for_env(ssh_home, env_to_deactivate)

    for file in symlinked_files:
        print(f'Unlinking file at path {file}.')
        file.unlink()


def activate_env(ssh_home, env_to_activate):
    files_to_symlink = get_all_files_to_symlink(env_to_activate)

    for file_path in files_to_symlink:
        file_name = file_path.name
        symlink_path = ssh_home / file_name

        if symlink_path.exists():
            raise IOError(f'{symlink_path} already exists')

        symlink_path.symlink_to(file_path)
        print(f'Symlinked {file_path} to {symlink_path}.')


def list_cmd(args):
    ssh_home = get_ssh_home()
    envs = get_envs(ssh_home)

    active_env = get_active_env(ssh_home, envs)

    print("Available environments:")
    for i, env in enumerate(envs):
        if env == active_env:
            print(f' *[{env["id"]}] {env["name"]}')
        else:
            print(f'  [{env["id"]}] {env["name"]}')


def deactivate_cmd(args):
    ssh_home = get_ssh_home()
    envs = get_envs(ssh_home)
    active_env = get_active_env(ssh_home, envs)

    if active_env is None:
        print('No environment is currently active.')
    else:
        deactivate_env(ssh_home, active_env)
        print(f'Environment {active_env["name"]} was deactivated.')


def switch_cmd(args):
    ssh_home = get_ssh_home()
    envs = get_envs(ssh_home)

    active_env = get_active_env(ssh_home, envs)

    env_to_switch_to_name = args.name

    try:
        env_to_switch_to_id = int(env_to_switch_to_name)
        env_to_switch_to = list(filter(lambda x: x['id'] == env_to_switch_to_id, envs))
    except ValueError:
        env_to_switch_to = list(filter(lambda x: x['name'] == env_to_switch_to_name, envs))

    if len(env_to_switch_to) > 1:
        print(f'There are multiple environments with the same name {env_to_switch_to_name}. '
              f'Please fix this before using sshenv.')
        sys.exit(1)
    elif not env_to_switch_to:
        print(f'Unable to find any environment called {env_to_switch_to_name}.')
        sys.exit(1)

    env_to_switch_to = env_to_switch_to[0]

    if env_to_switch_to == active_env:
        print(f'{env_to_switch_to["name"]} is already active.')
        return

    if active_env:
        print(f'Deactivating {active_env["name"]}.')
        deactivate_env(ssh_home, active_env)

    try:
        activate_env(ssh_home, env_to_switch_to)
        print(f'{env_to_switch_to["name"]} was activated.')
    except IOError as e:
        print(f'Unable to activate {env_to_switch_to["name"]}. Error: {e}. Rolling back any activation.')
        deactivate_env(ssh_home, env_to_switch_to)
        sys.exit(1)


def configure_argparser():
    parser = argparse.ArgumentParser()
    parser.set_defaults(func=lambda x: parser.print_help())

    sub_parsers = parser.add_subparsers(title='Commands')

    list_cmd_parser = sub_parsers.add_parser('list', aliases=['l'],
                                             help='Output a list of environments and exit.')
    list_cmd_parser.set_defaults(func=list_cmd)

    deactivate_cmd_parser = sub_parsers.add_parser('deactivate', aliases=['d'],
                                                   help='Deactivate the currently active env.')
    deactivate_cmd_parser.set_defaults(func=deactivate_cmd)

    switch_cmd_parser = sub_parsers.add_parser('switch', aliases=['s', 'activate', 'a'],
                                               help='Activates the named environment. If an environment is currently '
                                                    'active it is first deactivated.')
    switch_cmd_parser.add_argument('name')
    switch_cmd_parser.set_defaults(func=switch_cmd)

    return parser


def main():
    ssh_home = get_ssh_home()

    if not ssh_home.is_dir():
        print(
            f'"{ssh_home}" is set as the SSH home. However, that path is not a directory.'
        )
        sys.exit(1)

    can_modify_config, reason = can_modify_current_config(ssh_home)
    if not can_modify_config:
        print(
            f'Can not modify the current SSH config file. Reason: {reason}'
        )
        sys.exit(1)

    parser = configure_argparser()
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
