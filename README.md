# Mini Pico W OLED Departure Boards for Model Railway

This project uses a Raspberry Pi Pico with an OLED display to show departure boards for a model railway.

## Author

Adam Knowles

## Version

0.1

## Description

This project uses a Raspberry Pi Pico with an OLED display to show departure boards for a model railway. The departure data is fetched from a remote server and displayed on the OLED display.

## Features

1. **Live, real-time Departure Data**: Fetches real-time departure data from raildata.org.uk via a product from the Rail Data Group. This data source is reliable, free, for personal/hobby use, with unlimited access. The program also syncs the current time on startup.

2. **Travel Alerts**: Displays any relevant travel alerts on the available screens.

3. **Runs on Raspberry Pi Pico**: Built for the Raspberry Pi Pico, a cheap, easily available, small and versatile microcontroller.

4. **Runs two platform screens**: Runs one or two OLED (SSD1306) screens, the maximum for the 2 x I2C buses on the Pico. Each screen displays the first and second departures for that platform. Each screen will also show the "due" time for any delays on the first departure, and the calling points for the first departure.

## Installation

1. Clone the repository:

    ```bash
    git clone https://github.com/Pharkie/picow-railway-departure.git
    ```

2. Navigate to the project directory

## Usage

1. Run main.py

## Known Issues

The application doesn't handle DST change while the device is running, since it only checks at startup.

Working memory is limited on the Pico, so large API responses for rail data may crash the system?

## License

This project is licensed under the GNU General Public License (GPL).

## Acknowledgements

This project is based on work by Stewart Watkiss - PenguinTutor. 

Models for the 3D printed casing for the OLED panel(s) can be found in the upstream repo, as can docs for the SSD1306 and some other aspects I didn't wish to duplicate or extend.