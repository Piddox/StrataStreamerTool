# Strata Streamer Tool

Strata Streamer Tool is a Windows application for streamers using the [Strata](https://strata.gamereplays.org/) rating system on Generals Online (GO).

It automatically monitors your current replay file, detects when a match has finished, retrieves your latest Strata rating and rank, and writes the results to text files that can be displayed in OBS.

It also includes a graphical HUD overlay that can be displayed in OBS using a Browser Source.

For discussion, feedback, updates and support, see the [Strata Streamer Tool topic on GameReplays.org](https://www.gamereplays.org/community/index.php?showtopic=1084697).

You do not need Python or any programming knowledge to use the packaged Windows version.

## For Streamers

If you use Strata Streamer Tool on your stream, please include a link to Strata in your stream description.

This is expected for streams on YouTube, Twitch, Kick, and other streaming platforms.

[https://strata.gamereplays.org/](https://strata.gamereplays.org/)

## Download

Download the latest version from the [Releases](https://github.com/Piddox/StrataStreamerTool/releases/latest) page.

For normal use, you only need:

-   `StrataStreamerTool.exe`
-   `strata_streamer_watchdog.lua` if you want to use the graphical overlay with automatic OBS refresh.

The executable is standalone and does not require Python to be installed.

## What does it do?

Strata Streamer Tool is designed to make it easy to show Strata information on your stream.

While you play, the tool:

1.  Monitors your GO game client's replay file.
2.  Detects when an eligible 1v1 game has finished.
3.  Waits for the match result to appear in Strata.
4.  Retrieves your updated rating and rank.
5.  Updates text files containing your Strata information.
6.  Allows OBS to display those files automatically.

The tool does not need to be interacted with during normal use. Start it before playing and leave it running in the background.

## Requirements

### Windows

-   Windows 10 or later, 64-bit
-   Administrator privileges are not required

### Strata

You need:

-   A Strata account
-   A valid Strata API token
-   At least one Generals Online account linked to your Strata account

The application validates your API token and lets you select which linked GO account to use.

### Generals Online game client

The tool monitors the replay file created by the GO game client:

``` text
00000000.rep
```

The normal replay directory is:

``` text
%USERPROFILE%\Documents\Command and Conquer Generals Zero Hour Data\Replays
```

Your actual location may differ depending on your installation and
Windows configuration. The setup wizard asks you for your replay
directory and checks that the required replay file is present.

## Installation

### 1. Download the application

Download `StrataStreamerTool.exe` from the latest [release](https://github.com/Piddox/StrataStreamerTool/releases/latest).

You can put it anywhere you like, for example on your Desktop or in a dedicated folder.

Administrator privileges are not required to run it.

### 2. Start the tool

Run:

``` text
StrataStreamerTool.exe
```

On first launch, the setup wizard will ask for:

1.  Your Strata API token
2.  Your game's replay directory
3.  Which linked GO account you want to use

The configuration is saved automatically.

Once setup is complete, the tool will begin monitoring your replay file.

### 3. Leave the tool running

You can minimize the console window while streaming.

You do not need to manually update anything after each match. The tool will detect qualifying games and update the output files automatically.

## OBS setup

Strata Streamer Tool provides two ways to display Strata information in OBS:

1. The graphical HUD overlay
2. Plain-text output files

The graphical overlay is the recommended method for new setups.

### Graphical HUD overlay

The graphical overlay provides a complete HUD that displays your Strata information and automatically changes its position depending on whether you are in-game or in the game menu.

It is displayed in OBS using a Browser Source.

#### Basic setup

1. Start `StrataStreamerTool.exe`.
2. In OBS, add a **Browser Source**.
3. Set the Browser Source URL to:

```text
http://127.0.0.1:1337/overlay
```

4. Set the Browser Source dimensions to match your streaming resolution.
5. Position the Browser Source where you want it in your OBS scene.

The overlay supports 1920×1080 and 2560×1440 streaming resolutions.

The Browser Source should remain in your OBS scene while Strata Streamer Tool is running.

#### Overlay settings

The graphical overlay can be configured through the built-in settings page.

With Strata Streamer Tool running, open:

```text
http://127.0.0.1:1337/settings
```

The settings page lets you configure both HUD panels independently.

For each HUD, you can configure:

-   Visibility: always, in-game only, in-menu only, or never
-   Whether the HUD is hidden while observing a match
-   The information template
-   Overall or Monthly ladder information
-   Artwork size
-   Artwork color, including automatic faction-dependent artwork
-   Position mode
-   In-game position
-   In-menu position

The position mode determines which position is used:

-   **In-game** always uses the configured in-game position.
-   **In-menu** always uses the configured in-menu position.
-   **Automatic** switches between the two depending on whether you are currently in a game or not.

The settings are saved when you click **Save settings** and are stored in:

```text
%APPDATA%\StrataStreamerTool\config.json
```

The settings page does not need to remain open. Once the settings have been saved, close the page and leave the OBS Browser Source running as normal.

#### Automatic OBS refresh

The release includes `strata_streamer_watchdog.lua`, an optional OBS helper script that automatically refreshes the Browser Source when Strata Streamer Tool starts, stops, or crashes.

This is useful when OBS starts before Strata Streamer Tool, or when the application is restarted while OBS is already running.

To install it:

1. Open **Tools → Scripts** in OBS.
2. Add `strata_streamer_watchdog.lua`.
3. Select the Browser Source used for the Strata graphical overlay.
4. Leave the default check interval unless you have a reason to change it.

The watchdog does not continuously refresh the Browser Source. It only requests a refresh when the availability of Strata Streamer Tool changes.

No external Lua installation is required.

### Plain-text output files

The application also continues to generate plain-text files containing your current Strata information.

These can be displayed using OBS's built-in **Read from file** option.

To display a Strata value:

1. Create an OBS Text source.
2. Enable **Read from file**.
3. Select the Strata output file you want to display.
4. Position and format the source as desired.

This is useful if you want to create your own OBS layout instead of using the graphical overlay.

### Temporary text displays

The optional Lua integration can be used when you want a text source to appear temporarily after an update.

For example, you can use it to briefly display:

-   Rating gained or lost
-   Rank gained or lost
-   Other Strata update information

Download `strata_streamer_source.lua` from the same [release](https://github.com/Piddox/StrataStreamerTool/releases/latest) as the executable.

For more detailed OBS setup instructions, see [OBS Integration](https://github.com/Piddox/StrataStreamerTool/blob/main/obs/README.md).

## Output files

The application generates text files for the Strata information
available to OBS, including:

-   Overall rating
-   Overall rating change
-   Overall rank
-   Overall rank change
-   Monthly rating
-   Monthly rating change
-   Monthly rank
-   Monthly rank change
-   Session rating change
-   Session rank change
-   Combined rating/rank labels

The files are deliberately plain text so they can be used by OBS or other software without requiring an API integration. The graphical overlay uses the same Strata data while providing a complete HUD without requiring individual OBS Text sources.

### Where are the files?

When using the packaged Windows executable, the output files are stored
in:

``` text
%LOCALAPPDATA%\StrataStreamerTool\output
```

The application creates this directory automatically.

Your configuration is stored separately in:

``` text
%APPDATA%\StrataStreamerTool\config.json
```

You do not need to create either directory manually.

The application also displays the output directory during setup so you can easily find it when configuring OBS.

## Using the output files in OBS

If you are unsure which file to use, the filenames describe the information they contain.

For example:

``` text
overall_elo.txt
```

contains your current overall rating, while:

``` text
overall_elo_change.txt
```

contains the rating change from the most recent match.

The exact list of files is available in the application's output directory.

## Troubleshooting

### The graphical overlay is not displayed in OBS

Make sure:

-   Strata Streamer Tool is running.
-   The OBS Browser Source is configured with the correct local overlay URL.
-   The Browser Source is not hidden in the current scene.
-   The Browser Source dimensions match the intended streaming resolution.

If the overlay was configured while Strata Streamer Tool was not running, start the application and refresh the Browser Source.

If you have installed `strata_streamer_watchdog.lua`, make sure the correct Browser Source is selected in the script settings.

### The application cannot find the replay file

Check the replay directory configured in the application.

It should contain:

``` text
00000000.rep
```

The game must be creating the replay file in that directory.
The replay usually resides in the  \Command and Conquer Generals Zero Hour Data\Replays folder inside your Documents folder.

### The Strata token is rejected

Make sure:

-   The API token is valid.
-   The computer has an internet connection.
-   The token belongs to the correct Strata account.

### No linked Generals Online account is available

Your Strata account must have at least one GO account linked to it.

### The rating does not update after a game

The tool only retrieves a new rating from Strata after an qualifying game.

For example, AI games, LAN/Skirmish games, sandbox games, and other ineligible games will not trigger a rating update.

For a qualifying game, the tool also waits for the game to finish and for the result to become available in Strata before updating the output files.

### OBS text source is not updating a value

If you are using OBS's built-in **Read from file** option, verify that the Text source points to the correct file in:

``` text
%LOCALAPPDATA%\StrataStreamerTool\output
```

If you are using the Lua script, verify that the correct Scene, Text Source, and output file are selected in the script instance.

If you use multiple Strata text sources with temporary display durations, configure all of them through copies of the same Lua script so they share the same update mechanism.

## Running from source

This section is only relevant if you want to run or modify the Python source code.

The packaged Windows executable does not require Python.

### Requirements

-   Python 3.11 or newer
-   64-bit Python is recommended

Install the required package with:

``` bat
python -m pip install -r requirements.txt
```

The only third-party dependency is:

``` text
requests>=2.31.0
```

### Start the application from source

From the repository directory:

``` bat
python src\main.py
```

On first launch, the setup wizard will ask for:

1.  Your Strata API token
2.  Your Zero Hour replay directory
3.  Which linked GO account you want to use

The configuration is saved automatically.

### Testing the OBS setup without playing a match

The repository includes a manual simulation utility:

``` bat
python src\simulate_matches.py
```

This simulates one match and updates the output files.

To simulate multiple matches:

``` bat
python src\simulate_matches.py 5
```

Multiple simulations are separated by a short delay of 10 seconds so that the output and OBS behavior can be observed.

This utility does not contact the Strata API and uses generated test data.

## How it works

The application monitors the game's replay file for changes.

When a new game starts, the replay file becomes active. When the game ends, the replay header is updated with the end time.

The application then waits for the configured rating-update delay and checks Strata until the match result is reflected in the player's rating data.

Once the new rating data is available, the output files are updated.

The graphical overlay uses the local overlay server to display the current Strata information in OBS.

The OBS watchdog can monitor the availability of the local overlay server and refresh the Browser Source when Strata Streamer Tool starts, stops, or crashes.

The OBS Lua script, when used, can react to those output updates and temporarily display selected text sources.

The application uses replay information to determine whether a game is eligible for a Strata rating update before contacting the Strata API.

## Related projects

GO's game client is based on [The Super Hackers' GeneralsGameCode](https://github.com/TheSuperHackers/GeneralsGameCode), which is itself based on [EA's open-source release of Command & Conquer: Generals Zero Hour](https://github.com/electronicarts/CnC_Generals_Zero_Hour).

The [Generals Online GameClient](https://github.com/GeneralsOnlineDevelopmentTeam/GameClient) is a fork of The Super Hackers' project.

## Project status

Strata Streamer Tool is currently under active development.

The latest Windows executable is available on the [Releases](https://github.com/Piddox/StrataStreamerTool/releases/latest) page.

If you encounter a problem, please report it through the repository's [Issues](https://github.com/Piddox/StrataStreamerTool/issues) page.
