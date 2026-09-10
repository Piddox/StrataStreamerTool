# Strata Streamer Tool

Strata Streamer Tool is a Windows application for streamers using the Strata GameReplays rating system with Command & Conquer Generals: Zero Hour.

It monitors the Zero Hour replay file, retrieves the player's current Strata rating and rank, and writes values to text files that can be displayed in OBS.

## Requirements

### Windows

- Windows 10 or later, 64-bit
- Administrator privileges are not required

### Python

- Python 3.11 or newer
- 64-bit Python is recommended

### Python packages

Install the required package with:

```bat
python -m pip install -r requirements.txt
```

The only third-party dependency is:

```text
requests>=2.31.0
```

### Strata

You need:

- A Strata account
- A valid Strata API token
- At least one Generals Online account linked to your Strata account

The application validates the API token and retrieves your linked Generals Online accounts during setup.

### Generals: Zero Hour

The application monitors the Zero Hour replay file:

```text
00000000.rep
```

The normal replay directory is:

```text
%USERPROFILE%\Documents\Command and Conquer Generals Zero Hour Data\Replays
```

Your actual location may differ depending on your installation and Windows configuration. The setup wizard asks for the replay directory and verifies that the required replay file is present.

### OBS Studio

OBS is only required if you want to display the generated values in your stream.

The Strata Streamer Tool does **not** require the OBS Lua script for normal operation.

OBS can read the generated text files directly using its built-in **Read from file** option. This is sufficient when all text sources should remain visible normally.

The included Lua script is useful when you want one or more text sources to appear only briefly after an update.

If you use the Lua script for one temporary text source, it is recommended that you use the Lua script for **all Strata text sources**. This keeps the different Strata sources synchronized when the application updates them.

No external Lua installation is required.

### OBS Lua script

The Lua script is optional. OBS can display the generated text files directly using its built-in **Read from file** option.

The included Lua script is only needed if you want text sources to appear temporarily after an update. If you use the Lua script for one Strata text source, use it for all Strata text sources that you want synchronized.

For detailed OBS setup instructions, including script configuration, trigger files, temporary displays, synchronization, and grouped sources, see [OBS Integration](obs/README.md).

## Installation

Clone or download the repository.

Open Command Prompt in the repository directory and install the Python dependency:

```bat
python -m pip install -r requirements.txt
```

Start the application:

```bat
python src\main.py
```

On first launch, the setup wizard will ask for:

1. Your Strata API token
2. Your Zero Hour replay directory
3. Which linked Generals Online account you want to use

The configuration is saved automatically.

After setup, the application can be started again with:

```bat
python src\main.py
```

## Configuration

The application stores its configuration in:

```text
%APPDATA%\StrataStreamerTool\config.json
```

The generated output files are stored in:

```text
output\
```

inside the Strata Streamer Tool directory.

You do not need to create these directories manually.

The application provides commands for changing configuration while it is running. See the console output for the available commands.

## OBS setup

The application continuously updates a collection of text files containing the current Strata information.

To display a value in OBS without using the Lua script:

1. Create an OBS Text source.
2. Enable **Read from file**.
3. Select the appropriate Strata output file.
4. Position and format the source as desired.

This is the simplest setup and is sufficient if you do not need temporary text sources.

### Using the Lua script

Use the included script:

```text
obs\strata_streamer_source.lua
```

when you want a text source to be displayed for a limited amount of time after an update.

In OBS:

1. Open **Tools → Scripts**.
2. Add `strata_streamer_source.lua`.
3. Configure the script instance for the desired Scene and Text Source.
4. Select the Strata output file and configure the desired display duration.

You can add multiple instances of the script.

If you use the Lua script for any Strata text source, use it for all Strata text sources that you want synchronized with the Strata output updates.

The script supports text sources inside OBS groups and nested groups.

## Output files

The application generates text files for the values available to OBS, including:

- Overall rating
- Overall rating change
- Overall rank
- Overall rank change
- Monthly rating
- Monthly rating change
- Monthly rank
- Monthly rank change
- Session rating change
- Session rank change
- Combined rating/rank labels

The exact output filenames are the files generated in the `output` directory.

These files are deliberately plain text so they can be consumed by OBS or other software without requiring an API integration.

## Testing the OBS setup without playing a match

The repository includes a manual simulation utility:

```bat
python src\simulate_matches.py
```

This simulates one match and updates the output files.

To simulate multiple matches:

```bat
python src\simulate_matches.py 5
```

Multiple simulations are separated by a short delay of 10 seconds so that the output and OBS behavior can be observed.

This utility does not contact the Strata API and uses generated test data.

## How it works

The application monitors the Zero Hour replay file for changes.

When a new game starts, the replay file becomes active. When the game ends, the replay header is updated with the end time.

The application then waits for the configured rating-update delay and checks Strata until the match result is reflected in the player's rating data.

Once the new rating data is available, the output files are updated.

The OBS Lua script, when used, can react to those output updates and temporarily display selected text sources.

## Troubleshooting

### The application cannot find the replay file

Check the configured replay directory and make sure it contains:

```text
00000000.rep
```

The game must be creating the replay file in that directory.

### The Strata token is rejected

Make sure the API token is valid and that the computer has internet access.

### No linked player/account is available

The Strata account must have at least one Generals Online account linked to it.

### OBS is not updating a value

If you are using OBS's built-in **Read from file** option, verify that the Text source points to the correct file in the application's `output` directory.

If you are using the Lua script, verify that the correct Scene, Text Source and output file are selected in the script instance.

If you use multiple Strata text sources with temporary display durations, configure all of them through copies of the same Lua script so they share the same update mechanism.

## Project status

This repository currently provides the application as Python source code.

A packaged Windows executable may be provided separately in the future.
