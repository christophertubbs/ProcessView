import {Popup} from "./popup.js";
import {createTable} from "../elements.js";
import {closeAllDialogs, describeMemory, describeNumber} from "../utility.js";


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


export class ProcessView extends Popup {
    /**
     * @type {ProcessInformation}
     */
    #process;
    #tableID;
    #tableName;

    /**
     * @type {HTMLDivElement}
     */
    #tableContainer;

    /**
     * @type {HTMLDivElement}
     */
    #toolbar;

    /**
     * @type {HTMLButtonElement}
     */
    #killButton;

    /**
     * @type {function(MouseEvent): Promise}
     */
    #onKill;

    /**
     *
     * @param {ProcessInformation} info
     */
    set process(info) {
        this.#process = info;

        if (info.canModify) {
            $(this.#toolbar).show();
        } else {
            $(this.#toolbar).hide();
        }

        let rows = [
            {
                key: "Name",
                value: info.name
            },
            {
                key: "Command",
                value: info.command
            },
            {
                key: "Process ID",
                value: info.processID
            },
            {
                key: "Owner",
                value: info.username
            }
        ];

        if (info.startTime) {
            rows.push({
                key: "Launch Time",
                value: info.startTime
            })
        }

        rows = rows.concat([
            {
                key: "CPU",
                value: `${describeNumber(info.cpuPercent)}%`
            },
            {
                key: "Memory",
                value: `${describeNumber(info.memoryPercent)}%`
            },
            {
                key: "Memory Usage",
                value: describeMemory(info.memoryUsage)
            }
        ]);

        let newTable = createTable(
            this.#tableID,
            this.#tableName,
            rows,
            null,
            null,
            false
        );

        this.#tableContainer.replaceChildren(newTable);
        this.title = info.name;

        $(this.#killButton).attr("data-pid", info.processID);
    }

    /**
     * Construct and render a new Popup
     *
     * @param applicationPrefix
     * @param containerID
     * @param popupID
     * @param title
     * @param tableID
     * @param tableName
     * @param onKill
     * @returns {ProcessView}
     */
    static create(applicationPrefix, containerID, popupID, title, tableID, tableName, onKill) {
        return new this(applicationPrefix, containerID, popupID, title, tableID, tableName, onKill).render();
    }

    constructor(applicationPrefix, containerID, popupID, title, tableID, tableName, onKill) {
        super(applicationPrefix, containerID, popupID, title)
        this.#tableID = tableID;
        this.#tableName = tableName;
        this.#onKill = onKill;
    }


    /**
     * @returns {HTMLElement|HTMLElement[]}
     */
    createContent = () => {
        /**
         *
         * @type {HTMLElement[]}
         */

        this.#toolbar = $(`<div id="${this.popupID}-toolbar" class="pview-toolbar"></div>`)[0];

        this.#killButton = $(`<button id="${this.popupID}-kill-process-button">Kill Process</button>`)[0];
        this.#killButton.onclick = this.#onKill;

        this.#toolbar.append(this.#killButton)

        this.#tableContainer = $(`<div id="${this.popupID}-process-data" class="pview-table-container"></div>`)[0];

        return [
            this.#toolbar,
            this.#tableContainer
        ]
    }
}

pview.classes.ProcessView = ProcessView;