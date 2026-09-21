# OBS Integration

Strata Streamer Tool provides a graphical HUD overlay that can be displayed in OBS using a Browser Source.

For users who want to use the graphical overlay, the recommended setup is:

1. Add the graphical overlay as an OBS Browser Source.
2. Add `strata_streamer_watchdog.lua` to OBS to automatically refresh the Browser Source when Strata Streamer Tool starts, stops or crashes.

The plain-text output files are still available if you prefer to build your own OBS layout using text sources.

## Graphical HUD overlay

The graphical overlay is hosted locally by Strata Streamer Tool and can be displayed directly in OBS.

It provides:

- Faction-specific HUD artwork
- Automatic positioning depending on whether you are in a game or in the game menu
- Elo and rank information
- Support for 1920×1080 and 2560×1440 streaming resolutions

### Adding the Browser Source

In OBS:

1. Add a new **Browser** source.
2. Give it a name, for example:
   `Strata Overlay`
3. Set the URL to:
   `http://127.0.0.1:1337/overlay`
4. Set the Browser Source dimensions to match your streaming resolution:
   - `1920 × 1080`
   - `2560 × 1440`
5. Position the Browser Source as required.

The Browser Source should normally cover the full OBS canvas.

The overlay itself is transparent, so only the HUD elements are visible.

### Important

Strata Streamer Tool must be running for the graphical overlay to be available.

If OBS starts before Strata Streamer Tool, the Browser Source may initially show a blank page. The watchdog script described below can automatically refresh it when Strata Streamer Tool becomes available.

## Automatic Browser Source refresh

The included `strata_streamer_watchdog.lua` script can automatically refresh the graphical Browser Source when Strata Streamer Tool becomes available or unavailable.

This is useful when:

- OBS starts before Strata Streamer Tool.
- Strata Streamer Tool is restarted.
- Strata Streamer Tool crashes.
- The Browser Source would otherwise continue displaying an outdated HUD.

The watchdog does not control or update the HUD itself.

Strata Streamer Tool provides the graphical overlay. The watchdog only monitors whether Strata Streamer Tool is available and requests a refresh of the selected Browser Source when its availability changes.

### Installing the watchdog

Download `strata_streamer_watchdog.lua` from the Strata Streamer Tool release.

In OBS:

1. Open **Tools → Scripts**.
2. Click the `+` button.
3. Select `strata_streamer_watchdog.lua`.

The script can be added once and will monitor the selected Browser Source.

### Watchdog settings

The script has two settings.

#### Browser Source

Select the OBS Browser Source that contains the Strata graphical overlay.

The list is populated automatically with the Browser Sources available in OBS.

For example:

`Strata Overlay`

#### Check Interval

Controls how frequently the script checks whether Strata Streamer Tool is available.

The default is:

`1000 ms`

The default value is recommended for normal use.

### How the watchdog works

Strata Streamer Tool creates a small heartbeat file while it is running:

`%TEMP%\StrataStreamerTool.ready`

The watchdog checks this file periodically.

When Strata Streamer Tool becomes available, the watchdog requests a Browser Source refresh.

When Strata Streamer Tool becomes unavailable, the watchdog requests another Browser Source refresh.

This means the Browser Source is also refreshed after a crash or unexpected shutdown, preventing OBS from continuing to display an outdated HUD.

When Strata Streamer Tool becomes available again, the Browser Source is refreshed once more so that the graphical overlay can load again.

### Watchdog troubleshooting

#### The Browser Source is not refreshing

Check that:

- `strata_streamer_watchdog.lua` is loaded in OBS;
- the correct Browser Source is selected;
- the selected source is an OBS Browser Source;
- Strata Streamer Tool is running;
- the Browser Source URL is:
  `http://127.0.0.1:1337/overlay`

The watchdog writes diagnostic messages to the OBS script log.

#### The Browser Source is blank

Check that Strata Streamer Tool is running.

You can also open the following URL in a web browser:

`http://127.0.0.1:1337/overlay`

If the overlay is not available there either, the problem is with Strata Streamer Tool or its local overlay server rather than OBS.

## Plain-text output files

Strata Streamer Tool also generates plain-text output files.

These can be used if you prefer to build your own OBS layout from individual text sources instead of using the graphical overlay.

There are two ways to use the text files:

1. OBS's built-in **Read from file** option.
2. The included `strata_streamer_source.lua` script.

The Lua script is optional.

## Option 1: OBS "Read from file"

If you do not need text sources to appear only temporarily after an update, the Lua script is not necessary.

For each value you want to display:

1. Create an OBS Text source.
2. Enable **Read from file**.
3. Select the corresponding `.txt` file from the Strata Streamer Tool `output` directory.
4. Position and format the source as desired.

This is the simplest setup.

The text source remains visible and OBS reads the value directly from the file.

## Option 2: Strata Streamer Source Lua script

The included `strata_streamer_source.lua` script is an alternative for stream layouts where a text source should appear temporarily after the Strata data changes.

For example, you may want:

    +17 Elo

to appear for a few seconds after a match, and then disappear again.

The script can also be used with permanent sources. This is useful when you want all Strata sources to update through the same mechanism.

### Installing the script

Download `strata_streamer_source.lua` from the Strata Streamer Tool release.

In OBS:

1. Open **Tools → Scripts**.
2. Click the `+` button.
3. Select `strata_streamer_source.lua`.

The script can be added multiple times by making a copy of the script. Each instance controls one OBS Text source.

## Script settings

Each script instance has the following settings.

### Scene

Select the OBS scene containing the Text source.

The script uses this setting to find the Text source.

Text sources inside OBS groups and nested groups are supported.

### Text Source

Select the Text source that should be controlled.

The list is populated from the selected scene and includes Text sources inside groups and nested groups.

If you change the Scene, the Text Source list is rebuilt for that scene.

### Text File

Select the `.txt` file whose contents should be displayed.

For example:

    output\overall_elo.txt

The contents of this file are written to the selected OBS Text source when a trigger is detected.

### Trigger File

Select the trigger file that tells the script that the Strata output has changed.

For normal Strata output updates, use:

    output\output_update_trigger.txt

For temporary match overlays, use:

    output\match_update_trigger.txt

The script monitors the trigger file and reacts whenever its contents change.

The trigger files are updated by the Strata Streamer Tool after the relevant output files have been written.

### Display Duration

Controls how long the Text source remains visible after a trigger.

The value is specified in seconds.

`0` means permanent.

A value greater than `0` means temporary.

For example:

    Display Duration = 5

causes the source to become visible after an update and remain visible for approximately five seconds.

If another trigger arrives while the source is already visible, the timer is restarted.

### Poll Interval

Controls how frequently the Lua script checks the trigger file.

The default is:

    250 ms

Lower values make the script react more quickly but cause it to check the file more frequently.

For normal use, the default value is recommended.

## Before setting up temporary sources

The `match_update_trigger.txt` file may not exist immediately after completing the Strata Streamer Tool setup wizard.

This is expected.

The file is created when the tool detects the end of a game and successfully updates the rating information. Therefore, if you intend to use temporary match-related text sources, it is recommended to:

1. Complete the Strata Streamer Tool setup.
2. Start the tool and leave it running.
3. Play and finish at least one game.
4. Confirm that `match_update_trigger.txt` has appeared in the `output` directory.
5. Set up the temporary OBS sources.

The file does not need to be created manually.

## Choosing the trigger file

There are two trigger files generated by the application.

### `output_update_trigger.txt`

This is the general Strata output trigger.

It changes whenever the standard output files are updated.

Use this trigger for normal rating/rank sources.

For example, a source displaying:

    Overall Elo: 1842

could use:

    Text File:
    output\overall_elo.txt

    Trigger File:
    output\output_update_trigger.txt

### `match_update_trigger.txt`

This trigger is used specifically for confirmed match updates.

Use it for temporary match-related overlays.

For example:

    Text File:
    output\overall_elo_change.txt

    Trigger File:
    output\match_update_trigger.txt

    Display Duration:
    5

The source will appear when a new match result has been detected and the updated rating information has been retrieved.

Remember that this trigger file is only created after the tool has detected a completed game while it was running.

## Synchronizing multiple sources

This is the most important reason to use the Lua script for all Strata sources when temporary sources are involved.

Suppose your OBS layout contains:

    Elo:       1842
    Rank:      #12
    Change:    +17

and you want all three values to update together.

If all three script instances use the same trigger file:

    output\output_update_trigger.txt

they all react to the same Strata update.

For example:

    Text Source       Text File                     Trigger File
    ---------------------------------------------------------------------------
    Elo               overall_elo.txt              output_update_trigger.txt
    Rank              overall_rank.txt             output_update_trigger.txt
    Change            overall_elo_change.txt       output_update_trigger.txt

This ensures that the sources use the same update event.

### Important

If you use the Lua script for one Strata source that has a temporary display duration, use the Lua script for all Strata sources that you want synchronized with the Strata output updates.

Do not mix the Lua script and OBS's **Read from file** method for sources that need to be synchronized.

OBS's built-in file reader and the Lua script use different mechanisms for updating the sources, so their updates are not coordinated by the Strata trigger system.

## Permanent vs. temporary sources

The Lua script supports both.

### Permanent source

Set:

    Display Duration = 0

The source is made visible when the script initializes and remains visible.

When the trigger file changes, its contents are updated.

### Temporary source

Set:

    Display Duration > 0

The source is hidden initially.

When the trigger file changes:

1. The text file is read.
2. The OBS Text source is updated.
3. The source is made visible.
4. A timer starts.
5. The source is hidden when the timer expires.

If another update arrives before the timer expires, the timer is restarted.

## Recommended configurations

### Simple permanent overlay

If your overlay always displays your current rating:

    Text File:
    overall_elo.txt

    Trigger File:
    output_update_trigger.txt

    Display Duration:
    0

### Temporary match notification

If you want a rating change to appear briefly after a match:

    Text File:
    overall_elo_change.txt

    Trigger File:
    match_update_trigger.txt

    Display Duration:
    5

### Multiple synchronized sources

If your overlay contains several values that should update together, give each Lua instance the same trigger file:

    Elo       → overall_elo.txt
    Rank      → overall_rank.txt
    Change    → overall_elo_change.txt

with:

    Trigger File:
    output_update_trigger.txt

for all three.

Each instance can have a different Text File and Display Duration while sharing the same trigger.

## Multiple Lua instances

You can add the script multiple times in OBS.

Each instance has its own:

- Scene
- Text Source
- Text File
- Trigger File
- Display Duration
- Poll Interval

This allows you to build a complete overlay from multiple independently configured Text sources.

For example:

    Instance 1
    Scene:          Main Overlay
    Text Source:    Player Elo
    Text File:      overall_elo.txt
    Trigger File:   output_update_trigger.txt
    Duration:       0

    Instance 2
    Scene:          Main Overlay
    Text Source:    Elo Change
    Text File:      overall_elo_change.txt
    Trigger File:   match_update_trigger.txt
    Duration:       5

    Instance 3
    Scene:          Main Overlay
    Text Source:    Player Rank
    Text File:      overall_rank.txt
    Trigger File:   output_update_trigger.txt
    Duration:       0

## Groups and nested groups

The script can find Text sources inside OBS groups, including nested groups.

For example:

    Main Overlay
    └── Player Information
        └── Rating
            └── Player Elo

The `Player Elo` Text source can still be selected by the script.

The Scene setting should always refer to the scene containing the source.

## Troubleshooting

### The graphical overlay is not displayed in OBS

Check that:

- Strata Streamer Tool is running;
- the Browser Source URL is:
  `http://127.0.0.1:1337/overlay`
- the Browser Source dimensions match your streaming resolution;
- the Browser Source is not hidden in OBS;
- `strata_streamer_watchdog.lua` is configured with the correct Browser Source if you are using the watchdog.

You can also open the overlay URL directly in a web browser to check whether the local overlay server is working.

### The Text Source does not appear in the list

Check that:

- the correct Scene is selected;
- the source is actually an OBS Text source;
- the source exists inside the selected scene or one of its groups.

If you change the Scene, the Text Source list is rebuilt automatically.

### The source does not update

Check:

- the selected Text File exists;
- the selected Trigger File exists;
- the Strata Streamer Tool is running;
- the trigger file is being updated;
- the correct Scene and Text Source are selected.

The script writes diagnostic messages to the OBS script log.

### `match_update_trigger.txt` does not exist

This is normal if the tool has not yet detected a completed game while running.

Start the Strata Streamer Tool, play and finish a game, and wait for the rating update to complete. The file will then be created automatically.

Do not create the file manually.

### A temporary source does not disappear

Check that **Display Duration** is greater than zero.

If it is `0`, the source is intentionally permanent.

### Sources update at different times

If multiple Strata sources need to update together, make sure they are all controlled by the Lua script and use the same trigger file.

Do not mix Lua-controlled sources with OBS **Read from file** sources when synchronized updates are required.
