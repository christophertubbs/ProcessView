/**
 * @typedef {any} Value
 */

export class EventValue {
    static create(initialValue, ...onUpdate) {
        const newValue = new EventValue(initialValue, ...onUpdate);
        return [newValue.get, newValue.set, newValue.onUpdate];
    }

    /**
     * @type {Value}
     */
    #value
    /**
     *
     * @type {((oldValue: Value, newValue: Value) => any)[]}
     */
    #handlers = []

    constructor(initialValue, ...handler) {
        this.#value = initialValue;

        if (handler !== null) {
            this.#handlers.push(...handler);
        }
    }

    /**
     *
     * @param handler {(oldValue: Value, newValue: Value) => any}
     */
    onUpdate = (handler) => {
        this.#handlers.push(handler);
    }

    #handleUpdate = (oldValue, newValue) => {
        for (let handler of this.#handlers) {
            try {
                handler(oldValue, newValue);
            }
            catch (e) {
                console.error(e);
            }
        }
    }

    /**
     *
     * @returns {Value}
     */
    get = () => {
        return this.#value;
    }

    updateValue = (updatedValue) => {
        const oldValue = this.#value;
        this.#value = updatedValue;
        this.#handleUpdate(oldValue, updatedValue);
    }

    /**
     *
     * @param updatedValue {Value}
     */
    set = (updatedValue) => {
        this.updateValue(updatedValue);
    }

    valueOf() {
        return this.get()
    }

    toString() {
        return this.get()?.toString();
    }
}

export class BooleanValue {
    static create(initialValue, ...handler) {
        if (handler === null || handler.length === 0) {
            throw new Error("Update handlers must be passed when creating a new BooleanValue");
        }

        const newValue = new EventValue(initialValue, ...handler);
        return [newValue.get, newValue.set];
    }

    static get True() {
        return new BooleanValue(true);
    };

    static get False() {
        return new BooleanValue(false)
    };

    /**
     * @type {Boolean}
     */
    #value
    /**
     *
     * @type {((oldValue: boolean, newValue: boolean) => any)[]}
     */
    #handlers = []

    constructor(initialValue, ...handler) {
        this.#value = initialValue ?? false;

        if (handler !== null) {
            this.#handlers = this.#handlers.concat(...handler);
        }
    }

    /**
     *
     * @param handler {(oldValue: boolean, newValue: boolean) => any}
     */
    onUpdate = (handler) => {
        this.#handlers.push(handler);
    }

    #handleUpdate = (oldValue, newValue) => {
        for (let handler of this.#handlers) {
            try {
                handler(oldValue, newValue);
            }
            catch (e) {
                console.error(e);
            }
        }
    }

    /**
     *
     * @returns {boolean}
     */
    get = () => {
        return this.#value;
    }

    #updateValue = (updatedValue) => {
        const oldValue = this.#value;
        this.#value = updatedValue;
        this.#handleUpdate(oldValue, updatedValue);
    }

    get toggle() {
        this.#updateValue(!this.#value);
        return this;
    }

    get toTrue() {
        this.#updateValue(true);
        return this;
    }

    get toFalse() {
        this.#updateValue(false);
        return this;
    }

    get isTrue() {
        return this.#value === true;
    }

    get isFalse() {
        return this.#value === false;
    }

    valueOf() {
        return this.get()
    }

    toString() {
        return this.get()?.toString();
    }
}

export const ListValueAction = Object.freeze({
    DELETE: "delete",
    ADD: "add",
    MODIFY: "modify"
});

/**
 * Event data that will be passed when a ListValue is mutated
 */
export class ListValueEvent {
    #action
    #modifiedValue
    #data

    constructor (data, action, modifiedValue) {
        this.#action = action;
        this.#data = data;
        this.#modifiedValue = modifiedValue;
    }

    get action() {
        return this.#action;
    }

    get data() {
        return this.#data;
    }

    get modifiedValue() {
        return this.#modifiedValue;
    }
}

export class ListValue {

    /**
     * @type {Array}
     */
    #values = []

    /**
     *
     * @type {((event: ListValueEvent) => any)[]}
     */
    #handlers = []

    get data() {
        return this.#values;
    }

    /**
     *
     * @param initialValue {Array|undefined}
     * @param handlers{(event: ListValueEvent) => any}
     */
    constructor (initialValue, ...handlers) {
        if (Array.isArray(initialValue)) {
            this.#values.push(...initialValue);
        }
        else {
            this.#values.push(initialValue);
        }

        let handlerIndex = 0;
        for (; handlerIndex < handlers.length; handlerIndex++) {
            let handler = handlers[handlerIndex];

            if (typeof handler === 'function') {
                break;
            }

            this.#values.push(handler);
        }

        if (handlers.length > 0) {
            this.addHandlers(...handlers.splice(handlerIndex))
        }

        // Return a Proxy in order to allow list indexing
        return new Proxy(
            this,
            {
                get(target, name) {
                    if (name in target) {
                        return target[name];
                    }

                    const values = target.data;

                    if (typeof name !== 'number') {
                        throw new TypeError(`ListValues may only be indexed via numbers`)
                    }

                    // Support negative indexing
                    if (name < 0) {
                        name = values.length + name;
                    }

                    return values[name];
                },
                set(target, name, value) {
                    if (name in target) {
                        target[name] = value;
                    }
                    else {
                        if (typeof name !== 'number') {
                            throw new TypeError(`ListValues may only be indexed via numbers`)
                        }

                        const values = target.data;

                        // Support negative indexing
                        if (name < 0) {
                            name = values.length + name;
                        }

                        values[name] = value;
                    }
                    return true;
                }
            }
        );
    }

    addHandlers = (...handlers) => {
        if (handlers.length === 0) {
            return this;
        }

        const nonHandlers = handlers.filter((handler) => typeof handler !== 'function');

        if (nonHandlers.length > 0) {
            throw new Error(`Cannot add handlers - ${nonHandlers.join(", ")} isn't/aren't functions`)
        }

        this.#handlers.push(...handlers);
        return this;
    }

    #fire = (action, modifiedValues) => {
        const eventData = new ListValueEvent(
            this,
            action,
            modifiedValues
        )
        this.#handleUpdate(eventData);
    }

    #thisWasModified = () => {
        this.#fire(ListValueAction.MODIFY, this.#values);
    }

    #valueWasAdded = (addedValues) => {
        this.#fire(ListValueAction.ADD, addedValues);
    }

    #valueWasRemoved = (removedValues) => {
        this.#fire(ListValueAction.DELETE, removedValues);
    }

    get values() {
        return this.#values;
    }

    /**
     *
     * @param event {ListValueEvent}
     */
    #handleUpdate = (event) => {
        for (let handler of this.#handlers) {
            try {
                handler(event);
            }
            catch (e) {
                console.error(e);
            }
        }
    }

    get length() {
        return this.#values.length;
    }

    concat = (other) => {
        return this.#values.concat(other);
    }

    at = (index) => {
        return this.#values.at(index);
    }

    copyWithin = (target, start, end) => {
        this.#values.copyWithin(target, start, end);
        this.#thisWasModified()
        return this;
    }

    push = (...other) => {
        const amountChanged = this.#values.push(...other);
        this.#valueWasAdded(other.length === 1 ? other[0] : other)
        return amountChanged;
    }

    pop = () => {
        const modifiedValue = this.#values.pop();
        this.#valueWasRemoved(modifiedValue)
        return modifiedValue;
    }

    entries = () => {
        return this.#values.entries();
    }

    every = (predicate, thisArg) => {
        return this.#values.every(predicate, thisArg);
    }

    fill = (value, start, end) => {
        this.#values.fill(value, start, end);
        this.#thisWasModified()
        return this;
    }

    find = (predicate, thisArg) => {
        return this.#values.find(predicate, thisArg);
    }

    exists = (predicate, thisArg) => {
        const matchingValue = this.find(predicate, thisArg);
        return matchingValue !== undefined;
    }

    findIndex = (predicate, thisArg) => {
        return this.#values.findIndex(predicate, thisArg)
    }

    findLast = (predicate, thisArg) => {
        return this.#values.findLast(predicate, thisArg);
    }

    findLastIndex = (predicate, thisArg) => {
        return this.#values.findLastIndex(predicate, thisArg);
    }

    flat = (depth) => {
        return new ListValue(this.#values.flat(depth), ...this.#handlers);
    }

    flattenInPlace = (depth) => {
        this.#values = this.#values.flat(depth);
        this.#thisWasModified();
        return this;
    }

    flatMap = (callbackFn, thisArg) => {
        return new ListValue(this.#values.flatMap(callbackFn, thisArg), ...this.#handlers);
    }

    flatMapInPlace = (callbackFn, thisArg) => {
        this.#values = this.#values.flatMap(callbackFn, thisArg);
        this.#thisWasModified();
        return this;
    }

    forEach = (callbackFn, thisArg) => {
        this.#values.forEach(callbackFn, thisArg);
    }

    static from = (arrayLike, mapFn, thisArg) => {
        return new ListValue(Array.from(arrayLike, mapFn, thisArg));
    }

    /**
     *
     * @param arrayLike
     * @param mapFn
     * @param thisArg
     * @returns {Promise}
     */
    static fromAsync = (arrayLike, mapFn, thisArg) => {
        return Array.fromAsync(arrayLike, mapFn, thisArg).then((newArray) => new ListValue(newArray));
    }

    filter = (predicate, thisArg) => {
        return new ListValue(this.#values.filter(predicate, thisArg), ...this.#handlers)
    }

    filterInPlace = (predicate, thisArg) => {
        this.#values = this.#values.filter(predicate, thisArg);
        this.#thisWasModified();
        return this;
    }

    includes = (searchElement, fromIndex) => {
        return this.#values.includes(searchElement, fromIndex);
    }

    indexOf = (searchElement, fromIndex) => {
        return this.#values.indexOf(searchElement, fromIndex);
    }

    static isArray = (value) => {
        return value instanceof ListValue || Array.isArray(value);
    }

    join = (separator) => {
        return this.#values.join(separator);
    }

    keys = () => {
        return this.#values.keys();
    }

    lastIndexOf = (searchElement, fromIndex) => {
        return this.#values.lastIndexOf(searchElement, fromIndex);
    }

    map = (callbackFn, thisArg) => {
        return new ListValue(this.#values.map(callbackFn, thisArg), ...this.#handlers);
    }

    mapInPlace = (callbackFn, thisArg) => {
        this.#values = this.#values.map(callbackFn, thisArg);
        this.#thisWasModified();
        return this;
    }

    static of(...element) {
        return new ListValue(element);
    }

    reduce = (callbackFn, initialValue) => {
        return this.#values.reduce(callbackFn);
    }

    reduceRight = (callbackFn, initialValue) => {
        return this.#values.reduceRight(callbackFn, initialValue);
    }

    values = () => {
        return this.#values.values();
    }

    reverse = () => {
        this.#values.reverse();
        this.#thisWasModified()
        return this;
    }

    shift = () => {
        const removedElement = this.#values.shift();
        this.#valueWasRemoved(removedElement);
        return removedElement;
    }

    sort = (compareFn) => {
        this.#values.sort()
        this.#thisWasModified();
        return this;
    }

    some = (predicate, thisArg) => {
        return this.#values.some(predicate, thisArg);
    }

    slice = (start, end) => {
        return new ListValue(this.#values.slice(start, end), ...this.#handlers);
    }

    splice = (start, deleteCount, ...items) => {
        const splicedData = this.#values.splice(start, deleteCount);
        this.#valueWasRemoved(splicedData);
        return new ListValue(splicedData, ...this.#handlers);
    }

    toLocaleString = (locales, options) => {
        return this.#values.toLocaleString();
    }

    toReversed = () => {
        return new ListValue(this.#values.toReversed(), ...this.#handlers);
    }

    toSorted = (compareFn) => {
        return new ListValue(this.#values.toSorted(), ...this.#handlers);
    }

    toSpliced = (start, deleteCount, ...item) => {
        return new ListValue(this.#values.toSpliced(start, deleteCount, ...item), ...this.#handlers);
    }

    valueOf() {
        return this.#values;
    }

    toString() {
        return this.#values.toString();
    }

    unshift = (...element) => {
        this.#values.unshift(...element);
        this.#valueWasAdded(element);
        return this;
    }

    removeAt = (index) => {
        if (!(index in this.#values)) {
            throw new RangeError(`There is no index of ${index} in this list. A value cannot be removed.`);
        }

        if (index < 0) {
            index = this.#values.length + index;
        }

        const removedValue = this.#values[index];

        if (removedValue === undefined) {
            return this;
        }

        this.#values = this.#values.splice(0, index).concat(this.#values.splice(1));
        this.#valueWasRemoved(removedValue);
        return this;

    }

    isEmpty = () => {
        return this.#values.length === 0;
    }

    remove = (element) => {
        const index = this.findIndex((entry) => entry === element);
        if (index >= 0) {
            this.removeAt(index);
        }
        return this;
    }

    removeBy = (predicate, thisArg) => {
        const elementsToRemove = this.filter(predicate, thisArg);
        elementsToRemove.forEach(this.remove);
        return this;
    }

    with = (index, value) => {
        return new ListValue(this.#values.with(index, value), ...this.#handlers);
    }

    [Symbol.iterator]() {
        let index = 0;

        return {
            next() {
                if (index < this.#values.length) {
                    return {
                        value: this.#values[index],
                        done: false
                    }
                }
                else {
                    return {
                        done: true
                    }
                }
            }
        }
    }

    [Symbol.unscopables] = {
        at: true,
        copyWithin: true,
        entries: true,
        fill: true,
        find: true,
        findIndex: true,
        findLast: true,
        findLastIndex: true,
        flat: true,
        flatMap: true,
        includes: true,
        keys: true,
        toReversed: true,
        toSorted: true,
        toSpliced: true,
        values: true
    }
}

if (!('pview' in window)) {
    if (!Object.hasOwn(window, 'pview')) {
        console.log("Creating a new pview namespace from value.js");
        window.pview = {};
    }
}

pview.EventValue = EventValue;
pview.BooleanValue = BooleanValue;
pview.ListValue = ListValue;
pview.ListValueAction = ListValueAction;
pview.ListValueEvent = ListValueEvent;