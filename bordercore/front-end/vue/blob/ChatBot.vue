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
                    <select v-model="mode" class="chatbot-mode form-control me-2">
                        <option value="notes">
                            Query Notes
                        </option>
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
            csrfToken: {
                default: null,
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
            const mode = ref("notes");
            const prompt = ref("");
            const show = ref(false);

            function getMarkdown(content) {
                return markdown.render(content);
            };

            function handleChatFromEvent(event, content) {
                handleChat(content);
            };

            async function handleChat(content, questionUuid, exerciseUuid) {
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
                } else if (exerciseUuid) {
                    chatHistory.value = [];
                    id = 1;
                    prompt.value = "";
                    payload = {
                        "exercise_uuid": exerciseUuid,
                    };
                    mode.value = "chat";
                } else if (mode.value === "chat" || mode.value === "notes") {
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
                        "mode": mode.value,
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

                const formData = new FormData();
                for (const key in payload) {
                    if (payload.hasOwnProperty(key)) {
                        formData.append(key, payload[key]);
                    }
                }

                fetch(props.chatUrl, {
                    method: "POST",
                    headers: {
                        "X-Csrftoken": props.csrfToken,
                        "Responsetype": "stream",
                    },
                    body: formData,
                })
                    .then((response) => {
                        if (!response.ok) {
                            throw new Error("Network response was not ok");
                        }

                        const reader = response.body.getReader();
                        const decoder = new TextDecoder("utf-8");

                        // The content is initially empty.
                        // We'll fill it in as it streams in.
                        chatHistory.value.push(
                            {
                                id: id,
                                content: "",
                                role: "assistant",
                            },
                        );

                        return new ReadableStream({
                            start(controller) {
                                function push() {
                                    reader.read().then(({done, value}) => {
                                        if (done) {
                                            controller.close();
                                            return;
                                        }
                                        isWaiting.value = false;
                                        const newValue = chatHistory.value[chatHistory.value.length - 1];
                                        newValue.content = newValue.content + decoder.decode(value, {stream: true});
                                        chatHistory.value[chatHistory.value.length - 1] = newValue;

                                        controller.enqueue(value);
                                        push();
                                    })
                                          .catch((error) => {
                                              console.error(error);
                                              controller.error(error);
                                          });
                                }
                                push();
                            },
                        });
                    })
                    .then((stream) => {
                        return new Response(stream).text();
                    })
                    .then((result) => {
                    })
                    .catch((error) => {
                        console.error("Error:", error);
                    });
            };

            const filteredChatHistory = computed(() => {
                return chatHistory.value.filter((x) => x.role !== "system");
            });

            onMounted(() => {
                EventBus.$on("chat", (payload) => {
                    show.value = true;
                    handleChat(payload.content, payload.questionUuid, payload.exerciseUuid);
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
