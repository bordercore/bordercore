
/**
 * Use axios to perform an HTTP GET call.
 * @param {string} url The url to request.
 * @param {string} callback An optional callback function.
 * @param {string} errorMsg The message to display on error.
 */
export function doGet(url, callback, errorMsg) {
    axios.get(url)
        .then((response) => {
            if (response.data.status && response.data.status !== "OK") {
                EventBus.$emit(
                    "toast",
                    {
                        title: "Error!",
                        body: errorMsg,
                        variant: "danger",
                        autoHide: false,
                    },
                );
                console.log(errorMsg);
            } else {
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
 * @param {string} url The url to request.
 * @param {string} params The parameters for the POST body.
 * @param {string} callback An optional callback function.
 * @param {string} successMsg The message to display on success.
 * @param {string} errorMsg The message to display on error.
 */
export function doPost(url, params, callback, successMsg, errorMsg) {
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
        } else if (response.data.status && response.data.status !== "OK") {
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
 * @param {string} url The url to request.
 * @param {string} params The parameters for the POST body.
 * @param {string} callback An optional callback function.
 * @param {string} successMsg The message to display on success.
 * @param {string} errorMsg The message to display on error.
 */
export function doPut(url, params, callback, successMsg, errorMsg) {
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
        if ((pre.parentNode.parentNode.classList.contains("code-input") || pre.parentNode.classList.contains("code-input")) && pre.parentNode.parentNode.querySelector("button.copy-button")) {
            return;
        }

        if (!pre.classList.contains("python-console")) {
            // Create a wrapper div with positioning "relative", but only
            // for code blocks and not the Pyton console.
            // The "copy" button will be absolutely positioned
            // relative to this div rather than the <pre> container
            // which might contain horizontal scrollbars. We don't
            // want the "copy" button to scroll.
            const wrapper = document.createElement("div");
            wrapper.style.position = "relative";

            // set the wrapper as child (instead of the <pre> element)
            pre.parentNode.replaceChild(wrapper, pre);
            // set <pre> as child of wrapper
            wrapper.appendChild(pre);
        }

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

/**
 * Trigger an animate.css animation on demand via JavaScript.
 * @param {object} node the DOM element to animate
 * @param {string} animation the animaton to use
 * @param {string} prefix the class prefix
 */
export const animateCSS = (node, animation, prefix = "animate__") =>
// We create a Promise and return it
new Promise((resolve, reject) => {
    const animationName = `${prefix}${animation}`;
    node.classList.add(`${prefix}animated`, animationName);

    // When the animation ends, we clean the classes and resolve the Promise
    function handleAnimationEnd(event) {
        event.stopPropagation();
        node.classList.remove(`${prefix}animated`, animationName);
        resolve("Animation ended");
    }

    node.addEventListener("animationend", handleAnimationEnd, {once: true});
});

/**
 * Capitalize the first letter of a string (usually a word)
 * @param {string} string the string
 * @return {string} the transformed string
 */
export function capitalizeFirstLetter(string) {
    return string.charAt(0).toUpperCase() + string.slice(1);
};

/**
 * Surround substring with bold markup
 * @param {string} optionName the string
 * @param {string} substring the substring
 * @return {string} the transformed string
 */
export function boldenOption(optionName, substring) {
    const texts = substring.split(/[\s-_/\\|\.]/gm).filter((t) => !!t) || [""];
    return optionName.replace(new RegExp("(.*?)(" + texts.join("|") + ")(.*?)", "gi"), "$1<b>$2</b>$3");
};
