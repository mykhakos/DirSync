
# `dir_sync`: One-Way Directory Synchronization Tool

`dir_sync` is a pure Python library designed for one-way synchronization of files and directories from a source directory to a destination directory. It provides a flexible and efficient way to ensure that the destination directory mirrors the content of the source directory, with options for handling file metadata, file content checks, and access permissions.

## Features

- **One-way synchronization:** Mirrors the content from the source directory to the destination directory.
- **Two sync modes:** Users can choose between QUICK and FULL synchronization modes. QUICK mode relies on item metadata (e.g., file size or time of the last modification), while FULL mode additionally checks files' MD5 hashes if the required metadata has not changed.
- **Separate metadata sync:** Users may opt for additional metadata synchronization for items whose contents have not been modified.
- **Overridable access permissions:** Allows users to temporarily grant additional access permissions to mirrored items if needed.
- **Logging capabilities:** Provides detailed logs for tracking and debugging.
- **CLI and library usage:** Can be used both as a command-line tool and imported as a library in other Python scripts.
- **Cross-platform compatibility:** Works on multiple operating systems. Requires Python 3.6+.

## Installation

This tool can be installed using pip:

```
pip install "git+https://github.com/mykhakos/DirSync.git"
```

## Usage

### As a Command-Line Tool

You can use `dir_sync` directly from the command line. For example:

```
dir_sync /path/to/source /path/to/destination
```

Additional options are available for more detailed configurations. Use `--help` to see all options.

### As a Library

`dir_sync` can also be imported and used in Python scripts. Here's an example:

```python
from dir_sync import DirSync, DirSyncSettings, SyncMode

syncer = DirSync("/path/to/source", "/path/to/destination")
syncer.sync()
```
See more detailed examples in the **/examples** directory.

## Code Style

The code for `dir_sync` adheres to PEP 8 style guidelines and employs static typing, ensuring readability and maintainability.

## Contributing

Contributions to `dir_sync` are welcome! Please open an issue for any suggestions or enhancements.

## License

`dir_sync` is distributed under the MIT License. See LICENSE for more information.
