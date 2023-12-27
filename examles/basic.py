import logging

from dir_sync import DirSync


def main():
    # Paths for the source and destination directories
    src_dir = '/path/to/source/directory'
    dst_dir = '/path/to/destination/directory'

    # Create a DirSync instance with default settings
    dir_syncer = DirSync(src_dir, dst_dir)

    # Perform the synchronization
    dir_syncer.sync()

    # For continuous sync, use:
    # dir_syncer.sync_forever(interval=60)  # Sync every 60 seconds,
    #                                       # interrupt by CTRL+C


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(levelname)s - %(message)s'
        )
    main()
