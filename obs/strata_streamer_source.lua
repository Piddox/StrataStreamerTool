obs = obslua


--------------------------------------------------
-- GLOBAL SETTINGS
--------------------------------------------------

scene_name = ""
source_name = ""

text_file = ""
trigger_file = ""

display_duration = 0
poll_interval = 250


--------------------------------------------------
-- RUNTIME STATE
--------------------------------------------------

last_trigger_value = nil
source_visible = false


--------------------------------------------------
-- LOGGING
--------------------------------------------------

function log(message)

    print(
        "[Strata Streamer Source] "
        .. message
    )

end


--------------------------------------------------
-- READ FILE
--------------------------------------------------

function read_file(path)

    if path == nil or path == "" then
        return nil
    end


    local file = io.open(
        path,
        "r"
    )

    if file == nil then
        return nil
    end


    local content = file:read("*all")

    file:close()


    if content == nil then
        return nil
    end


    -- Remove trailing line endings.

    content = content:gsub(
        "[\r\n]+$",
        ""
    )


    return content

end


--------------------------------------------------
-- UPDATE TEXT SOURCE
--------------------------------------------------

function update_text_source()

    if source_name == nil or source_name == "" then
        return false
    end


    local content = read_file(
        text_file
    )


    if content == nil then

        log(
            "Could not read text file: "
            .. text_file
        )

        return false

    end


    local source = obs.obs_get_source_by_name(
        source_name
    )


    if source == nil then

        log(
            "Could not find source: "
            .. source_name
        )

        return false

    end


    local settings = obs.obs_data_create()


    obs.obs_data_set_string(
        settings,
        "text",
        content
    )


    obs.obs_source_update(
        source,
        settings
    )


    obs.obs_data_release(
        settings
    )

    obs.obs_source_release(
        source
    )


    return true

end

--------------------------------------------------
-- FIND SCENE ITEM RECURSIVELY
--------------------------------------------------

function find_scene_item_recursive(
    scene,
    target_source_name
)

    if scene == nil then
        return nil
    end


    local scene_items = (
        obs.obs_scene_enum_items(
            scene
        )
    )


    if scene_items == nil then
        return nil
    end


    for _, scene_item in ipairs(
        scene_items
    ) do

        local source = (
            obs.obs_sceneitem_get_source(
                scene_item
            )
        )


        if source ~= nil then

            local name = (
                obs.obs_source_get_name(
                    source
                )
            )


            --------------------------------------------------
            -- TARGET SOURCE
            --------------------------------------------------

            if name == target_source_name then

                obs.sceneitem_list_release(
                    scene_items
                )

                return scene_item

            end


            --------------------------------------------------
            -- GROUP
            --------------------------------------------------

            if obs.obs_source_is_group(
                source
            ) then

                local group_scene = (
                    obs.obs_group_from_source(
                        source
                    )
                )


                local found_item = (
                    find_scene_item_recursive(
                        group_scene,
                        target_source_name
                    )
                )


                if found_item ~= nil then

                    obs.sceneitem_list_release(
                        scene_items
                    )

                    return found_item

                end

            end

        end

    end


    obs.sceneitem_list_release(
        scene_items
    )


    return nil

end


--------------------------------------------------
-- GET SCENE ITEM
--------------------------------------------------

function get_scene_item()

    if scene_name == nil
        or scene_name == ""
    then

        log(
            "No scene selected."
        )

        return nil, nil

    end


    if source_name == nil
        or source_name == ""
    then

        log(
            "No source selected."
        )

        return nil, nil

    end


    local scene_source = (
        obs.obs_get_source_by_name(
            scene_name
        )
    )


    if scene_source == nil then

        log(
            "Could not find scene: "
            .. scene_name
        )

        return nil, nil

    end


    local scene = obs.obs_scene_from_source(
        scene_source
    )


    if scene == nil then

        log(
            "Could not access scene: "
            .. scene_name
        )

        obs.obs_source_release(
            scene_source
        )

        return nil, nil

    end


    local scene_item = (
        find_scene_item_recursive(
            scene,
            source_name
        )
    )


    if scene_item == nil then

        log(
            "Could not find source '"
            .. source_name
            .. "' in scene '"
            .. scene_name
            .. "'."
        )

        obs.obs_source_release(
            scene_source
        )

        return nil, nil

    end


    return scene_item, scene_source

end

--------------------------------------------------
-- SET SOURCE VISIBILITY
--------------------------------------------------

function set_source_visibility(visible)

    local scene_item, scene_source = (
        get_scene_item()
    )


    if scene_item == nil then

        return false

    end


    obs.obs_sceneitem_set_visible(
        scene_item,
        visible
    )


    obs.obs_source_release(
        scene_source
    )


    source_visible = visible


    return true

end


--------------------------------------------------
-- HIDE SOURCE
--------------------------------------------------

function hide_source()

    obs.timer_remove(
        hide_source
    )


    if source_visible then

        set_source_visibility(
            false
        )

    end

end


--------------------------------------------------
-- PROCESS TRIGGER
--------------------------------------------------

function process_trigger()

    local updated = update_text_source()

    if not updated then
        return
    end


    --------------------------------------------------
    -- PERMANENT SOURCE
    --------------------------------------------------

    if display_duration <= 0 then

        if not source_visible then

            set_source_visibility(
                true
            )

        end

        return

    end


    --------------------------------------------------
    -- TEMPORARY SOURCE
    --------------------------------------------------

    obs.timer_remove(
        hide_source
    )


    set_source_visibility(
        true
    )


    obs.timer_add(
        hide_source,
        display_duration * 1000
    )

end


--------------------------------------------------
-- CHECK TRIGGER FILE
--------------------------------------------------

function check_trigger_file()

    local current_value = read_file(
        trigger_file
    )

    if current_value == nil then

        return

    end


    --------------------------------------------------
    -- FIRST READ = BASELINE
    --------------------------------------------------

    if last_trigger_value == nil then

        last_trigger_value = (
            current_value
        )

        log(
            "Trigger baseline established: "
            .. current_value
        )

        return

    end


    --------------------------------------------------
    -- TRIGGER CHANGED
    --------------------------------------------------

    if current_value ~= last_trigger_value then

        last_trigger_value = (
            current_value
        )

        log(
            "Trigger change detected."
        )

        process_trigger()

    end

end

--------------------------------------------------
-- SCRIPT DEFAULTS
--------------------------------------------------

function script_defaults(settings)

    obs.obs_data_set_default_int(
        settings,
        "display_duration",
        0
    )

    obs.obs_data_set_default_int(
        settings,
        "poll_interval",
        250
    )

end

--------------------------------------------------
-- IS TEXT SOURCE
--------------------------------------------------

function is_text_source(source)

    if source == nil then
        return false
    end


    local properties = (
        obs.obs_source_properties(
            source
        )
    )


    if properties == nil then
        return false
    end


    local text_property = (
        obs.obs_properties_get(
            properties,
            "text"
        )
    )


    local is_text = (
        text_property ~= nil
    )


    obs.obs_properties_destroy(
        properties
    )


    return is_text

end


--------------------------------------------------
-- ADD TEXT SOURCES FROM SCENE
--------------------------------------------------

function add_text_sources_from_scene(
    scene,
    source_property
)

    if scene == nil then
        return
    end


    local scene_items = (
        obs.obs_scene_enum_items(
            scene
        )
    )


    if scene_items == nil then
        return
    end


    for _, scene_item in ipairs(
        scene_items
    ) do

        local source = (
            obs.obs_sceneitem_get_source(
                scene_item
            )
        )


        if source ~= nil then

            --------------------------------------------------
            -- TEXT SOURCE
            --------------------------------------------------

            if is_text_source(
                source
            ) then

                local name = (
                    obs.obs_source_get_name(
                        source
                    )
                )

                obs.obs_property_list_add_string(
                    source_property,
                    name,
                    name
                )

            end


            --------------------------------------------------
            -- GROUP
            --------------------------------------------------

            if obs.obs_source_is_group(
                source
            ) then

                local group_scene = (
                    obs.obs_group_from_source(
                        source
                    )
                )

                add_text_sources_from_scene(
                    group_scene,
                    source_property
                )

            end

        end

    end


    obs.sceneitem_list_release(
        scene_items
    )

end

--------------------------------------------------
-- POPULATE TEXT SOURCES FOR SELECTED SCENE
--------------------------------------------------

function populate_text_sources(
    source_property,
    scene_name
)

    if scene_name == nil
        or scene_name == ""
    then
        return
    end


    local scene_source = (
        obs.obs_get_source_by_name(
            scene_name
        )
    )


    if scene_source == nil then
        return
    end


    local scene = (
        obs.obs_scene_from_source(
            scene_source
        )
    )


    if scene ~= nil then

        add_text_sources_from_scene(
            scene,
            source_property
        )

    end


    obs.obs_source_release(
        scene_source
    )

end

--------------------------------------------------
-- SCENE CHANGED CALLBACK
--------------------------------------------------

function on_scene_changed(
    properties,
    property,
    settings
)

    local source_property = (
        obs.obs_properties_get(
            properties,
            "source_name"
        )
    )


    if source_property == nil then
        return false
    end


    obs.obs_property_list_clear(
        source_property
    )


    local scene_name = (
        obs.obs_data_get_string(
            settings,
            "scene_name"
        )
    )


    populate_text_sources(
        source_property,
        scene_name
    )


    --------------------------------------------------
    -- Clear previously selected source.
    --
    -- A source from the previous scene may not exist
    -- in the newly selected scene.
    --------------------------------------------------

    obs.obs_data_set_string(
        settings,
        "source_name",
        ""
    )


    return true

end

--------------------------------------------------
-- SCRIPT PROPERTIES
--------------------------------------------------

function script_properties()

    local properties = (
        obs.obs_properties_create()
    )


    --------------------------------------------------
    -- SCENE
    --------------------------------------------------

    local scene_property = (
        obs.obs_properties_add_list(
            properties,
            "scene_name",
            "Scene",
            obs.OBS_COMBO_TYPE_LIST,
            obs.OBS_COMBO_FORMAT_STRING
        )
    )


    local scenes = (
        obs.obs_frontend_get_scenes()
    )


    if scenes ~= nil then

        for _, scene_source in ipairs(
            scenes
        ) do

            local name = (
                obs.obs_source_get_name(
                    scene_source
                )
            )

            obs.obs_property_list_add_string(
                scene_property,
                name,
                name
            )

        end


        obs.source_list_release(
            scenes
        )

    end


    obs.obs_property_set_modified_callback(
        scene_property,
        on_scene_changed
    )


    --------------------------------------------------
    -- TEXT SOURCE
    --------------------------------------------------

    local source_property = (
        obs.obs_properties_add_list(
            properties,
            "source_name",
            "Text Source",
            obs.OBS_COMBO_TYPE_LIST,
            obs.OBS_COMBO_FORMAT_STRING
        )
    )


    populate_text_sources(
        source_property,
        scene_name
    )


    --------------------------------------------------
    -- Add all text sources from all scenes,
    -- including sources inside groups.
    --------------------------------------------------

    local selected_scene = (
        obs.obs_data_get_string(
            settings,
            "scene_name"
        )
    )


    populate_text_sources(
        source_property,
        selected_scene
    )


    --------------------------------------------------
    -- TEXT FILE
    --------------------------------------------------

    obs.obs_properties_add_path(
        properties,
        "text_file",
        "Text File",
        obs.OBS_PATH_FILE,
        "Text Files (*.txt)",
        nil
    )


    --------------------------------------------------
    -- TRIGGER FILE
    --------------------------------------------------

    obs.obs_properties_add_path(
        properties,
        "trigger_file",
        "Trigger File",
        obs.OBS_PATH_FILE,
        "Text Files (*.txt)",
        nil
    )


    --------------------------------------------------
    -- DISPLAY DURATION
    --------------------------------------------------

    obs.obs_properties_add_int(
        properties,
        "display_duration",
        "Display Duration (seconds, 0 = permanent)",
        0,
        3600,
        1
    )


    --------------------------------------------------
    -- POLL INTERVAL
    --------------------------------------------------

    obs.obs_properties_add_int(
        properties,
        "poll_interval",
        "Poll Interval (ms)",
        50,
        5000,
        50
    )


    return properties

end

function initialize_source()

    --------------------------------------------------
    -- Stop initialization timer.
    --------------------------------------------------

    obs.timer_remove(
        initialize_source
    )


    --------------------------------------------------
    -- TEMPORARY SOURCE
    --------------------------------------------------

    if display_duration > 0 then

        log(
            "Initializing temporary source."
        )

        set_source_visibility(
            false
        )


    --------------------------------------------------
    -- PERMANENT SOURCE
    --------------------------------------------------

    else

        log(
            "Initializing permanent source."
        )

        local updated = (
            update_text_source()
        )

        if updated then

            set_source_visibility(
                true
            )

        end

    end

end


--------------------------------------------------
-- SCRIPT UPDATE
--------------------------------------------------

function script_update(settings)

    --------------------------------------------------
    -- Stop existing timers.
    --------------------------------------------------

    obs.timer_remove(
        check_trigger_file
    )

    obs.timer_remove(
        hide_source
    )


    --------------------------------------------------
    -- Reset runtime state.
    --------------------------------------------------

    source_visible = false

    last_trigger_value = nil


    --------------------------------------------------
    -- Read settings.
    --------------------------------------------------

    scene_name = obs.obs_data_get_string(
        settings,
        "scene_name"
    )

    source_name = obs.obs_data_get_string(
        settings,
        "source_name"
    )

    text_file = obs.obs_data_get_string(
        settings,
        "text_file"
    )

    trigger_file = obs.obs_data_get_string(
        settings,
        "trigger_file"
    )

    display_duration = obs.obs_data_get_int(
        settings,
        "display_duration"
    )

    poll_interval = obs.obs_data_get_int(
        settings,
        "poll_interval"
    )

    if poll_interval <= 0 then

        poll_interval = 250

    end

    --------------------------------------------------
    -- DELAYED INITIALIZATION
    --------------------------------------------------

    obs.timer_remove(
        initialize_source
    )

    obs.timer_add(
        initialize_source,
        500
    )


    --------------------------------------------------
    -- Start polling.
    --------------------------------------------------

    if trigger_file ~= "" then

        log(
            "Starting trigger monitoring."
        )

        log(
            "Trigger file: "
            .. trigger_file
        )

        log(
            "Poll interval: "
            .. tostring(poll_interval)
            .. " ms"
        )


        obs.timer_add(
            check_trigger_file,
            poll_interval
        )

    end

end


--------------------------------------------------
-- SCRIPT LOAD
--------------------------------------------------

function script_load(settings)

    script_update(
        settings
    )

end


--------------------------------------------------
-- SCRIPT UNLOAD
--------------------------------------------------

function script_unload()

    obs.timer_remove(
        check_trigger_file
    )

    obs.timer_remove(
        hide_source
    )

end


--------------------------------------------------
-- SCRIPT DESCRIPTION
--------------------------------------------------

function script_description()

    return [[
Strata Streamer Tool OBS Source Controller

Updates an OBS text source from a text file whenever a
trigger file changes.

Display Duration:
0 seconds = permanent source
Greater than 0 = temporary source that hides automatically

For sources controlled by this script, disable "Read from file"
in the OBS Text (GDI+) source.
]]

end