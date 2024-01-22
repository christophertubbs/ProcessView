export class Communicator {
    #errorHandler;

    constructor(errorHandler) {
        this.#errorHandler = errorHandler;
    }

    async #handleError(info) {
        console.error(info);
        let handledResult = this.#errorHandler(info);

        while (handledResult instanceof Promise) {
            handledResult = await handledResult;
        }
    }

    async communicate(input, onSuccess) {
        let response;
        let responseData;
        try {
            response = await fetch(input);
            responseData = await response.json()
        } catch (exception) {
            const error_data = {
                message_id: null,
                message_type: "Could not reach server",
                error_message: exception.toString()
            }
            await this.#handleError(error_data);
            return false;
        }

        if (response.status < 400) {
            try {
                let successRun = onSuccess(responseData);

                while (successRun instanceof Promise) {
                    successRun = await successRun;
                }
            } catch (exception) {
                const error_data = {
                    message_id: null,
                    message_type: "Error after fetching remote data",
                    error_message: exception.toString()
                }
                await this.#handleError(error_data);
                return false;
            }
        }
        else {
            await this.#handleError(responseData);
        }

        return response.status < 400
    }
}