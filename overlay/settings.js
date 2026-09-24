(() => {
    "use strict";

    const HUD_NAMES = ["hud_1", "hud_2"];

    const form = document.getElementById("settings-form");
    const saveButton = document.getElementById("save-button");
    const resetButton = document.getElementById("reset-button");
    const saveStatus = document.getElementById("save-status");

    let loadedConfig = null;

    function getElementId(hudName, fieldName) {
        return `${hudName.replace("_", "-")}-${fieldName.replaceAll("_", "-")}`;
    }

    function getField(hudName, fieldName) {
        return document.getElementById(getElementId(hudName, fieldName));
    }

    function setStatus(message, type = "") {
        saveStatus.textContent = message;
        saveStatus.className = `status-message${type ? ` ${type}` : ""}`;
    }

    function setSaving(isSaving) {
        saveButton.disabled = isSaving;
        resetButton.disabled = isSaving;
        saveButton.textContent = isSaving ? "Saving..." : "Save settings";
    }

    function updatePositionFields(hudName) {
        const positionMode = getField(hudName, "position_mode").value;
        const inGamePosition = getField(hudName, "in_game_position");
        const inMenuPosition = getField(hudName, "in_menu_position");

        inGamePosition.disabled = positionMode === "in_menu";
        inMenuPosition.disabled = positionMode === "in_game";
    }

    function updateAllPositionFields() {
        HUD_NAMES.forEach(updatePositionFields);
    }

    function populateForm(config) {
        HUD_NAMES.forEach((hudName) => {
            const hudConfig = config[hudName];

            getField(hudName, "visibility_mode").value =
                hudConfig.visibility_mode;

            getField(hudName, "hide_when_observing").checked =
                hudConfig.hide_when_observing;

            getField(hudName, "template").value =
                hudConfig.template;

            getField(hudName, "ladder").value =
                hudConfig.ladder;

            getField(hudName, "artwork_size").value =
                hudConfig.artwork_size;

            getField(hudName, "artwork_color").value =
                hudConfig.artwork_color;

            getField(hudName, "position_mode").value =
                hudConfig.position_mode;

            getField(hudName, "in_game_position").value =
                hudConfig.in_game_position;

            getField(hudName, "in_menu_position").value =
                hudConfig.in_menu_position;
        });

        updateAllPositionFields();
    }

    function collectFormConfig() {
        const config = {
            hud_1: {},
            hud_2: {}
        };

        HUD_NAMES.forEach((hudName) => {
            config[hudName] = {
                visibility_mode:
                    getField(hudName, "visibility_mode").value,

                hide_when_observing:
                    getField(hudName, "hide_when_observing").checked,

                template:
                    getField(hudName, "template").value,

                ladder:
                    getField(hudName, "ladder").value,

                artwork_size:
                    getField(hudName, "artwork_size").value,

                artwork_color:
                    getField(hudName, "artwork_color").value,

                position_mode:
                    getField(hudName, "position_mode").value,

                in_game_position:
                    getField(hudName, "in_game_position").value,

                in_menu_position:
                    getField(hudName, "in_menu_position").value
            };
        });

        return config;
    }

    async function loadConfig() {
        setStatus("Loading settings...");

        try {
            const response = await fetch("/config", {
                cache: "no-store"
            });

            if (!response.ok) {
                throw new Error(
                    `Server returned HTTP ${response.status}.`
                );
            }

            const config = await response.json();

            if (
                !config ||
                typeof config !== "object" ||
                !config.hud_1 ||
                !config.hud_2
            ) {
                throw new Error(
                    "The server returned an invalid overlay configuration."
                );
            }

            loadedConfig = structuredClone(config);
            populateForm(loadedConfig);
            setStatus("");
        } catch (error) {
            console.error(
                "Could not load overlay settings:",
                error
            );

            setStatus(
                `Could not load settings: ${error.message}`,
                "error"
            );
        }
    }

    async function saveConfig() {
        const config = collectFormConfig();

        setSaving(true);
        setStatus("Saving settings...");

        try {
            const response = await fetch("/config", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(config)
            });

            let responseData = null;

            try {
                responseData = await response.json();
            } catch {
                // The server may have returned a non-JSON error response.
            }

            if (!response.ok) {
                const message =
                    responseData?.error ||
                    `Server returned HTTP ${response.status}.`;

                throw new Error(message);
            }

            if (
                !responseData ||
                typeof responseData !== "object" ||
                !responseData.hud_1 ||
                !responseData.hud_2
            ) {
                throw new Error(
                    "The server returned an invalid saved configuration."
                );
            }

            loadedConfig = structuredClone(responseData);
            populateForm(loadedConfig);

            setStatus("Settings saved.", "success");
        } catch (error) {
            console.error(
                "Could not save overlay settings:",
                error
            );

            setStatus(
                `Could not save settings: ${error.message}`,
                "error"
            );
        } finally {
            setSaving(false);
        }
    }

    function resetForm() {
        if (loadedConfig === null) {
            return;
        }

        populateForm(loadedConfig);
        setStatus("Changes reset.");
    }

    HUD_NAMES.forEach((hudName) => {
        getField(
            hudName,
            "position_mode"
        ).addEventListener(
            "change",
            () => updatePositionFields(hudName)
        );
    });

    form.addEventListener("submit", (event) => {
        event.preventDefault();
        saveConfig();
    });

    resetButton.addEventListener(
        "click",
        resetForm
    );

    loadConfig();
})();