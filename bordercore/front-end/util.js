
/**
 * Use axios to perform an HTTP GET call.
 * @param {string} scope The Vue scope.
 * @param {string} url The url to request.
 * @param {string} callback An optional callback function.
 * @param {string} errorMsg The message to display on error.
 */
export function doGet(scope, url, callback, errorMsg) {
    axios.get(url)
        .then((response) => {
            if (response.data.status && response.data.status != "OK") {
                const vNodesMsg = getErrorMessage(scope, errorMsg);
                EventBus.$emit(
                    "toast",
                    {
                        title: "Error!",
                        body: vNodesMsg,
                        variant: "danger",
                        autoHide: false,
                    },
                );
                console.log(errorMsg);
            } else {
                console.log("Success");
                return callback(response);
            }
        })
        .catch((error) => {
            EventBus.$emit(
                "toast",
                {
                    title: "Error!",
                    body: `${errorMsg}: ${error.message}`,
                    variant: "danger",
                    autoHide: false,
                },
            );
            console.error(error);
        });
}

/**
 * Use axios to perform an HTTP POST call.
 * @param {string} scope The Vue scope.
 * @param {string} url The url to request.
 * @param {string} params The parameters for the POST body.
 * @param {string} callback An optional callback function.
 * @param {string} successMsg The message to display on success.
 * @param {string} errorMsg The message to display on error.
 */
export function doPost(scope, url, params, callback, successMsg, errorMsg) {
    const bodyFormData = new URLSearchParams();

    for (const [key, value] of Object.entries(params)) {
        bodyFormData.append(key, value);
    }

    axios(url, {
        method: "POST",
        data: bodyFormData,
    }).then((response) => {
        if (response.data.status && response.data.status === "Warning") {
            EventBus.$emit(
                "toast",
                {
                    title: "Error",
                    body: response.data.message,
                    variant: "warning",
                    autoHide: false,
                },
            );
            console.log("Warning: ", response.data.message);
        } else if (response.data.status && response.data.status != "OK") {
            EventBus.$emit(
                "toast",
                {
                    title: "Error",
                    body: response.data.message,
                    variant: "danger",
                    autoHide: false,
                },
            );
            console.log("Error: ", response.data.message);
        } else {
            const body = response.data.message ? response.data.message : successMsg;
            if (body) {
                EventBus.$emit(
                    "toast",
                    {
                        title: "Success",
                        body: response.data.message ? response.data.message : successMsg,
                        variant: "info",
                    },
                );
            }
            console.log("Success: ", response.data);
            callback(response);
        }
    })
        .catch((error) => {
            EventBus.$emit(
                "toast",
                {
                    title: "Error",
                    body: error.message,
                    variant: "danger",
                    autoHide: false,
                },
            );
            console.error(error);
        });
}

/**
 * Use axios to perform an HTTP PUT call.
 * @param {string} scope The Vue scope.
 * @param {string} url The url to request.
 * @param {string} params The parameters for the POST body.
 * @param {string} callback An optional callback function.
 * @param {string} successMsg The message to display on success.
 * @param {string} errorMsg The message to display on error.
 */
export function doPut(scope, url, params, callback, successMsg, errorMsg) {
    const bodyFormData = new URLSearchParams();

    for (const [key, value] of Object.entries(params)) {
        bodyFormData.append(key, value);
    }

    axios(url, {
        method: "PUT",
        data: bodyFormData,
    }).then((response) => {
        if (response.status != 200) {
            EventBus.$emit(
                "toast",
                {
                    title: "Error",
                    body: response.data.message,
                    variant: "danger",
                    autoHide: false,
                },
            );
            console.log("Error: ", response.statusText);
        } else {
            const body = response.data.message ? response.data.message : successMsg;
            if (body) {
                EventBus.$emit(
                    "toast",
                    {
                        title: "Success",
                        body: response.data.message ? response.data.message : successMsg,
                        variant: "info",
                    },
                );
            }
            console.log("Success: ", response.data);
            callback(response);
        }
    })
        .catch((error) => {
            EventBus.$emit(
                "toast",
                {
                    title: "Error",
                    body: error.message,
                    variant: "danger",
                    autoHide: false,
                },
            );
            console.error(error);
        });
}

/**
 * Return a Vue Vnode containing a formatted error message
 * @param {string} vue Vue component
 * @param {string} errorMsg the error message to display
 * @return {VNodes} the new Vnode
 */
function getErrorMessage(vue, errorMsg) {
    const h = vue.$createElement;
    const vNodesMsg = [
        h("font-awesome-icon", {
            props: {
                icon: "exclamation-triangle",
            },
        }),
        h("span", {"class": ["ms-2"]}, [errorMsg]),
    ];

    return vNodesMsg;
}


/**
 * Return a formatted date.
 * @param {string} date The date to format.
 * @param {string} monthFormat The url to request.
 * @return {string} The formatted date string.
 */
export function getFormattedDate(date, monthFormat="short") {
    const formattedDate = new Date(date);
    const options = {year: "numeric", month: monthFormat, day: "numeric"};
    return formattedDate.toLocaleDateString("en-US", options);
}


/**
 * Resets the copy button text
 * @param {string} target The DOM element to reset.
 */
function resetCopyButton(target) {
    target.textContent = "Copy";
}


/**
 * Create a prism.js hook which adds an "on-hover" copy button to code blocks.
 */
export function addCopyButton() {
    Prism.hooks.add("complete", function(env) {
    const code = (env.element);
    const pre = (code.parentNode);

    // If this is the code console, since the autoloader rehighlights and
    //  calls this function as you type, only add the copy button once.
    if (pre.parentNode.classList.contains("code-input") && pre.parentNode.querySelector("button.copy-button")) {
        return;
    }

    const copyDiv = document.createElement("div");
    copyDiv.className = "copy-button";

    const button = document.createElement("button");
    button.className = "copy-button";
    button.setAttribute("type", "button");
    button.addEventListener("click", function(evt) {
        if (navigator.clipboard) {
            navigator.clipboard.writeText(code.textContent);
            linkSpan.textContent = "Copied!";
            setTimeout(resetCopyButton.bind(null, evt.currentTarget), 5000);
        }
    });

    const linkSpan = document.createElement("span");
    linkSpan.textContent = "Copy";
    button.appendChild(linkSpan);

    const parentNode = pre.parentNode;
    if (parentNode.classList.contains("code-input")) {
        pre.parentNode.appendChild(button);
        button.classList.add("console");
    } else {
        pre.appendChild(button);
    }
});
}
