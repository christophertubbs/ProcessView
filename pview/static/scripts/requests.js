export class Request {
    send_handlers;

    constructor () {
        this.send_handlers = [];
    }

    getRawPayload = () => {
        throw new Error("getRawPayload was not implemented for this request");
    }

    getOperation = () => {
        throw new Error("getOperation was not implemented for this request");
    }

    sent = () => {
        for (let handler of this.send_handlers) {
            handler();
        }
    }

    onSend = (handler) => {
        this.send_handlers.push(handler);
    };
}

export class FileSelectionRequest extends Request {
    operation = "load"
    path
    row_count
    constructor ({path, row_count}) {
        super();

        this.path = path
        if (row_count !== null && row_count !== undefined) {
            this.row_count = row_count
        }
        else {
            this.row_count = 20;
        }
    }

    getRawPayload = () => {
        return {
            "operation": this.operation,
            "path": this.path,
            "row_count": this.row_count
        };
    }

    getOperation = () => {
        return "load"
    }
}

export class Filter {
    field
    operator
    value

    constructor ({field, operator, value}) {
        this.field = field;
        this.operator = operator;
        this.value = value;
    }

    getPayload = () => {
        return {
            field: this.field,
            operator: this.operator,
            value: this.value
        }
    }
}

export class DataRequest extends Request {
    /**
     * @member {string}
     */
    data_id
    /**
     * @member {string[]|null|undefined}
     */
    columns
    /**
     * @member {number|null}
     */
    page_number
    /**
     * @member {number|null}
     */
    row_count
    /**
     * @member {Filter[]|null|undefined}
     */
    filters

    constructor ({data_id, columns, page_number, row_count, filters}) {
        super()

        this.data_id = data_id;
        this.columns = columns;
        this.page_number = page_number
        this.row_count = row_count
        this.filters = filters
    }

    getRawPayload = () => {
        const payload = {
            operation: this.getOperation(),
            data_id: this.data_id
        }

        if (this.columns !== null && this.columns !== undefined && this.columns.length > 0) {
            payload['columns'] = this.columns;
        }

        if (this.row_count !== null && this.row_count !== undefined && this.row_count > 0) {
            payload['row_count'] = this.row_count;
        }

        if (this.filters !== null && this.filters !== undefined && this.filters.length > 0) {
            payload['filters'] = [];

            for (let filter of this.filters) {
                payload['filters'].push(filter.getPayload());
            }
        }

        if (this.page_number !== null && this.page_number !== undefined && this.page_number >= 0) {
            payload['page_number'] = this.page_number
        }

        return payload;
    }
}

export class FilterRequest extends DataRequest {
    getOperation = () => {
        return "filter";
    }
}

export class PageRequest extends DataRequest {
    getOperation = () => {
        return "page"
    }
}

if (!Object.hasOwn(window, "pview")) {
    console.log("Creating a new pview namespace");
    window.pview = {};
}

window.pview.FilterRequest = FilterRequest;
window.pview.PageRequest = PageRequest;
window.pview.DataRequest = DataRequest;
window.pview.Filter = Filter;
window.pview.FileSelectionRequest = FileSelectionRequest;