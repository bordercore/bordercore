const path = require("path");
// const webpack = require("webpack")

const BundleAnalyzerPlugin = require("webpack-bundle-analyzer").BundleAnalyzerPlugin;

config = {
    entry: "./front-end/index.js",
    output: {
        filename: "index-bundle.js",
        path: path.resolve(__dirname, "./static"),
    },
    mode: "production",
    resolve: {
        alias: {
            vue$: "vue/dist/vue.esm.js"
        }
    },
    // plugins: [
    //     new BundleAnalyzerPlugin({analyzerPort: 9999})
    // ]
};

module.exports = (env, argv) => {
    if (argv.mode == "development") {
        config.output.filename = "index-bundle-dev.js";
    }
    return config;
}
