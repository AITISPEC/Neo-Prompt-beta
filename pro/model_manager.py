import gradio as gr

from .formatters import format_response_display, format_thinking_display
from .neo_client import NeoClient


class ModelManager:
    def __init__(self):
        self.neo = NeoClient()
        self.available_presets = []
        self.current_presets = [None, None, None, None, None]
        self.chain_responses = []
        self.current_step = 0
        self.user_message = ""
        self.auto_mode = True
        self.always_new_chat = False

    def check_neo_status(self):
        result = self.neo.check_server_status()
        if result["status"] == "online":
            return f"✅ {result['model']} ({result['context']} токенов)"
        elif result["status"] == "online_no_model":
            return "⚠️ Сервер онлайн, модель не выбрана"
        else:
            return f"❌ Офлайн: {result.get('message', '')}"

    def refresh_presets(self, presets_list):
        self.available_presets = presets_list
        choices = [f"{p['name']} ({p['file']})" for p in self.available_presets]
        choices.insert(0, "")
        return choices

    def select_preset(self, slot_index, preset_display_name):
        if not preset_display_name or preset_display_name == "":
            self.current_presets[slot_index] = None
            return f"❌ Слот {slot_index + 1}: не выбран"

        for p in self.available_presets:
            display = f"{p['name']} ({p['file']})"
            if display == preset_display_name:
                self.current_presets[slot_index] = p["id"]
                return f"✅ Слот {slot_index + 1}: {p['name']}"
        return f"❌ Слот {slot_index + 1}: пресет не найден"

    def get_active_presets_count(self):
        return sum(1 for p in self.current_presets if p is not None)

    def set_auto_mode(self, mode):
        self.auto_mode = mode
        return mode

    def set_always_new_chat(self, enabled):
        self.always_new_chat = enabled

    def start_chain_stream(self, message, history, always_new=False):
        self.always_new_chat = always_new
        self.user_message = message
        self.chain_responses = []
        self.current_step = 0

        active_count = self.get_active_presets_count()

        if active_count == 0:
            response = self.neo.send_message(message, reset_context=always_new)
            if isinstance(response, dict):
                content = response.get("content", "")
                reasoning = response.get("reasoning", "")
            else:
                content = response
                reasoning = ""

            display_content = format_response_display(content)
            display_thinking = format_thinking_display(reasoning, is_final=True)

            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": display_content})

            yield (
                history,
                history,
                "",
                0,
                gr.update(interactive=False),
                display_thinking,
                reasoning,
                display_content,
            )
            return

        current_input = message
        last_reasoning = ""

        for i, preset_id in enumerate(self.current_presets):
            if preset_id is None:
                continue

            for (
                partial_content,
                partial_reasoning,
                status,
            ) in self.neo.send_message_with_preset_stream(
                current_input, preset_id, reset_context=self.always_new_chat
            ):
                if status == "error":
                    history.append({"role": "user", "content": message})
                    history.append({"role": "assistant", "content": partial_content})
                    yield (
                        history,
                        history,
                        "",
                        i + 1,
                        gr.update(interactive=False),
                        "",
                        "",
                        "",
                    )
                    return

                if status == "thinking":
                    display_thinking = format_thinking_display(
                        partial_reasoning, is_final=False
                    )
                    yield (
                        history,
                        history,
                        "",
                        i + 1,
                        gr.update(interactive=False),
                        display_thinking,
                        partial_reasoning,
                        partial_content,
                    )
                else:  # final
                    current_input = partial_content
                    last_reasoning = partial_reasoning
                    self.chain_responses.append(
                        {"content": current_input, "reasoning": last_reasoning}
                    )
                    # Здесь важно передать response_raw
                    display_content = format_response_display(current_input)
                    display_thinking = format_thinking_display(
                        last_reasoning, is_final=True
                    )

                    history.append({"role": "user", "content": message})
                    history.append({"role": "assistant", "content": display_content})

                    yield (
                        history,
                        history,
                        "",
                        i + 1,
                        gr.update(interactive=False),
                        display_thinking,
                        last_reasoning,
                        display_content,
                    )
                    return

        # Этот код вряд ли выполнится, но на всякий случай
        display_content = format_response_display(current_input)
        display_thinking = format_thinking_display(last_reasoning, is_final=True)

        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": display_content})

        yield (
            history,
            history,
            "",
            active_count,
            gr.update(interactive=False),
            display_thinking,
            last_reasoning,
            display_content,
        )

    def reset_chain(self):
        self.chain_responses = []
        self.current_step = 0
        self.user_message = ""
        self.neo.reset_chat()
        return [], [], ""

    def get_preset_by_index(self, index):
        if 0 <= index < len(self.available_presets):
            return self.available_presets[index]
        return None
