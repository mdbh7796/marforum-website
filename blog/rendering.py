import bleach
import markdown

ALLOWED_TAGS = [
    'p', 'br', 'hr', 'strong', 'em', 'u', 's', 'del', 'ins', 'sub', 'sup',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li',
    'blockquote', 'code', 'pre', 'tt', 'kbd', 'samp', 'var',
    'a', 'img', 'span', 'div',
    'table', 'thead', 'tbody', 'tfoot', 'tr', 'th', 'td', 'caption',
]

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'rel', 'target'],
    'img': ['src', 'alt', 'title', 'width', 'height'],
    'th': ['align', 'colspan', 'rowspan'],
    'td': ['align', 'colspan', 'rowspan'],
    'code': ['class'],
    'pre': ['class'],
    'span': ['class'],
    'div': ['class'],
}

ALLOWED_PROTOCOLS = ['http', 'https', 'mailto']


def render_markdown(content):
    html = markdown.markdown(
        content or '',
        extensions=['fenced_code', 'codehilite', 'tables', 'nl2br']
    )
    return bleach.clean(
        html,
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )