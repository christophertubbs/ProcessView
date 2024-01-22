export class BaseMessage {
    #messageID;
    #operation;

    static from(object) {
        return new this(object.message_id, object.operation);
    }

    constructor(messageID, operation) {
        this.#messageID = messageID;
        this.#operation = operation;
    }

    get operation() {
        return this.#operation;
    }

    get messageID() {
        return this.#messageID;
    }
}