obs = obslua

-- Strata Streamer Tool - OBS Browser Source watchdog
--
-- Refreshes the configured Browser Source ONCE when
-- StrataStreamerTool becomes available after being unavailable.
--
-- The Python application writes a heartbeat to:
--   %TEMP%\StrataStreamerTool.ready
--
-- The file contains:
--   PID=<process id>
--   TIMESTAMP=<Unix timestamp>

SOURCE_NAME = "Strata Overlay"
CHECK_INTERVAL_MS = 1000
HEARTBEAT_TIMEOUT = 3.0
READY_FILE = os.getenv("TEMP") .. "\\StrataStreamerTool.ready"

was_ready = false


function script_description()
    return [[
Strata Streamer Tool - Browser Source Watchdog

Automatically refreshes the configured OBS Browser Source once when
StrataStreamerTool becomes available.

The Browser Source is not refreshed continuously. A refresh only occurs
on an unavailable -> available transition.

Availability is determined by the heartbeat timestamp written by
StrataStreamerTool.
]]
end


function script_properties()
    local props = obs.obs_properties_create()

    --------------------------------------------------
    -- BROWSER SOURCE
    --------------------------------------------------

    local source_property = obs.obs_properties_add_list(
        props,
        "source_name",
        "Browser Source",
        obs.OBS_COMBO_TYPE_LIST,
        obs.OBS_COMBO_FORMAT_STRING
    )

    local sources = obs.obs_enum_sources()

    if sources ~= nil then
        for _, source in ipairs(sources) do
            local source_id = obs.obs_source_get_unversioned_id(source)

            if source_id == "browser_source" then
                local name = obs.obs_source_get_name(source)

                obs.obs_property_list_add_string(
                    source_property,
                    name,
                    name
                )
            end
        end

        obs.source_list_release(sources)
    end

    --------------------------------------------------
    -- CHECK INTERVAL
    --------------------------------------------------

    obs.obs_properties_add_int(
        props,
        "interval",
        "Check interval (ms)",
        250,
        10000,
        250
    )

    return props
end


function script_defaults(settings)
    obs.obs_data_set_default_string(settings, "source_name", "Strata Overlay")
    obs.obs_data_set_default_int(settings, "interval", 1000)
end


function script_update(settings)
    SOURCE_NAME = obs.obs_data_get_string(settings, "source_name")
    CHECK_INTERVAL_MS = obs.obs_data_get_int(settings, "interval")

    if SOURCE_NAME == "" then
        SOURCE_NAME = "Strata Overlay"
    end

    if CHECK_INTERVAL_MS < 250 then
        CHECK_INTERVAL_MS = 250
    end

    obs.timer_remove(check_ready)
    obs.timer_add(check_ready, CHECK_INTERVAL_MS)
end


function script_load(settings)
    SOURCE_NAME = obs.obs_data_get_string(settings, "source_name")
    CHECK_INTERVAL_MS = obs.obs_data_get_int(settings, "interval")

    if SOURCE_NAME == "" then
        SOURCE_NAME = "Strata Overlay"
    end

    if CHECK_INTERVAL_MS < 250 then
        CHECK_INTERVAL_MS = 250
    end

    was_ready = false
    obs.timer_add(check_ready, CHECK_INTERVAL_MS)
end


function script_unload()
    obs.timer_remove(check_ready)
end


function is_ready()
    local file = io.open(READY_FILE, "r")

    if file == nil then
        return false
    end

    local timestamp = nil

    for line in file:lines() do
        local value = line:match("^TIMESTAMP=(.+)$")

        if value ~= nil then
            timestamp = tonumber(value)
            break
        end
    end

    file:close()

    if timestamp == nil then
        return false
    end

    local age = os.time() - timestamp

    return age >= 0 and age < HEARTBEAT_TIMEOUT
end


function refresh_browser_source()
    if SOURCE_NAME == nil or SOURCE_NAME == "" then
        print("[Strata Watchdog] No Browser Source selected")
        return false
    end

    local source = obs.obs_get_source_by_name(SOURCE_NAME)

    if source == nil then
        print("[Strata Watchdog] Browser Source not found: " .. SOURCE_NAME)
        return false
    end

    local source_id = obs.obs_source_get_unversioned_id(source)

    if source_id ~= "browser_source" then
        print(
            "[Strata Watchdog] Source is not a Browser Source: "
            .. SOURCE_NAME
            .. " ("
            .. source_id
            .. ")"
        )

        obs.obs_source_release(source)
        return false
    end

    local properties = obs.obs_source_properties(source)

    if properties == nil then
        print("[Strata Watchdog] Could not get Browser Source properties")
        obs.obs_source_release(source)
        return false
    end

    local refresh_property =
        obs.obs_properties_get(properties, "refreshnocache")

    if refresh_property == nil then
        print(
            "[Strata Watchdog] Browser Source refresh property not found: "
            .. SOURCE_NAME
        )

        obs.obs_properties_destroy(properties)
        obs.obs_source_release(source)
        return false
    end

    obs.obs_property_button_clicked(refresh_property, source)

    obs.obs_properties_destroy(properties)
    obs.obs_source_release(source)

    print(
        "[Strata Watchdog] Browser Source refresh requested: "
        .. SOURCE_NAME
    )

    return true
end


function check_ready()
    local ready = is_ready()

    if ready and not was_ready then
        print("[Strata Watchdog] StrataStreamerTool is available")
        refresh_browser_source()
    elseif not ready and was_ready then
        print("[Strata Watchdog] StrataStreamerTool is no longer available")
        refresh_browser_source()
    end

    was_ready = ready
end
