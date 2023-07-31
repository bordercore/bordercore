<template>
    <div v-show="show" class="flex-column align-items-center px-3">
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
                            <div v-html="getMarkdown(message.content)" />
                        </div>
                        <div v-if="isWaiting" class="chatbot-waiting ms-3">
                            Waiting...
                        </div>
                    </div>
                </div>
                <div class="d-flex">
                    <input v-model="prompt" type="text" class="form-control me-2" placeholder="Send a message" @keydown.enter.prevent="handleChatFromEvent">
                    <select v-model="mode" class="chatbot-mode form-control me-2" @change="handleChat">
                        <option value="chat">
                            Chat
                        </option>
                        <option v-if="blobUuid" value="blob">
                            Query Blob
                        </option>
                    </select>
                </div>
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
            const show = ref(false);

            function getMarkdown(content) {
                return markdown.render(content);
            };

            function handleChatFromEvent(event, content) {
                handleChat(content);
            };

            function handleChat(content, questionUuid) {
                let id = null;
                let payload = {};

                if (questionUuid) {
                    chatHistory.value = [];
                    id = 1;
                    prompt.value = "";
                    payload = {
                        "question_uuid": questionUuid,
                    };
                    mode.value = "chat";
                } else if (mode.value === "chat") {
                    chatHistory.value.push(
                        {
                            id: chatHistory.value.length + 1,
                            content: content || prompt.value,
                            role: "user",
                        },
                    );
                    prompt.value = "";
                    id = chatHistory.value.length + 1;
                    payload = {
                        "chat_history": JSON.stringify(chatHistory.value),
                    };
                } else if (mode.value === "blob") {
                    if (prompt.value === "") {
                        return;
                    }
                    chatHistory.value = [];
                    id = 1;
                    content = prompt.value;
                    prompt.value = "";
                    payload = {
                        "content": content,
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

            onMounted(() => {
                EventBus.$on("chat", (payload) => {
                    show.value = true;
                    handleChat(payload.content, payload.questionUuid);
                });
            });

            return {
                chatHistory,
                getMarkdown,
                filteredChatHistory,
                handleChat,
                handleChatFromEvent,
                isWaiting,
                mode,
                prompt,
                show,
            };
        },
    };

</script>
