import argparse
import enum
import hashlib
import logging
import operator
import os
import shutil
import stat
import time
import typing


class ArgValidators:
    """
    A collection of static methods for validating different types of input
    arguments. These methods are designed to be used with the argparse module
    to ensure that command line arguments passed to the program are
    of the expected format and value.
    """

    @staticmethod
    def is_valid_src(path: typing.Any) -> str:
        """
        Verifies if a given path exists and is a directory.

        Args:
            path (typing.Any): The path to validate as a .

        Raises:
            argparse.ArgumentTypeError: If the path does not exist or
            is not a directory.

        Returns:
            str: The normalized path to the source directory if valid.
        """
        path = os.path.normpath(path)
        if not os.path.exists(path):
            err = f'Source directory "{path}" does not exist.'
            raise argparse.ArgumentTypeError(err)
        if not os.path.isdir(path):
            err = f'Source "{path}" is not a directory.'
            raise argparse.ArgumentTypeError(err)
        return path

    @staticmethod
    def is_valid_dst(path: typing.Any) -> str:
        """
        Ensures the path is a valid directory if it exists.

        Args:
            path (typing.Any): The path to validate as a destination directory.

        Raises:
            argparse.ArgumentTypeError: If the path exists but
            is not a directory.

        Returns:
            str: The normalized path to the destination directory if valid.
        """
        path = os.path.normpath(path)
        if os.path.exists(path) and not os.path.isdir(path):
            err = f'Destination "{path}" is not a directory.'
            raise argparse.ArgumentTypeError(err)
        return path

    @staticmethod
    def is_valid_logfile(path: typing.Any) -> str:
        """
        Validates if a given path can serve as a log file.
        Checks for file existence, type, and write permissions.

        Args:
            path (typing.Any): The path to validate as a log file.

        Raises:
            argparse.ArgumentTypeError: If the path is not a file,
            not writable, or its directory lacks required permissions.

        Returns:
            str: The normalized path to the logfile if valid.
        """
        path = os.path.normpath(path)
        if os.path.exists(path):
            if not os.path.isfile(path):
                err = f'"{path}" is not a file.'
                raise argparse.ArgumentTypeError(err)
            if not os.access(path, os.W_OK):
                err = f'File "{path}" is not writable.'
                raise argparse.ArgumentTypeError(err)
            required_access_mode = os.X_OK
        else:
            required_access_mode = os.W_OK | os.X_OK
        # check if every folder within the logfile path
        # has sufficient permissions
        path_split = path.split(os.sep)
        dir_names = (
            f"{os.sep}".join(path_split[:i+1])
            for i in range(len(path_split)-1)
            )
        for name in dir_names:
            if not os.access(name, required_access_mode):
                err = f'File directory "{name}" is not writable.'
                raise argparse.ArgumentTypeError(err)
        return path

    @staticmethod
    def is_positive_float(value: typing.Any) -> float:
        """
        Validates whether the provided value can be converted to
        a positive float.

        Args:
            value (typing.Any): The value to validate.
            Can be of any type that is convertible to a float.

        Raises:
            argparse.ArgumentTypeError: If the value cannot be converted to
            a float, or if the resulting float is not positive.

        Returns:
            float: The validated positive float value.
        """
        try:
            value = float(value)
        except Exception as exp:
            raise argparse.ArgumentTypeError(exp)
        if value <= 0:
            err = f'{value} is not a valid positive float value.'
            raise argparse.ArgumentTypeError(err)
        return value

    @staticmethod
    def is_log_level(level: typing.Any) -> int:
        """
        Validates and converts the given log level to its
        corresponding integer value.

        Args:
            level (typing.Any): The log level to validate.

        Raises:
            argparse.ArgumentTypeError: If the level is invalid.

        Returns:
            int: The integer value of the log level.
        """
        if isinstance(level, str):
            try:
                levels = logging.getLevelNamesMapping()
                level = levels[level.strip().upper()]
            except KeyError:
                raise argparse.ArgumentTypeError(f'Invalid log level: {level}')
        elif not isinstance(level, int) or level < 0:
            raise argparse.ArgumentTypeError(f'Invalid log level: {level}')
        return level

    @staticmethod
    def is_sync_mode(mode: typing.Any) -> 'SyncMode':
        """
        Validates and converts the given mode into a `SyncMode` enum.

        Args:
            mode (typing.Any): The synchronization mode to validate.

        Raises:
            argparse.ArgumentTypeError: If the mode
            is not a valid `SyncMode` enum member.

        Returns:
            SyncMode: The `SyncMode` enum member corresponding to
            the given mode.
        """
        try:
            mode = SyncMode(mode.strip().upper())
        except Exception as exp:
            err = f'Invalid synchronization mode: {mode} ({exp}).'
            raise argparse.ArgumentTypeError(err)
        return mode


def parse_args():
    parser = argparse.ArgumentParser(description="Directory Syncer")
    parser.add_argument(
        'src_dir',
        type=ArgValidators.is_valid_src,
        help='Path to the source directory.'
    )
    parser.add_argument(
        'dst_dir',
        type=ArgValidators.is_valid_dst,
        help='Path to the destination directory.'
    )
    parser.add_argument(
        '--sync_interval',
        type=ArgValidators.is_positive_float,
        default=2.0,
        help='Synchronization interval in seconds (default: %(default)s).'
    )
    parser.add_argument(
        '--sync_mode',
        default=SyncMode.FULL,
        type=ArgValidators.is_sync_mode,
        help=(
            'Synchronization mode: QUICK / FULL (default: %(default)s). '
            'QUICK mode relies on item metadata (size and time of last '
            'modification). FULL mode additionaly directly checks files\' '
            'contents.'
        )
    )
    parser.add_argument(
        '--sync_meta',
        action='store_true',
        help=(
            'Synchronize directories\' and files\' metadata, even if their '
            'contents have not been modified (default: False).'
        )
    )
    parser.add_argument(
        '--force_copy',
        action='store_true',
        help=(
            'Allow to temporarily modify destination items\' access rights if '
            'needed to perform synchronization operations (default: False).'
        )
    )
    parser.add_argument(
        '--log_file',
        type=ArgValidators.is_valid_logfile,
        default='sync.log',
        help='Name of the log file (default: ./%(default)s).'
    )
    parser.add_argument(
        '--console_log_level',
        default=logging.INFO,
        type=ArgValidators.is_log_level,
        help='Log level for console output (default: %(default)s).'
    )
    parser.add_argument(
        '--file_log_level',
        default=logging.DEBUG,
        type=ArgValidators.is_log_level,
        help='Log level for file output (default: %(default)s).'
    )
    args = parser.parse_args()
    return args


def setup_logger(
    logger: logging.Logger,
    log_file: str,
    console_log_level: int,
    file_log_level: int
) -> None:
    logger.setLevel(logging.DEBUG)
    # create console handler
    ch = logging.StreamHandler()
    ch.setLevel(console_log_level)
    # create file handler
    fh = logging.FileHandler(log_file)
    fh.setLevel(file_log_level)
    # create formatter and add it to the handlers
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    # add the handlers to the logger
    logger.addHandler(fh)
    logger.addHandler(ch)


logger = logging.getLogger('dir_sync')


class SyncMode(enum.StrEnum):
    """Directory synchronization modes"""
    QUICK = 'QUICK'
    """
    Relies on item metadata (e.g. file size or time of the last modification).
    Does NOT check file contents.
    """
    FULL = 'FULL'
    """
    Relies on item metadata (e.g. file size or time of the last modification).
    AND file contents. The latter are compared via MD5 hashes after
    the required metadata change is not detected.
    """


class DirSyncSettings:
    """
    Settings configuration for directory synchronization, including
    customization of the sync mode, behavior regarding file metadata, and
    control over modifying file permissions when necessary.
    """
    def __init__(
        self,
        sync_mode: typing.Union[SyncMode, str] = SyncMode.FULL,
        force_copy: bool = False,
        sync_meta: bool = False,
    ) -> None:
        """
        Initializes the `DirSyncSettings` object with the specified settings.

        Args:
            sync_mode (typing.Union[SyncMode, str], optional): Directory
            synchronization mode (QUICK or FULL). Defaults to SyncMode.FULL.
            force_copy (bool, optional): Allow to temporarily grant additional
            access permissions to mirrored items if needed. Defaults to False.
            sync_meta (bool, optional): Ebable additional metatada
            synchronization for items, the contents of which are not changed.
            Defaults to False.
        """
        self._sync_mode = self._to_sync_mode(sync_mode)
        self.force_copy = force_copy
        self.sync_meta = sync_meta

    @property
    def sync_mode(self) -> SyncMode:
        return self._sync_mode

    @sync_mode.setter
    def sync_mode(self, sync_mode: typing.Union[SyncMode, str]) -> None:
        self._sync_mode = self._to_sync_mode(sync_mode)

    @staticmethod
    def _to_sync_mode(sync_mode: typing.Union[SyncMode, str]) -> SyncMode:
        try:
            sync_mode_checked = ArgValidators.is_sync_mode(sync_mode)
        except argparse.ArgumentTypeError as err:
            raise ValueError(err)
        return sync_mode_checked


class DirSync:
    def __init__(
        self,
        src_dir: str,
        dst_dir: str,
        settings: typing.Optional[DirSyncSettings] = None
    ) -> None:
        self.src_dir = os.path.normpath(src_dir)
        self.dst_dir = os.path.normpath(dst_dir)
        if not settings:
            settings = DirSyncSettings()
        self.settings = settings
        self._original_st_modes: list[tuple[str, int]] = []

    def _get_src_path(self, dst_path: str) -> str:
        return dst_path.replace(self.dst_dir, self.src_dir, 1)

    def _get_dst_path(self, src_path: str) -> str:
        return src_path.replace(self.src_dir, self.dst_dir, 1)

    @staticmethod
    def _compare_timestamps(
        timestamp_1: typing.Union[int, float],
        timestamp_2: typing.Union[int, float],
        comparator: typing.Callable[
            [typing.Union[int, float], typing.Union[int, float]], bool
            ]
    ) -> bool:
        timestamp_1 = int(timestamp_1 * 1000)
        timestamp_2 = int(timestamp_2 * 1000)
        return comparator(timestamp_1, timestamp_2)

    @staticmethod
    def _calculate_md5(file_path) -> str:
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b''):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def _is_md5_different(self, file_path_1: str, file_path_2: str) -> bool:
        file_1_md5 = self._calculate_md5(file_path_1)
        file_2_md5 = self._calculate_md5(file_path_2)
        return file_1_md5 != file_2_md5

    def _create_dir(self, path: str, mode: int) -> tuple[bool, str]:
        logger.debug('Creating directory "%s" (mode: %o)', path, mode)
        try:
            os.mkdir(path, mode)
            logger.debug(
                'Successfully created directory "%s" (mode: %o)', path, mode
                )
            return True, ''
        except (OSError, IOError) as err:
            return False, str(err)

    def _create_symlink(self, src: str, dst: str) -> tuple[bool, str]:
        logger.debug('Creating symlink from "%s" to "%s"', src, dst)
        try:
            os.symlink(os.readlink(src), dst)
            logger.debug(
                'Successfully created symlink from "%s" to "%s"', src, dst
                )
            return True, ''
        except (OSError, IOError) as err:
            return False, str(err)

    def _create_file(self, src: str, dst: str) -> tuple[bool, str]:
        logger.debug('Copying file "%s" to "%s"', src, dst)
        if not os.access(src, os.R_OK):
            err = (
                f'Insufficient access permissions '
                f'(file "{src}" is not readable)'
                )
            return False, err
        try:
            shutil.copy2(src, dst)
            logger.debug('Successfully copied file "%s" to "%s"', src, dst)
            return True, ''
        except PermissionError as err:
            if not self.settings.force_copy:
                return False, str(err)
            try:
                logger.debug(
                    'Failed to copy file "%s" to "%s" (permission denied).'
                    'Attempting to temporarily grant additional permissions '
                    '(666) to file "%s"', src, dst, dst
                    )
                os.chmod(dst, 0o666)
                logger.debug(
                    'Successfully granted additional permissions (666) '
                    'to file "%s"', dst
                    )
                logger.debug('Copying file "%s" to "%s"', src, dst)
                shutil.copy2(src, dst)
                logger.debug('Successfully copied file "%s" to "%s"', src, dst)
                return True, ''
            except (OSError, IOError) as err:
                return False, str(err)
        except (OSError, IOError) as err:
            return False, str(err)

    def _remove(self, path: str, is_dir: bool) -> tuple[bool, str]:
        logger.debug('Removing "%s"', path)
        try:
            if is_dir:
                os.rmdir(path)
            else:
                os.remove(path)
            logger.debug('Successfully removed "%s"', path)
            return True, ''
        except PermissionError as err:
            if not self.settings.force_copy:
                return False, str(err)
            try:
                mode = 0o777 if is_dir else 0o666
                logger.debug(
                    'Failed to remove "%s" (permission denied).'
                    'Attempting to temporarily grant additional permissions '
                    '(%o) to "%s"', path, mode, path
                    )
                os.chmod(path, mode)
                logger.debug(
                    'Successfully granted additional permissions (%o) '
                    'to "%s"', mode, path
                    )
                logger.debug('Removing "%s"', path)
                if is_dir:
                    os.rmdir(path)
                else:
                    os.remove(path)
                logger.debug('Successfully removed "%s"', path)
                return True, ''
            except (OSError, IOError) as err:
                return False, str(err)
        except (OSError, IOError) as err:
            return False, str(err)

    def _sync_dir(self, src_dir: str, dst_dir: str) -> None:
        src_dir_stat = os.stat(src_dir)
        if not os.path.exists(dst_dir):
            logger.info('Creating directory "%s"', dst_dir)
            res, err = self._create_dir(dst_dir, src_dir_stat.st_mode)
            if res is False:
                logger.warning(
                    'Failed to create directory "%s" (%s)', dst_dir, err
                    )
            return
        dst_dir_stat = os.stat(dst_dir)
        if not stat.S_ISDIR(dst_dir_stat.st_mode):
            logger.info('Updating directory "%s"', dst_dir)
            res, err = self._remove(dst_dir, is_dir=False)
            if res is False:
                logger.warning(
                    'Failed to update directory "%s" (%s)', dst_dir, err
                    )
                return
            res, err = self._create_dir(dst_dir, src_dir_stat.st_mode)
            if res is False:
                logger.warning(
                    'Failed to update directory "%s" (%s)', dst_dir, err
                    )
        elif (
            self.settings.sync_meta and
            self._compare_timestamps(
                src_dir_stat.st_mtime, dst_dir_stat.st_mtime, operator.ne
                ) or
            src_dir_stat.st_uid != dst_dir_stat.st_uid or
            src_dir_stat.st_gid != dst_dir_stat.st_gid
        ):
            logger.info('Updating directory metadata "%s"', dst_dir)
            try:
                shutil.copystat(src_dir, dst_dir)
            except (OSError, IOError) as err:
                logger.warning(
                    'Failed to update directory metadata "%s" (%s)',
                    dst_dir, err
                    )

    def _sync_dirs(
        self, src_root: str, dst_root: str, dirs: list[str]
    ) -> None:
        if not os.access(dst_root, os.R_OK | os.W_OK | os.X_OK):
            if self.settings.force_copy:
                original_st_mode = (dst_root, os.stat(dst_root).st_mode)
                self._original_st_modes.append(original_st_mode)
                try:
                    logger.debug(
                        'Failed to access directory "%s" (Insufficient access '
                        'permissions). Attempting to temporarily grant '
                        'additional permissions (777) to directory "%s"',
                        dst_root, dst_root
                        )
                    os.chmod(dst_root, 0o777)
                    logger.debug(
                        'Successfully granted additional permissions (777) '
                        'to directory "%s"', dst_root
                        )
                except (OSError, IOError) as err:
                    logger.warning(
                        'Failed to access directory "%s" (%s)', dst_root, err
                        )
                    return
            else:
                logger.warning(
                    'Failed to access directory "%s" (Insufficient access '
                    'permissions)', dst_root
                    )
                return
        for dir_name in dirs:
            src_dir = os.path.join(src_root, dir_name)
            dst_dir = os.path.join(dst_root, dir_name)
            self._sync_dir(src_dir, dst_dir)

    def _sync_symlink(self, src_symlink: str, dst_symlink: str) -> None:
        if not os.path.exists(dst_symlink):
            logger.debug(
                'Creating symlink from "%s" to "%s"', src_symlink, dst_symlink
                )
            res, err = self._create_symlink(src_symlink, dst_symlink)
            if res is False:
                logger.warning(
                    'Failed to create symlink from "%s" to "%s" (%s)',
                    src_symlink, dst_symlink, err
                    )
            return
        src_stat = os.lstat(src_symlink)
        dst_stat = os.lstat(dst_symlink)
        if (
            not stat.S_ISLNK(dst_stat.st_mode) or
            os.readlink(src_symlink) != os.readlink(dst_symlink)
        ):
            logger.info('Updating symlink "%s"', dst_symlink)
            is_dir = stat.S_ISDIR(dst_stat.st_mode)
            res, err = self._remove(dst_symlink, is_dir)
            if res is False:
                logger.warning(
                    'Failed to update symlink "%s" (%s)', dst_symlink, err
                    )
                return
            res, err = self._create_symlink(src_symlink, dst_symlink)
            if res is False:
                logger.warning(
                    'Failed to update symlink "%s" (%s)', dst_symlink, err
                    )
        elif (
            self.settings.sync_meta and
            self._compare_timestamps(
                src_stat.st_mtime, dst_stat.st_mtime, operator.ne
                )
        ):
            logger.info('Updating symlink metadata "%s"', src_symlink)
            try:
                new_timestamps = (src_stat.st_atime, src_stat.st_mtime)
                os.utime(dst_symlink, new_timestamps, follow_symlinks=False)
            except (OSError, IOError) as err:
                logger.warning(
                    'Failed to update symlink metadata "%s" (%s)',
                    dst_symlink, err
                    )

    def _sync_file(self, src_file: str, dst_file: str) -> None:
        if not os.path.exists(dst_file):
            logger.info('Creating file "%s"', dst_file)
            res, err = self._create_file(src_file, dst_file)
            if res is False:
                logger.warning(
                    'Failed to create file "%s" (%s)', dst_file, err
                    )
            return
        src_stat = os.stat(src_file)
        dst_stat = os.stat(dst_file)
        if not stat.S_ISREG(dst_stat.st_mode):
            logger.info('Updating file "%s"', dst_file)
            is_dir = stat.S_ISDIR(dst_stat.st_mode)
            res, err = self._remove(dst_file, is_dir)
            if res is False:
                logger.warning(
                    'Failed to update file "%s" (%s)', dst_file, err
                    )
                return
            res, err = self._create_file(src_file, dst_file)
            if res is False:
                logger.warning(
                    'Failed to update file "%s" (%s)', dst_file, err
                    )
        elif (
            src_stat.st_size != dst_stat.st_size or
            self._compare_timestamps(
                src_stat.st_mtime, dst_stat.st_mtime, operator.gt
                ) or
            (
                self.settings.sync_mode == SyncMode.FULL and
                self._is_md5_different(src_file, dst_file)
            )
        ):
            logger.info('Updating file "%s"', dst_file)
            res, err = self._create_file(src_file, dst_file)
            if res is False:
                logger.warning(
                    'Failed to update file "%s" (%s)', dst_file, err
                    )
        elif (
            self.settings.sync_meta and
            src_stat.st_mode != dst_stat.st_mode or
            src_stat.st_uid != dst_stat.st_uid or
            src_stat.st_gid != dst_stat.st_gid
        ):
            try:
                logger.info('Updating file metadata "%s"', dst_file)
                shutil.copystat(src_file, dst_file)
            except (OSError, IOError) as err:
                logger.warning(
                    'Failed to update file metadata "%s" (%s)', dst_file, err
                    )

    def _sync_files_symlinks(
        self, src_root: str, dst_root: str, files: list[str]
    ) -> None:
        for file in files:
            src = os.path.join(src_root, file)
            dst = os.path.join(dst_root, file)
            if os.path.islink(src):
                self._sync_symlink(src, dst)
            elif os.path.isfile(src):
                self._sync_file(src, dst)
            else:
                logging.warning(
                    'Failed to synchronize item "%s" (item type is not '
                    'supported)', src
                    )

    def _sync_deleted(self) -> None:
        rm_dirs = []
        rm_files = []
        for dst_root, dirs, files in os.walk(self.dst_dir):
            src_root = self._get_src_path(dst_root)
            if not os.path.exists(src_root):
                rm_dirs.append(dst_root)
            for file in files:
                src_file_path = os.path.join(src_root, file)
                if not os.path.exists(src_file_path):
                    dst_file_path = os.path.join(dst_root, file)
                    rm_files.append(dst_file_path)
        for file_path in rm_files:
            item = 'file' if os.path.isfile(file_path) else 'symlink'
            logger.info('Removing %s "%s"', item, file_path)
            res, err = self._remove(file_path, is_dir=False)
            if res is False:
                logger.warning(
                    'Failed to remove %s "%s" (%s)', item, file_path, err
                    )
        for dir_path in rm_dirs:
            logger.info('Removing directory: "%s"', dir_path)
            res, err = self._remove(dir_path, is_dir=True)
            if res is False:
                logger.warning(
                    'Failed to remove directory "%s" (%s)', dir_path, err
                    )

    def _restore_access_modes(self) -> None:
        for path, mode in self._original_st_modes:
            try:
                os.chmod(path, mode)
            except (OSError, IOError) as err:
                logger.warning(
                    'Failed to restore directory access mode "%s" (%s)',
                    path, err
                    )
        self._original_st_modes.clear()

    def sync(self) -> None:
        """
        Performs a one-time synchronization from the source directory to the
        destination directory.

        This method ensures that the destination directory mirrors the content
        of the source directory after it is called. It handles file creation,
        updates, and deletion as needed to achieve this.
        """
        logger.debug('Synchronizing...')
        if os.path.exists(self.dst_dir):
            self._sync_deleted()
        else:
            logger.info('Creating directory "%s"', self.dst_dir)
            self._create_dir(self.dst_dir, mode=os.stat(self.src_dir).st_mode)
        for src_root, dirs, files in os.walk(self.src_dir):
            dst_root = self._get_dst_path(src_root)
            self._sync_dirs(src_root, dst_root, dirs)
            self._sync_files_symlinks(src_root, dst_root, files)
        self._restore_access_modes()
        logger.debug('Synchronization finished')

    def sync_forever(self, interval: float = 1.0) -> None:
        """
        Continuously performs synchronization from the source directory to the
        destination directory at specified intervals by calling the `sync`
        method repeatedly at the given interval. The process can be stopped
        with a keyboard interrupt.

        Args:
            interval (float, optional): The time interval (in seconds) at which
            synchronization should be repeated. Defaults to 1.0 seconds.
        """
        logger.info(
            'Initializing synchronization of directory "%s" to directory "%s"',
            self.src_dir, self.dst_dir
            )
        try:
            interval = ArgValidators.is_positive_float(interval)
        except argparse.ArgumentTypeError as err:
            logger.critical('Aborting: %s', err)
            return
        try:
            while True:
                self.sync()
                time.sleep(interval)
        except KeyboardInterrupt:
            logger.info('Synchronization stopped by keyboard interrupt')
        except Exception as exp:
            logger.critical('Unexpected exception occured: %s', exp)
        finally:
            self._restore_access_modes()


def main() -> None:
    args = parse_args()
    setup_logger(
        logger,
        log_file=args.log_file,
        console_log_level=args.console_log_level,
        file_log_level=args.file_log_level
        )
    settings = DirSyncSettings(
        sync_mode=args.sync_mode,
        force_copy=args.force_copy,
        sync_meta=args.sync_meta
        )
    sync_manager = DirSync(args.src_dir, args.dst_dir, settings)
    sync_manager.sync_forever(interval=args.sync_interval)


if __name__ == "__main__":
    main()
