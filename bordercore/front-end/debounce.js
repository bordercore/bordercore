// This debounce method is meant to be used as a composable for Vue components

const delay = 300; // default debounce delay in milliseconds

export default function() {
    let debounceTimer = null;

    function debounce(method, timer = delay) {
        if (debounceTimer !== null) {
            clearTimeout(debounceTimer);
        }
        debounceTimer = setTimeout(method, timer);
    };

    function created() {
        debounceTimer = null;
    };

    return {
        created,
        debounce,
    };
};
