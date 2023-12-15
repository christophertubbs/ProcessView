import {Request} from "./requests.js"

function sleep(ms, message) {
    if (ms === null || ms === undefined) {
        ms = 500;
    }
    if (message === null || message === undefined) {
        message = `Waiting ${ms}ms...`;
    }

    console.log(message);
    return new Promise(resolve => setTimeout(resolve, ms));
}

const ReadyState = Object.freeze({
    Connecting: 0,
    Open: 1,
    Closing: 2,
    Closed: 3
})

export class PViewClient {
    /**
     *
     * @type {WebSocket|null}
     */
    #socket = null;
    #handlers = {};
    #id = null;
    #payloadTypes = {}
    #currentPath = null;
    
    constructor () {
        this.#id = this.#generateID();
    }
    
    addHandler = (operation, action) => {
        if (!Object.hasOwn(this.#handlers, operation)) {
            this.#handlers[operation] = [];
        }
        
        this.#handlers[operation].push(action);
    }

    getID = () => {
        return this.#id;
    }
    
    #handle = (operation, payload) => {
        if (Object.hasOwn(this.#payloadTypes, operation)) {
            payload = new this.#payloadTypes[operation](payload);
        }

        if (Object.hasOwn(this.#handlers, operation)) {
            this.#handlers[operation].forEach(action => action(payload));
        }
    }

    #generateID = (length) => {
        if (length === null || length === undefined) {
            length = 8;
        }

        const characterSet = "0123456789ABCDEF";
        function getRandomCharacter() {
            const characterIndex = Math.floor(Math.random() * characterSet.length);
            return characterSet[characterIndex];
        }

        let generatedID = "";

        for (let counter = 0; counter < length; counter++) {
            generatedID += getRandomCharacter();
        }

        return generatedID;
    }

    /**
     *
     * @param payload {Request|object}
     */
    send = async (payload) => {
        if (this.#currentPath === null || this.#currentPath === undefined) {
            throw new Error(`Cannot send message through client '${this.getID()}' - please connect first.`);
        }

        let rawPayload;
        if (payload instanceof Request) {
            rawPayload = payload.getRawPayload();
        }
        else {
            rawPayload = payload;
        }

        if (!Object.hasOwn(rawPayload, "message_id")) {
            rawPayload['message_id'] = this.#generateID()
        }

        const payloadText = JSON.stringify(rawPayload, null, 4)

        if (!this.isConnected()) {
            await this.connect(this.#currentPath)
        }

        while (this.#socket.readyState === ReadyState.Connecting) {
            await sleep(1000);
        }

        this.#socket.send(payloadText);

        if (payload instanceof Request) {
            payload.sent();
        }
    }
    
    sendRawMessage = (message) => {
        const payload = {
            "message_id": this.#generateID(),
            "message": message
        }
        const requestData = JSON.stringify(payload, null, 4);
        this.#socket.send(requestData);
    }
    
    #build_websocket_url = (path) => {
        const location = window.location;
        return `ws://${location.host}/${path}`;
    }

    connect = async (path) => {
        this.#socket?.close()
        
        const url = this.#build_websocket_url(path);
        this.#socket = new WebSocket(url);
        this.#socket.onmessage = this.#handleMessage;
        this.#socket.onopen = this.#handleOpen;
        this.#socket.onclose = this.#handleClose;
        this.#socket.onerror = this.#handleError;

        while (this.#socket.readyState === ReadyState.Connecting) {
            await sleep(1000);
        }

        this.#currentPath = path;
    }

    /**
     *
     * @param event {MessageEvent}
     */
    #handleMessage = (event) => {
        const payload = event.data;
        console.log(payload);
        let deserializedPayload
        try {
            deserializedPayload = JSON.parse(payload);
        } catch (e) {
            console.log("Could not deserialize message from server");
            console.error(e);
            return;
        }

        let operation;
        try {
            operation = deserializedPayload.operation;
        } catch (e) {
            console.error("Could not find the operation on the deserialized payload");
            console.error(e);
            return
        }

        try {
            this.#handle(operation, deserializedPayload);
        } catch (e) {
            console.error("An error occurred while trying to handle an event")
            console.error(e);
        }
    }

    #handleError = (event) => {
        this.#handle("error", event.data ?? {})
    }

    #handleOpen = (event) => {
        console.log("Connection opened");
        this.#handle("open", event.data ?? {});
    }

    #handleClose = (event) => {
        console.log("Connection closed");
        this.#socket = null;
        this.#handle("closed", event.data ?? {});
    }

    registerPayloadType = (operation, payloadType) => {
        this.#payloadTypes[operation] = payloadType;
    }

    isConnected = () => {
        if (this.#socket === null || this.#socket === undefined) {
            return false;
        }

        return this.#socket.readyState === ReadyState.Open;
    }
}

if (!Object.hasOwn(window, "pview")) {
    console.log("Creating a new pview namespace from client.js");
    window.pview = {};
}

window.pview.PViewClient = PViewClient;