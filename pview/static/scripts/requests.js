export class Request {
    #sendHandlers;

    #responseHandlers;

    #errorHandlers;

    constructor () {
        this.#sendHandlers = [];
        this.#responseHandlers = [];
        this.#errorHandlers = [];
    }

    getRawPayload = () => {
        throw new Error("getRawPayload was not implemented for this request");
    }

    getOperation = () => {
        throw new Error("getOperation was not implemented for this request");
    }

    async sent() {
        for (let handler of this.#sendHandlers) {
            let result = handler();

            while (result instanceof Promise) {
                result = await result;
            }
        }
    }

    async handleResponse(response) {
        for (let handler of this.#responseHandlers) {
            let result = handler(response);

            while (result instanceof Promise) {
                result = await result;
            }
        }
    }

    async handlerError(error) {
        for (let handler of this.#errorHandlers) {
            let result = handler(error);

            while (result instanceof Promise) {
                result = await result;
            }
        }
    }

    async send(address, options) {
        const promisedResponse = fetch(address, options);
        await this.sent();
        const response = await promisedResponse.then(response => response.json())
    }

    onSend = (handler) => {
        this.#sendHandlers.push(handler);
    };

    onResponse = (handler) => {
        this.#responseHandlers.push(handler);
    }

    onError = (handler) => {
        this.#errorHandlers.push(handler);
    }
}

export class ProcessRequest extends Request {
    #processID;

    constructor(processID) {
        super()
    }
}