import operator
import os
import platform
import pytest
import shutil
import warnings


from dir_sync._dir_sync import DirSync, DirSyncSettings, SyncMode


TEST_SRC_DIR = os.path.join(os.path.dirname(__file__), "test_src")
TEST_DST_DIR = os.path.join(os.path.dirname(__file__), "test_dst")
TEST_TEMPFILE_NAME = 'tempfile.txt'


def test_settings_init():
    settings = DirSyncSettings(
        sync_mode='full',
        force_copy=False,
        sync_meta=False
    )
    assert settings.force_copy is False
    assert settings.sync_meta is False
    assert settings.sync_mode == SyncMode.FULL


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
def test_settings_set_sync_mode_valid(sync_mode_input, sync_mode_output):
    settings = DirSyncSettings()
    settings.sync_mode = sync_mode_input
    assert settings.sync_mode == sync_mode_output


@pytest.mark.parametrize(
    "sync_mode_input",
    [0, "ful l", "quick+full", None, ["full"]]
)
def test_settings_set_sync_mode_invalid(sync_mode_input):
    settings = DirSyncSettings()
    with pytest.raises(ValueError):
        settings.sync_mode = sync_mode_input


@pytest.fixture(scope='module')
def dir_sync_obj():
    if os.path.exists(TEST_SRC_DIR):
        shutil.rmtree(TEST_SRC_DIR)
    os.mkdir(TEST_SRC_DIR)
    if os.path.exists(TEST_DST_DIR):
        shutil.rmtree(TEST_DST_DIR)
    yield DirSync(TEST_SRC_DIR, TEST_DST_DIR)
    shutil.rmtree(TEST_SRC_DIR)
    if os.path.exists(TEST_DST_DIR):
        shutil.rmtree(TEST_DST_DIR)


@pytest.fixture
def temp_file():
    temp_file_path = os.path.join(TEST_SRC_DIR, TEST_TEMPFILE_NAME)
    with open(temp_file_path, 'w', encoding='utf-8') as tf:
        tf.write("foo")
    yield temp_file_path
    if os.path.exists(temp_file_path):
        try:
            os.remove(temp_file_path)
        except PermissionError:
            os.chmod(temp_file_path, 0o666)
            os.remove(temp_file_path)


@pytest.mark.parametrize(
    ("ts_1", "ts_2", "op"),
    [
        (0, 0, operator.eq),
        (1000000, 0, operator.gt),
        (0, 1234567.890, operator.lt),
        (1234, 5678, operator.ne),
    ]
)
def test_compare_timestamps(dir_sync_obj: DirSync, ts_1, ts_2, op):
    assert dir_sync_obj._compare_timestamps(ts_1, ts_2, op) is True


def test_file_create(dir_sync_obj: DirSync, temp_file):
    # sync and check if the destination file copy has been created
    dir_sync_obj.sync()
    file_src = os.path.join(TEST_SRC_DIR, TEST_TEMPFILE_NAME)
    file_dst = os.path.join(TEST_DST_DIR, TEST_TEMPFILE_NAME)
    assert os.path.exists(file_dst)
    assert dir_sync_obj._is_md5_different(file_src, file_dst) is False


def test_file_update(dir_sync_obj: DirSync, temp_file):
    test_file_create(dir_sync_obj, temp_file)
    file_src = os.path.join(TEST_SRC_DIR, TEST_TEMPFILE_NAME)
    file_dst = os.path.join(TEST_DST_DIR, TEST_TEMPFILE_NAME)
    # update the source file
    with open(file_src, 'w', encoding='utf-8') as file:
        file.write('bar')
    assert dir_sync_obj._is_md5_different(file_src, file_dst) is True
    # sync and check if the destination file is also updated
    dir_sync_obj.sync()
    assert dir_sync_obj._is_md5_different(file_src, file_dst) is False


@pytest.mark.skipif(
    platform.system() == 'Windows',
    reason="Cannot remove file read access on Windows with os.chmod"
)
def test_file_update_src_not_readable(dir_sync_obj: DirSync, temp_file):
    test_file_create(dir_sync_obj, temp_file)
    file_src = os.path.join(TEST_SRC_DIR, TEST_TEMPFILE_NAME)
    file_dst = os.path.join(TEST_DST_DIR, TEST_TEMPFILE_NAME)
    # update source file
    with open(file_src, 'w', encoding='utf-8') as file:
        file.write('bar')
    # save original permissions
    original_permissions = os.stat(file_src).st_mode
    try:
        # remove read permission before sync
        os.chmod(file_src, 0o222)
        dir_sync_obj.sync()
    except Exception as exp:
        warnings.warn(
            f'Failed to execute test scenario '
            f'"test_file_update_src_not_readable" ({exp}).'
            )
    finally:
        # restore permissions
        os.chmod(file_src, original_permissions)
    # assert MD5 hashes are different before re-sync
    assert dir_sync_obj._is_md5_different(file_src, file_dst) is True
    # sync again and check if hashes are now the same
    dir_sync_obj.sync()
    assert dir_sync_obj._is_md5_different(file_src, file_dst) is False


@pytest.mark.parametrize("allow_force_copy", [False, True])
def test_file_update_dst_not_writable(
    dir_sync_obj: DirSync, temp_file, allow_force_copy
):
    test_file_create(dir_sync_obj, temp_file)
    file_src = os.path.join(TEST_SRC_DIR, TEST_TEMPFILE_NAME)
    file_dst = os.path.join(TEST_DST_DIR, TEST_TEMPFILE_NAME)
    # update source file
    with open(file_src, 'w', encoding='utf-8') as file:
        file.write('bar')
    # save original permissions
    original_permissions = os.stat(file_dst).st_mode
    try:
        # remove write permission before sync
        os.chmod(file_dst, 0o444)
        dir_sync_obj.settings.force_copy = allow_force_copy
        dir_sync_obj.sync()
    except Exception as exp:
        warnings.warn(
            f'Failed to execute test scenario '
            f'"test_file_update_unsufficient_rights" ({exp}).'
            )
    finally:
        # restore permissions
        os.chmod(file_dst, original_permissions)
    if allow_force_copy:
        # if force_copy, syncer should be able to adjust permissions right away
        assert dir_sync_obj._is_md5_different(file_src, file_dst) is False
    else:
        assert dir_sync_obj._is_md5_different(file_src, file_dst) is True
    # sync again and check if hashes are now the same
    dir_sync_obj.sync()
    assert dir_sync_obj._is_md5_different(file_src, file_dst) is False


def test_file_delete(dir_sync_obj: DirSync, temp_file):
    test_file_create(dir_sync_obj, temp_file)
    file_src = os.path.join(TEST_SRC_DIR, TEST_TEMPFILE_NAME)
    file_dst = os.path.join(TEST_DST_DIR, TEST_TEMPFILE_NAME)
    # delete the source file
    os.remove(file_src)
    # sync and check if the destination file is also removed
    dir_sync_obj.sync()
    assert not os.path.exists(file_dst)
