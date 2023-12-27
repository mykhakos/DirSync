import argparse
import os
import pytest

from unittest import mock

from dir_sync._dir_sync import ArgValidators, SyncMode


@pytest.mark.parametrize(
    "level_input, level_output",
    [
        (0, 0),
        (10, 10),
        (20, 20),
        (35, 35),
        ("DEBUG", 10),
        ("info", 20),
        ("WarNIng", 30),
        ("  error    ", 40)
    ]
)
def test_is_log_level_valid(level_input, level_output):
    assert ArgValidators.is_log_level(level_input) == level_output


@pytest.mark.parametrize(
    "level_input",
    [-1, "invalid_log_level", "ten", "inf o", "", None, 4.2]
)
def test_is_log_level_invalid(level_input):
    with pytest.raises(argparse.ArgumentTypeError):
        ArgValidators.is_log_level(level_input)


@pytest.mark.parametrize(
    "num_input, num_output",
    [(1.0, 1.0), (4.2, 4.2), (int(1.0), 1.0), ("2.1", 2.1)]
    )
def test_is_positive_float_valid(num_input, num_output):
    num = ArgValidators.is_positive_float(num_input)
    assert isinstance(num, float)
    assert num == num_output


@pytest.mark.parametrize(
    "num_input",
    [-1, 0, -2.7, "one", "", None, [1, 2]]
)
def test_is_positive_float_invalid(num_input):
    with pytest.raises(argparse.ArgumentTypeError):
        ArgValidators.is_positive_float(num_input)


@pytest.mark.parametrize(
    ("sync_mode_input", "sync_mode_output"),
    [
        (SyncMode.FULL, SyncMode.FULL),
        (SyncMode.QUICK, SyncMode.QUICK),
        ("FULL", SyncMode.FULL),
        ("FuLl  ", SyncMode.FULL),
        ("quick", SyncMode.QUICK),
        ("QUiCK", SyncMode.QUICK)
    ]
)
def test_is_sync_mode_valid(sync_mode_input, sync_mode_output):
    assert ArgValidators.is_sync_mode(sync_mode_input) == sync_mode_output


@pytest.mark.parametrize(
    "sync_mode_input",
    [0, "ful l", "quick+full", None, ["full"]]
)
def test_is_sync_mode_invalid(sync_mode_input):
    with pytest.raises(argparse.ArgumentTypeError):
        ArgValidators.is_sync_mode(sync_mode_input)


def test_is_valid_src_existing_directory():
    path_input = "path/to/existing/dir "
    path_output = os.path.normpath(path_input)
    with (
        mock.patch('os.path.exists', return_value=True),
        mock.patch('os.path.isdir', return_value=True)
    ):
        assert ArgValidators.is_valid_src(path_input) == path_output


def test_is_valid_src_nonexistent_path():
    with mock.patch('os.path.exists', return_value=False):
        with pytest.raises(argparse.ArgumentTypeError):
            ArgValidators.is_valid_src("/path/to/nonexistent/dir")


def test_is_valid_src_not_a_directory():
    with (
        mock.patch('os.path.exists', return_value=True),
        mock.patch('os.path.isdir', return_value=False)
    ):
        with pytest.raises(argparse.ArgumentTypeError):
            ArgValidators.is_valid_src("/path/to/not-a-dir")


def test_is_valid_logfile_existing_file():
    path_input = "path/to/existing/logfile.log"
    path_output = os.path.normpath(path_input)
    with (
        mock.patch('os.path.exists', return_value=True),
        mock.patch('os.path.isfile', return_value=True),
        mock.patch('os.access', return_value=True)
    ):
        assert ArgValidators.is_valid_logfile(path_input) == path_output


def test_is_valid_logfile_nonexistent_file():
    path_input = "path/to/nonexistent/logfile.log"
    path_output = os.path.normpath(path_input)
    with (
        mock.patch('os.path.exists', return_value=False),
        mock.patch('os.access', return_value=True)
    ):
        assert ArgValidators.is_valid_logfile(path_input) == path_output


def test_is_valid_logfile_not_a_file():
    path_input = "path/to/not-a-file"
    with (
        mock.patch('os.path.exists', return_value=True),
        mock.patch('os.path.isfile', return_value=False)
    ):
        with pytest.raises(argparse.ArgumentTypeError):
            ArgValidators.is_valid_logfile(path_input)
