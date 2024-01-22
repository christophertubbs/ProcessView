/**
 * Get the names of all member fields in a list of objects
 *
 * @param objects {({}|Object)[]|{}|Object} A list of objects that have common fields
 * @param all {boolean?} Retrieve every field name, even if they aren't shared by all members
 * @returns {string[]}
 */
export function getColumnNames(objects, all) {
    if (!Array.isArray(objects)) {
        return Object.entries(objects)
            .filter(
                ([key, value]) => typeof value !== 'function'
            )
            .map(
                ([key, value]) => key
            )
    }

    if (all === null || all === undefined) {
        all = false;
    }

    let commonFields = [];

    for (let objectIndex = 0; objectIndex < objects.length; objectIndex++) {
        let obj = objects[objectIndex];

        if (objectIndex === 0 || all) {
            for (let [key, value] of Object.entries(obj)) {
                if (!['function', 'object'].includes(typeof value)) {
                    commonFields.push(key);
                }
            }
        }
        else if (!all) {
            let keysToRemove = [];
            let thisObjectsKeys = Object.keys(obj);

            for (let key of commonFields) {
                if (!thisObjectsKeys.includes(key)) {
                    keysToRemove.push(key);
                }
            }

            commonFields = commonFields.filter(
                (value) => !keysToRemove.includes(value)
            )
        }
    }

    return commonFields;
}

export function closeAllDialogs() {
    $(".pview-dialog").dialog("close");
}

export function openDialog(selector) {
    closeAllDialogs();
    $(selector).dialog("open");
}

export async function request_json(input, init) {
    const raw_response = await fetch(input, init).then(response => response.text());
    let response;
    try {
        response = JSON.parse(raw_response);
    } catch (e) {
        response = {
            text: raw_response,
            error: e.toString()
        }
    }

    return response;
}

export const MEMORY_FACTORS = Object.freeze({
    B: 1000**0,
    KB: 1000**1,
    MB: 1000**2,
    GB: 1000**3
});

export function describeNumber(amount) {
    if (typeof amount !== 'number') {
        return "??";
    }
    return amount.toLocaleString()
}

export function describeMemory(amount, unit) {
    let current_amount = undefined;
    let current_unit = null;

    if (["null", "undefined"].includes(typeof unit)) {
        unit = MEMORY_FACTORS.B;
    }

    amount = amount * unit;

    for (let [memory_unit, bytes_in_memory_unit] of Object.entries(MEMORY_FACTORS)) {
        if (typeof current_unit !== 'undefined' && current_amount < 1000) {
            break;
        }

        current_amount = amount / bytes_in_memory_unit;
        current_unit = memory_unit;
    }

    let described_amount = describeNumber(current_amount);
    return `${described_amount}${current_unit}`;
}