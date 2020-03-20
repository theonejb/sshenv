sshenv
===

`sshenv` is a Python 3 based CLI utility
to manage multiple SSH environments. See **What are SSH Environments**
section below for the rationale behind creating this.

## Installation
The only dependency is a recent version of Python. `sshenv` was
developed on Python 3.7.0 but should work with any recent version.

Personally I sym-link the `sshenv.py` file into a directory on my
`$PATH` (`~/.local/bin/`) as `sshenv` and make it executable by
`chmod u+x sshenv`. I can then use the `sshenv` command from my shell
in any directory to switch environments.

## Usage
```
sshenv -h  
usage: sshenv [-h] {list,l,deactivate,d,switch,s,activate,a} ...

optional arguments:
  -h, --help            show this help message and exit

Commands:
  {list,l,deactivate,d,switch,s,activate,a}
    list (l)            Output a list of environments and exit.
    deactivate (d)      Deactivate the currently active env.
    switch (s, activate, a)
                        Activates the named environment. If an environment is
                        currently active it is first deactivated.
```

By default it uses `~/.ssh` as the `SSH_HOME` but you can customize
this by setting a different value of the environment variable `SSH_HOME`
when running the script.

Any directories under `SSH_HOME` **that contain** a `.sshenv`
file are considered valid environments that can be activated.

## What are SSH Environments?
As part of my day job, side projects, and freelancing projects,
I have to use different SSH keys to connect to different
systems.

Systems can be servers on some cloud provide (AWS, GCP, DigitalOcean),
source code repos (GitHub, BitBucket), etc...

Until now, I've managed these using a `config` file in my `.ssh`
directory. Unfortunately it gets a bit difficult because:
- I have to update the `config` file every time.
- Some systems like BitBucket only allow me to add a SSH key to
1 account. Working with different clients means I have to have a
different SSH key to use with BitBucket for each client and having
to configure aliases like `clientbucket` in `config` and then
using that in `git clone git@clientbucket:/...`. This gets tiring.

An SSH environment is the set of key files and optionally a `config` 
for a particular project.

For example, say I have 2 projects, client1 & client2. To use
`sshenv` I need have the following directory structure:

```
~/.ssh
+
|
+--+client1
|  |
|  +-+id_rsa
|  |
|  +-+id_rsa.pub
|  |
|  +-+config
|  |
|  +-+.sshenv
|
|
+--+client2
   |
   +-+id_rsa
   |
   +-+bitbucket
   |
   +-+aws_us_east_1
   |
   +-+.sshenv
```

With this structure, I can now run `sshenv switch client2` and
all the files inside the `client2` environment will be sym-linked
into my `.ssh/` directory.

I can also run `sshenv switch client1` and:
1. The files sym-linked for `client2` will be removed
2. All files under the `client1` environment will be sym-linked
into `.ssh/`.

## Other tools

The idea for `sshenv` is heavily inspired by how `pyenv` works. But
this is not the first tool that allows managing a set of key files.
Some alternatives are:
- https://github.com/KennethanCeyer/gowap
- https://github.com/TimothyYe/skm