# FolderSyncer

FolderSyncer is a Windows-based application designed to synchronize two folders on a scheduled basis. It provides a user-friendly interface for setting up folder pairs, specifying synchronization times, and managing notifications. FolderSyncer runs in the system tray, allowing you to manage your sync tasks without keeping the main window open.

## Features

- **Easy Setup**: Add new folder pairs to sync with a few clicks.
- **Scheduled Syncing**: Set specific times to automatically synchronize your folders daily.
- **Manual Sync**: Start synchronization manually at any time.
- **Notification Management**: Enable or disable notifications for individual sync tasks or globally.
- **Progress Tracking**: View the progress of ongoing syncs with real-time updates.
- **System Tray Integration**: The app minimizes to the system tray, allowing it to run quietly in the background.

## Installation

You can download the latest version of FolderSyncer from the [Releases](https://github.com/Amirabbasjadidi/FolderSyncer/releases) section. 

1. Download the `SyncSetup.exe` file from the latest release.
2. Run the installer and follow the on-screen instructions.

Once installed, you can launch FolderSyncer from the Start menu or by double-clicking its icon on your desktop.

## Usage

1. **Add New Sync Schedule**: Click on the "Add New Schedule" button, select the folders you wish to sync, and set the time.
2. **Manual Sync**: Click the "Sync Now" button to start syncing immediately.
3. **Sync Status**: Click on the "Sync Status" button to view the progress of your sync tasks.
4. **Toggle Notifications**: Use the "All Notifications" button to enable or disable notifications for all sync tasks.
5. **System Tray**: FolderSyncer runs in the system tray. Right-click on the tray icon to show the main window or exit the application.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/Amirabbasjadidi/FolderSyncer/blob/main/LICENSE) file for details.

## Contributing

Contributions are welcome! Please open an issue to discuss what you would like to change or add. You can also fork the repository and submit a pull request with your improvements.

## Known Issues

- Currently, FolderSyncer is optimized for Windows. Compatibility with other operating systems is not guaranteed.
- Large folders may take time to sync depending on the size and number of files.

## Acknowledgments

This project uses the following libraries:

- `Tkinter` for the graphical user interface
- `pystray` for system tray integration
- `schedule` for handling scheduled tasks
- `Pillow` for image processing in the system tray icon

## Contact

If you have any questions, issues, or suggestions, feel free to contact me via [GitHub Issues](https://github.com/Amirabbasjadidi/FolderSyncer/issues).

---

Thank you for using FolderSyncer! Your feedback is highly appreciated.
