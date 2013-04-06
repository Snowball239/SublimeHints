# vim: set fileencoding=utf-8 :

import tempfile
import webbrowser
import os

from SublimeHints import HintsRenderer, SublimeUtilMixin, PLUGIN_DIRECTORY
from jinja2 import Environment, FileSystemLoader, escape, Markup, contextfilter

VIEWER_DIRECTORY = os.path.join('viewers', 'browser')
env = Environment(loader=FileSystemLoader(os.path.join(PLUGIN_DIRECTORY, VIEWER_DIRECTORY, 'templates')))
env.globals['static_files_dir'] = os.path.join(PLUGIN_DIRECTORY, VIEWER_DIRECTORY, 'static')

@contextfilter
def inject_hints(context, code):
    def region_to_pair(region):
        return (region.begin(), region.end())
    if 'hints' not in context:
        return escape(code)
    hints = context['hints']
    bounds = set([0, len(code)])
    for hint in hints:
        hint.places = map(region_to_pair, hint.places)
        bounds.update(*hint.places)
    bounds = sorted(list(bounds))
    regions = zip(bounds[:-1], bounds[1:])
    code_chunks = []
    for start, end in regions:
        escaped_fragment = escape(code[start:end])
        if not escaped_fragment:
            continue
        classes = []
        for i, hint in enumerate(hints):
            if filter(lambda p: p[0] <= start and end <= p[1], hint.places):
                classes.append('hint%d' % i)
        if classes:
            escaped_fragment = '<span class="%s">%s</span>' % (' '.join(classes), escaped_fragment)
        code_chunks.append(escaped_fragment)

    preprocessed = ''.join(code_chunks)
    if context.eval_ctx.autoescape:
        return Markup(preprocessed)
    return preprocessed

env.filters['inject_hints'] = inject_hints


class BrowserViewCommand(SublimeUtilMixin, HintsRenderer):
    def render(self, hints_file):
        print 'In browser_view command'
        _, tmp_file = tempfile.mkstemp(suffix='.xhtml')
        env.get_template('layout.xhtml').stream(
            title='stub',
            code=self.file_content(),
            hints=hints_file.hints
        ).dump(tmp_file, encoding='utf-8')
        webbrowser.open_new_tab(tmp_file)
