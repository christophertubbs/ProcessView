import {closeAllDialogs, openDialog} from "./utility.js";
import {AcknowledgementResponse, DataResponse, OpenResponse} from "./responses.js";
import {DatasetView} from "./views/metadata.js";
import {BooleanValue, ListValue, ListValueAction} from "./value.js";

const PREVIOUS_PATH_KEY = "previousPath";

function initializeBackingVariables() {
    const connected = BooleanValue.True;
    connected.onUpdate(socketIsConnected);

    Object.defineProperty(
        pview,
        "connected",
        {
            get() {
                return connected.isTrue;
            },
            set(newValue) {
                if (newValue) {
                    return connected.toTrue
                }
                return connected.toFalse
            },
            enumerable: true
        }
    )

    Object.defineProperty(
        pview,
        "datasets",
        {
            value: new ListValue(
                [],
                handleDatasetAddition,
                handleDatasetRemoval,
                toggleContentLoadStatus
            ),
            enumerable: true
        }
    )
}

async function initializeClient() {

    const client = new pview.PViewClient();

    client.addHandler("open", () => pview.connected = true);
    client.addHandler("closed", () => pview.connected = false);
    client.addHandler("load", dataLoaded);
    client.addHandler("error", handleError);

    client.registerPayloadType("connection_opened", OpenResponse);
    client.registerPayloadType("data", DataResponse);
    client.registerPayloadType("acknowledgement", AcknowledgementResponse);
    client.registerPayloadType("load", DataResponse)

    Object.defineProperty(
        pview,
        "client",
        {
            value: client,
            enumerable: true
        }
    )

    pview.connected = false;
    await pview.client.connect("ws");
}

function toggleContentLoadStatus() {
    const isEmpty = pview.datasets.isEmpty();

    const contentToShow = $(isEmpty ? "#no-content-block" : "#content");
    const contentToHide = $(isEmpty ? "#content" : "#no-content-block");

    contentToShow.show();
    contentToHide.hide();
}

function contentHasBeenLoaded(wasLoaded, isNowLoaded) {
    if (wasLoaded === isNowLoaded) {
        return;
    }

    const contentToHide = $(isNowLoaded ? "#no-content-block" : "#content");
    const contentToShow = $(isNowLoaded ? "#content" : "#no-content-block");

    contentToHide.hide();
    contentToShow.show();

    console.log("The content loaded state should now be reflected");
}

function socketIsConnected(wasConnected, isNowConnected) {
    if (wasConnected === isNowConnected) {
        return;
    }

    const contentToHide = $(isNowConnected ? ".pview-when-disconnected" : ".pview-when-connected");
    const contentToShow = $(isNowConnected ? ".pview-when-connected" : ".pview-when-disconnected");

    contentToHide.hide();
    contentToShow.show();
}

/**
 *
 * @param payload {DataResponse}
 */
function addDatasetView(payload) {
    try {
        const view = new DatasetView(payload);
        view.render("#content", "#content-tabs");
    } catch (e) {
        console.error(e);
    }
    closeLoadingModal();
}

async function handleError(payload) {
    $("#failed_message_type").text(Boolean(payload['message_type']) ? payload["message_type"] : "Unknown")
    $("#failed-message-id").text(payload['message_id']);
    $("#error-message").text(payload['error_message']);
    openDialog("#error-dialog");
}

function initializeModals() {
    $(".pview-modal:not(#load-dialog):not(#loading-modal)").dialog({
        modal: true,
        autoOpen: false
    });

    $("#error-dialog").dialog({
        modal: true,
        autoOpen: false,
        width: "20%"
    });

    $("#loading-modal").dialog({
        modal: true,
        autoOpen: false,
        width: "50%",
        height: 200
    })
}

async function initialize() {
    initializeBackingVariables();
    initializeModals();
    $("#loading-progress-bar").progressbar({value: false});
    $("button").button();
    $("#content").tabs();
    toggleContentLoadStatus();

    Object.defineProperty(
        pview,
        "refreshTabs",
        {
            value: () => {
                const tabsView = $("#content").tabs();
                tabsView.tabs("refresh");
                tabsView.off("click");
                tabsView.on("click", "span.ui-icon-close", function() {
                    pview.removeData(this.dataset.data_id);
                });
            },
            enumerable: true
        }
    );

    Object.defineProperty(
        pview,
        "removeData",
        {
            value: (data_id) => {
                const responseIndex = pview.datasets.findIndex((response) => response.data_id === data_id);

                if (responseIndex >= 0) {
                    pview.datasets.removeAt(responseIndex);
                }
            }
        }
    )

    $("#close-loading-modal-button").on("click", closeLoadingModal);

    await initializeClient();
}

function removeTab(removalEvent) {

}

async function loadDataClicked(event) {
    const url = $("input#open-path").val();
    await getData(url);
    localStorage.setItem(PREVIOUS_PATH_KEY, url);
}

document.addEventListener("DOMContentLoaded", async function(event) {
    $("#root-selector").on("change", rootChanged);
    //await initialize();
    await loadPS()
});

function closeLoadingModal() {
    closeAllDialogs();
}

window.diagnostics = {}

async function loadPS() {
    const psData = await fetch("/ps").then((response) => response.json());
    window.pview.traces = {};

    $("#total-cpu-used").text(psData.cpu_percent);
    $("#total-memory-used").text(psData.memory_usage);

    window.diagnostics['plotData'] = psData;

    $("#root-selector > *").remove()

    for (let dataIndex = 0; dataIndex < psData.data.length; dataIndex++) {
        let name = psData.data[dataIndex].name;
        let trace = {
            data: [psData.data[dataIndex]],
            layout: psData.layout
        }
        window.pview.traces[name] = trace;
        $("#root-selector").append(`<option value="${name}">${name}</option>`)
    }

    const firstName = psData.data[0].name;

    $("#root-selector").val(firstName).change();
}

async function rootChanged(event) {
    let selectedTraceName = $(event.target).val();
    await selectTrace(selectedTraceName)
}

async function selectTrace(traceName) {
    const trace = window.pview.traces[traceName];
    $("#content > *").remove()
    window.pview.currentPlot = await Plotly.newPlot("content", trace);
    $("#content").on("plotly_click", onPlotClick)
}

async function onPlotClick(event, clickEventAndPoints) {
    debugger;
    const points = clickEventAndPoints['points']
    if (!Array.isArray(points)) {
        throw new Error(`The returned 'points' data was not a valid array`);
    }
    else if (points.length === 0) {
        return
    }

    const point = points[0];
    if (typeof point.id !== "number") {
        return;
    }

    const processInfo = await fetch(`/pid/${point.id}`).then(response => response.json())
    debugger;
}