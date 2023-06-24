<template>
    <div id="chatbot" class="d-flex flex-column align-items-center px-3">
        <div class="chatbot-container w-75 p-3">
            <div class="chatbot-messages d-flex flex-column-reverse mb-3">
                <div>  <!-- Add empty div to reverse sort -->
                    <div v-for="message in filteredChatHistory" :key="message.id" :class="'chatbot-' + message.role" class="d-flex px-3 mb-2">
                        <div v-if="message.role === 'user'" class="fw-bold me-2">
                            You
                        </div>
                        <div v-else class="fw-bold me-2">
                            AI
                        </div>
                        <div v-html="message.content" />
                    </div>
                    <div v-if="isWaiting" class="chatbot-waiting ms-3">
                        Waiting...
                    </div>
                </div>
            </div>
            <div class="d-flex">
                <input v-model="prompt" type="text" class="form-control me-2" placeholder="Send a message" @keydown.enter.prevent="handleChat">
                <select v-model="mode" class="chatbot-mode form-control me-2">
                    <option value="chat">
                        Chat
                    </option>
                    <option value="query">
                        Query Blob
                    </option>
                </select>
            </div>
        </div>
    </div>
</template>

<script>

    export default {
        props: {
            blobUuid: {
                default: "",
                type: String,
            },
            chatUrl: {
                default: "",
                type: String,
            },
        },
        setup(props) {
            const chatHistory = ref(
                [
                    {
                        id: 1,
                        content: "You are a helpful assistant.",
                        role: "system",
                    },
                ],
            );
            const isWaiting = ref(false);
            const mode = ref("chat");
            const prompt = ref("");

            /* function _handleChat() {
             *     chatHistory.value.push(
             *         {
             *             id: chatHistory.value.length + 1,
             *             content: prompt.value,
             *             role: "user",
             *         },
             *     );
             *     prompt.value = "";
             *     isWaiting.value = true;
             *     doPost(
             *         props.chatUrl,
             *         {
             *             "chat_history": JSON.stringify(chatHistory.value),
             *         },
             *         (response) => {
             *             isWaiting.value = false;
             *             chatHistory.value.push(
             *                 {
             *                     id: chatHistory.value.length + 1,
             *                     content: response.data.response,
             *                     role: "assistant",
             *                 },
             *             );
             *         },
             *     );
             * }; */

            function handleChat() {
                let id = null;
                let payload = {};
                if (mode.value === "chat") {
                    chatHistory.value.push(
                        {
                            id: chatHistory.value.length + 1,
                            content: prompt.value,
                            role: "user",
                        },
                    );
                    prompt.value = "";
                    id = chatHistory.value.length + 1;
                    payload = {
                        "chat_history": JSON.stringify(chatHistory.value),
                    };
                } else {
                    id = 1;
                    chatHistory.value = [];
                    payload = {
                        "content": prompt.value,
                        "blob_uuid": props.blobUuid,
                    };
                }
                isWaiting.value = true;
                doPost(
                    props.chatUrl,
                    payload,
                    (response) => {
                        isWaiting.value = false;
                        chatHistory.value.push(
                            {
                                id: id,
                                content: response.data.response,
                                role: "assistant",
                            },
                        );
                    },
                );
            };

            const filteredChatHistory = computed(() => {
                return chatHistory.value.filter((x) => x.role !== "system");
            });

            return {
                chatHistory,
                filteredChatHistory,
                handleChat,
                isWaiting,
                mode,
                prompt,
            };
        },
    };

</script>
