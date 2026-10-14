import re

from django.db import migrations
from django.utils.html import format_html, linebreaks

FENCE = re.compile(r'^```[^\n]*\n(.*?)^```[ \t]*$', re.M | re.S)


def plaintext_to_html(text):
    """The Milestone 4 renderer: escape everything, ``` fences become <pre><code>."""
    return ''.join(
        format_html('<pre><code>{}</code></pre>', part) if i % 2
        else linebreaks(part.strip(), autoescape=True)
        for i, part in enumerate(FENCE.split(text)) if part.strip()
    )


def forwards(apps, schema_editor):
    BlogPost = apps.get_model('blog', 'BlogPost')
    for post in BlogPost.objects.all():
        post.body = plaintext_to_html(post.body)
        post.save(update_fields=['body'])


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0002_attachments_comments'),
    ]

    # Not reversible: once posts are edited as HTML there is no plaintext to return to.
    operations = [
        migrations.RunPython(forwards),
    ]
