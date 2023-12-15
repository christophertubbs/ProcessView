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