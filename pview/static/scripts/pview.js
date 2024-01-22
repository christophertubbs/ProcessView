import {closeAllDialogs, describeMemory, describeNumber, openDialog, request_json} from "./utility.js";
import {BooleanValue} from "./value.js";
import {createTable} from "./elements.js";
import {ErrorView} from "./views/error.js";
import {ProcessKilledView} from "./views/kill.js";
import {Communicator} from "./communication.js";
import {ProcessView} from "./views/process.js";
import {ProcessInformationResponse} from "./messaging/response.js";
import {ProcessInformation} from "./process.js";

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

function initializeModals() {
    $(".pview-modal:not(#load-dialog):not(#loading-modal)").dialog({
        modal: true,
        autoOpen: false
    });

    $("#loading-modal").dialog({
        modal: true,
        autoOpen: false,
        width: "50%",
        height: 200
    })

    $("#loading-progress-bar").progressbar({
        value: false
    })

    pview.errorView = new ErrorView(document.getElementsByTagName("body")[0]);
    pview.processView = ProcessView.create(
        "pview",
        "popup-container",
        "process-dialog",
        "Process",
        "process-info",
        "process-info",
        killProcess
    )
    pview.killedProcessView = ProcessKilledView.create(
        "pview",
        "popup-container",
        "killed-process-info",
        "Process Killed"
    )
}

async function initialize() {
    $("#root-selector").on("change", rootChanged);

    initializeBackingVariables();
    initializeModals();

    $("button").button();

    $("#loading-modal").dialog("open");
    $("#kill-process-button").on("click", killProcess)
    $("#resample-button").on("click", resample);
}

document.addEventListener(
    "DOMContentLoaded",
    async function() {
        await initialize();
        const dataLoaded = await loadPS();

        if (dataLoaded) {
            closeAllDialogs();
        }
        else {
            $("#loading-modal").dialog("close");
        }
});

async function resample() {
    closeAllDialogs();

    $("#loading-modal").dialog("open");
    const success = await loadPS();

    if (success) {
        closeAllDialogs();
    }
}

async function loadPS() {
    return await pview.communicate(
        "/ps",
        function(psData) {
            $("#total-cpu-used").text(psData.cpu_percent);
            $("#total-memory-used").text(psData.memory_usage);

            pview.diagnostics['plotData'] = psData;

            $("#root-selector > *").remove()
            const rootSelector = $("#root-selector");

            for (let dataIndex = 0; dataIndex < psData.data.length; dataIndex++) {
                let name = psData.data[dataIndex].name;
                pview.traces[name] = {
                    data: [psData.data[dataIndex]],
                    layout: psData.layout
                }
                rootSelector.append(`<option value="${name}">${name}</option>`)
            }

            const firstName = psData.data[0].name;

            rootSelector.val(firstName).change();
        }
    )
}

async function rootChanged(event) {
    let selectedTraceName = $(event.target).val();
    await selectTrace(selectedTraceName)
}

async function selectTrace(traceName) {
    const trace = pview.traces[traceName];
    $("#content > *").remove()
    pview.currentPlot = await Plotly.newPlot("content", trace);
    $("#content").on("plotly_click", onPlotClick)
}

async function onPlotClick(event, clickEventAndPoints) {
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

    //await pview.communicate(`/pid/${point.id}`, loadProcessInformation);
    await pview.communicate(
        `/pid/${point.id}`,
        function(response) {
            const data = new ProcessInformation(response);
            pview.processView.process = data;
            pview.processView.show();
        }
    );
}

function loadProcessInformation(processInfo) {
    if (processInfo.can_modify) {
        $("#process-toolbar").show();
    } else {
        $("#process-toolbar").hide();
    }

    let rows = [
        {
            key: "Name",
            value: processInfo.name
        },
        {
            key: "Command",
            value: processInfo.command
        },
        {
            key: "Process ID",
            value: processInfo.process_id
        },
        {
            key: "Owner",
            value: processInfo.username
        }
    ];

    if (processInfo.create_time) {
        rows.push({
            key: "Launch Time",
            value: processInfo.create_time
        })
    }

    rows = rows.concat([
        {
            key: "CPU",
            value: `${describeNumber(processInfo.cpu_percent)}%`
        },
        {
            key: "Memory",
            value: `${describeNumber(processInfo.memory_percent)}%`
        },
        {
            key: "Memory Usage",
            value: describeMemory(processInfo.memory_usage)
        }
    ]);

    let processTable = createTable(
        "processTable",
        "process",
        rows,
        null,
        null,
        false
    );

    $("#process-data *").remove();
    $("#process-data").append(processTable);

    const processDialog = $("#process-dialog")

    processDialog.dialog("option", "width", "auto");
    processDialog.dialog("option", "height", "auto");
    processDialog.dialog("option", "title", processInfo.name);

    processDialog.dialog("open");

    $("#kill-process-button").attr("data-pid", processInfo.process_id);
}


async function killProcess(event) {
    const pid = event.target.dataset['pid'];

    closeAllDialogs()

    await pview.communicate(
        `/kill/${pid}`,
        async function(response) {
            pview.killedProcessView.messageID = response.message_id;
            pview.killedProcessView.killedProcess = response.process;
            pview.killedProcessView.killedProcessMessage = response.message;
            pview.killedProcessView.show()
            await loadPS();
    });
}

function reportError(errorData) {
    closeAllDialogs();
    pview.errorView.show(
        errorData.message_id,
        errorData.message_type,
        errorData.error_message
    );
}

window.pview.Communicator = new Communicator(reportError);
window.pview.communicate = async (address, onSuccess) => window.pview.Communicator.communicate(address, onSuccess);