const path = require("path");

const BundleAnalyzerPlugin = require("webpack-bundle-analyzer").BundleAnalyzerPlugin;

module.exports = {
    entry: "./front-end/index.js",
    output: {
        filename: "index-bundle.js",
        path: path.resolve(__dirname, "./static"),
    },
    // plugins: [
    //     new BundleAnalyzerPlugin({analyzerPort: 9999})
    // ]
};
