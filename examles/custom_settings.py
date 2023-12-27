import logging

from dir_sync import DirSync, DirSyncSettings, SyncMode


def main():
    # Define source and destination directories
    src_dir = '/path/to/source/directory'
    dst_dir = '/path/to/destination/directory'

    # Initialize DirSyncSettings with custom settings
    initial_settings = DirSyncSettings(
        sync_mode=SyncMode.FULL,    # Start with FULL mode
        force_copy=True,            # Allow force copying files
        sync_meta=True              # Sync metadata
    )

    # Create DirSync instance with the initial settings
    dir_syncer = DirSync(src_dir, dst_dir, settings=initial_settings)

    # Perform initial synchronization
    dir_syncer.sync()

    # Adjust settings after initialization
    dir_syncer.settings.sync_mode = SyncMode.QUICK  # Change to FULL sync mode
    dir_syncer.settings.sync_meta = False           # Disable syncing metadata

    # Perform synchronization with adjusted settings
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
