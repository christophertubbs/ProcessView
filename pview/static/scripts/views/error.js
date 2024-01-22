import {EventValue} from "../value.js";

/**
 * Builds a view on the page that allows a user to inspect loaded netcdf data
 */
export class ErrorView {
    static popupClass = "pview-error-popup";

    messageIDBlockElementID = "error-message-id-block";

    messageIDElementID = "error-messsage-id"

    messageID;

    messageTypeElementID = "error-message-type"

    messageType;

    errorMessageElementID = "error-message";

    errorMessage;

    /**
     * @type {HTMLElement}
     */
    container;

    popupID;

    /**
     * Constructor
     */
    constructor (containerID, popupID) {
        if (!containerID) {
            throw new Error("An ID for a container must be passed to create an error view");
        }

        if (typeof containerID === 'string') {
            let finder;
            if (containerID.startsWith(".")) {
                finder = function(name) {
                    const foundItems = document.getElementsByClassName(name);

                    if (foundItems.length) {
                        return foundItems[0];
                    }

                    return null;
                }
            }
            else {
                finder = document.getElementById;
            }

            let cleanID;

            if (containerID.startsWith(".") || containerID.startsWith("#")) {
                cleanID = containerID.slice(1);
            } else {
                cleanID = containerID;
            }

            if (cleanID.search(/[.#+:? ]/) >= 0) {
                throw new Error(
                    `Cannot create an ErrorView - The container ID ('${containerID}') is not a valid HTML ID.`
                )
            }

            let foundItem = finder(cleanID);

            if (foundItem === null) {
                throw new Error(`An error view cannot be created - it's container ('${containerID}') cannot be found`);
            }

            this.container = foundItem;
        } else if (containerID instanceof HTMLElement) {
            this.container = containerID;
        } else {
            throw new Error(`${typeof containerID} objects cannot contain error views`);
        }

        if (!Boolean(popupID)) {
            const instanceCount = $(`.${ErrorView.popupClass}`).length;
            popupID = `error-view-${instanceCount + 1}`;
        }

        if (typeof popupID !== 'string') {
            throw new Error(`A popup ID for an ErrorView must be a string, received '${popupID}' (${typeof popupID})`);
        }

        if (popupID.search(/[.# +:?]/) >= 0) {
            throw new Error(`'${popupID}' is an invalid string for the HTML ID for an ErrorView`)
        }

        this.popupID = popupID;

        this.errorMessageElementID = `${this.popupID}-${this.errorMessageElementID}`;
        this.messageIDBlockElementID = `${this.popupID}-${this.messageIDBlockElementID}`;
        this.messageIDElementID = `${this.popupID}-${this.messageIDElementID}`;
        this.messageTypeElementID = `${this.popupID}-${this.messageTypeElementID}`;

        this.errorMessage = new EventValue(
            null,
            (oldValue, newValue) => $(`#${this.errorMessageElementID}`).text(newValue)
        );
        this.messageID = new EventValue(
            null,
            (oldValue, newValue) => {
                if (Boolean(newValue)) {
                    $(`#${this.messageIDElementID}`).text(newValue);
                    $(`#${this.messageIDBlockElementID}`).show();
                }
                else {
                    $(`#${this.messageIDBlockElementID}`).hide();
                }
            }
        );
        this.messageType = new EventValue(
            null,
            (oldValue, newValue) => $(`#${this.messageTypeElementID}`).text(newValue)
        )

        this.render();
    }

    show = (messageID, messageType, errorMessage) => {
        this.messageID.set(messageID);
        this.messageType.set(messageType);
        this.errorMessage.set(errorMessage);

        $(`#${this.popupID}`).dialog("open");
    }

    /**
     * Render this view
     */
    render = () => {
        /**
         *
         * @type {HTMLDivElement}
         */
        const errorDialog = document.createElement("div");
        errorDialog.id = this.popupID;
        errorDialog.title = "Error";

        const dialogClasses = [
            'pview-dialog',
            'pview-modal',
            'pview-error-dialog'
        ]

        errorDialog.className = dialogClasses.join(" ");

        /**
         *
         * @type {HTMLDivElement}
         */
        const dialogContent = document.createElement("div")
        dialogContent.id = `${this.popupID}-content`;

        const dialogContentClasses = [
            'pview-dialog-content',
            'pview-error-content'
        ]

        dialogContent.className = dialogContentClasses.join(" ");

        /**
         *
         * @type {HTMLSpanElement}
         */
        const messageIDBlock = document.createElement("span");
        messageIDBlock.id = this.messageIDBlockElementID;

        /**
         *
         * @type {HTMLElement}
         */
        const messageIDLabel = document.createElement("b");
        messageIDLabel.textContent = "Message ID: ";

        messageIDBlock.appendChild(messageIDLabel)

        /**
         *
         * @type {HTMLSpanElement}
         */
        const messageIDField = document.createElement("span");
        messageIDField.id = this.messageIDElementID;
        messageIDField.className = "pview-error-details";

        messageIDBlock.appendChild(messageIDField);

        dialogContent.appendChild(messageIDBlock);

        dialogContent.appendChild(document.createElement("br"));

        /**
         *
         * @type {HTMLElement}
         */
        const failedOnLabel = document.createElement("b")
        failedOnLabel.textContent = "Failed On: ";

        dialogContent.appendChild(failedOnLabel);

        /**
         *
         * @type {HTMLSpanElement}
         */
        const failedMessageTypeBlock = document.createElement("span");
        failedMessageTypeBlock.id = this.messageTypeElementID;
        failedMessageTypeBlock.className = "pview-error-details"

        dialogContent.appendChild(failedMessageTypeBlock);

        /**
         *
         * @type {HTMLParagraphElement}
         */
        const errorMessageBlock = document.createElement("p");
        errorMessageBlock.id = this.errorMessageElementID;
        errorMessageBlock.className = 'pview-error-message'

        dialogContent.append(errorMessageBlock);

        errorDialog.appendChild(dialogContent);
        this.container.appendChild(errorDialog);

        $(`#${this.popupID}`).dialog({
            autoOpen: false,
            modal: true,
            width: "20%"
        })
    }
}

