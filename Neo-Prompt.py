try:
    import gradio as gr

    from pro import STYLES, ModelManager, load_presets_from_files
except KeyboardInterrupt:
    print("\n🛑 Скрипт остановлен пользователем (Ctrl+C)")
    print("👋 Выход...")
except ImportError:
    pass

manager = ModelManager()
presets_list = load_presets_from_files()

with gr.Blocks(title="Neo Prompt - 5 пресетов") as demo:
    gr.Markdown(
        """
	# 🌙 Neo Prompt
	### Цепочка из 5 пресетов
	"""
    )

    with gr.Row():
        neo_status = gr.Textbox(
            label="Статус", value="❌ Не подключён", interactive=False, scale=3
        )
        neo_refresh = gr.Button("🔄 Проверить", scale=1, size="sm")

    with gr.Row():
        refresh_presets_btn = gr.Button(
            "🔄 Обновить пресеты", variant="primary", size="sm"
        )

    gr.Markdown("---")
    gr.Markdown("### Выберите пресеты для каждого шага")

    preset_dropdowns = []
    preset_statuses = []

    for i in range(5):
        with gr.Row():
            with gr.Column(scale=1):
                gr.Markdown(f"**Шаг {i + 1}**")
            with gr.Column(scale=4):
                dropdown = gr.Dropdown(
                    label="",
                    choices=[""],
                    interactive=True,
                    allow_custom_value=False,
                    container=False,
                )
                preset_dropdowns.append(dropdown)
            with gr.Column(scale=2):
                status = gr.Textbox(
                    label="",
                    value="",
                    interactive=False,
                    show_label=False,
                    container=False,
                )
                preset_statuses.append(status)

    gr.Markdown("---")

    with gr.Row():
        with gr.Column(scale=1):
            auto_mode_checkbox = gr.Checkbox(
                label="Авто", value=True, info="Автоматическое выполнение"
            )
        with gr.Column(scale=1):
            always_new_chat_checkbox = gr.Checkbox(
                label="Новый чат", value=False, info="Каждое сообщение - новый диалог"
            )
        with gr.Column(scale=2):
            step_counter = gr.Number(
                label="Шаг:", value=0, minimum=0, maximum=5, interactive=False
            )
        with gr.Column(scale=2):
            next_step_btn = gr.Button(
                "Следующий шаг", variant="secondary", interactive=False, size="sm"
            )
            next_step_hint = gr.HTML(
                value="<div style='text-align: center; font-size: 0.8em; color: #666;'>Авто режим</div>"
            )

    gr.HTML(STYLES)

    thinking_display = gr.HTML(label="", visible=True)

    thinking_state = gr.State("")
    response_state = gr.State("")

    neo_chatbot = gr.Chatbot(height=400, show_label=False)

    with gr.Row():
        neo_msg = gr.Textbox(
            label="", placeholder="Напишите что-нибудь...", scale=4, container=False
        )
        send_btn = gr.Button("🚀", scale=1, variant="primary", size="lg")

    neo_history = gr.State([])

    with gr.Row():
        neo_clear = gr.Button("🗑️ Очистить чат", size="sm")

    gr.Markdown("---")

    with gr.Row():
        gr.Markdown("### 📊 Статистика последнего ответа")

    with gr.Row():
        token_speed = gr.Textbox(
            label="Скорость", value="0 т/с", interactive=False, scale=1, container=True
        )
        token_count = gr.Textbox(
            label="Токенов", value="0", interactive=False, scale=1, container=True
        )
        token_time = gr.Textbox(
            label="Время", value="0.0 с", interactive=False, scale=1, container=True
        )

    with gr.Row():
        gr.Markdown("### 📈 Всего использовано")

    with gr.Row():
        total_tokens = gr.Textbox(
            label="Токенов в контексте",
            value="0 / 8192",
            interactive=False,
            scale=1,
            container=True,
        )

    def refresh_all():
        return manager.check_neo_status()

    neo_refresh.click(fn=refresh_all, outputs=[neo_status])

    def update_preset_lists():
        global presets_list
        presets_list = load_presets_from_files()
        choices = manager.refresh_presets(presets_list)
        # Возвращаем только обновленные dropdown, статусы оставляем пустыми
        updates = []
        for i in range(5):
            updates.append(gr.Dropdown(choices=choices))
        for i in range(5):
            updates.append("")
        return updates

    refresh_presets_btn.click(
        fn=update_preset_lists, outputs=preset_dropdowns + preset_statuses
    )

    for i, dropdown in enumerate(preset_dropdowns):
        dropdown.change(
            fn=lambda idx, val: manager.select_preset(idx, val),
            inputs=[gr.State(i), dropdown],
            outputs=preset_statuses[i],
        )

    def toggle_auto_mode(mode):
        manager.set_auto_mode(mode)
        hint = "Авто режим" if mode else "Ручной режим"
        return (
            gr.Button(interactive=not mode),
            f"<div style='text-align: center; font-size: 0.8em; color: #666;'>{hint}</div>",
        )

    auto_mode_checkbox.change(
        fn=toggle_auto_mode,
        inputs=auto_mode_checkbox,
        outputs=[next_step_btn, next_step_hint],
    )

    always_new_chat_checkbox.change(
        fn=manager.set_always_new_chat, inputs=always_new_chat_checkbox, outputs=None
    )

    def handle_send_stream(message, history, auto_mode, always_new):
        if not message or message.strip() == "":
            yield (
                history,
                history,
                "",
                0,
                gr.update(interactive=False),
                "",
                "",
                "",
                "0 т/с",
                "0",
                "0.0 с",
                "0 / 8192",
            )
            return

        for result in manager.start_chain_stream(message, history, always_new):
            (
                chatbot,
                state,
                msg,
                step,
                btn,
                thinking_html,
                thinking_raw,
                response_raw,
            ) = result
            stats = manager.neo.get_last_stats()
            speed = f"{stats['speed']} т/с"
            tokens = str(stats["tokens"])
            times = f"{stats['time']} с"
            used, total, _ = manager.neo.get_token_progress()
            total_str = f"{used} / {total}"

            yield (
                chatbot,
                state,
                msg,
                step,
                btn,
                thinking_html,
                thinking_raw,
                response_raw,
                speed,
                tokens,
                times,
                total_str,
            )

    send_btn.click(
        fn=handle_send_stream,
        inputs=[neo_msg, neo_history, auto_mode_checkbox, always_new_chat_checkbox],
        outputs=[
            neo_chatbot,
            neo_history,
            neo_msg,
            step_counter,
            next_step_btn,
            thinking_display,
            thinking_state,
            response_state,
            token_speed,
            token_count,
            token_time,
            total_tokens,
        ],
    )

    neo_msg.submit(
        fn=handle_send_stream,
        inputs=[neo_msg, neo_history, auto_mode_checkbox, always_new_chat_checkbox],
        outputs=[
            neo_chatbot,
            neo_history,
            neo_msg,
            step_counter,
            next_step_btn,
            thinking_display,
            thinking_state,
            response_state,
            token_speed,
            token_count,
            token_time,
            total_tokens,
        ],
    )

    def clear_all():
        history, chatbot, msg = manager.reset_chain()
        return (
            history,
            chatbot,
            msg,
            0,
            gr.Button(interactive=False),
            "",
            "",
            "",
            "0 т/с",
            "0",
            "0.0 с",
            "0 / 8192",
        )

    neo_clear.click(
        fn=clear_all,
        outputs=[
            neo_history,
            neo_chatbot,
            neo_msg,
            step_counter,
            next_step_btn,
            thinking_display,
            thinking_state,
            response_state,
            token_speed,
            token_count,
            token_time,
            total_tokens,
        ],
    )

if __name__ == "__main__":
    try:
        demo.launch(
            share=False,
            server_name="127.0.0.1",
            server_port=7860,
            theme=gr.themes.Soft(),
        )
    except KeyboardInterrupt:
        print("\n🛑 Скрипт остановлен пользователем (Ctrl+C)")
        print("👋 Выход...")
    except (KeyError, ValueError):
        pass
