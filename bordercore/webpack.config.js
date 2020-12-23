const path = require("path");
const BundleAnalyzerPlugin = require("webpack-bundle-analyzer").BundleAnalyzerPlugin;
const CompressionPlugin = require("compression-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const FixStyleOnlyEntriesPlugin = require("webpack-fix-style-only-entries");
const StylelintPlugin = require("stylelint-webpack-plugin");
const VueLoaderPlugin = require("vue-loader/lib/plugin")

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

            // Lint my SCSS
            new StylelintPlugin({
                files: "**/bordercore.scss"
            }),

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
            }),

            // Responsible for cloning any other rules you have defined and applying them
            //  to the corresponding language blocks in .vue files
            new VueLoaderPlugin()
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
                },
                // this will apply to both plain `.css` files
                // AND `<style>` blocks in `.vue` files,
                {
                    test: /\.css$/,
                    use: [
                        "vue-style-loader",
                        "css-loader"
                    ]
                },
                {
                    test: /\.vue$/,
                    loader: "vue-loader"
                }
            ]
        }
    };

    if (devMode) {
        config.output.filename = "[name]-bundle.js";
    }

    return config;

}
