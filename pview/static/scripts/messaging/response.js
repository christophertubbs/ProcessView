import {ProcessInformation} from "../process.js";

class MappedField {
    #fieldName;
    #objectName;
    #transformation;
    #required;
    #defaultValue;

    constructor(fieldName, objectName, transformation, required, defaultValue) {
        if ([undefined, null].includes(transformation)) {
            transformation = value => value;
        }

        if ([undefined, null].includes(required)) {
            required = false;
        }

        this.#fieldName = fieldName;
        this.#objectName = objectName;
        this.#transformation = transformation;
        this.#required = required;
        this.#defaultValue = defaultValue;
    }

    get defaultValue() {
        return this.#defaultValue;
    }

    get fieldName() {
        return this.#fieldName
    }

    get objectName() {
        return this.#objectName;
    }

    get transformation() {
        return this.#transformation;
    }

    get required() {
        return this.#required;
    }

    transform = (object) => {
        if ([undefined, null].includes(object)) {
            throw new Error("Cannot transform a non-existent object");
        }

        const hasData = Object.hasOwn(object, "data");
        const hasField = Object.hasOwn(object, this.#objectName);
        const dataHasField = typeof hasData !== 'undefined' && Object.hasOwn(object.data, this.#objectName);

        if (!hasField && !dataHasField) {
            if (this.#required) {
                throw new Error(`Invalid object - the ${this.#objectName} key is required, but missing`);
            }
        }
        const valueToTransform = !hasField && dataHasField ? object.data[this.#objectName] : object[this.#objectName];

        return this.#transformation(valueToTransform);
    }

    apply = (target, source) => {
        if (!this.isValid(source)) {
            throw new Error(`Cannot create an instance of an object - the field '${this.#objectName}' is missing`);
        }
        const newValue = this.transform(source);

        if (typeof newValue !== 'undefined' || this.#required) {
            target[this.#fieldName] = newValue;
        }

        return target;
    }

    isValid = (source) => {
        return Object.hasOwn(source, this.#objectName) ||
            Object.hasOwn(source, 'data') && Object.hasOwn(source.data, this.#objectName) ||
            !this.#required;
    }

    score = (source) => {
        if (Object.hasOwn(source, this.#objectName)) {
            return 2;
        } else if (Object.hasOwn(source, 'data') && Object.hasOwn(source.data, this.#objectName)) {
            return 1;
        }

        return -999;
    }
}

export class Response {
    /**
     *
     * @type {Set<Class<Response>>}
     */
    static derivedClasses = new Set();

    /**
     * @returns {MappedField[]}
     */
    static getFieldMapping() {
        return [
            new MappedField("messageID", "message_id", null, false, null),
            new MappedField("operation", "operation", null, true)
        ]
    }

    static matchScore(source) {
        const mapping = this.getFieldMapping();
        return mapping.reduce(
            (previousScore, mapping) => previousScore + mapping.score(source),
            0
        );
    }

    #messageID;
    #operation;

    get messageID () {
        return this.#messageID;
    }

    get operation () {
        return this.#operation;
    }

    constructor(response) {
        const fieldMapping = this.constructor.getFieldMapping();
        fieldMapping.forEach(field => field.apply(this, response));

        for (let mapping of fieldMapping) {
            mapping.apply(this, response);
        }
    }
}

export class ErrorResponse extends Response {
    static deriveRegistration = Response.derivedClasses.add(this);
    static getFieldMapping() {
        const mapping = super.getFieldMapping()

        mapping.push(...[
            new MappedField("errorMessage", "error_message", null, true),
            new MappedField("code", "code", null, true),
            new MappedField("messageType", "message_type", null, true)
        ])
        return mapping;
    }

    errorMessage;
    code;
    messageType;
}

export class ProcessErrorResponse extends ErrorResponse {
    static deriveRegistration = Response.derivedClasses.add(this);
    static getFieldMapping() {
        const mapping = super.getFieldMapping()

        mapping.push(...[
            new MappedField(
                "process",
                "process_data",
                    value => new ProcessInformation(value),
                true
            )
        ])

        return mapping;
    }

    process;
}

export class ProcessInformationResponse extends Response {
    static deriveRegistration = Response.derivedClasses.add(this);
    static getFieldMapping() {
        const mapping = super.getFieldMapping()

        mapping.push(...[
            new MappedField(
                "process",
                "process",
                    value => new ProcessInformation(value),
                true
            )
        ])

        return mapping;
    }
    process;
}

export class KillResponse extends ProcessInformationResponse {
    static deriveRegistration = Response.derivedClasses.add(this);
    static getFieldMapping() {
        const mapping = super.getFieldMapping()

        mapping.push(...[
            new MappedField(
                "message",
                "message",
                    null,
                true
            ),
            new MappedField("success", "success", null, false, true)
        ])

        return mapping;
    }

    message;
    success;
}

export function deserializeResponse(response) {
    /**
     *
     * @type {Class<Response>|null}
     */
    let highestRatedMatch = null;
    let highestDegree = 0;

    for (let derivedClass of Response.derivedClasses) {
        let degreeOfMatch = derivedClass.matchScore(response);

        if (degreeOfMatch > 0) {
            if (highestRatedMatch === null || degreeOfMatch > highestDegree) {
                highestRatedMatch = derivedClass;
                highestDegree = degreeOfMatch;
            }
        }
    }

    if (highestRatedMatch === null) {
        return response;
    } else {
        return new highestRatedMatch(response);
    }
}