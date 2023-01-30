"""
"""

import collections
import subprocess
from pathlib import Path
from typing import Union, List, Tuple

import pytest

from bib_lookup.cli import str2bool


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


PROJECT_DIR = Path(__file__).resolve().parents[1]
SAMPLE_DATA_DIR = PROJECT_DIR / "sample-files"
LARGE_DATABASE = SAMPLE_DATA_DIR / "large_database.bib"
SAMPLE_INPUT_TXT = SAMPLE_DATA_DIR / "sample_input.txt"

TMP_DIR = PROJECT_DIR / "tmp"
TMP_DIR.mkdir(exist_ok=True)
OUTPUT_FILE = TMP_DIR / "test_cli_output.bib"


def test_cli():
    cmd = f"bib-lookup --check-file {str(LARGE_DATABASE)}"
    exitcode, output_msg = execute_cmd(cmd)
    assert exitcode == 0

    cmd = (
        "bib-lookup 10.1109/CVPR.2016.90 10.1109/tpami.2019.2913372 "
        "--format text --style apa --ignore-errors true --timeout 10"
    )
    exitcode, output_msg = execute_cmd(cmd)
    assert exitcode == 0

    cmd = (
        f"bib-lookup --input {str(SAMPLE_INPUT_TXT)} --output {str(OUTPUT_FILE)} "
        "--check-file y --timeout 10 --ignore-errors true --verbose 3"
    )
    exitcode, output_msg = execute_cmd(cmd)

    tex_entry_file = SAMPLE_DATA_DIR / "sample-source.tex"
    default_output_file = tex_entry_file.parent / f"{tex_entry_file.stem}_in_one.tex"
    if default_output_file.exists():
        default_output_file.unlink()
    cmd = f"bib-lookup --gather {str(tex_entry_file)}"
    exitcode, output_msg = execute_cmd(cmd)
    assert default_output_file.exists()

    # errors are printed
    exitcode, output_msg = execute_cmd(cmd)
    default_output_file.unlink()

    cmd = f"bib-lookup 10.1109/CVPR.2016.90 --gather {str(tex_entry_file)}"
    # warnings are printed
    exitcode, output_msg = execute_cmd(cmd)
    default_output_file.unlink()

    tex_entry_file = SAMPLE_DATA_DIR / "not-exist.tex"
    cmd = f"bib-lookup --gather {str(tex_entry_file)}"
    # errors are printed
    exitcode, output_msg = execute_cmd(cmd)
    assert not (SAMPLE_DATA_DIR / "not-exist_in_one.tex").exists()


def test_str2bool():
    for s in ("yes", "true", "t", "y", "1", "True", "Yes"):
        assert str2bool(s) is True
        assert str2bool(s.upper()) is True
    for s in ("no", "false", "f", "n", "0", "False", "No"):
        assert str2bool(s) is False
        assert str2bool(s.upper()) is False
    assert str2bool(True) is True
    assert str2bool(False) is False
    with pytest.raises(ValueError, match="Boolean value expected"):
        str2bool("foo")
