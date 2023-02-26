const path = require("path");
const webpack = require("webpack");
const CompressionPlugin = require("compression-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const RemoveEmptyScriptsPlugin = require("webpack-remove-empty-scripts");
const StylelintPlugin = require("stylelint-webpack-plugin");
const {VueLoaderPlugin} = require("vue-loader");

/**
 * Only return CSS webpack entries if the environment
 * variable WEBPACK_CSS_ONLY is set.
 * @param {string} value The array value to potentially filter
 * @return {value} the filtered value
 */
function filterEntries(value) {
    if (process.env.WEBPACK_CSS_ONLY) {
        if (value[0].search("/css/") !== -1) {
            return value;
        }
    } else {
        return value;
    }
}

module.exports = (env, argv) => {
    const devMode = argv.mode == "development";

    config = {
        entry: Object.entries({
            "dist/js/javascript": ["./front-end/index.js"],
            "dist/css/bordercore": ["./static/scss/bordercore.scss"],
            "dist/css/vue-sidebar-menu": ["./static/css/vue-sidebar-menu/vue-sidebar-menu.scss"],
        })
            .filter(filterEntries)
            .reduce((a, [name, entry]) => Object.assign(a, {[name]: entry}), {}),
        output: {
            filename: "[name]-bundle.min.js",
            path: path.resolve(__dirname, "./static"),
        },
        mode: "production",
        resolve: {
            alias: {
                vue$: "vue/dist/vue.esm-bundler.js",
            },
        },
        plugins: [
            // Lint my SCSS
            new StylelintPlugin({
                // By default compiler.options.output.path is included
                // in the exclude list, which would mean our 'static'
                // folder would be skipped. So set it to the empty list.
                exclude: [],
                files: "static/scss/**.scss",
            }),

            // Remove the boilerplate JS files from chunks of CSS only entries
            new RemoveEmptyScriptsPlugin(),

            // Extract generated CSS into separate files
            new MiniCssExtractPlugin({
                filename: devMode ? "[name].css" : "[name].min.css",
            }),

            // Define these to improve tree-shaking and muffle browser warnings
            new webpack.DefinePlugin({
                __VUE_OPTIONS_API__: true,
                __VUE_PROD_DEVTOOLS__: false,
            }),

            // Responsible for cloning any other rules you have defined and applying them
            //  to the corresponding language blocks in .vue files
            new VueLoaderPlugin(),
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
                        "style-loader",
                        {
                            loader: "css-loader",
                            options: {
                                esModule: false,
                            },
                        },
                    ],
                },
                {
                    test: /\.vue$/,
                    loader: "vue-loader",
                },
                {
                    test: /\.(js|jsx)$/,
                    use: "babel-loader",
                },
                {
                    test: /\.(png|woff|woff2|eot|ttf|svg)$/,
                    loader: "url-loader",
                },
            ],
        },
    };

    if (devMode) {
        config.output.filename = "[name]-bundle.js";
    }

    if (process.env.ANALYZER) {
        const BundleAnalyzerPlugin = require("webpack-bundle-analyzer").BundleAnalyzerPlugin;
        config.plugins.push(new BundleAnalyzerPlugin({analyzerPort: 9999}));
    } else {
        // Compress the JavaScript bundles.
        //  We include this here because it is not compatible
        //  with the "webpack-bundle-analyzer" plugin.
        config.plugins.push(new CompressionPlugin({
            test: /\.js$/i,
            deleteOriginalAssets: true,
        }));
    }

    return config;
};
