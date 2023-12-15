import {DataResponse} from "../responses.js";
import {Dataset} from "../model.js";
import {createFieldSet, createSimpleList, createTable} from "../elements.js";

/**
 * Builds a view on the page that allows a user to inspect loaded netcdf data
 */
export class DatasetView {
    /**
     * The response that brought back the netcdf data
     * @member {DataResponse}
     */
    data

    /**
     * Details about the netcdf file
     * @member {Dataset}
     */
    dataset
    /**
     * A unique identifier for this data that also matches what is on the server
     * @member {string}
     */
    data_id

    /**
     * The anchor that activates the tab for this when clicked
     *
     * @member {HTMLAnchorElement|undefined}
     */
    tabLink;

    /**
     * Constructor
     *
     * @param data {DataResponse} The response from the server that provided this data
     */
    constructor (data) {
        this.data = data;
        this.data_id = data.data_id;
        this.dataset = new Dataset(data.data);
    }

    open = () => {
        this.tabLink.click();
    }

    get #tabID() {
        return `${this.data_id}-tab`
    }

    /**
     * Add a tab for this dataset in the set of tabs
     *
     * @param tabSelector {string}
     */
    #addTab = (tabSelector) => {
        const tabs = $(tabSelector);

        // Only add this tab if there isn't already one like it
        if ($(`${tabSelector} li#${this.#tabID}`).length === 0) {
            /**
             * @type {HTMLLIElement}
             */
            const tab = document.createElement("li")
            tab.id = this.#tabID

            /**
             *
             * @type {HTMLAnchorElement}
             */
            const tabLink = document.createElement("a")
            tabLink.href = `#${this.data_id}`;

            if (this.dataset.name) {
                const nameParts = this.dataset.name.split(/(\\|\/)/);
                tabLink.innerText = nameParts[nameParts.length - 1];
            }
            else {
                tabLink.innerText = this.data_id;
            }

            const tabCloseButton = document.createElement("span");
            tabCloseButton.className = "ui-icon ui-icon-close";
            tabCloseButton.dataset['data_id'] = this.data_id
            tabCloseButton.dataset['container_selector'] = `#${this.data_id}`
            tabCloseButton.dataset['tab_selector'] = `#${this.#tabID}`

            this.tabLink = tabLink;

            tab.appendChild(tabLink);
            tab.appendChild(tabCloseButton);
            tabs.append(tab);
        }
    }

    /**
     * Render this view at the given tab container
     *
     * @param tabContainerSelector {string} The selector for the containers where tab data is added
     * @param tabListSelector {string} The selector for the list of tabs where the handle will be placed
     */
    render = (tabContainerSelector, tabListSelector) => {
        /**
         * The container that holds all tab content
         *
         * @type {jQuery}
         */
        const tabContainer = $(tabContainerSelector);

        if (!tabContainer) {
            throw new Error(`No elements could be found at '${tabContainerSelector}' - a new view cannot be rendered`)
        }

        if ($(tabListSelector).length === 0) {
            throw new Error(`No tab list could be found at '${tabListSelector}' - a new view cannot be rendered`)
        }

        if ($(`#${this.data_id}`).length > 0) {
            console.warn(`There is already a view for dataset ${this.data_id}`)
        }

        /**
         *
         * @type {HTMLDivElement}
         */
        const newTab = document.createElement("div");
        newTab.id = this.data_id;

        const containerCSSClasses = [
            `pview-container`,
            'pview-tab',
            `pview-dataset`
        ]

        newTab.className = containerCSSClasses.join(" ");
        newTab.dataset['dataset'] = this.data_id;
        newTab.dataset['tab'] = this.#tabID;

        /**
         *
         * @type {HTMLDivElement}
         */
        const innerContainer = document.createElement("div");
        innerContainer.id = `${this.data_id}-field-wrapper`;

        const innerContainerCSSClasses = [
            "pview-field-wrapper"
        ]

        innerContainer.className = innerContainerCSSClasses.join(" ");

        const metadataFieldset = createFieldSet(
            `${this.data_id}-metadata`,
            `${this.data_id}-metadata`,
            "Metadata"
        );

        if (this.dataset.name) {
            const nameLabel = document.createElement("b")
            nameLabel.innerText = "Name: "
            nameLabel.className = "pview-detail-label"

            const nameTag = document.createElement("span")
            nameTag.innerText = this.dataset.name
            nameTag.className = 'pview-detail';

            metadataFieldset.appendChild(nameLabel)
            metadataFieldset.appendChild(nameTag)
            metadataFieldset.appendChild(document.createElement("br"))
        }

        const idLabel = document.createElement("b");
        idLabel.innerText = "Generated ID: ";
        idLabel.className = "pview-detail-label";

        const idTag = document.createElement("span");
        idTag.innerText = this.data_id;
        idTag.className = 'pview-detail';

        metadataFieldset.appendChild(idLabel);
        metadataFieldset.appendChild(idTag);
        metadataFieldset.appendChild(document.createElement("br"))

        innerContainer.appendChild(metadataFieldset);

        const renderedDimensions = this.renderDimensions(this.dataset.dimensions);

        if (renderedDimensions) {
            innerContainer.appendChild(renderedDimensions);
        }

        const renderedVariables = this.renderVariables(this.dataset.variables);

        if (renderedVariables) {
            innerContainer.appendChild(renderedVariables);
        }

        let globalAttributes = createTable(
            `${this.data_id}-global-attributes`,
            "Global Attributes",
            this.dataset.attributes
        )

        if (globalAttributes) {
            const globalAttributesField = createFieldSet(
                `${this.data_id}-global-fields`,
                "global-attributes",
                "Global Attributes"
            );
            globalAttributesField.appendChild(globalAttributes);
            innerContainer.appendChild(globalAttributesField);
        }

        newTab.appendChild(innerContainer);

        tabContainer.append(newTab)

        $(".pview-accordion").accordion({
            heightStyle: "content"
        });

        this.#addTab(tabListSelector);
        //tabContainer.tabs("refresh");
        pview.refreshTabs()

        this.open();
    }

    /**
     *
     * @param dimensions {Dimension[]}
     * @returns {HTMLFieldSetElement}
     */
    renderDimensions = (dimensions) => {
        const dimensionsID = `${this.data_id}-dimensions`;

        const dimensionsFieldset = createFieldSet(
            dimensionsID,
            "dimensions-fields",
            "Dimensions"
        )

        const rows = dimensions.map(
            (dimension) => {
                let dimensionData = {
                    name: dimension.name,
                    datatype: dimension.datatype,
                    minimum: dimension.minimum,
                    maximum: dimension.maximum,
                    count: dimension.count
                };
                if (dimension.attributes !== null && dimension.attributes !== undefined) {
                    Object.assign(dimensionData, dimension.attributes);
                }
                return dimensionData;
            });

        const tableID = `${dimensionsID}-table`

        const dimensionsTable = createTable(
            tableID,
            "Dimensions",
            rows,
            null,
            {
                "name": "Name",
                "datatype": "Data Type",
                "minimum": "Minimum",
                "maximum": "Maximum"
            }
        )

        dimensionsFieldset.appendChild(dimensionsTable);


        return dimensionsFieldset;
    }

    /**
     *
     * @param variables {Variable[]}
     * @returns {HTMLDivElement}
     */
    renderVariables = (variables) => {
        /**
         *
         * @type {HTMLDivElement}
         */
        const accordion = document.createElement("div");
        accordion.id = `${this.data_id}-accordion`;
        accordion.className = "pview-variable-accordion pview-accordion"

        const notGlobal = false;

        for (let variable of variables) {
            const variableID = `${this.data_id}-${variable.name}`;

            /**
             *
             * @type {HTMLHeadingElement}
             */
            let variableHeader = document.createElement("h3")
            variableHeader.id = `${variableID}-bar`;
            variableHeader.className = "pview-variable-bar";

            let datatype;

            if (/^\|S1/.test(variable.datatype)) {
                datatype = '';
            }
            else if (/^\|S\d+/.test(variable.datatype)) {
                datatype = "string ";
            }
            else if (/^[Ii][Nn][Tt]\d+/.test(variable.datatype)) {
                datatype = "int "
            }
            else if (/^[Ff][Ll][Oo][Aa][Tt]\d+/.test(variable.datatype)) {
                datatype = "float "
            }
            else {
                datatype = `${variable.datatype} `;
            }

            let variableName = `${datatype}${variable.name}`;

            if (variable.dimensions.length > 0) {
                let dimensionNames = [];
                for (let dimension of variable.dimensions) {
                    dimensionNames.push(dimension.name)
                }
                variableName = `${variableName}(${dimensionNames.join(", ")})`
            }

            if (Object.keys(variable.attributes).includes("units")) {
                variableName = `${variableName} => ${variable.attributes['units']}`;
            }
            else if (Object.keys(variable.attributes).includes("unit")) {
                variableName = `${variableName} => ${variable.attributes["unit"]}`
            }

            variableHeader.textContent = variableName;
            accordion.appendChild(variableHeader);

            /**
             *
             * @type {HTMLDivElement}
             */
            let variableContents = document.createElement("div");
            variableContents.id = `${variableID}-contents`;

            const toolbar = document.createElement("div");
            toolbar.id = `${variableID}-toolbar`;
            const toolbarClassNames = [
                "pview-toolbar",
                "pview-variable-toolbar"
            ];

            toolbar.className = toolbarClassNames.join(" ");

            /**
             *
             * @type {HTMLButtonElement}
             */
            let plotButton = document.createElement("button")
            plotButton.id = `plot-${variableID}`
            plotButton.innerText = "Plot";
            plotButton.className = [
                'pview-button',
                'pview-plot-button'
            ].join(" ");

            toolbar.appendChild(plotButton);

            variableContents.appendChild(toolbar);

            variableContents.appendChild(
                this.#renderAttributesTable(variable.attributes, notGlobal, variableID)
            );

            if (variable.examples.length > 0) {
                /**
                 * @type {HTMLFieldSetElement}
                 */
                const exampleContainer = createFieldSet(
                    `${variableID}-examples`,
                    "Example Values",
                    "Example Values"
                );
                let exampleList = createSimpleList(
                    `${variableID}-example-list`,
                    "Examples",
                    variable.examples
                );

                exampleContainer.appendChild(exampleList)
                variableContents.appendChild(exampleContainer);
            }

            accordion.appendChild(variableContents);
        }

        return accordion;
    }

    /**
     *
     * @param attributes {{string: any}}
     * @param isGlobal {boolean}
     * @param variableID {string|undefined|null}
     * @returns {HTMLTableElement|HTMLParagraphElement}
     */
    #renderAttributesTable = (attributes, isGlobal, variableID) => {
        if (isGlobal === null || isGlobal === undefined) {
            isGlobal = false;
        }

        const scope = isGlobal ? "global" : "variable";

        if (!variableID && !isGlobal) {
            throw new Error(
                "An attributes table cannot be rendered - a table is marked as variable level yet has not variable ID"
            );
        }
        else if (!variableID) {
            variableID = "global";
        }

        const variableName = isGlobal ? null : variableID.replace(`${this.data_id}-`, "")

        if (attributes === null || attributes === undefined || Object.keys(attributes).length === 0) {
            /**
             *
             * @type {HTMLParagraphElement}
             */
            const lackOfAttributesParagraph = document.createElement("p");

            if (isGlobal) {
                lackOfAttributesParagraph.innerText = `Dataset ${this.data_id} has no global attributes`;
            }
            else {
                lackOfAttributesParagraph.innerText = `The ${variableName} variable has no attributes`;
            }

            return lackOfAttributesParagraph;
        }

        const tableID = variableID ? `${variableID}-attributes` : `${scope}-attributes`;

        return createTable(
            tableID,
            `${scope}-attributes`,
            attributes
        );
    }
}

