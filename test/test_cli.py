"""
"""

import subprocess
import collections
from pathlib import Path
from typing import Union, List, Tuple


def execute_cmd(
    cmd: Union[str, List[str]], raise_error: bool = True
) -> Tuple[int, List[str]]:
    """
    execute shell command using `Popen`

    Parameters
    ----------
    cmd: str or list of str,
        the shell command to be executed,
        or a list of .sh files to be executed
    raise_error: bool, default True,
        if True, error will be raised when occured

    Returns
    -------
    exitcode, output_msg: int, list of str,
        exitcode: exit code returned by `Popen`
        output_msg: outputs from `stdout` of `Popen`

    """
    shell_arg, executable_arg = True, None
    s = subprocess.Popen(
        cmd,
        shell=shell_arg,
        executable=executable_arg,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        close_fds=True,
    )
    debug_stdout = collections.deque(maxlen=1000)
    print("\n" + "*" * 10 + "  execute_cmd starts  " + "*" * 10 + "\n")
    while 1:
        line = s.stdout.readline().decode("utf-8", errors="replace")
        if line.rstrip():
            debug_stdout.append(line)
            # print(line)
        exitcode = s.poll()
        if exitcode is not None:
            for line in s.stdout:
                debug_stdout.append(line.decode("utf-8", errors="replace"))
            if exitcode is not None and exitcode != 0:
                error_msg = " ".join(cmd) if not isinstance(cmd, str) else cmd
                error_msg += "\n"
                error_msg += "".join(debug_stdout)
                s.communicate()
                s.stdout.close()
                print("\n" + "*" * 10 + "  execute_cmd failed  " + "*" * 10 + "\n")
                if raise_error:
                    raise subprocess.CalledProcessError(exitcode, error_msg)
                else:
                    output_msg = list(debug_stdout)
                    return exitcode, output_msg
            else:
                break
    s.communicate()
    s.stdout.close()
    output_msg = list(debug_stdout)

    print("\n" + "*" * 10 + "  execute_cmd succeeded  " + "*" * 10 + "\n")

    exitcode = 0

    return exitcode, output_msg


SAMPLE_DATA_DIR = Path(__file__).resolve().parents[1] / "sample-files"
LARGE_DATABASE = SAMPLE_DATA_DIR / "large_database.bib"
SAMPLE_INPUT_TXT = SAMPLE_DATA_DIR / "sample_input.txt"

TMP_DIR = Path(__file__).resolve().parents[1] / "tmp"
TMP_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = TMP_DIR / "cli_output.bib"


def test_cli():
    cmd = f"bib-lookup --check-file {str(LARGE_DATABASE)}"
    exitcode, output_msg = execute_cmd(cmd)
    assert exitcode == 0

    cmd = "bib-lookup 10.1109/CVPR.2016.90 10.1109/tpami.2019.2913372"
    exitcode, output_msg = execute_cmd(cmd)
    assert exitcode == 0

    cmd = f"bib-lookup --input {str(SAMPLE_INPUT_TXT)} --output {str(OUTPUT_FILE)} --check_file y"
    exitcode, output_msg = execute_cmd(cmd)
    assert exitcode == 0
