from bs4 import BeautifulSoup

ALLOWED_TAGS = {
    'p', 'br', 'strong', 'b', 'em', 'i', 'u', 's', 'del', 'ins',
    'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
    'ul', 'ol', 'li', 'blockquote', 'pre', 'code',
    'a', 'img', 'table', 'thead', 'tbody', 'tr', 'th', 'td',
    'hr', 'span', 'div', 'sup', 'sub', 'figure', 'figcaption',
}

ALLOWED_ATTRS = {
    'a': {'href', 'title', 'target', 'rel'},
    'img': {'src', 'alt', 'width', 'height', 'loading'},
    'td': {'colspan', 'rowspan'},
    'th': {'colspan', 'rowspan'},
    'span': {'style'},
    'div': {'style'},
    'p': {'style'},
}

DANGEROUS_SCHEMES = {'javascript', 'data', 'vbscript'}


def sanitize_html(html_str):
    if not html_str:
        return ''
    soup = BeautifulSoup(html_str, 'html.parser')
    for el in soup.descendants:
        if el.name is None:
            continue
        if el.name not in ALLOWED_TAGS:
            el.unwrap()
            continue
        allowed = ALLOWED_ATTRS.get(el.name, set())
        for attr in list(el.attrs):
            if attr not in allowed:
                del el[attr]
            elif attr == 'href':
                val = el[attr] or ''
                if any(val.lower().startswith(s + ':') for s in DANGEROUS_SCHEMES):
                    el[attr] = '#blocked'
            elif attr == 'style' and el.get('style', ''):
                if any(kw in el['style'].lower() for kw in ('expression', 'javascript', 'behavior')):
                    del el['style']
    return str(soup)
