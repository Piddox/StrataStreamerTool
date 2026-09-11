# Strata Streamer Tool

Strata Streamer Tool is a Windows application for streamers using the [Strata](https://strata.gamereplays.org/) rating system on Generals Online.

It automatically monitors your current replay file, detects when a match has finished, retrieves your latest Strata rating and rank, and writes the results to text files that can be displayed in OBS.

You do not need Python or any programming knowledge to use the packaged Windows version.

## Download

Download the latest version from the [Releases](https://github.com/Piddox/StrataStreamerTool/releases/latest) page.

For normal use, you only need:

-   `StrataStreamerTool.exe`
-   `strata_streamer_source.lua` if you want to use the optional OBS Lua integration. It is only needed if you want temporary rating/rank notifications in OBS.

The executable is standalone and does not require Python to be installed.

## What does it do?

Strata Streamer Tool is designed to make it easy to show Strata information on your Generals Online stream.

While you play, the tool:

1.  Monitors your Generals Online replay file.
2.  Detects when a qualifying 1v1 Internet game has finished.
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

The application validates your API token and lets you select which linked Generals Online account to use.

### Generals Online

The tool monitors the replay file created by Generals Online:

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
2.  Your Generals Online replay directory
3.  Which linked Generals Online account you want to use

The configuration is saved automatically.

Once setup is complete, the tool will begin monitoring your replay file.

### 3. Leave the tool running

You can minimize the console window while streaming.

You do not need to manually update anything after each match. The tool will detect qualifying games and update the output files automatically.

## OBS setup

The tool generates plain text files containing your current Strata information. OBS can read these files directly using its built-in text source functionality.

The simplest setup does not require the Lua script.

### Simple OBS setup

To display a Strata value in OBS:

1.  Create an OBS Text source.
2.  Enable **Read from file**.
3.  Select the Strata output file you want to display.
4.  Position and format the source as desired.

This is sufficient if you simply want your rating, rank, or another value to remain visible on your stream.

### Temporary text displays

The optional Lua integration can be used when you want a text source to appear temporarily after an update.

For example, you can use it to briefly display:

-   Rating gained or lost
-   Rank gained or lost
-   Other Strata update information

Download `strata_streamer_source.lua` from the same [release](https://github.com/Piddox/StrataStreamerTool/releases/latest) as the executable.

In OBS:

1.  Open **Tools → Scripts**.
2.  Add `strata_streamer_source.lua`.
3.  Configure the script instance for the desired Scene and Text Source.
4.  Select the Strata output file.
5.  Configure the desired display duration.

You can add multiple instances of the script.

If you use the Lua script for any Strata text source, use it for all Strata text sources that you want synchronized with the Strata output updates. This keeps the different sources synchronized.

The script supports text sources inside OBS groups and nested groups.

No external Lua installation is required.

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

The files are deliberately plain text so they can be used by OBS or other software without requiring an API integration.

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

Your Strata account must have at least one Generals Online account linked to it.

### The rating does not update after a game

The tool only retrieves a new rating from Strata after an qualifying game.

For example, AI games, LAN/Skirmish games, sandbox games, and other ineligible games will not trigger a rating update.

For a qualifying game, the tool also waits for the game to finish and for the result to become available in Strata before updating the output files.

### OBS is not updating a value

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
3.  Which linked Generals Online account you want to use

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

The application monitors the Generals Online replay file for changes.

When a new game starts, the replay file becomes active. When the game ends, the replay header is updated with the end time.

The application then waits for the configured rating-update delay and checks Strata until the match result is reflected in the player's rating data.

Once the new rating data is available, the output files are updated.

The OBS Lua script, when used, can react to those output updates and temporarily display selected text sources.

The application uses replay information to determine whether a game is eligible for a Strata rating update before contacting the Strata API.

## Related projects

Generals Online's game client is based on [The Super Hackers' GeneralsGameCode](https://github.com/TheSuperHackers/GeneralsGameCode), which is itself based on [EA's open-source release of Command & Conquer: Generals Zero Hour](https://github.com/electronicarts/CnC_Generals_Zero_Hour).

The [Generals Online GameClient](https://github.com/GeneralsOnlineDevelopmentTeam/GameClient) is a fork of The Super Hackers' project.

## Project status

Strata Streamer Tool is currently under active development.

The latest Windows executable is available on the [Releases](https://github.com/Piddox/StrataStreamerTool/releases/latest) page.

If you encounter a problem, please report it through the repository's [Issues](https://github.com/Piddox/StrataStreamerTool/issues) page.
