STYLES = """
<style>
.message {
    white-space: pre-wrap;
    word-wrap: break-word;
    overflow-wrap: break-word;
    word-break: break-word;
    hyphens: none;
}

.thinking-container {
    background: #2b2b2b;
    color: #e0e0e0;
    border-radius: 8px;
    padding: 12px;
    margin: 5px 0 15px 0;
    font-family: monospace;
    font-size: 0.95em;
    border-left: 4px solid #4A6572;
}

.thinking-animated {
    animation: pulse 1.5s infinite;
}

.thinking-preview {
    white-space: pre-wrap;
    word-break: break-word;
}

.thinking-dots {
    display: inline-block;
    animation: blink 1.4s infinite;
}

.thinking-details summary {
    cursor: pointer;
    color: #6b8c9c;
}

@keyframes pulse {
    0% { opacity: 0.8; }
    50% { opacity: 1; }
    100% { opacity: 0.8; }
}

@keyframes blink {
    0% { opacity: 0.3; }
    20% { opacity: 1; }
    100% { opacity: 0.3; }
}
</style>
"""

COPY_BUTTON_JS = ""
COPY_BUTTON_HTML = ""
