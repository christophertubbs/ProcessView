import {describeMemory, describeNumber, MEMORY_FACTORS} from "./utility.js";

export class ProcessInformation {
    get processID() {
        return this.#processID;
    }

    get parentProcessID() {
        return this.#parentProcessID;
    }

    get status() {
        return this.#status;
    }

    get username() {
        return this.#username;
    }

    get command() {
        return this.#command;
    }

    get arguments() {
        return this.#arguments;
    }

    get cpuPercent() {
        return this.#cpuPercent;
    }

    get memoryPercent() {
        return this.#memoryPercent;
    }

    get memoryUsage() {
        return this.#memoryUsage;
    }

    get workingDirectory() {
        return this.#workingDirectory;
    }

    get name() {
        return this.#name;
    }

    get threadCount() {
        return this.#threadCount;
    }

    get fileDescriptors() {
        return this.#fileDescriptors;
    }

    get openFileCount() {
        return this.#openFileCount;
    }

    get startTime() {
        return this.#startTime;
    }

    get canModify() {
        return this.#canModify;
    }
    #processID;
    #parentProcessID;
    #status;
    #username;
    #command;
    #arguments;
    #cpuPercent;
    #memoryPercent;
    #memoryUsage;
    #workingDirectory;
    #name;
    #threadCount;
    #fileDescriptors;
    #openFileCount;
    #startTime;
    #canModify;

    constructor(object) {
        this.#processID = object["process_id"];
        this.#parentProcessID = object["parent_process_id"]
        this.#status = object["status"];
        this.#username = object['username'];
        this.#command = object['command'];
        this.#arguments = object['arguments']
        this.#cpuPercent = object['cpu_percent'];
        this.#memoryPercent = object['memory_percent'];
        this.#memoryUsage = object['memory_usage'];
        this.#workingDirectory = object['working_directory'];
        this.#name = object['name'];
        this.#threadCount = object['thread_count'];
        this.#fileDescriptors = object['file_descriptors'];
        this.#openFileCount = object['open_file_count'];
        this.#startTime = object['start_time'];
        this.#canModify = Boolean(object['can_modify'])
    }

    get object() {
        const obj = {
            Name: this.name,
            "Process ID": this.processID
        };

        if (this.startTime) {
            obj["Start Time"] = this.startTime;
        }

        if (this.username) {
            obj.User = this.username;
        }

        if (this.command) {
            obj.Command = this.command;
        }

        if (this.arguments) {
            obj.Arguments = this.arguments;
        }

        if (this.status) {
            obj.Status = this.status;
        }

        if (this.memoryUsage) {
            obj.Memory = describeMemory(this.memoryUsage, MEMORY_FACTORS.KB);
        }

        if (this.cpuPercent) {
            obj["Percent of Compute"] = describeNumber(this.cpuPercent)
        }

        if (this.memoryPercent) {
            obj['Percent of Memory'] = describeNumber(this.memoryPercent)
        }

        return obj;
    }


}