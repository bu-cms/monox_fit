# Author: Andrea Malara, Arne Reimers
"""Utilities for parallelization and timing of tasks using multiprocessing, threading, and subprocess management."""

import os
import sys
import time
import subprocess
import functools
from typing import Optional, Any, Union
from collections.abc import Callable
from types import SimpleNamespace
from multiprocessing import Pool
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm  # type: ignore
from utils.generic.colors import blue, red


def timeit(method: Callable) -> Callable:
    """Decorator to measure and log the execution time of a function."""

    @functools.wraps(method)
    def timed(*args: Any, **kwargs: Any) -> Any:
        """Log the execution time of the decorated function."""
        print(blue(f"Start of {method.__name__}"))
        start_time = time.time()
        result = method(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        if "log_time" in kwargs:
            name = kwargs.get("log_name", method.__name__.upper())
            kwargs["log_time"][name] = int(elapsed_time)
        else:
            print(blue(f"End of {method.__name__}: time = {elapsed_time:.2f} s"))
        return result

    return timed


def multi_process(func: Callable, arglist: list[dict[str, Any]], ncores: int = 8) -> list[Any]:
    """Run a function in parallel using multiprocessing.

    Args:
        func (Callable): Function to execute.
        arglist (list[dict[str, Any]]): Arguments for the function, which will be called once for each item in the list.
        ncores (int): Number of cores to use.

    Returns:
        list[Any]: Results from the function calls.
    """
    if len(arglist) == 0:
        return []

    global func_single_arg  # pylint: disable=W0601

    def func_single_arg(kwargs: dict[str, Any]) -> Any:
        """Wraps a function to accept a single argument as a dictionary."""
        return func(**kwargs)

    with Pool(processes=ncores) as pool:
        results = list(
            tqdm(
                pool.imap(func_single_arg, arglist),  # type: ignore
                total=len(arglist),
                desc="Processed",
            )
        )
    del globals()["func_single_arg"]
    return results


def multi_thread(func: Callable, arglist: list[dict[str, Any]], ncores: int = 8) -> list[Any]:
    """Run a function in parallel using multithreading.

    Args:
        func (Callable): Function to execute.
        arglist (list[dict[str, Any]]): Arguments for the function.
        ncores (int): Number of threads to use.

    Returns:
        list[Any]: Results from the function calls.
    """
    results = []
    with ThreadPoolExecutor(max_workers=ncores) as executor:
        futures = [executor.submit(func, **kwargs) for kwargs in arglist]

        for future in tqdm(as_completed(futures), total=len(futures), desc="Processed"):
            results.append(future.result())

    return results


@timeit
def parallelize(
    commands: Union[list[str], list[list[str]]],
    getoutput: bool = False,
    logfiles: Optional[list[str]] = None,
    ncores: int = 8,
    cwd: bool = False,
    niceness: Optional[int] = 10,
    remove_temp_files: bool = True,
    time_to_sleep: float = 0.5,
    wait_time: Optional[float] = None,
) -> dict[int, dict[str, Any]]:
    """Parallelize command execution using subprocess.

    Args:
        commands (Union[list[str], list[list[str]]]): Commands to execute.
        getoutput (bool): If True, capture command outputs.
        logfiles (Optional[list[str]]): Log files to write command outputs. If not provided, will create log files in the current directory.
        ncores (int): Number of parallel jobs.
        cwd (bool): Working directory for commands.
        niceness (Optional[int]): Niceness value for prioritizing commands.
        remove_temp_files (bool): If True, delete temporary log files.
        time_to_sleep (float): Sleep time between process checks.
        wait_time (Optional[float]): Maximum time to wait for a process.

    Returns:
        dict[int, dict[str, Any]]: Outputs of the commands if `getoutput` is True.
    """

    def wait_for_process(state: SimpleNamespace) -> None:
        """Wait for running processes to complete."""
        for idx in list(state.processes.keys()):
            state.processes[idx]["iter"] += state.time_to_sleep
            if wait_time is not None and state.processes[idx]["iter"] >= wait_time:
                kill(state.processes[idx]["proc"].pid)  # type: ignore # pylint: disable=E0602 # noqa: F821
                state.processes[idx]["proc"].wait()
            if state.processes[idx]["proc"].poll() is not None:
                state.processes[idx]["proc"].wait()
                state.n_running -= 1
                state.n_completed += 1
                if state.getoutput:
                    output = state.processes[idx]["proc"].communicate()
                    state.outputs[idx] = {
                        "stdout": output[0],
                        "stderr": output[1],
                        "returncode": state.processes[idx]["proc"].returncode,
                        "command": state.commands[idx],
                    }
                else:
                    state.log_files[idx].close()
                del state.processes[idx]
        progress = round(float(state.n_completed) / float(state.n_jobs) * 100, 1)
        sys.stdout.write(blue(f"  --> {state.n_completed} of {state.n_jobs} ({progress:.1f}%) jobs done using {ncores} cores.\r"))
        sys.stdout.flush()
        time.sleep(state.time_to_sleep)

    state = SimpleNamespace(
        processes={},
        outputs={},
        log_files={},
        commands=commands,
        getoutput=getoutput,
        n_running=0,
        n_completed=0,
        n_jobs=len(commands),
        time_to_sleep=time_to_sleep if len(commands) < 10000 else time_to_sleep / 10000.0,
    )
    logfiles = logfiles or []
    is_log_given = not state.getoutput and len(logfiles) == state.n_jobs

    for index, command in enumerate(state.commands):
        working_dir = command[0] if cwd else None
        proc = command[1:] if cwd else command
        if isinstance(proc, list):
            proc = " ".join(proc)
        if niceness:
            proc = f"nice -n {niceness} {proc}"
        if not isinstance(proc, str):
            raise RuntimeError(red("parallelize:: Commands must be strings or lists of strings."))
        if state.getoutput:
            stdout, stderr = subprocess.PIPE, subprocess.STDOUT
        else:
            log_path = logfiles[index] if is_log_given else os.path.join(working_dir if working_dir else "", f"parallelize_log_{index}.txt")
            state.log_files[index] = open(log_path, "w")  # pylint: disable=consider-using-with
            stdout, stderr = state.log_files[index], state.log_files[index]
        state.processes[index] = {
            "proc": subprocess.Popen(proc, stdout=stdout, stderr=stderr, shell=True, cwd=working_dir),  # pylint: disable=consider-using-with
            "iter": 0,
        }
        state.n_running += 1
        while state.n_running >= ncores:
            wait_for_process(state)
    while state.n_completed < state.n_jobs:
        wait_for_process(state)
    if remove_temp_files:
        for log in state.log_files.values():
            os.remove(log.name)
    return state.outputs


def run_parallel_commands(commands: list[str], ncores: int, remove_temp_files: bool) -> list[str]:
    """Executes commands in parallel and returns failed commands."""
    results = parallelize(commands, getoutput=True, ncores=ncores, remove_temp_files=remove_temp_files)
    return [result["command"] for result in results.values() if result["returncode"] != 0]
