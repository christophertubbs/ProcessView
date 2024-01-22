import {EventValue} from "../value.js";
import {Popup} from "./popup.js";
import {createTable} from "../elements.js";

export class ProcessKilledView extends Popup {
    /**
     * @type {EventValue.<Number>}
     */
    #messageID;
    /**
     * @type {EventValue.<Object>}
     */
    #killedProcess;

    /**
     * @type {EventValue.<string>}
     */
    #killedProcessMessage;

    #killedMessageIDBlockElementID;
    #killedMessageIDElementID;
    #killedProcessElementID;
    #killedProcessMessageElementID;
    #killedProcessTableName;

    /**
     * Construct and render a new Popup
     *
     * @param applicationPrefix
     * @param containerID
     * @param popupID
     * @param title
     * @returns {ProcessKilledView}
     */
    static create(applicationPrefix, containerID, popupID, title) {
        return new this(applicationPrefix, containerID, popupID, title).render();
    }

    /**
     *
     * @param {string} applicationPrefix
     * @param {string} containerID
     * @param {string?} popupID
     * @param {string?} title
     */
    constructor(applicationPrefix, containerID, popupID, title) {
        super(applicationPrefix, containerID, popupID, title);

        this.#killedMessageIDElementID = `${this.popupID}-message-id`;
        this.#killedMessageIDBlockElementID = `${this.popupID}-message-id-block`
        this.#killedProcessMessageElementID = `${this.popupID}-message`;
        this.#killedProcessElementID = `${this.popupID}-process-data`;
        this.#killedProcessTableName = `${this.popupID}-process-table`;

        this.#messageID = new EventValue(
            null,
            (oldValue, newValue) => {
                if (newValue) {
                    $(`#${this.#killedMessageIDElementID}`).text(newValue);
                    $(`#${this.#killedMessageIDBlockElementID}`).show();
                } else {
                    $(`#${this.#killedMessageIDBlockElementID}`).hide();
                }
            }
        );

        this.#killedProcess = new EventValue(
            null,
            (oldValue, newValue) => {
                $(`#${this.#killedProcessElementID} > *`).remove()
                if (newValue) {
                    let processTable = createTable(
                        this.#killedProcessElementID,
                        this.#killedProcessTableName,
                        newValue
                    );
                    document.getElementById(this.#killedProcessElementID).appendChild(processTable);
                }
            }
        );

        this.#killedProcessMessage = new EventValue(
            null,
            (oldValue, newValue) => {
                $(`#${this.#killedProcessMessageElementID}`).text(newValue);
            }
        )
    }

    /**
     * @returns {HTMLElement|HTMLElement[]}
     */
    createContent = () => {
        /**
         *
         * @type {HTMLElement[]}
         */

        const raw = `
<span id="${this.#killedMessageIDBlockElementID}"><b>Message ID:</b> <span id="${this.#killedMessageIDElementID}"></span></span>
<p id="${this.#killedProcessMessageElementID}" class="${this.applicationPrefix}-info-message"></p>
<h4>State Prior to Process Death</h4>
<div id="${this.#killedProcessElementID}" class="${this.applicationPrefix}-table-container"></div>
`;
        const rawBlock = $(raw);
        return Array.from(rawBlock);
    }

    set messageID(newMessageID) {
        this.#messageID.set(newMessageID);
    }

    set killedProcess(newProcess) {
        this.#killedProcess.set(newProcess)
    }

    set killedProcessMessage(newMessage) {
        this.#killedProcessMessage.set(newMessage);
    }
}

pview.classes.ProcessKilledView = ProcessKilledView;