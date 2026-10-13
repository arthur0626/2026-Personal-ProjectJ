import re

from django import template
from django.utils.html import format_html, linebreaks
from django.utils.safestring import mark_safe

register = template.Library()

FENCE = re.compile(r'^```[^\n]*\n(.*?)^```[ \t]*$', re.M | re.S)


@register.filter
def render_body(text):
    """Escape everything; fenced blocks become <pre><code>, the rest paragraphs."""
    # shortcut: only ``` fences are understood, not full Markdown; switch to a
    # Markdown library plus an HTML sanitizer when richer formatting is needed.
    return mark_safe(''.join(
        format_html('<pre><code>{}</code></pre>', part) if i % 2
        else linebreaks(part.strip(), autoescape=True)
        for i, part in enumerate(FENCE.split(text)) if part.strip()
    ))
