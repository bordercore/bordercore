
export function doGet(scope, url, callback, errorMsg) {

    axios.get(url)
        .then(response => {
            if (response.data.status && response.data.status != "OK") {
                scope.$bvToast.toast(errorMsg, {
                    title: "Error!",
                    autoHideDelay: 5000,
                    variant: "danger"
                })
                console.log(errorMsg);
            } else {
                console.log("Success");
                return callback(response);
            }
        })
        .catch((error) => {
            scope.$bvToast.toast(`${errorMsg}: ${error.message}`, {
                title: "Error!",
                autoHideDelay: 60000,
                variant: "danger"
            })
            console.error(error);
        });
}

export function doPost(scope, url, params, callback, successMsg, errorMsg) {

    const bodyFormData = new URLSearchParams();

    for (const [key, value] of Object.entries(params)) {
        bodyFormData.append(key, value);
    }

    axios(url, {
        method: "POST",
        data: bodyFormData,
    }).then(response => {
        if (response.data.status === "Warning") {
            scope.$bvToast.toast(response.data.message, {
                title: "Error",
                autoHideDelay: 10000,
                variant: "warning"
            })
            console.log("Warning: ", response.data.message);
        } else if (response.data.status != "OK") {
            scope.$bvToast.toast(response.data.message, {
                title: "Error",
                noAutoHide: true,
                variant: "danger"
            })
            console.log("Error: ", response.data.message);
        } else {
            scope.$bvToast.toast(
                response.data.message ? response.data.message : successMsg,
                {
                    title: "Success",
                    variant: "success"
                }
            )
            console.log("Success: ", response.data);
            callback(response);
        }
    })
        .catch((error) => {
            scope.$bvToast.toast(error.message, {
                title: "Error",
                noAutoHide: true,
                variant: "danger"
            })
            console.error(error);
        });

}

export function getFormattedDate(date, monthFormat="short") {
    var formattedDate  = new Date(date);
    var options = { year: "numeric", month: monthFormat, day: "numeric" };
    return formattedDate.toLocaleDateString("en-US", options);
}

export function getMarkdown() {
    var md = markdownit({
        highlight: function (str, lang) {
            if (lang && hljs.getLanguage(lang)) {
                try {
                    return hljs.highlight(str, { language: lang }).value;
                } catch (__) {}
            }

            return ''; // use external default escaping
        }
    });
    return md;
}
