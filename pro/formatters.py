import re


def format_thinking_display(text, is_final=False, visible_lines=3):
    if not text or text.strip() == "":
        return ""

    lines = text.strip().split("\n")
    lines = [line for line in lines if line.strip()]

    def join_with_br(lines):
        return "<br" + ">".join(lines)

    if is_final:
        if len(lines) > visible_lines:
            display_lines = lines[:visible_lines]
            hidden_count = len(lines) - visible_lines
            preview = join_with_br(display_lines)
            full_preview = join_with_br(lines)
            return f"""
            <div class="thinking-container">
                <div class="thinking-preview">{preview}</div>
                <details class="thinking-details">
                    <summary style="font-weight: bold; font-size: 1.05em; cursor: pointer;">Показать ещё {hidden_count} строк</summary>
                    <div class="thinking-full">{full_preview}</div>
                </details>
            </div>
            """
        else:
            preview = join_with_br(lines)
            return f"""
            <div class="thinking-container">
                <div class="thinking-preview">{preview}</div>
            </div>
            """
    else:
        display_lines = lines[-visible_lines:] if len(lines) > visible_lines else lines
        preview = join_with_br(display_lines)
        return f"""
        <div class="thinking-container thinking-animated">
            <div class="thinking-preview">{preview}</div>
            <span class="thinking-dots">...</span>
        </div>
        """


def format_response_display(text):
    if not text:
        return ""
    text = re.sub(r"\*\*Ответ:?\*\*:?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^Ответ:?\s*", "", text, flags=re.IGNORECASE)
    text = re.sub(r"^\*\*. *?\*\*\s*", "", text)
    return text.strip()
