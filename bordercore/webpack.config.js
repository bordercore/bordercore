const path = require("path");
const BundleAnalyzerPlugin = require("webpack-bundle-analyzer").BundleAnalyzerPlugin;
const CompressionPlugin = require("compression-webpack-plugin");
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const FixStyleOnlyEntriesPlugin = require("webpack-fix-style-only-entries");
const StylelintPlugin = require("stylelint-webpack-plugin");
const VueLoaderPlugin = require("vue-loader/lib/plugin");

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
            "dist/css/theme-light": ["./static/scss/themes/theme-light.scss"],
            "dist/css/theme-dark": ["./static/scss/themes/theme-dark.scss"],
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
                vue$: "vue/dist/vue.esm.js",
            },
        },
        plugins: [
            // new BundleAnalyzerPlugin({analyzerPort: 9999}),

            // Lint my SCSS
            new StylelintPlugin({
                files: "static/scss/**.scss",
            }),

            // Remove the boilerplate JS files from chunks of CSS only entries
            new FixStyleOnlyEntriesPlugin(),

            // Compress the JavaScript bundles
            new CompressionPlugin({
                test: /\.js$/i,
                deleteOriginalAssets: true,
            }),

            // Extract generated CSS into separate files
            new MiniCssExtractPlugin({
                filename: devMode ? "[name].css" : "[name].min.css",
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
                        "vue-style-loader",
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

    return config;
};
