import {EventValue} from "../value.js";

export class Popup {
    /**
     *
     * @type {RegExp}
     */
    INVALID_STRING_PATTERN = /[.#+:?><\[\](){} =*&^%$@!~`'"\\/,|]/;
    /**
     * @type {HTMLElement}
     */
    container;
    /**
     * @type {string}
     */
    popupID;
    /**
     * @type {string}
     */
    applicationPrefix;
    /**
     * @type {EventValue.<string>}
     */
    #title;
    constructor(applicationPrefix, containerID, popupID, title) {
        if (applicationPrefix.search(this.INVALID_STRING_PATTERN) >= 0) {
            throw new Error(
                `Cannot create a ${this.className} Popup - The application prefix contains illegal characters.`
            )
        }

        if (!containerID) {
            throw new Error(`An ID for a container must be passed to create a ${this.className} Popup`);
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
                finder = (elementID) => document.getElementById(elementID);
            }

            let cleanID;

            if (containerID.startsWith(".") || containerID.startsWith("#")) {
                cleanID = containerID.slice(1);
            } else {
                cleanID = containerID;
            }

            if (cleanID.search(this.INVALID_STRING_PATTERN) >= 0) {
                throw new Error(
                    `Cannot create a ${this.className} Popup - ` +
                    `The container ID ('${containerID}') is not a valid HTML ID.`
                )
            }

            let foundItem = finder(cleanID);

            if (foundItem === null) {
                throw new Error(
                    `An ${this.className} Popup cannot be created - its container ('${containerID}') cannot be found`
                );
            }

            this.container = foundItem;
        } else if (containerID instanceof HTMLElement) {
            this.container = containerID;
        } else {
            throw new Error(`${typeof containerID} objects cannot contain a ${this.className} Popup`);
        }

        if (!Boolean(popupID)) {
            const instanceCount = $(`.${this.getPopupClass()}`).length;
            popupID = `${this.applicationPrefix}-${instanceCount + 1}`;
        }

        if (typeof popupID !== 'string') {
            throw new Error(
                `A popup ID for a ${this.className} Popup must be a string - received '${popupID}' (${typeof popupID})`
            );
        }

        if (popupID.search(this.INVALID_STRING_PATTERN) >= 0) {
            throw new Error(`'${popupID}' is an invalid string for the HTML ID for a ${this.className} Popup`)
        }

        if (Boolean(title)) {
            if (typeof title !== 'string') {
                throw new Error(
                    `Cannot create a ${this.className} Popup - titles must be strings, but received a '${typeof title}'`
                )
            }
        }

        this.#title = new EventValue(
            title,
            (oldValue, newValue) => $(`#${this.popupID}`).dialog("option", "title", newValue)
        );
        this.popupID = popupID;
    }

    /**
     * @returns {HTMLElement|HTMLElement[]}
     */
    createContent = () => {
        throw new Error(`'${this.className}.createContent' must be implemented`);
    }

    render = () => {
        /**
         *
         * @type {HTMLDivElement}
         */
        const dialog = document.createElement("div");
        dialog.id = this.popupID;

        if (this.title) {
            dialog.title = this.title;
        }

        const dialogClasses = this.getDialogCSSClasses();

        if (!dialogClasses) {
            throw new Error(
                `Cannot create the ${this.className} popup named '${this.popupID}' - ` +
                `valid CSS classes for the dialog were not provided`
            );
        }

        const invalidDialogClasses = dialogClasses.split(" ")
            .filter(cls => cls.search(this.INVALID_STRING_PATTERN) >= 0)

        if (invalidDialogClasses.length) {
            throw new Error(
                `Cannot create the ${this.className} popup named '${this.popupID}' - ` +
                `the following CSS classes for the dialog are invalid: ${invalidDialogClasses.join(', ')}`
            )
        }

        dialog.className = dialogClasses;

        /**
         *
         * @type {HTMLDivElement}
         */
        const dialogContent = document.createElement("div")
        dialogContent.id = `${this.popupID}-content`;

        const dialogContentClasses = this.getDialogContentCSSClasses();

        if (!dialogContentClasses) {
            throw new Error(
                `Cannot create the popup named '${this.popupID}' - ` +
                `valid CSS classes for the dialog content were not provided`
            )
        }

        const invalidDialogContentClasses = dialogContentClasses.split(" ")
            .filter(cls => cls.search(this.INVALID_STRING_PATTERN) >= 0)

        if (invalidDialogContentClasses.length) {
            throw new Error(
                `Cannot create the ${this.className} popup named '${this.popupID}' - ` +
                `the following CSS classes for the dialog content are invalid: ${invalidDialogContentClasses.join(', ')}`
            )
        }

        dialogContent.className = dialogContentClasses;

        const content = this.createContent();

        if (Array.isArray(content)) {
            content.forEach(
                (element) => dialogContent.appendChild(element)
            );
        }
        else {
            dialogContent.appendChild(content);
        }

        dialog.appendChild(dialogContent);
        this.container.appendChild(dialog);

        $(`#${this.popupID}`).dialog({
            autoOpen: false,
            modal: true,
            width: this.getDefaultWidth()
        })

        return this;
    }

    rerender = () => {
        $(`#${this.popupID}`).remove();
        return this.render();
    }

    show = () => {
        if(document.getElementById(this.popupID) === null) {
            this.render();
        }

        const popup = $(`#${this.popupID}`);

        popup.dialog("option", "width", "auto");
        popup.dialog("option", "height", "auto");
        popup.dialog("open");
    }

    getPopupClass = () => {
        return `${this.applicationPrefix}-${this.className}-popup`
    }

    getDefaultWidth = () => {
        return "20%";
    }

    getDialogCSSClasses = () => {
        const cssClasses = [
            this.getPopupClass(),
            `${this.applicationPrefix}-modal`,
            `${this.applicationPrefix}-dialog`
        ]
        return cssClasses.join(" ");
    }

    getDialogContentCSSClasses = () => {
        const cssClasses = [
            `${this.getPopupClass()}-content`,
            `${this.applicationPrefix}-dialog-content`,
        ]
        return cssClasses.join(" ");
    }

    /**
     *
     * @returns {string}
     */
    get className() {
        return this.constructor.name;
    }

    /**
     * @returns {string}
     */
    get title() {
        return this.#title.get();
    }

    /**
     *
     * @param {string} newTitle
     */
    set title(newTitle) {
        return this.#title.set(newTitle);
    }
}