const path = require("path");
const BundleAnalyzerPlugin = require("webpack-bundle-analyzer").BundleAnalyzerPlugin;
const CompressionPlugin = require("compression-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const FixStyleOnlyEntriesPlugin = require("webpack-fix-style-only-entries");

module.exports = (env, argv) => {

    let devMode = argv.mode == "development";

    config = {
        entry: {
            "js/javascript": ["./front-end/index.js"],
            "css/theme-light": ["./static/css/theme-light.scss"],
            "css/theme-dark": ["./static/css/theme-dark.scss"],
        },
        output: {
            filename: "[name]-bundle.min.js",
            path: path.resolve(__dirname, "./static"),
        },
        mode: "production",
        resolve: {
            alias: {
                vue$: "vue/dist/vue.esm.js"
            }
        },
        plugins: [
            // new BundleAnalyzerPlugin({analyzerPort: 9999}),

            // Remove the boilerplate JS files from chunks of CSS only entries
            new FixStyleOnlyEntriesPlugin(),

            // Compress the JavaScript bundles
            new CompressionPlugin({
                test: /\.js$/i,
                deleteOriginalAssets: true
            }),

            // Extract generated CSS into separate files
            new MiniCssExtractPlugin({
                filename: devMode ? "[name].css" : "[name].min.css",
            })
        ],
        module: {
            rules: [
                {
                    test: /\.scss$/i,
                    use: [
                        MiniCssExtractPlugin.loader,
                        // Translates CSS into CommonJS
                        "css-loader",
                        // Compiles Sass to CSS
                        "sass-loader",
                    ],
                }
            ]
        }
    };

    if (devMode) {
        config.output.filename = "[name]-bundle.js";
    }

    return config;

}
