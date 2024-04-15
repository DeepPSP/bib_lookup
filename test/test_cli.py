"""
"""

import collections
import json
import subprocess
from pathlib import Path
from typing import List, Tuple, Union

import yaml

from bib_lookup._const import CONFIG_FILE as _CONFIG_FILE


def execute_cmd(cmd: Union[str, List[str]], raise_error: bool = True) -> Tuple[int, List[str]]:
    """Execute shell command using `Popen`.

    Parameters
    ----------
    cmd : str or list of str
        Shell command to be executed,
        or a list of .sh files to be executed.
    raise_error : bool, default True
        If True, error will be raised when occured.

    Returns
    -------
    exitcode : int
        Exit code returned by `Popen`.
    output_msg : list of str
        Outputs from `stdout` of `Popen`.

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

    # output version info
    cmd = "bib-lookup --version"
    exitcode, output_msg = execute_cmd(cmd)

    # config file
    cmd = "bib-lookup --config show"
    assert not _CONFIG_FILE.exists()
    exitcode, output_msg = execute_cmd(cmd)  # prints the default config
    cmd = "bib-lookup --config reset"
    exitcode, output_msg = execute_cmd(cmd)  # reset the config

    # set config using KEY=VALUE pairs
    cmd = """bib-lookup --config "timeout=2.0;print_result=true;ignore_fields=['url','pdf'];hehe=1" """
    exitcode, output_msg = execute_cmd(cmd)  # set the config, invalid key will be ignored
    assert _CONFIG_FILE.exists()
    cmd = "bib-lookup --config show"
    exitcode, output_msg = execute_cmd(cmd)  # prints the config
    # delete config
    cmd = "bib-lookup --config reset"
    exitcode, output_msg = execute_cmd(cmd)  # reset the config
    assert not _CONFIG_FILE.exists()

    # set config from json file
    new_config = {"timeout": 3.0, "print_result": False, "ignore_fields": ["url"]}
    new_config_file = SAMPLE_DATA_DIR / "new_config.json"
    new_config_file.write_text(json.dumps(new_config))
    cmd = f"bib-lookup --config {str(new_config_file)}"
    exitcode, output_msg = execute_cmd(cmd)  # set the config from file
    cmd = "bib-lookup --config show"
    exitcode, output_msg = execute_cmd(cmd)
    assert _CONFIG_FILE.exists()
    new_config_file.unlink()
    # delete config
    cmd = "bib-lookup --config reset"
    exitcode, output_msg = execute_cmd(cmd)  # reset the config
    assert not _CONFIG_FILE.exists()

    # set config from yaml file
    new_config_file = SAMPLE_DATA_DIR / "new_config.yaml"
    new_config_file.write_text(yaml.dump(new_config))
    cmd = f"bib-lookup --config {str(new_config_file)}"
    exitcode, output_msg = execute_cmd(cmd)  # set the config from file
    cmd = "bib-lookup --config show"
    exitcode, output_msg = execute_cmd(cmd)  # prints the config
    assert _CONFIG_FILE.exists()
    new_config_file.unlink()

    # simplify bib file
    tex_entry_file = SAMPLE_DATA_DIR / "sample-source.tex"
    cmd = f"bib-lookup --simplify-bib {str(tex_entry_file)} -i {str(LARGE_DATABASE)}"
    exitcode, output_msg = execute_cmd(cmd)
    result_file = LARGE_DATABASE.parent / (LARGE_DATABASE.stem + "_simplified.bib")
    assert result_file.exists()
    result_file.unlink()
