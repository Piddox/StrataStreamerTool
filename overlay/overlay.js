const DESIGN_WIDTH = 3840;
const OVERLAY_COORDINATES_VISUAL_REFERENCE_SIZE = 2560;

const ARTWORK_REFERENCE_WIDTHS = {
    small: 521,
    big: 600
};

const HUD_FADE_OUT_MS = 200;
const HUD_FADE_IN_MS = 200;
const SESSION_CONTENT_FADE_MS = 200;

const TEMPLATE_CHANGE_DISPLAY_MS = 8000;
const TEMPLATE_CHANGE_TRANSITION_MS = 250;
const ARTWORK_SIZE_SMALL_MAX_CONTENT_WIDTH = 455;
const ARTWORK_SIZE_BIG_MAX_CONTENT_WIDTH = 525;


const panelContentTokens = {
    "hud-1": 0,
    "hud-2": 0
};

/*
    Every HUD panel owns exactly one runtime.

    appliedState / appliedVisible describe what the DOM actually shows
    right now. They are only written after the DOM has been changed, so
    an interrupted transition can never leave a state behind that was
    never rendered.

    desiredState / desiredConfig describe what the DOM should show.
    Renders only write the desired state and wake the panel loop, so a
    new render can never corrupt a running transition.
*/

function createPanelRuntime() {
    return {
        elements: null,

        appliedState: null,
        appliedVisible: false,

        desiredState: null,
        desiredConfig: null,

        contentDirty: false,
        contentChangeRequested: false,

        generation: 0,
        running: null,
        animation: null,
        wake: null
    };
}

const panelRuntimes = {
    "hud-1": createPanelRuntime(),
    "hud-2": createPanelRuntime()
};

function getPanelRuntime(element) {
    let runtime =
        panelRuntimes[element.id];

    if (!runtime) {
        runtime = createPanelRuntime();

        panelRuntimes[element.id] =
            runtime;
    }

    return runtime;
}

/*
    Every lookup is restricted to a single HUD panel, so hud-1 can
    never read or modify elements belonging to hud-2 and vice versa.
*/

function queryPanelScoped(element, selector) {
    const matches = [];

    for (const node of element.querySelectorAll(selector)) {
        if (node.closest(".hud-panel") === element) {
            matches.push(node);
        }
    }

    return matches;
}

function getPanelElements(element) {
    const runtime =
        getPanelRuntime(element);

    if (runtime.elements) {
        return runtime.elements;
    }

    const first = selector =>
        queryPanelScoped(
            element,
            selector
        )[0] || null;

    runtime.elements = {
        artwork: first(".hud-artwork"),

        templates: queryPanelScoped(
            element,
            "[data-template]"
        ),

        basicTemplate: first(".basic-elo-rank"),
        basicRatingRow: first(".basic-elo-row"),
        basicRankRow: first(".basic-rank-row"),

        sessionRatingRow: first(".session-elo-row"),
        sessionRankRow: first(".session-rank-row")
    };

    return runtime.elements;
}

const IN_GAME_POSITIONS = {
    left_top: {
        left: 0,
        bottom: 1050
    },
    left_middle: {
        left: 0,
        bottom: 750
    },
    left_bottom: {
        left: 0,
        bottom: 454
    },
    right_top: {
        right: 0,
        bottom: 1050
    },
    right_middle: {
        right: 0,
        bottom: 750
    },
    right_bottom: {
        right: 0,
        bottom: 454
    },
    hud_left: {
        left: 453,
        bottom: 0
    },
    hud_right: {
        right: 393,
        bottom: 0
    }
};

const IN_MENU_POSITIONS = {
    left_top: {
        left: 0,
        bottom: 750
    },
    left_middle: {
        left: 0,
        bottom: 270
    },
    left_bottom: {
        left: 0,
        bottom: 0
    },
    right_top: {
        right: 0,
        bottom: 750
    },
    right_middle: {
        right: 0,
        bottom: 490
    },
    right_bottom: {
        right: 0,
        bottom: 230
    }
};

function getResolutionProfile() {
    const width = window.innerWidth;

    if (width >= 2240) {
        return {
            width: 2560,
            height: 1440
        };
    }

    return {
        width: 1920,
        height: 1080
    };
}

function applyResolution() {
    const profile = getResolutionProfile();

    const templateScale =
        profile.width / DESIGN_WIDTH;

    // Basic template

    document.documentElement.style.setProperty(
        "--basic-font-size",
        `${80 * templateScale}px`
    );

    document.documentElement.style.setProperty(
        "--basic-row-left",
        `${47 * templateScale}px`
    );

    document.documentElement.style.setProperty(
        "--basic-row-1-bottom",
        `${220 * templateScale}px`
    );

    document.documentElement.style.setProperty(
        "--basic-row-2-bottom",
        `${100 * templateScale}px`
    );

    document.documentElement.style.setProperty(
        "--basic-normal-gap",
        `${35 * templateScale}px`
    );

    document.documentElement.style.setProperty(
        "--basic-change-label-gap",
        `${15 * templateScale}px`
    );

    document.documentElement.style.setProperty(
        "--basic-change-indicator-size",
        `${50 * templateScale}px`
    );

    document.documentElement.style.setProperty(
        "--basic-change-indicator-gap",
        `${2 * templateScale}px`
    );


    // Session template

    document.documentElement.style.setProperty(
        "--session-change-indicator-size",
        `${50 * templateScale}px`
    );

    document.documentElement.style.setProperty(
        "--session-font-size",
        `${80 * templateScale}px`
    );

    document.documentElement.style.setProperty(
        "--session-title-font-size",
        `${55 * templateScale}px`
    );

    document.documentElement.style.setProperty(
        "--session-row-left",
        `${47 * templateScale}px`
    );

    document.documentElement.style.setProperty(
        "--session-title-bottom",
        `${265 * templateScale}px`
    );

    document.documentElement.style.setProperty(
        "--session-row-1-bottom",
        `${160 * templateScale}px`
    );

    document.documentElement.style.setProperty(
        "--session-row-2-bottom",
        `${60 * templateScale}px`
    );
}

function getPanelState(panelConfig) {
    const configuredVisibilityMode =
        panelConfig.visibility_mode;

    let visible;

    const inGame =
        OverlayData.isInGame();

    const localPlayerFaction =
        OverlayData.getData().local_player_faction;

    let visibilityMode =
        configuredVisibilityMode;

    if (
        inGame &&
        panelConfig.hide_when_observing &&
        localPlayerFaction === "Observer"
    ) {
        visibilityMode = "never";
    }

    if (visibilityMode === "never") {
        visible = false;
    } else if (
        visibilityMode === "in_game"
    ) {
        visible = inGame;
    } else if (
        visibilityMode === "in_menu"
    ) {
        visible = !inGame;
    } else {
        visible = true;
    }

    let position;
    let positionIdentity;

    if (panelConfig.position_mode === "in_game") {
        position = panelConfig.in_game_position;

        positionIdentity =
            `in_game:${position}`;

    } else if (
        panelConfig.position_mode === "in_menu"
    ) {
        position = panelConfig.in_menu_position;

        positionIdentity =
            `in_menu:${position}`;

    } else {
        if (inGame) {
            position =
                panelConfig.in_game_position;

            positionIdentity =
                `in_game:${position}`;
        } else {
            position =
                panelConfig.in_menu_position;

            positionIdentity =
                `in_menu:${position}`;
        }
    }

    const artworkSize =
        panelConfig.artwork_size;

    const artworkColor =
        getEffectiveArtworkColor(
            panelConfig
        );

    return {
        visible,
        position,
        positionIdentity,
        artworkSize,
        artworkColor,
        template: panelConfig.template
    };
}

function getPanelChanges(
    oldState,
    newState
) {
    const positionChanged =
        oldState.positionIdentity !==
        newState.positionIdentity;

    const artworkSizeChanged =
        oldState.artworkSize !==
        newState.artworkSize;

    const artworkColorChanged =
        oldState.artworkColor !==
        newState.artworkColor;

    const visibilityChanged =
        oldState.visible !==
        newState.visible;

    return {
        positionChanged,
        artworkSizeChanged,
        artworkColorChanged,
        visibilityChanged,
        needsTransition:
            positionChanged ||
            artworkSizeChanged ||
            artworkColorChanged ||
            visibilityChanged
    };
}

function positionPanel(
    element,
    position,
    positionIdentity
) {
    let positions;

    if (positionIdentity.startsWith("in_game:")) {
        positions = IN_GAME_POSITIONS;
    } else if (
        positionIdentity.startsWith("in_menu:")
    ) {
        positions = IN_MENU_POSITIONS;
    } else {
        return;
    }

    const anchor = positions[position];

    if (!anchor) {
        return;
    }

    const profile = getResolutionProfile();

    const scale =
        profile.width /
        OVERLAY_COORDINATES_VISUAL_REFERENCE_SIZE;

    element.style.left = "";
    element.style.right = "";
    element.style.top = "";
    element.style.bottom = "";
    element.style.transform = "";

    if (anchor.left !== undefined) {
        element.style.left =
            `${anchor.left * scale}px`;
    }

    if (anchor.right !== undefined) {
        element.style.right =
            `${anchor.right * scale}px`;
    }

    if (anchor.bottom !== undefined) {
        element.style.bottom =
            `${anchor.bottom * scale}px`;
    }
}

function formatChange(value) {
    if (value === null || value === undefined) {
        return "0";
    }

    return value >= 0
        ? `+${value}`
        : `${value}`;
}

function getOverallValues(data) {
    const overall = data?.overall || {};

    return {
        rating: overall.rating ?? null,
        rank: overall.rank ?? null
    };
}

function getOverallChanges(data) {
    const changes = data?.changes || {};

    return {
        rating: changes.overall_rating_change ?? 0,
        rank: changes.overall_rank_change ?? 0
    };
}

function getMonthlyValues(data) {
    const monthly = data?.monthly || {};

    return {
        rating: monthly.rating ?? null,
        rank: monthly.rank ?? null
    };
}

function getMonthlyChanges(data) {
    const changes = data?.changes || {};

    return {
        rating:
            changes.monthly_rating_change  ?? 0,
        rank:
            changes.monthly_rank_change  ?? 0
    };
}

function getOverallSessionChanges(data) {
    const changes = data?.changes || {};

    return {
        rating:
            changes.overall_session_rating_change ?? 0,
        rank:
            changes.overall_session_rank_change ?? 0
    };
}

function getMonthlySessionChanges(data) {
    const changes = data?.changes || {};

    return {
        rating:
            changes.monthly_session_rating_change ?? 0,
        rank:
            changes.monthly_session_rank_change ?? 0
    };
}

function getLadderValues(data, ladder) {
    if (ladder === "monthly") {
        return getMonthlyValues(data);
    }

    return getOverallValues(data);
}

function getLadderChanges(data, ladder) {
    if (ladder === "monthly") {
        return getMonthlyChanges(data);
    }

    return getOverallChanges(data);
}

function getSessionChanges(data, ladder) {
    if (ladder === "monthly") {
        return getMonthlySessionChanges(data);
    }

    return getOverallSessionChanges(data);
}

function formatRank(rank) {
    if (rank === null || rank === undefined) {
        return "Unranked";
    }

    return `#${rank}`;
}

function getChangeIndicatorClass(change) {
    if (change > 0) {
        return "up";
    }

    if (change < 0) {
        return "down";
    }

    return "equal";
}

function setChangeIndicator(indicator, change) {
    indicator.classList.remove(
        "up",
        "down",
        "equal"
    );

    indicator.classList.add(
        getChangeIndicatorClass(change)
    );
}

function getTemplateElements(element) {
    const elements =
        getPanelElements(element);

    return {
        ratingRow: elements.basicRatingRow,
        rankRow: elements.basicRankRow
    };
}

function updateBasicRow(
    row,
    normalValue,
    changeValue
) {
    row.querySelector(
        ".basic-normal-value"
    ).textContent = normalValue;

    const indicator =
        row.querySelector(
            ".basic-change-indicator"
        );

    setChangeIndicator(
        indicator,
        changeValue
    );

    row.querySelector(
        ".basic-change-number"
    ).textContent =
        formatChange(changeValue);
}

function renderBasicTemplate(
    element,
    data,
    panelConfig
) {
    const values =
        getLadderValues(
            data,
            panelConfig.ladder
        );

    const changes =
        getLadderChanges(
            data,
            panelConfig.ladder
        );

    const elements =
        getTemplateElements(element);

    if (
        !elements.ratingRow ||
        !elements.rankRow
    ) {
        return;
    }

    updateBasicRow(
        elements.ratingRow,
        values.rating === null
            ? "N/A"
            : String(values.rating),
        changes.rating
    );

    updateBasicRow(
        elements.rankRow,
        formatRank(values.rank),
        changes.rank
    );
}

function renderSessionTemplate(
    element,
    data,
    panelConfig
) {
    const changes =
        getSessionChanges(
            data,
            panelConfig.ladder
        );

    const elements =
        getPanelElements(element);

    const eloRow =
        elements.sessionRatingRow;

    const rankRow =
        elements.sessionRankRow;

    if (!eloRow || !rankRow) {
        return;
    }

    updateSessionRow(
        eloRow,
        changes.rating
    );

    updateSessionRow(
        rankRow,
        changes.rank
    );
}


function updateSessionRow(
    row,
    change
) {
    const indicator =
        row.querySelector(
            ".session-change-indicator"
        );

    const value =
        row.querySelector(
            ".session-value"
        );

    setChangeIndicator(
        indicator,
        change
    );

    value.textContent =
        formatChange(change);
}

function setBasicTemplateMode(
    element,
    showChanges
) {
    const elements =
        getPanelElements(element);

    const rows = [
        elements.basicRatingRow,
        elements.basicRankRow
    ];

    for (const row of rows) {
        if (!row) {
            continue;
        }

        if (showChanges) {
            row.classList.add("change-mode");
        } else {
            row.classList.remove("change-mode");
        }
    }
}

function clearContentTimer(panelId) {
    const token =
        panelContentTokens[panelId];

    panelContentTokens[panelId] =
        token + 1;
}

function showBasicTemplateChanges(
    element,
    panelId,
    artworkSize
) {
    const token =
        panelContentTokens[panelId] + 1;

    panelContentTokens[panelId] =
        token;

    setBasicTemplateMode(
        element,
        true
    );

    applyTemplateScale(
        element, artworkSize
    );

    setTimeout(() => {
        if (
            token !==
            panelContentTokens[panelId]
        ) {
            return;
        }

        setBasicTemplateMode(
            element,
            false
        );

        applyTemplateScale(
            element, artworkSize
        );
    }, TEMPLATE_CHANGE_DISPLAY_MS);
}

function applyTemplateScale(element, artworkSize) {
    const elements =
        getPanelElements(element);

    const template =
        elements.basicTemplate;

    if (!template) {
        return;
    }

    const rows = [
        elements.basicRatingRow,
        elements.basicRankRow
    ];

    template.style.transform = "scale(1)";

    void template.offsetWidth;

    let widestRow = 0;

    for (const row of rows) {
        if (!row) {
            continue;
        }

        widestRow = Math.max(
            widestRow,
            row.getBoundingClientRect().width
        );
    }

    if (widestRow === 0) {
        template.style.transform = "scale(1)";

        return;
    }

    const profile =
        getResolutionProfile();

    const templateScale =
        profile.width / DESIGN_WIDTH;

    const maxContentWidth =
        artworkSize  === "small"
            ? ARTWORK_SIZE_SMALL_MAX_CONTENT_WIDTH
            : ARTWORK_SIZE_BIG_MAX_CONTENT_WIDTH;

    const maxWidth =
        maxContentWidth *
        templateScale;

    const scale =
        Math.min(
            1,
            maxWidth / widestRow
        );

    template.style.transform =
        `scale(${scale})`;
}

function applyPanelContent(
    element,
    panelConfig,
    panelState
) {
    const elements =
        getPanelElements(element);

    for (const templateElement of elements.templates) {
        templateElement.classList.toggle(
            "active",
            templateElement.dataset.template ===
                panelConfig.template
        );
    }

    const profile =
        getResolutionProfile();

    const artwork =
        elements.artwork;

    const artworkColor =
        panelState.artworkColor;

    if (artwork) {
        artwork.src = getArtworkPath(
            artworkColor,
            panelConfig.artwork_size
        );
    }

    const artworkScale =
        profile.width / DESIGN_WIDTH;

    const artworkWidth =
        ARTWORK_REFERENCE_WIDTHS[
            panelConfig.artwork_size
        ] * artworkScale;

    element.style.width =
        `${artworkWidth}px`;

    if (panelConfig.template === "rating_rank") {
        renderBasicTemplate(
            element,
            OverlayData.getData(),
            panelConfig
        );
    } else if (panelConfig.template === "session") {
        renderSessionTemplate(
            element,
            OverlayData.getData(),
            panelConfig
        );
    }

    applyTemplateScale(
        element, panelConfig.artwork_size
    );
}

/*
    Geometry and content are applied independently of visibility, so a
    hidden panel is always fully prepared and can be shown immediately
    and correctly.
*/

function applyPanelPresentation(
    element,
    panelConfig,
    panelState
) {
    positionPanel(
        element,
        panelState.position,
        panelState.positionIdentity
    );

    applyPanelContent(
        element,
        panelConfig,
        panelState
    );
}

/*
    The visible class is the only thing that controls visibility, and it
    is only ever set to the requested target state.
*/

function setPanelVisibility(
    element,
    runtime,
    visible
) {
    element.classList.toggle(
        "visible",
        visible
    );

    runtime.appliedVisible = visible;
}

function wait(milliseconds) {
    return new Promise(
        resolve => setTimeout(
            resolve,
            milliseconds
        )
    );
}

/*
    Opacity is driven by the Web Animations API instead of a CSS
    transition plus a parallel timer, so a transition can be awaited
    exactly, interrupted at any point, and restarted from the opacity
    the panel currently has.
*/

function getPanelOpacity(element, runtime) {
    if (!runtime.animation) {
        return runtime.appliedVisible
            ? 1
            : 0;
    }

    const opacity =
        parseFloat(
            window.getComputedStyle(
                element
            ).opacity
        );

    if (Number.isNaN(opacity)) {
        return runtime.appliedVisible
            ? 1
            : 0;
    }

    return opacity;
}

function cancelPanelAnimation(runtime) {
    if (!runtime.animation) {
        return;
    }

    runtime.animation.cancel();

    runtime.animation = null;
}

function waitForPanelChange(runtime) {
    return new Promise(
        resolve => {
            runtime.wake = resolve;
        }
    );
}

function wakePanel(runtime) {
    if (!runtime.wake) {
        return;
    }

    const wake = runtime.wake;

    runtime.wake = null;

    wake();
}

/*
    Returns true when the animation finished and this generation is
    still the current one. Returns false when a newer render superseded
    it, in which case the panel loop immediately re-converges towards
    the new desired state.
*/

async function awaitPanelAnimation(
    runtime,
    generation
) {
    const animation =
        runtime.animation;

    if (!animation) {
        return generation === runtime.generation;
    }

    await Promise.race([
        animation.finished.catch(() => {}),
        waitForPanelChange(runtime)
    ]);

    runtime.wake = null;

    if (generation !== runtime.generation) {
        return false;
    }

    if (runtime.animation === animation) {
        animation.cancel();

        runtime.animation = null;
    }

    return true;
}

async function fadePanel(
    element,
    runtime,
    generation,
    visible,
    durationMilliseconds
) {
    const from =
        getPanelOpacity(element, runtime);

    const to = visible
        ? 1
        : 0;

    cancelPanelAnimation(runtime);

    if (typeof element.animate !== "function") {
        setPanelVisibility(
            element,
            runtime,
            visible
        );

        return generation === runtime.generation;
    }

    runtime.animation = element.animate(
        [
            { opacity: from },
            { opacity: to }
        ],
        {
            duration: durationMilliseconds,
            easing: "ease",
            fill: "both"
        }
    );

    setPanelVisibility(
        element,
        runtime,
        visible
    );

    return awaitPanelAnimation(
        runtime,
        generation
    );
}

/*
    Brings the DOM in line with the desired state exactly once.

    The rules are:

    1. Geometry, artwork and content may only change while the panel is
       fully transparent, so a change is never visible as a jump.
    2. Content values are refreshed in place, also while hidden.
    3. The visible class always matches the requested target state.
    4. Applied state is committed the moment the DOM receives it.
*/

async function convergePanel(
    element,
    runtime,
    generation
) {
    const target =
        runtime.desiredState;

    const panelConfig =
        runtime.desiredConfig;

    if (!runtime.appliedState) {
        applyInitialPanelState(
            element,
            runtime,
            panelConfig,
            target
        );

        return;
    }

    const changes =
        getPanelChanges(
            runtime.appliedState,
            target
        );

    const structuralChange =
        changes.positionChanged ||
        changes.artworkSizeChanged ||
        changes.artworkColorChanged;

    if (
        runtime.contentChangeRequested &&
        (
            structuralChange ||
            target.visible !== runtime.appliedVisible
        )
    ) {
        clearContentTimer(element.id);
    }

    if (
        structuralChange &&
        getPanelOpacity(element, runtime) > 0
    ) {
        const faded = await fadePanel(
            element,
            runtime,
            generation,
            false,
            HUD_FADE_OUT_MS
        );

        if (!faded) {
            return;
        }
    }

    if (
        structuralChange ||
        runtime.contentDirty
    ) {
        applyPanelPresentation(
            element,
            panelConfig,
            target
        );

        runtime.appliedState = target;
        runtime.contentDirty = false;
    }

    if (target.visible !== runtime.appliedVisible) {
        const faded = await fadePanel(
            element,
            runtime,
            generation,
            target.visible,
            target.visible
                ? HUD_FADE_IN_MS
                : HUD_FADE_OUT_MS
        );

        if (!faded) {
            return;
        }

    } else if (runtime.animation) {
        const finished = await awaitPanelAnimation(
            runtime,
            generation
        );

        if (!finished) {
            return;
        }
    }

    if (runtime.contentChangeRequested) {
        runtime.contentChangeRequested = false;

        showBasicTemplateChanges(
            element,
            element.id,
            panelConfig.artwork_size
        );
    }
}

/*
    The very first render snaps into the configured state without a
    fade, exactly as before.
*/

function applyInitialPanelState(
    element,
    runtime,
    panelConfig,
    target
) {
    // Opacity is owned by the animation API from here on.
    element.style.transition = "none";

    applyPanelPresentation(
        element,
        panelConfig,
        target
    );

    runtime.appliedState = target;
    runtime.contentDirty = false;

    cancelPanelAnimation(runtime);

    setPanelVisibility(
        element,
        runtime,
        target.visible
    );

    if (
        panelConfig.template ===
        "rating_rank"
    ) {
        setBasicTemplateMode(
            element,
            false
        );
    }

    runtime.contentChangeRequested = false;
}

async function runPanel(element, runtime) {
    try {
        while (true) {
            const generation =
                runtime.generation;

            await convergePanel(
                element,
                runtime,
                generation
            );

            if (
                generation === runtime.generation
            ) {
                return;
            }
        }

    } finally {
        runtime.running = null;
        runtime.wake = null;
    }
}

function renderPanel(
    element,
    panelConfig,
    contentChanged = false
) {
    const runtime =
        getPanelRuntime(element);

    runtime.desiredState =
        getPanelState(panelConfig);

    runtime.desiredConfig =
        panelConfig;

    runtime.contentDirty = true;

    if (
        contentChanged &&
        panelConfig.template === "rating_rank" &&
        runtime.appliedState
    ) {
        runtime.contentChangeRequested = true;
    }

    runtime.generation++;

    if (runtime.running) {
        wakePanel(runtime);

        return;
    }

    runtime.running =
        runPanel(element, runtime).catch(
            () => {}
        );
}

function getArtworkPath(
    artworkColor,
    artworkSize
) {
    const artworkPrefixes = {
        blue: "usa",
        red: "china",
        green: "gla"
    };

    const prefix =
        artworkPrefixes[artworkColor];

    if (!prefix) {
        return "";
    }

    return `/overlay/artwork/${prefix}_${artworkSize}.png`;
}

function getEffectiveArtworkColor(
    panelConfig
) {
    const artworkColor =
        panelConfig.artwork_color;

    // Explicit color selection always wins.
    if (artworkColor !== "faction_dependent") {
        return artworkColor;
    }

    // Faction-dependent artwork defaults to USA
    // when no game is active.
    if (!OverlayData.isInGame()) {
        return "blue";
    }

    const faction =
        OverlayData.getData().local_player_faction;

    const factionColors = {
        USA: "blue",
        China: "red",
        GLA: "green"
    };

    return factionColors[faction] || "blue";
}

function render(contentChanged = false) {
    const config =
        OverlayData.getConfig();

    const inGame =
        OverlayData.isInGame();

    if (!config) {
        return;
    }

    if (inGame === null) {
        return;
    }

    renderPanel(
        document.getElementById("hud-1"),
        config.hud_1,
        contentChanged
    );

    renderPanel(
        document.getElementById("hud-2"),
        config.hud_2,
        contentChanged
    );
}

window.renderOverlay = render;

window.addEventListener(
    "resize",
    () => {
        applyResolution();
        render();
    }
);