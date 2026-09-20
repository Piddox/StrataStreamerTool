const OverlayData = (() => {
    let overlayConfig = null;
    let overlayData = null;
    let inGame = null;
    let lastMatchUpdateTrigger = null;
    let initialized = false;

    function getConfig() {
        return overlayConfig;
    }

    function getData() {
        return overlayData;
    }

    function isInGame() {
        return inGame;
    }


    async function refreshState() {
        try {
            const response =
                await fetch("/state", {
                    cache: "no-store"
                });

            if (!response.ok) {
                return;
            }

            const state =
                await response.json();

            if (state.in_game !== inGame) {
                inGame = state.in_game;

                if (initialized) {
                    window.renderOverlay();
                }
            }
        } catch (error) {
            // The local server may be restarting.
        }
    }

    async function refreshData() {
        try {
            const response =
                await fetch("/data", {
                    cache: "no-store"
                });

            if (!response.ok) {
                return;
            }

            const newData =
                await response.json();

            const oldValues =
                getOverallValues(
                    overlayData
                );

            const newValues =
                getOverallValues(
                    newData
                );

            const dataChanged =
                JSON.stringify(newData) !==
                JSON.stringify(overlayData);

            const matchUpdateTriggered =
                initialized &&
                newData.match_update_trigger !==
                lastMatchUpdateTrigger;

            const contentChanged =
                matchUpdateTriggered &&
                (
                    oldValues.rating !==
                        newValues.rating ||
                    oldValues.rank !==
                        newValues.rank
                );

            overlayData = newData;

            lastMatchUpdateTrigger =
                newData.match_update_trigger;

            if (dataChanged) {
                window.renderOverlay(contentChanged);
            }
        } catch (error) {
            // The local server may be restarting.
        }
    }

    async function refreshConfig() {
        try {
            const response =
                await fetch("/config", {
                    cache: "no-store"
                });

            if (!response.ok) {
                return;
            }

            const newConfig =
                await response.json();

            const configChanged =
                JSON.stringify(newConfig) !==
                JSON.stringify(overlayConfig);

            overlayConfig =
                newConfig;

            if (configChanged) {
                render();
            }
        } catch (error) {
            // The local server may be restarting.
        }
    }

    async function initialize() {
        await refreshConfig();
        await refreshData();
        await refreshState();

        applyResolution();

        if (
            overlayConfig !== null &&
            overlayData !== null &&
            inGame !== null
        ) {
            initialized = true;
            render();

            document
                .getElementById("overlay")
                .classList.add("ready");
        }
    }

    initialize();

    setInterval(
        refreshConfig,
        250
    );

    setInterval(
        refreshState,
        250
    );

    setInterval(
        refreshData,
        250
    );

    return {
        getConfig,
        getData,
        isInGame
    };
})();