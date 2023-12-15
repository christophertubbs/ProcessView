import {getColumnNames} from "./utility.js";

/**
 * Create a common type of div
 * @param elementID {string} The id of the element
 * @param name {string} The name associated with the div
 * @param attributes {{}?} An optional set of attributes
 * @return HTMLDivElement
 */
export function createDiv(elementID, name, attributes) {
    const div = document.createElement("div")
    div.id = elementID;

    const cleanName = name.trim().replace(" ", "_");

    const containerCSSClasses = [
        `pview-container`,
        `pview-${cleanName}`
    ]

    div.className = containerCSSClasses.join(" ");

    for (let [key, value] of Object.entries(attributes ?? {})) {
        div.attributes[key] = value;
    }

    return div
}

/**
 * Create a common type of fieldset
 * @param elementID {string} The ID for the fieldset
 * @param name {string} The name for the data within the fieldset
 * @param title {string} The name in the legend for the fieldset
 */
export function createFieldSet(elementID, name, title) {
    const cleanID = elementID.replace(" ", "_");
    const cleanName = name.replace(" ", "_");

    /**
     *
     * @type {HTMLFieldSetElement}
     */
    const fieldSet = document.createElement("fieldset")
    fieldSet.dataset['name'] = name;
    fieldSet.id = cleanID;

    const fieldsetCSSClasses = [
        "pview-fields",
        `pview-${cleanName}-fields`
    ];

    fieldSet.className = fieldsetCSSClasses.join(" ");

    /**
     * @type {HTMLLegendElement}
     */
    const legend = document.createElement("legend");
    legend.id = `${cleanID}-legend`;

    const legendCSSClasses = [
        "pview-legend",
        `pview-${cleanName}-legend`
    ]

    legend.className = legendCSSClasses.join(" ");
    legend.innerText = title;

    fieldSet.appendChild(legend);

    return fieldSet;
}

/**
 * Creates a common type of table
 *
 * @param elementID {string} The ID for the table
 * @param name {string} The name for the type of data
 * @param rows {({}|Object)[]|Object|{any: any}} A name-indexible mapping of values
 * @param columns {string[]?} The names of the columns to insert into rows
 * @param titles {{string: string}?} An optional mapping from column names to names that will be in the header
 * @param includeHeader {boolean?} Include the header row
 *
 * @returns {HTMLTableElement}
 */
export function createTable(elementID, name, rows, columns, titles, includeHeader) {
    const cleanID = elementID.trim().replace(" ", "_");
    const cleanName = name.trim().replace(" ", "_");

    let tableType = 'pview-standard-table';

    if (!Array.isArray(rows)) {
        tableType = 'pview-key-value-table'
        columns = ['key', 'value'];

        if (includeHeader === null || includeHeader === undefined) {
            includeHeader = false;
        }

        rows = Object.entries(rows)
            .filter(
                ([key, value]) => typeof value !== 'function'
            )
            .map(
                ([key, value]) => {
                    return {"key": key, "value": value}
                }
            )
    }

    if (columns === null || columns === undefined || columns.length === 0) {
        columns = getColumnNames(rows)
    }

    if (includeHeader === null || includeHeader === undefined) {
        includeHeader = true;
    }

    /**
     *
     * @type {HTMLTableElement}
     */
    const table = document.createElement("table");
    table.id = cleanID

    const tableCSS = [
        "pview-table",
        `pview-${cleanName}-table`,
        tableType
    ]

    table.className = tableCSS.join(" ");

    if (includeHeader) {
        /**
         *
         * @type {HTMLTableSectionElement}
         */
        const head = document.createElement("thead");
        const headCSS = [
            "pview-table-head",
            `pview-${cleanName}-table-head`
        ]

        head.className = headCSS.join(" ");

        /**
         *
         * @type {HTMLTableRowElement}
         */
        const headerRow = document.createElement("tr");
        const headerRowCSS = [
            "pview-table-row",
            "pview-header-row",
            `pview-${cleanName}-header-row`
        ]

        headerRow.className = headerRowCSS.join(" ");
        headerRow.id = `${elementID}-header`

        for (let column of columns) {
            /**
             *
             * @type {HTMLTableCellElement}
             */
            let headerCell = document.createElement("th");
            headerCell.dataset['column'] = column;

            if (titles && Object.keys(titles).includes(column)) {
                headerCell.innerText = titles[column];
            } else {
                headerCell.innerText = column;
            }

            headerRow.appendChild(headerCell);
        }

        head.appendChild(headerRow)

        table.appendChild(head);
    }

    const body = document.createElement("tbody");
    const bodyCSS = [
        'pview-table-body',
        `pview-${cleanName}-table-body`
    ]
    body.className = bodyCSS.join(" ");

    const baseRowCSS = [
        "pview-table-row",
        `pview-${cleanName}-row`
    ]

    const baseCellCSS = [
        "pview-table-cell"
    ]

    let rowID = 0;
    for (let rowData of rows) {
        /**
         *
         * @type {HTMLTableRowElement}
         */
        let row = document.createElement("tr")
        let specificRowCSS = [
            `pview-${rowID % 2 === 0 ? "odd" : "even"}-table-row`,
        ]
        row.className = (baseRowCSS.concat(specificRowCSS)).join(" ");
        row.dataset['row_number'] = rowID;
        row.id = `${cleanID}-${rowID}`;

        for (let column of columns) {
            let cleanColumnName = column.trim().replace(" ", "_");

            /**
             *
             * @type {HTMLTableCellElement}
             */
            let cell = document.createElement("td")

            let specificCellCSS = [
                `pview-${cleanColumnName}-table-cell`
            ]
            cell.className = (baseCellCSS.concat(specificCellCSS)).join(" ")
            cell.dataset['column'] = column;

            let cellName = titles && Object.keys(titles).includes(column) ? titles[column] : column;

            if (Object.keys(rowData).includes(column)) {
                let value = rowData[column];

                if (value !== null && value !== undefined && typeof value === 'string' && value.length > 100) {
                    value = value.replaceAll(",", ', ');
                }
                cell.innerText = value;
                cell.title = `${cellName}: ${value}`

                row.attributes[`data-${column}`] = value;
            }
            else {
                cell.title = `${cellName}: null`
                row.attributes[`data-${column}`] = null;
            }

            row.appendChild(cell);
        }

        body.appendChild(row)
        rowID++;
    }

    table.appendChild(body)


    return table;
}

/**
 *
 * @param elementID {string} The ID for the element
 * @param name {string}
 * @param entries {any[]}
 * @param ordered {boolean?}
 * @returns {HTMLUListElement|HTMLOListElement}
 */
export function createSimpleList(elementID, name, entries, ordered) {
    if (ordered === null || ordered === undefined) {
        ordered = false;
    }

    const listType = ordered ? "ol" : "ul";

    const cleanID = elementID.trim().replace(" ", "_")
    const cleanName = name.trim().replace(" ", "_");

    /**
     *
     * @type {HTMLUListElement|HTMLOListElement}
     */
    const list = document.createElement(listType)
    list.id = cleanID;

    const listCSS = [
        'pview-list',
        `pview-${cleanName}-list`,
        `pview-${ordered ? 'ordered' : 'unordered'}-list`
    ]

    let listItemID = 0;

    const baseListItemCSS = [
        'pview-list-item',
        `pview-${cleanName}-list-item`
    ]

    for (let item of entries) {
        /**
         *
         * @type {HTMLLIElement}
         */
        let listItem = document.createElement("li");
        listItem.id = `${list.id}-${listItemID}`;
        listItem.innerText = item;
        listItem.dataset['value'] = item;
        listItem.dataset['index'] = listItemID;

        let specificListItemCSS = [];
        listItem.className = (baseListItemCSS.concat(specificListItemCSS)).join(" ");

        list.appendChild(listItem);
        listItemID++;
    }

    return list;
}