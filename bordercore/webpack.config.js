const path = require("path");

module.exports = {
    entry: "./front-end/index.js",  // path to our input file
    output: {
        filename: "index-bundle.js",  // output bundle file name
        path: path.resolve(__dirname, "./static"),  // path to our Django static directory
    },
};
