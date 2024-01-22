import {BaseMessage} from "./base.js";

export class ErrorResponse extends BaseMessage {
    #messageType;
    #errorMessage;
    #code;

    static from(object) {
        return new this(
            object.message_id,
            object.operation,
            object.message_type,
            object.error_message,
            object.code
        );
    }

    constructor(messageID, operation, messageType, errorMessage, code) {
        super(messageID, operation);
        this.#messageType = messageType;
        this.#errorMessage = errorMessage;
        this.#code = code;
    }

    get messageType() {
        return this.#messageType;
    }

    get errorMessage() {
        return this.#errorMessage;
    }

    get code() {
        return this.#code;
    }
}

export class ProcessErrorResponse extends ErrorResponse {
    #processData;

    static from(object) {
        return new this(
            object.message_id,
            object.operation,
            object.message_type,
            object.error_message,
            object.code,
            object.processData
        )
    }

    constructor(messageID, operation, messageType, errorMessage, code, processData) {
        super(messageID, operation, messageType, errorMessage, code);
        this.#processData = processData;
    }

    get processData() {
        return this.#processData;
    }
}