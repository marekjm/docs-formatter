#!/usr/bin/env python3

import datetime
import json
import os
import re
import shutil
import sys
import textwrap

try:
    import colored
except ImportError:
    colored = None


__version__ = '0.0.7'
__commit__ = 'HEAD'


# Available rendering modes.
RENDERING_MODE_ASCII_ART = 'RENDERING_MODE_ASCII_ART'
RENDERING_MODE_HTML_ASCII_ART = 'RENDERING_MODE_HTML_ASCII_ART'
RENDERING_MODE_HTML = 'RENDERING_MODE_HTML'

# Selected rendering mode.
RENDERING_MODE = os.environ.get('RENDERING_MODE', RENDERING_MODE_ASCII_ART)

RENDERED_LINES = []
_preserved_old_print = print
def print(*args, **kwargs):
    RENDERED_LINES.append(' '.join(args))


COLOR_SECTION_INDEX = 'red'
COLOR_SECTION_NAME = 'light_yellow'
COLOR_SECTION_SLUG = 'green'
COLOR_REF = 'green'
COLOR_SOURCE = 'light_green'

def colorise(text, color):
    if RENDERING_MODE == RENDERING_MODE_HTML_ASCII_ART:
        if os.environ.get('COLOR') != 'no':
            return '<span style="color: {color};">{text}</span>'.format(color = color, text = str(text).replace('<', '&lt;').replace('>', '&gt;'))
        return str(text)
    if colored is None or os.environ.get('COLOR') == 'no':
        return str(text)
    return (colored.fg(color) + str(text) + colored.attr('reset'))


DEBUG_LONGEN = False
def longen_line(line, width):
    chunks = line.split()
    length_of_chunks = len(''.join(chunks))
    spaces_to_fill = (width - length_of_chunks)
    no_of_splits = len(chunks) - 1
    spaces_per_split = (spaces_to_fill // (no_of_splits or 1))
    spaces_left = (spaces_to_fill - (spaces_per_split * no_of_splits))
    no_of_double_spaces = spaces_left

    if DEBUG_LONGEN:
        sys.stderr.write('---- for line: {}\n'.format(repr(line)))
        sys.stderr.write('length_of_chunks = {}\n'.format(length_of_chunks))
        sys.stderr.write('spaces_to_fill = {}\n'.format(spaces_to_fill))
        sys.stderr.write('no_of_splits = {}\n'.format(no_of_splits))
        sys.stderr.write('spaces_per_split = {}\n'.format(spaces_per_split))
        sys.stderr.write('spaces_left = {}\n'.format(spaces_left))

    new_line = [chunks[0]]

    normal_spacing = ('  ' if spaces_per_split == 2 else ' ')
    for each in chunks[1:]:
        if no_of_double_spaces:
            new_line.append('  ')
            no_of_double_spaces -= 1
        else:
            new_line.append(normal_spacing)
        new_line.append(each)

    new_line = ''.join(new_line)

    # If the desired width was not reached, do not introduce any "double spaces" and
    # just return the simples representation possible.
    if len(new_line) != width:
        new_line = ' '.join(chunks)

    if DEBUG_LONGEN:
        new_line = '[{}:{}] {}'.format(len(new_line), width, new_line)
    return new_line

def longen(lines, width):
    return [longen_line(each, width) for each in lines]


RENDER_TIMESTAMP = os.environ.get('RENDER_TIMESTAMP', 'none')
MARGIN_COLUMNS = 2
LINE_WIDTH = int(os.popen('stty size', 'r').read().split()[1])
if 'RENDER_COLUMNS' in os.environ:
    x = os.environ.get('RENDER_COLUMNS', LINE_WIDTH)
    if x.startswith('<'):
        LINE_WIDTH = min(LINE_WIDTH, int(x[1:]))
    else:
        LINE_WIDTH = int(x)
LINE_WIDTH -= MARGIN_COLUMNS

TOP_MARKER = '^^^^'
# See https://www.unicode.org/charts/beta/nameslist/n_2190.html
# 21B5 ↵ Downwards Arrow With Corner Leftwards
NEWLINE_MARKER = '↵'
INDENT_MARKER = '   '
NESTED_CALL_MARKER = '↳ '


TITLE = None


REFS_FILE = os.path.join('.', 'refs.json')
REFS = None
REF_NOT_FOUND_MARKER = '????'
if os.path.isfile(REFS_FILE):
    with open(REFS_FILE) as ifstream:
        REFS = json.loads(ifstream.read())


def stringify_encoding(encoding):
    stringified = []

    size_so_far = 0
    for each in encoding:
        if each == '@opcode':
            head = '{} ... {}'.format(size_so_far, size_so_far + 7)
            size_so_far += 8
            stringified.append(
                (head, 'OP',),
            )
        elif each == '@register':
            head = '{} ... {}'.format(size_so_far, size_so_far + 7)
            size_so_far += 8
            stringified.append(
                (head, 'AS',),
            )

            head = '{} ... {}'.format(size_so_far, size_so_far + 7)
            size_so_far += 8
            stringified.append(
                (head, 'RS',),
            )

    max_lengths = list(map(lambda pair: max(len(pair[0]), len(pair[1])), stringified))
    heads = []
    bodies = []
    for i, each in enumerate(stringified):
        head, body = each
        heads.append(head.center(max_lengths[i]))
        bodies.append(body.center(max_lengths[i]))

    return (
        size_so_far,
        '| {} |'.format(' | '.join(heads)),
        '| {} |'.format(' | '.join(bodies))
    )


DEFAULT_INDENT_WIDTH = 2
COMMENT_MARKER = '%%'
KEYWORD_REFLOW_OFF_REGEX = re.compile(r'\\reflow{off}')
KEYWORD_REFLOW_ON_REGEX = re.compile(r'\\reflow{on}')
KEYWORD_SOURCE_BEGIN_REGEX = re.compile(r'\\source{begin}')
KEYWORD_SOURCE_END_REGEX = re.compile(r'\\source{end}')
KEYWORD_WRAP_BEGIN_REGEX = re.compile(r'\\wrap{begin}')
KEYWORD_WRAP_END_REGEX = re.compile(r'\\wrap{end}')
KEYWORD_LIST_BEGIN_REGEX = re.compile(r'\\list{begin}')
KEYWORD_LIST_END_REGEX = re.compile(r'\\list{end}')
KEYWORD_LISTED_BEGIN_REGEX = re.compile(r'\\listed{begin}')
KEYWORD_LISTED_END_REGEX = re.compile(r'\\listed{end}')
KEYWORD_ITEM_REGEX = re.compile(r'\\item')
KEYWORD_INDENT_REGEX = re.compile(r'\\indent{(\d*)}')
KEYWORD_DEDENT_REGEX = re.compile(r'\\dedent{(\d*|all)}')
KEYWORD_SECTION_BEGIN_REGEX = re.compile(r'\\section{begin}')
KEYWORD_SECTION_END_REGEX = re.compile(r'\\section{end}')
KEYWORD_HEADING_REGEX = re.compile(r'\\heading{([^}]+)}')
PARAMETER_REGEX = re.compile(r'{([a-z_]+)(?:(=[^}]*))?}')
KEYWORD_INSTRUCTION_REGEX = re.compile(r'\\instruction{([a-z]+)}')
KEYWORD_SYNTAX_REGEX = re.compile(r'\\syntax{([0-9]+)}')
KEYWORD_REF_REGEX = re.compile(r'\\ref{([a-z_][a-z0-9_]*(?:[:.][a-z0-9_]+)*)}')
KEYWORD_NAMEREF_REGEX = re.compile(r'\\nameref{([a-z_][a-z0-9_]*(?:[:.][a-z_][a-z0-9_]*)*)}')
KEYWORD_COLOR_REGEX = re.compile(r'\\color{([a-z]+)}{([^}]+)}')
KEYWORD_INCLUDE = re.compile(r'\\include{(.*)}')
KEYWORD_TITLE_REGEX = re.compile(r'\\title{(.*)}')
KEYWORD_HORIZONTAL_SEPARATOR = r'\hr'
KEYWORD_EMPTY_LINE = r'\emptyline'
KEYWORD_CALLSEQUENCE_BEGIN = r'\callsequence{begin}'
KEYWORD_CALLSEQUENCE_END = r'\callsequence{end}'
KEYWORD_CALL_BEGIN = r'\call{begin}'
KEYWORD_CALL_END = r'\call{end}'
KEYWORD_CALLOF = re.compile(r'\\callof{(.*)}')
def paragraph_visible(para):
    para = (para[0] if para else None)
    if para is None:
        return True
    if para == r'\reflow{off}' or para == r'\reflow{on}':
        return False
    if para == r'\section{begin}' or para == r'\section{end}':
        return False
    if KEYWORD_INDENT_REGEX.match(para) or KEYWORD_DEDENT_REGEX.match(para):
        return False
    return True


def into_paragraphs(text):
    raw_lines = text.splitlines()
    paragraphs = []
    para = []

    lines = []
    for each in raw_lines:
        if lines and lines[-1] and (lines[-1][-1] == '\\' and lines[-1][-2] != '\\'):
            lines[-1] = lines[-1][:-1] + each
            continue
        if lines and lines[-1] and (lines[-1][-1] == '\\' and lines[-1][-2] == '\\'):
            lines[-1] = lines[-1][:-1]

        lines.append(each)

    for each in lines:
        if not each:
            if para:
                paragraphs.append(para)
            para = []

            # No reason to append breaking paragraph after an invisible one.
            if (not paragraphs) or not paragraph_visible(paragraphs[-1]):
                continue

            # If the last paragraph is also empty, push only one paragraph-break.
            if not paragraphs[-1]:
                continue

            # Append the paragraph, and the paragraph-break after it.
            # Empty lines on their own introduce paragraph breaks.
            # Use \break on its own to introduce line-break without an empty line.
            paragraphs.append([])

            continue
        if each == r'\toc{overview}':
            if para:
                paragraphs.append(para)
            para = []
            paragraphs.append([r'\toc{overview}'])
            continue
        if each == r'\toc{full}':
            if para:
                paragraphs.append(para)
            para = []
            paragraphs.append([r'\toc{full}'])
            continue
        if each == r'\break':
            paragraphs.append(para)
            para = []
            continue
        if each == r'\reflow{off}' or each == r'\reflow{on}':
            if para:
                paragraphs.append(para)
            paragraphs.append([each])
            para = []
            continue
        if each == KEYWORD_LIST_BEGIN_REGEX.match(each) or each == r'\list{end}':
            if para:
                paragraphs.append(para)
            paragraphs.append([each])
            para = []
            continue
        if KEYWORD_LISTED_BEGIN_REGEX.match(each) or each == r'\listed{end}':
            if para:
                paragraphs.append(para)
            paragraphs.append([each])
            para = []
            continue
        if each == r'\item':
            if para:
                paragraphs.append(para)
            paragraphs.append([each])
            para = []
            continue
        if each == r'\wrap{begin}' or each == r'\wrap{end}':
            if para:
                paragraphs.append(para)
            paragraphs.append([each])
            para = []
            continue
        if each == r'\section{begin}' or each == r'\section{end}':
            if para:
                paragraphs.append(para)
            paragraphs.append([each])
            para = []
            continue
        if KEYWORD_SOURCE_BEGIN_REGEX.match(each) or KEYWORD_SOURCE_END_REGEX.match(each):
            if para:
                paragraphs.append(para)
            paragraphs.append([each])
            para = []
            continue
        if KEYWORD_INDENT_REGEX.match(each) or KEYWORD_DEDENT_REGEX.match(each):
            if para:
                paragraphs.append(para)
            paragraphs.append([each])
            para = []
            continue
        if KEYWORD_HEADING_REGEX.match(each):
            if para:
                paragraphs.append(para)
            paragraphs.append([])
            paragraphs.append([each])
            paragraphs.append([])
            para = []
            continue
        if KEYWORD_TITLE_REGEX.match(each):
            global TITLE
            if TITLE is not None:
                raise Exception('title already set to {}'.format(repr(TITLE)))
            TITLE = KEYWORD_TITLE_REGEX.match(each).group(1)
            continue
        if KEYWORD_HORIZONTAL_SEPARATOR == each:
            if para:
                paragraphs.append(para)
            paragraphs.append([each])
            para = []
            continue
        if KEYWORD_EMPTY_LINE == each:
            if para:
                paragraphs.append(para)
            para = []
            continue
        if KEYWORD_CALLSEQUENCE_BEGIN == each or KEYWORD_CALLSEQUENCE_END == each:
            if para:
                paragraphs.append(para)
            paragraphs.append([each])
            para = []
            continue
        if KEYWORD_CALL_BEGIN == each or KEYWORD_CALL_END == each:
            if para:
                paragraphs.append(para)
            paragraphs.append([each])
            para = []
            continue
        if KEYWORD_CALLOF.match(each):
            if para:
                paragraphs.append(para)
            paragraphs.append([each])
            para = []
            continue
        if each.startswith(COMMENT_MARKER):
            continue
        para.append(each)
    if para:
        paragraphs.append(para)

    return ['\n'.join(each) for each in paragraphs]


class SectionTracker:
    class TooManyEnds(Exception):
        pass

    def __init__(self, start_counting_at = 0):
        self._start_counting_at = start_counting_at
        self._depth = 0
        self._path = []
        self._counters = { '': self._start_counting_at, }
        self._recorded_headings = []

    def data(self):
        recorded = self._recorded_headings
        indexes = {}
        for each in recorded:
            indexes[each[0]] = each
        labels = {}
        for each in recorded:
            if each[4] is None:
                continue
            labels[each[4]] = {
                'index': each[0],
                'extra': each[3],
                'name': each[1],
            }
        refs = {
            'recorded': recorded,
            'indexes': indexes,
            'labels': labels,
        }
        return refs

    def depth(self):
        return self._depth

    def recorded_headings(self):
        return self._recorded_headings

    def slug(self, index, ref = None):
        return (ref or index).replace('.', '-')

    def current_base_index(self):
        return '.'.join(map(str, self._path))

    def heading(self, text, noise = False, extra = None, ref = None):
        base_index = self.current_base_index()
        counter_at_base_index = self._counters[base_index]

        index = '{base}{sep}{counter}'.format(
            base = base_index,
            sep = ('.' if base_index else ''),
            counter = counter_at_base_index,
        )
        self._recorded_headings.append( (index, text, noise, extra, ref,) )

        self._counters[base_index] += 1

        return index

    def begin(self):
        # This marker is only useful for tracking how many sections were opened to
        # prevent calling .end() too many times.
        self._depth += 1

        current_index = self.current_base_index()
        counter = self._counters[current_index] - 1
        self._path.append(counter)

        base_index = self.current_base_index()
        if base_index not in self._counters:
            self._counters[base_index] = self._start_counting_at

    def end(self):
        if self._depth == 0:
            raise SectionTracker.TooManyEnds()
        self._depth -= 1
        self._path.pop()
section_tracker = SectionTracker(1)


class InvalidReference(Exception):
    pass

class UnknownInstruction(Exception):
    pass

class UnknownArgument(Exception):
    pass

class MissingArgument(Exception):
    pass


def parse_and_expand(text, syntax, documented_instructions):
    expanded_text = text

    reg = re.compile(r'\\syntax{(\d+)}')
    found_syntax_refs = re.findall(reg, text)
    for i in found_syntax_refs:
        if int(i) >= len(syntax):
            raise InvalidReference('invalid syntax reference: \\syntax{{{}}}\n'.format(i))
        expanded_text = expanded_text.replace((r'\syntax{' + i + '}'), syntax[int(i)])

    found_instruction_refs = re.compile(r'\\instruction{([a-z]+)}').findall(expanded_text)
    for each in found_instruction_refs:
        if each not in documented_instructions:
            raise UnknownInstruction(each)
        pat = (r'\instruction{' + each + '}')
        replacement = each
        if RENDERING_MODE == RENDERING_MODE_HTML_ASCII_ART:
            for a in REFS['recorded']:
                if a[3] is None:
                    continue
                if a[3].get('instruction') and a[1] == each.upper():
                    replacement = '<a href="#{location}">{name}</a>'.format(
                        location = a[0].replace('.', '-'),
                        name = each,
                    )
                    break
        expanded_text = expanded_text.replace(pat, replacement)

    found_colorisations = re.compile(r'\\color{([a-z]+)}{([^}]+)}').findall(expanded_text)
    for each in found_colorisations:
        color, text = each
        pat = (r'\color{' + color + '}{' + text + '}')
        expanded_text = expanded_text.replace(pat, colorise(text, color))

    found_refs = re.compile(r'\\ref{([a-z_][a-z0-9_]*(?::[a-z_][a-z0-9_]*)*)}').findall(expanded_text)
    for each in found_refs:
        if REFS is not None and each not in REFS['labels']:
            raise InvalidReference('invalid reference: \\ref{{{}}}\n'.format(each))
        replacement = (REFS['labels'][each].get('index') if REFS is not None else None)
        if RENDERING_MODE == RENDERING_MODE_HTML_ASCII_ART:
            replacement = '<a href="#{location}">{name}</a>'.format(
                location = (replacement or REF_NOT_FOUND_MARKER).replace('.', '-'),
                name = replacement,
            )
        expanded_text = expanded_text.replace(
            (r'\ref{' + each + '}'),
            (replacement or REF_NOT_FOUND_MARKER),
        )

    found_name_refs = re.compile(r'\\nameref{([a-z_][a-z0-9_]*(?::[a-z_][a-z0-9_]*)*)}').findall(expanded_text)
    for each in found_refs:
        if REFS is not None and each not in REFS['labels']:
            raise InvalidReference('invalid reference: \\nameref{{{}}}\n'.format(each))
        replacement = (REFS['labels'][each].get('name') if REFS is not None else None)
        if RENDERING_MODE == RENDERING_MODE_HTML_ASCII_ART:
            replacement = '<a href="#{location}">{name}</a>'.format(
                location = (replacement or REF_NOT_FOUND_MARKER).replace('.', '-'),
                name = replacement,
            )
        else:
            replacement = colorise(replacement, COLOR_REF)
        expanded_text = expanded_text.replace(
            (r'\nameref{' + each + '}'),
            (replacement or REF_NOT_FOUND_MARKER),
        )

    return expanded_text

def render_multiline_heading(heading_text, index, indent, noise, extra, ref):
    format_line_title = '{prefix}[{index}] {text}'
    format_line_ref = '{prefix}{index_prefix}{ref}'
    ref_name = ''
    if ref is not None:
        ref_name = ' {{{}}}'.format(colorise(ref, COLOR_SECTION_SLUG))
    top_marker = ''
    top_marker_spacing = ''

    slug = section_tracker.slug(index, ref)
    index_slug = index.replace('.', '-')
    index_prefix = len(index) + 2   # +2 for '[' and ']'

    if RENDERING_MODE == RENDERING_MODE_HTML_ASCII_ART:
        format_line_title = '{prefix}[{index}] <a id="{slug}"><a id="{index_slug}"></a><a href="#{slug}">{text}</a>{top_marker_spacing}{top_marker}'
        if slug == index_slug:
            format_line_title = '{prefix}[{index}] <a id="{index_slug}"></a><a href="#{slug}">{text}</a>{top_marker_spacing}{top_marker}'
        format_line_ref = '{prefix}{index_prefix}{ref}'
        top_marker_spacing = (' ' * (LINE_WIDTH - indent - len(index) - len(heading_text) - 1 -
            len(TOP_MARKER) - 2))
        top_marker = '<a href="#0">{}</a>'.format(TOP_MARKER)

    print(format_line_title.format(
        prefix = (' ' * indent),
        index = colorise(index, COLOR_SECTION_INDEX),
        index_slug = index,
        slug = slug,
        text = colorise(heading_text, COLOR_SECTION_NAME),
        top_marker = top_marker,
        top_marker_spacing = top_marker_spacing,
    ))
    print(format_line_ref.format(
        prefix = (' ' * indent),
        index_prefix = (' ' * index_prefix),
        ref = ref_name,
    ))

def render_heading(heading_text, indent, noise = False, extra = None, ref = None):
    format_line = '{prefix}[{index}] {text}{ref}'
    index = section_tracker.heading(heading_text, noise = noise, extra = extra, ref = ref)
    ref_name = ''
    if ref is not None:
        ref_name = ' {{{}}}'.format(ref)
    top_marker = ''
    top_marker_spacing = ''

    slug = section_tracker.slug(index, ref)
    index_slug = index.replace('.', '-')
    index_prefix = len(index) + 2

    if RENDERING_MODE == RENDERING_MODE_HTML_ASCII_ART:
        format_line = '{prefix}[{index}] <a id="{slug}"></a><a id="{index_slug}"></a><a href="#{slug}"><strong>{text}</strong></a>{ref}{top_marker_spacing}{top_marker}'
        if slug == index_slug:
            format_line = '{prefix}[{index}] <a id="{index_slug}"></a><a href="#{slug}"><strong>{text}</strong></a>{ref}{top_marker_spacing}{top_marker}'
        top_marker_spacing = (
            ' ' *
            (LINE_WIDTH - indent - len(index) - len(heading_text) - len(ref_name) - 1 - len(TOP_MARKER) - 2)
        )
        top_marker = '<a href="#0">{}</a>'.format(TOP_MARKER)

    rendered_line = format_line.format(
        prefix = (' ' * indent),
        index = colorise(index, COLOR_SECTION_INDEX),
        index_slug = index_slug,
        slug = slug,
        text = colorise(heading_text, COLOR_SECTION_NAME),
        ref = (
            ' {{{}}}'.format(colorise(ref, COLOR_SECTION_SLUG))
            if ref is not None else
            ''
        ),
        top_marker = top_marker,
        top_marker_spacing = top_marker_spacing,
    )

    visible_width = indent + index_prefix + 1 + len(section_tracker.slug(index, ref)) + len(ref_name)
    if visible_width >= (LINE_WIDTH - len(TOP_MARKER)):
        return render_multiline_heading(heading_text, index, indent, noise, extra, ref)

    print(rendered_line)

class Types:
    @staticmethod
    def boolean(value):
        if value == 'true':
            return True
        elif value == 'false':
            return False
        else:
            raise ArgumentError(value)

    @staticmethod
    def integer(value):
        try:
            return int(value)
        except Exception:
            raise ArgumentError(value)

    @staticmethod
    def string(value):
        return value

    @staticmethod
    def any(value):
        return value

    @staticmethod
    def stringify(something):
        if something is Types.boolean:
            return 'boolean'
        elif something is Types.any:
            return 'any'

def build_params(raw, description, required = (), default = None):
    params = {}
    for key, value in raw:
        if not value:
            value = None

        if key not in description:
            raise UnknownArgument(key, value)

        if value is None:
            value = 'true'
        else:
            # Cut the '='
            value = value[1:]

        params[key] = description[key](value)

    if default is not None:
        for key, value in default.items():
            if key not in params:
                params[key] = value

    for each in required:
        if each not in params:
            raise MissingArgument(each + ' : ' + Types.stringify(description[each]))

    return params

def text_reflow(text, indent):
    return '\n'.join(longen(textwrap.wrap(text,
        width=(LINE_WIDTH - indent)),
        width=(LINE_WIDTH - indent))
    )

def text_wrap(text, indent):
    lines = text.split('\n')
    wrapped_lines = []
    wrap_to_length = (LINE_WIDTH - indent)
    for each in lines:
        if len(each) <= wrap_to_length:
            wrapped_lines.append(each)
            continue

        remaining = each
        part = remaining[:wrap_to_length - len(NEWLINE_MARKER)] + NEWLINE_MARKER
        remaining = remaining[wrap_to_length - 1:]
        wrapped_lines.append(part)

        while remaining:
            if len(remaining) <= (wrap_to_length - len(INDENT_MARKER)):
                part = (INDENT_MARKER + remaining[:wrap_to_length - len(INDENT_MARKER)])
                remaining = remaining[wrap_to_length - len(INDENT_MARKER):]
            else:
                part = (INDENT_MARKER + remaining[:wrap_to_length - 1 - len(INDENT_MARKER)] + NEWLINE_MARKER)
                remaining = remaining[wrap_to_length - 1 - len(INDENT_MARKER):]
            wrapped_lines.append(part)
    return '\n'.join(wrapped_lines)

class RENDERING_MODE_ASCII_RENDERER:
    @staticmethod
    def render(text, syntax, documented_instructions):
        m = KEYWORD_SYNTAX_REGEX.match(text)
        if m:
            i = int(m.group(1))
            if i >= len(syntax):
                raise InvalidReference(
                    'invalid syntax reference: \\syntax{{{}}}'.format(i)
                )
            return "`{}'".format(syntax[i])

        m = KEYWORD_INSTRUCTION_REGEX.match(text)
        if m:
            instruction = m.group(1)
            if instruction not in documented_instructions:
                raise UnknownInstruction(instruction)
            return instruction

        m = KEYWORD_REF_REGEX.match(text)
        if m:
            name = m.group(1)
            if REFS is not None and name not in REFS['labels']:
                raise InvalidReference('invalid reference: \\ref{{{}}}\n'.format(name))
            replacement = (REFS['labels'][name].get('index') if REFS is not None else None)
            return (
                colorise(replacement, COLOR_REF)
                if replacement is not None else
                REF_NOT_FOUND_MARKER
            )

        m = KEYWORD_NAMEREF_REGEX.match(text)
        if m:
            name = m.group(1)
            if REFS is not None and name not in REFS['labels']:
                raise InvalidReference('invalid reference: \\nameref{{{}}}\n'.format(name))
            replacement = (REFS['labels'][name].get('name') if REFS is not None else None)
            return (
                colorise(replacement, COLOR_REF)
                if replacement is not None else
                REF_NOT_FOUND_MARKER
            )

        m = KEYWORD_COLOR_REGEX.match(text)
        if m:
            color = m.group(1)
            content = m.group(2)
            return colorise(text, color)
        return text

    @staticmethod
    def length(text, syntax, documented_instructions):
        m = KEYWORD_SYNTAX_REGEX.match(text)
        if m:
            i = int(m.group(1))
            if i >= len(syntax):
                raise InvalidReference(
                    'invalid syntax reference: \\syntax{{{}}}'.format(i)
                )
            return len(syntax[i]) + 2

        m = KEYWORD_INSTRUCTION_REGEX.match(text)
        if m:
            instruction = m.group(1)
            if instruction not in documented_instructions:
                raise UnknownInstruction(instruction)
            return len(instruction)

        m = KEYWORD_REF_REGEX.match(text)
        if m:
            name = m.group(1)
            if REFS is not None and name not in REFS['labels']:
                raise InvalidReference('invalid reference: \\ref{{{}}}\n'.format(name))
            replacement = (REFS['labels'][name].get('index') if REFS is not None else None)
            return len(replacement or REF_NOT_FOUND_MARKER)

        m = KEYWORD_NAMEREF_REGEX.match(text)
        if m:
            name = m.group(1)
            if REFS is not None and name not in REFS['labels']:
                raise InvalidReference('invalid reference: \\ref{{{}}}\n'.format(name))
            replacement = (REFS['labels'][name].get('name') if REFS is not None else None)
            return len(replacement or REF_NOT_FOUND_MARKER)

        m = KEYWORD_COLOR_REGEX.match(text)
        if m:
            content = m.group(2)
            return len(content)
        return len(text)

class RENDERING_MODE_HTML_ASCII_ART_RENDERER:
    @staticmethod
    def render(text, syntax, documented_instructions):
        m = KEYWORD_SYNTAX_REGEX.match(text)
        if m:
            i = int(m.group(1))
            if i >= len(syntax):
                raise InvalidReference(
                    'invalid syntax reference: \\syntax{{{}}}'.format(i)
                )
            return "`{}'".format(syntax[i])

        m = KEYWORD_INSTRUCTION_REGEX.match(text)
        if m:
            instruction = m.group(1)
            if instruction not in documented_instructions:
                raise UnknownInstruction(instruction)
            replacement = instruction
            for a in REFS['recorded']:
                if a[3] is None:
                    continue
                if a[3].get('instruction') and a[1] == instruction.upper():
                    replacement = '<a href="#{location}">{name}</a>'.format(
                        location = a[0].replace('.', '-'),
                        name = instruction,
                    )
                    break
            return replacement

        m = KEYWORD_REF_REGEX.match(text)
        if m:
            name = m.group(1)
            if REFS is not None and name not in REFS['labels']:
                raise InvalidReference('invalid reference: \\ref{{{}}}\n'.format(name))
            replacement = (REFS['labels'][name].get('index') if REFS is not None else REF_NOT_FOUND_MARKER)
            replacement = '<a href="#{location}">{name}</a>'.format(
                location = replacement.replace('.', '-'),
                name = replacement,
            )
            return replacement

        m = KEYWORD_NAMEREF_REGEX.match(text)
        if m:
            name = m.group(1)
            if REFS is not None and name not in REFS['labels']:
                raise InvalidReference('invalid reference: \\ref{{{}}}\n'.format(name))
            location = (REFS['labels'][name].get('index') if REFS is not None else REF_NOT_FOUND_MARKER)
            replacement = (REFS['labels'][name].get('name') if REFS is not None else REF_NOT_FOUND_MARKER)
            replacement = '<a href="#{location}">{name}</a>'.format(
                location = location.replace('.', '-'),
                name = replacement,
            )
            return replacement

        m = KEYWORD_COLOR_REGEX.match(text)
        if m:
            color = m.group(1)
            content = m.group(2)
            return colorise(content, color)

        text = text.replace('<', '&lt;').replace('>', '&gt;')
        return text

    @staticmethod
    def length(text, syntax, documented_instructions):
        m = KEYWORD_SYNTAX_REGEX.match(text)
        if m:
            i = int(m.group(1))
            if i >= len(syntax):
                raise InvalidReference(
                    'invalid syntax reference: \\syntax{{{}}}'.format(i)
                )
            return len(syntax[i]) + 2

        m = KEYWORD_INSTRUCTION_REGEX.match(text)
        if m:
            instruction = m.group(1)
            if instruction not in documented_instructions:
                raise UnknownInstruction(instruction)
            return len(instruction)

        m = KEYWORD_REF_REGEX.match(text)
        if m:
            name = m.group(1)
            if REFS is not None and name not in REFS['labels']:
                raise InvalidReference('invalid reference: \\ref{{{}}}\n'.format(name))
            replacement = (REFS['labels'][name].get('index') if REFS is not None else None)
            return len(replacement or REF_NOT_FOUND_MARKER)

        m = KEYWORD_NAMEREF_REGEX.match(text)
        if m:
            name = m.group(1)
            if REFS is not None and name not in REFS['labels']:
                raise InvalidReference('invalid reference: \\ref{{{}}}\n'.format(name))
            replacement = (REFS['labels'][name].get('name') if REFS is not None else None)
            return len(replacement or REF_NOT_FOUND_MARKER)

        m = KEYWORD_COLOR_REGEX.match(text)
        if m:
            content = m.group(2)
            return len(content)
        return len(text)

class Token:
    def __init__(self, text):
        self._text = text

    def __repr__(self):
        return repr(self._text)

    def render(self, syntax, documented_instructions):
        if RENDERING_MODE == RENDERING_MODE_ASCII_ART:
            return RENDERING_MODE_ASCII_RENDERER.render(
                text = self._text,
                syntax = syntax,
                documented_instructions = documented_instructions,
            )
        if RENDERING_MODE == RENDERING_MODE_HTML_ASCII_ART:
            return RENDERING_MODE_HTML_ASCII_ART_RENDERER.render(
                text = self._text,
                syntax = syntax,
                documented_instructions = documented_instructions,
            )

    def length(self, syntax, documented_instructions):
        if RENDERING_MODE == RENDERING_MODE_ASCII_ART:
            return RENDERING_MODE_ASCII_RENDERER.length(
                text = self._text,
                syntax = syntax,
                documented_instructions = documented_instructions,
            )
        if RENDERING_MODE == RENDERING_MODE_HTML_ASCII_ART:
            return RENDERING_MODE_HTML_ASCII_ART_RENDERER.length(
                text = self._text,
                syntax = syntax,
                documented_instructions = documented_instructions,
            )

TOKENS_THAT_SHOULD_NOT_BE_PRECEDED_BY_WHITESPACE = (
    '.',
    ',',
    ')',
)
TOKENS_THAT_SHOULD_NOT_BE_SUCCEEDED_BY_WHITESPACE = (
    '(',
)
def simple_join_with_spaces(chunks):
    if not chunks:
        return ''

    new_line = [chunks[0]['rendered']]
    for each in chunks[1:]:
        text = each['rendered']
        if (text[0] not in TOKENS_THAT_SHOULD_NOT_BE_PRECEDED_BY_WHITESPACE) and (new_line[-1] not in
                TOKENS_THAT_SHOULD_NOT_BE_SUCCEEDED_BY_WHITESPACE):
            new_line.append(' ')
        new_line.append(text)
    return ''.join(new_line)

def longen_tokenised_line(chunks, width):
    length_of_chunks = sum(map(lambda x: x['length'], chunks))
    spaces_to_fill = (width - length_of_chunks)
    no_of_splits = len(chunks) - 1
    spaces_per_split = (spaces_to_fill // (no_of_splits or 1))
    spaces_left = (spaces_to_fill - (spaces_per_split * no_of_splits))
    no_of_double_spaces = spaces_left

    if DEBUG_LONGEN:
        sys.stderr.write('length_of_chunks = {}\n'.format(length_of_chunks))
        sys.stderr.write('spaces_to_fill = {}\n'.format(spaces_to_fill))
        sys.stderr.write('no_of_splits = {}\n'.format(no_of_splits))
        sys.stderr.write('spaces_per_split = {}\n'.format(spaces_per_split))
        sys.stderr.write('spaces_left = {}\n'.format(spaces_left))

    if chunks:
        new_line = [chunks[0]['rendered']]
        line_length = chunks[0]['length']
    else:
        new_line = ''
        line_length = 0

    normal_spacing = ('  ' if spaces_per_split == 2 else ' ')
    for each in chunks[1:]:
        text = each['rendered']
        if text[0] not in TOKENS_THAT_SHOULD_NOT_BE_PRECEDED_BY_WHITESPACE:
            if no_of_double_spaces:
                new_line.append('  ')
                line_length += 2
                no_of_double_spaces -= 1
            else:
                new_line.append(normal_spacing)
                line_length += 1
        new_line.append(text)
        line_length += each['length']

    new_line = ''.join(new_line)

    # If the desired width was not reached, do not introduce any "double spaces" and
    # just return the simplest representation possible.
    if line_length != width:
        new_line = simple_join_with_spaces(chunks)

    if DEBUG_LONGEN:
        new_line = '[{}:{}] {}'.format(len(new_line), width, new_line)
    return new_line

def render_tokenised(tokens, syntax, documented_instructions, reflow, wrapping, width):
    stream_of_rendered = []

    for each in tokens:
        rendered_text = each.render(
            syntax = syntax,
            documented_instructions = documented_instructions,
        )
        visible_length = each.length(
            syntax = syntax,
            documented_instructions = documented_instructions,
        )
        stream_of_rendered.append({
            'source': each,
            'rendered': rendered_text,
            'length': visible_length,
        })

    lines = []

    line = []
    length_of_current_line = 0
    for each in stream_of_rendered:
        if (length_of_current_line + each['length']) <= width:
            line.append(each)
            length_of_current_line += (each['length'] + 1)
            continue
        else:
            lines.append(line)
            line = [each]
            length_of_current_line = (line[0]['length'] + 1)
    if line:
        lines.append(line)

    rendered_lines = []
    for l in lines:
        rendered_lines.append(longen_tokenised_line(l, width))

    return rendered_lines

def tokenise(text):
    tokens = []
    tok = ''
    i = 0
    while i < len(text):
        if text[i] == '\n':
            if tok: tokens.append(tok)
            tok = ''
            i += 1
            continue
        if text[i].isspace():
            if tok: tokens.append(tok)
            tok = ''
            i += 1
            continue
        if text[i] != '\\':
            tok += text[i]
            i += 1
            continue
        if tok: tokens.append(tok)
        tok = ''

        m = KEYWORD_INSTRUCTION_REGEX.match(text[i:])
        if m is not None:
            tokens.append(m.group(0))
            i += len(tokens[-1])
            continue

        m = KEYWORD_SYNTAX_REGEX.match(text[i:])
        if m is not None:
            tokens.append(m.group(0))
            i += len(tokens[-1])
            continue

        m = KEYWORD_REF_REGEX.match(text[i:])
        if m is not None:
            tokens.append(m.group(0))
            i += len(tokens[-1])
            continue

        m = KEYWORD_NAMEREF_REGEX.match(text[i:])
        if m is not None:
            tokens.append(m.group(0))
            i += len(tokens[-1])
            continue

        m = KEYWORD_COLOR_REGEX.match(text[i:])
        if m is not None:
            tokens.append(m.group(0))
            i += len(tokens[-1])
            continue

        i += 1
    if tok:
        tokens.append(tok)
    tokens = list(map(Token, tokens))
    return tokens

def render_paragraphs(paragraphs, documented_instructions, syntax = None, indent = 4, section_depth = 0):
    original_indent = indent
    reflow = True
    wrapping = False
    in_source = False

    in_list = False
    in_list_enumerated = False
    in_list_items = 0
    in_list_enumerated_indent = 0
    new_list_item = False
    in_list_index = 0

    in_listed = False
    in_listed_sorted = False
    listed_items = []

    in_callsequence = False
    callsequence_depth = 0

    for each in paragraphs:
        current_content = each

        if each == r'\toc{overview}':
            print(each)
            continue
        if each == r'\toc{full}':
            print(each)
            continue
        if each == r'\reflow{off}':
            reflow = False
            continue
        if each == r'\reflow{on}':
            reflow = True
            continue
        if each == r'\wrap{begin}':
            wrapping = True
            reflow = False
            continue
        if each == r'\wrap{end}':
            wrapping = False
            reflow = True
            continue
        if KEYWORD_SOURCE_BEGIN_REGEX.match(each):
            in_source = True
            wrapping = True
            reflow = False
            indent += 2
            if RENDERING_MODE == RENDERING_MODE_HTML_ASCII_ART:
                print('<div class="source_code_listing">')
            continue
        if KEYWORD_SOURCE_END_REGEX.match(each):
            in_source = False
            wrapping = False
            reflow = True
            indent -= 2
            if RENDERING_MODE == RENDERING_MODE_HTML_ASCII_ART:
                print('')
                print('</div> <!-- source code listing -->')
            continue
        if each.startswith(r'\list{begin}'):
            params = build_params(PARAMETER_REGEX.findall(each[len(r'\list{begin}'):]), {
                'enumerated': Types.boolean,
                'items': Types.integer,
            }, default = {
                'enumerated': False,
                'items': None,
            })


            in_list = True
            in_list_enumerated = params['enumerated']
            in_list_items = params['items']

            if in_list_enumerated and in_list_items is None:
                sys.stderr.write(
                    'error: enumerated list must specify number of items\n')
                sys.stderr.write(
                    'note: the number is given as an order of magnitude, i.e.\n'
                    '      items=n means that at most 10^n items are on the list\n')
                exit(1)

            if in_list_enumerated:
                in_list_items = (10 ** in_list_items)

            in_list_index = 0

            in_list_enumerated_indent = 0
            if in_list_enumerated:
                in_list_enumerated_indent = len(str(in_list_items))
                if in_list_enumerated_indent % 2:
                    in_list_enumerated_indent += 1

            indent += (2 + in_list_enumerated_indent)

            continue
        if each == r'\list{end}':
            in_list = False
            indent -= (2 + in_list_enumerated_indent)
            continue
        if each.startswith(r'\listed{begin}'):
            params = build_params(PARAMETER_REGEX.findall(each[len(r'\listed{begin}'):]), {
                'sorted': Types.boolean,
            }, default = {
                'sorted': False,
            })

            in_listed = True
            in_listed_sorted = params['sorted']
            continue
        if each == r'\listed{end}':
            in_listed = False
            continue
        if each == r'\item':
            new_list_item = True
            in_list_index += 1
            continue
        if KEYWORD_INDENT_REGEX.match(each):
            count = int(KEYWORD_INDENT_REGEX.match(each).group(1) or DEFAULT_INDENT_WIDTH)
            indent += count
            continue
        if KEYWORD_DEDENT_REGEX.match(each):
            count = (KEYWORD_DEDENT_REGEX.match(each).group(1) or str(DEFAULT_INDENT_WIDTH))
            indent = (original_indent if count == 'all' else (indent - int(count)))
            continue
        if each == r'\section{begin}':
            section_tracker.begin()
            # INDENT MODIFICATION
            # indent += DEFAULT_INDENT_WIDTH
            continue
        if each == r'\section{end}':
            section_tracker.end()
            # INDENT MODIFICATION
            # indent -= DEFAULT_INDENT_WIDTH
            continue
        if KEYWORD_HEADING_REGEX.match(each):
            heading_text = KEYWORD_HEADING_REGEX.match(each).group(1)

            # +2 is for { and }
            # +8 is for \heading
            params = build_params(PARAMETER_REGEX.findall(each[len(heading_text) + 2 + 8:]), {
                'noise': Types.boolean,
                'ref': Types.string,
            }, default = {
                'noise': False,
                'ref': None,
            })
            render_heading(heading_text, indent, noise = params['noise'], ref = params['ref'])
            continue
        if each.startswith(COMMENT_MARKER):
            continue
        if KEYWORD_INCLUDE.match(each):
            file_path = KEYWORD_INCLUDE.match(each).group(1)
            with open(file_path, 'r') as ifstream:
                render_free_form_text(
                    ifstream.read(),
                    documented_instructions = [],
                    syntax = None,
                    indent = indent,
                )
            continue
        if KEYWORD_HORIZONTAL_SEPARATOR == each:
            print('{}{}'.format(
                (' ' * indent),
                '-' * (LINE_WIDTH - indent),
            ))
            continue
        if KEYWORD_EMPTY_LINE == each:
            print('')
            continue
        if KEYWORD_CALLSEQUENCE_BEGIN == each:
            in_callsequence = True
            indent += DEFAULT_INDENT_WIDTH
            continue
        if KEYWORD_CALLSEQUENCE_END == each:
            in_callsequence = False
            indent -= DEFAULT_INDENT_WIDTH
            continue
        if KEYWORD_CALL_BEGIN == each:
            indent += DEFAULT_INDENT_WIDTH
            callsequence_depth += 1
            continue
        if KEYWORD_CALL_END == each:
            indent -= DEFAULT_INDENT_WIDTH
            callsequence_depth -= 1
            continue
        if KEYWORD_CALLOF.match(each):
            current_content = KEYWORD_CALLOF.match(each).group(1).strip()
            reflow = False
            if callsequence_depth:
                indent -= DEFAULT_INDENT_WIDTH
                current_content = NESTED_CALL_MARKER + current_content

        current_indent_text = (' ' * indent)

        if KEYWORD_CALLOF.match(each):
            whole_line = current_content + current_indent_text
            if len(whole_line) >= LINE_WIDTH:
                sys.stderr.write('line too long: {} >= {}: {}\n'.format(
                    len(whole_line),
                    LINE_WIDTH,
                    repr(current_content)
                ))

                def simple_lex(text):
                    toks = []
                    i = 0
                    s = ''
                    in_string = False
                    breaking_chars = (
                        '(',
                        ')',
                        '{',
                        '}',
                        ',',
                    )
                    while i < len(text):
                        char = text[i]

                        if char in breaking_chars:
                            if s:
                                toks.append(s)
                                s = ''
                            toks.append(char)
                            i += 1
                            continue

                        s += char
                        i += 1
                    return toks

                def format_indented_args(arg_indent, arg_tokens):
                    braces = (
                        '(',
                        ')',
                        '{',
                        '}',
                    )
                    lines = []

                    grouped_args = []
                    in_struct = False
                    group = []
                    for each in arg_tokens:
                        if each == '{':
                            in_struct = True
                        elif each == '}':
                            in_struct = False
                        elif each == ',' and not in_struct:
                            grouped_args.append(group)
                            group = []

                        group.append(each)
                    grouped_args.append(group)

                    lines.append((' ' * (arg_indent + 2)) + ''.join(grouped_args[0]))
                    lines.extend([((' ' * arg_indent) + ''.join(each)) for each in grouped_args[1:]])

                    return lines

                toks = simple_lex(KEYWORD_CALLOF.match(each).group(1).strip())

                opening = NESTED_CALL_MARKER + toks[0] + toks[1]      # name and opening (
                closing = (' ' * len(NESTED_CALL_MARKER)) + toks[-1]  # closing )
                arg_indent = len(opening)

                lines = []

                if len(toks) > 3:
                    args = toks[2:-1]
                    if len(args) > 1:
                        lines = format_indented_args(arg_indent, args)
                    else:
                        lines.append('{}{}'.format(
                            # Do not use full argument indent since the resulting line
                            # would still be too long (if a single-argument call line
                            # is too long).
                            (' ' * (indent + DEFAULT_INDENT_WIDTH)),
                            args[0],
                        ))

                text = '{}\n'.format('\n'.join([opening] + lines + [closing]))
                text = textwrap.indent(
                    text = text,
                    prefix = current_indent_text,
                )
                print(text)

                reflow = True
                if callsequence_depth:
                    indent += DEFAULT_INDENT_WIDTH

                continue

        if in_listed:
            listed_items.append(current_content)
            continue
        if (not in_listed) and listed_items:
            listed_items = [each.strip() for each in listed_items[0].splitlines()]
            longest_item = max(map(len, listed_items))
            charactes_for_one_item = longest_item + 4

            if in_listed_sorted:
                listed_items = sorted(listed_items)

            def chunks(seq, chunk_length):
                chunked = []

                i = 0
                while i < len(seq):
                    chunked.append(seq[i : i + chunk_length])
                    i += chunk_length

                return chunked

            listed_indent = (indent + DEFAULT_INDENT_WIDTH)
            words_per_chunk = ((LINE_WIDTH - listed_indent) // charactes_for_one_item)

            chunked = chunks(listed_items, chunk_length = words_per_chunk)
            chunked = [list(map(lambda element: element.ljust(charactes_for_one_item), each))
                       for each
                       in chunked]

            text = '\n'.join([''.join(each) for each in chunked])
            text = textwrap.indent(
                text = text,
                prefix = (
                    current_indent_text
                    + (' ' * DEFAULT_INDENT_WIDTH)
                ),
            )
            print(text)

            listed_items = []
            continue

        text = parse_and_expand(current_content, syntax = syntax, documented_instructions = documented_instructions)
        if reflow:
            _ = tokenise(current_content)
            _ = render_tokenised(_,
                syntax = syntax,
                documented_instructions = documented_instructions,
                reflow = reflow,
                wrapping = wrapping,
                width = (LINE_WIDTH - indent),
            )
            text = '\n'.join(_)

        if wrapping:
            text = text_wrap(text, indent)
        text = textwrap.indent(
            text = text,
            prefix = current_indent_text,
        )
        if in_list and new_list_item:
            list_index = '-'
            x = 0
            if in_list_enumerated:
                x = len(str(in_list_items))
                list_index = '{{:{}d}}'.format(x).format(in_list_index)
            text = (
                  current_indent_text[:-(2 + x)]
                + list_index
                + text[indent - 1 - x + (len(list_index) - 1):]
            )
            new_list_item = False

        # We need this because basic replacement is performed as part of the
        # render_tokenised() function which is only called for the "reflow"
        # parts of the text.
        if in_source and (RENDERING_MODE == RENDERING_MODE_HTML_ASCII_ART):
            text = text.replace('<', '&lt;').replace('>', '&gt;')
        if in_source and (RENDERING_MODE != RENDERING_MODE_HTML_ASCII_ART):
            text = '\n'.join(
                colorise(each, COLOR_SOURCE) for each in text.splitlines())

        print(text)

        if KEYWORD_CALLOF.match(each):
            reflow = True
            if callsequence_depth:
                indent += DEFAULT_INDENT_WIDTH

def render_free_form_text(source, documented_instructions, syntax = None, indent = 4):
    return render_paragraphs(
        into_paragraphs(source),
        documented_instructions = documented_instructions,
        syntax = syntax,
        indent = indent
    )

def render_file(path, documented_instructions, indent = DEFAULT_INDENT_WIDTH):
    source = ''
    with open(path) as ifstream:
        source = ifstream.read().strip()
    return render_free_form_text(source, documented_instructions = documented_instructions, indent = indent)

def render_section(section, documented_instructions):
    with open(os.path.join('.', 'sections', section, 'title')) as ifstream:
        title = ifstream.read().strip().splitlines()
        render_heading(title[0], indent = 2, ref = (None if len(title) < 2 else title[1]))
    print()
    res = render_file(
        os.path.join('.', 'sections', section, 'text'),
        documented_instructions = documented_instructions
    )
    print()
    return res


def old_render_view(args):
    # Print introduction, but only if the user requested full documentation.
    # If the user requested docs only for a specific group of instructions, or
    # a list of instructions do not print the introduction.
    # It looks like the user knows what they want anyway.
    if (not args) and selected_group is None:
        print('VIUA VM MANUAL'.center(LINE_WIDTH))
        print()

        print(r'\toc{overview}')
        print()

        print(r'\toc{full}')
        print()

        render_section('introduction', documented_instructions = documented_opcodes)
        render_section('assembly', documented_instructions = documented_opcodes)
        render_section('tooling', documented_instructions = documented_opcodes)
        render_section('the_environment', documented_instructions = documented_opcodes)
        render_section('instruction_set_architecture', documented_instructions = documented_opcodes)

        print('-' * LINE_WIDTH)
        print()


    render_heading('INSTRUCTIONS', DEFAULT_INDENT_WIDTH, ref = 'isa:instructions')
    print()
    section_tracker.begin()

    render_file(
        'instructions',
        indent = 2 * DEFAULT_INDENT_WIDTH,
        documented_instructions = documented_opcodes,
    )
    print()

    # Render documentation for all requested instructions.
    # If no instructions were explicitly requested then print the full documentation.
    first_opcode_being_documented = True
    for each in (args or documented_opcodes):
        # Instructions are grouped into groups.
        # Every instruction is in at least 1 group.
        # If an instruction does not have any explicitly assigned groups then
        # a group is created for it.
        groups = []
        with open(os.path.join('.', 'opcodes', each, 'groups')) as ifstream:
            groups = ifstream.read().splitlines()
        if not groups:
            groups = [each]


        # If the user requested a group documentation and current instruction does
        # not belong to the requested group - skip it.
        if selected_group is not None and selected_group not in groups:
            continue


        # Every instruction should come with at least one syntax sample.
        syntax = []
        with open(os.path.join('.', 'opcodes', each, 'syntax')) as ifstream:
            syntax = ifstream.read().splitlines()


        # Every instruction should be described.
        # If it's not - how are we to know what does it do?
        description = ''
        with open(os.path.join('.', 'opcodes', each, 'description')) as ifstream:
            description = ifstream.read().strip()


        # encoding = []
        # with open(os.path.join('.', 'opcodes', each, 'encoding')) as ifstream:
        #     encoding = ifstream.read().splitlines()


        # An exception may (or may not) throw exceptions.
        # As an example, "checkedsmul" will throw an exception if the arithmetic operation
        # would overflow.
        #
        # Only explicitly listed exceptions are printed here.
        # "Default" exceptions (e.g. access to register out of range for selected register set,
        # read from an empty register) are not printed here.
        exceptions = []
        try:
            for each_ex in os.listdir(os.path.join('.', 'opcodes', each, 'exceptions')):
                with open(os.path.join('.', 'opcodes', each, 'exceptions', each_ex)) as ifstream:
                    exceptions.append( (each_ex, ifstream.read().strip(),) )
        except FileNotFoundError:
            sys.stderr.write('no exceptions defined for "{}" instruction\n'.format(each))


        # Print any examples provided for this instruction.
        examples = []
        try:
            for each_ex in os.listdir(os.path.join('.', 'opcodes', each, 'examples')):
                with open(os.path.join('.', 'opcodes', each, 'examples', each_ex)) as ifstream:
                    examples.append( (each_ex, ifstream.read().strip(),) )
        except FileNotFoundError:
            sys.stderr.write('no examples defined for "{}" instruction\n'.format(each))


        # Apart from a description, instruction may come with a list of "remarks".
        # These are additional notes, describin peculiarities of an instruction, its differences from
        # other instructions (and its relations with them).
        # Anything that does not fit the "description" field is put here.
        remarks = []
        try:
            with open(os.path.join('.', 'opcodes', each, 'remarks')) as ifstream:
                remarks = ifstream.read().strip()
            if not remarks:
                raise FileNotFoundError()
            remarks = into_paragraphs(remarks)
        except FileNotFoundError:
            pass


        # Any other instructions that are related to the currently rendered instruction.
        see_also = []
        try:
            with open(os.path.join('.', 'opcodes', each, 'see_also')) as ifstream:
                see_also = ifstream.read().splitlines()
        except FileNotFoundError:
            pass


        # Instructions should be separated by a '------' line.
        # This will make the documentation more readable.
        if first_opcode_being_documented:
            first_opcode_being_documented = False
        else:
            print()
            print('-' * LINE_WIDTH)
            print()


        render_heading(each.upper(), 2 * DEFAULT_INDENT_WIDTH, extra = {
            'instruction': True,
        }, ref = 'opcode:{}'.format(each.lower()))
        section_tracker.begin()

        print('{}in group{}: {}'.format(
            (' ' * (4 * DEFAULT_INDENT_WIDTH)),
            ('' if len(groups) == 1 else 's'),
            ', '.join(groups)
        ))
        print()


        render_heading('SYNTAX', indent = 3 * DEFAULT_INDENT_WIDTH, noise = True)
        print()
        for i, syn in enumerate(syntax):
            print('{}({})    {}'.format(
                (' ' * (4 * DEFAULT_INDENT_WIDTH)),
                colorise(i, COLOR_SYNTAX_SAMPLE_INDEX),
                colorise(syn, COLOR_SYNTAX_SAMPLE)
            ))
        print()


        render_heading('DESCRIPTION', indent = 3 * DEFAULT_INDENT_WIDTH, noise = True)
        print()
        section_tracker.begin()
        render_free_form_text(
            source = description,
            documented_instructions = documented_opcodes,
            syntax = syntax,
            indent = (4 * DEFAULT_INDENT_WIDTH),
        )
        section_tracker.end()
        print()

        render_heading('EXCEPTIONS', indent = 3 * DEFAULT_INDENT_WIDTH, noise = True)
        if exceptions:
            section_tracker.begin()
            for each_ex in exceptions:
                try:
                    render_file(
                        os.path.join('.', 'exceptions', each_ex[0]),
                        indent = 4 * DEFAULT_INDENT_WIDTH,
                        documented_instructions = documented_opcodes
                    )
                except FileNotFoundError as e:
                    sys.stderr.write('exception not defined on generic list: {}\n'.format(e))
                    render_file(
                        os.path.join('.', 'opcodes', each, 'exceptions', each_ex[0]),
                        indent = 4 * DEFAULT_INDENT_WIDTH,
                        documented_instructions = documented_opcodes,
                    )
                print()
            section_tracker.end()
        else:
            print(textwrap.indent('None.', prefix = (' ' * (4 * DEFAULT_INDENT_WIDTH))))
            print()


        render_heading('EXAMPLES', indent = 3 * DEFAULT_INDENT_WIDTH, noise = True)
        if examples:
            print()
            for each_ex in examples:
                print(textwrap.indent(
                    each_ex[1],
                    prefix = (' ' * (4 * DEFAULT_INDENT_WIDTH)),
                ))
        else:
            print(textwrap.indent('None.', prefix = (' ' * (4 * DEFAULT_INDENT_WIDTH))))
        print()


        # print('  ENCODING')
        # instruction_size, encoding_header, encoding_body = stringify_encoding(encoding)
        # print('    on {} bits'.format(instruction_size))
        # print()
        # print('    MSB{}LSB'.format(' ' * (len(encoding_header) - 6)))
        # print('    {}'.format(encoding_header))
        # print('    {}'.format(encoding_body))
        # print()
        # print('    OP: opcode')
        # print('    AS: access specifier')
        # print('    RS: register set type')
        # print()


        render_heading('REMARKS', indent = 3 * DEFAULT_INDENT_WIDTH, noise = True)
        if remarks:
            print()
            for each_paragraph in remarks:
                print(parse_and_expand(textwrap.indent(
                        text = '\n'.join(
                            longen(textwrap.wrap(each_paragraph,
                                width=(LINE_WIDTH - (4 * DEFAULT_INDENT_WIDTH))),
                            width=(LINE_WIDTH - (4 * DEFAULT_INDENT_WIDTH)))).strip(),
                        prefix = (' ' * (4 * DEFAULT_INDENT_WIDTH)),
                    ),
                    syntax = syntax,
                    documented_instructions = documented_opcodes,
                ))
        else:
            print(textwrap.indent('None.', prefix = (' ' * (4 * DEFAULT_INDENT_WIDTH))))
        print()


        if see_also:
            render_heading('SEE ALSO', indent = 3 * DEFAULT_INDENT_WIDTH, noise = True)
            print(textwrap.indent(', '.join(see_also), prefix = (' ' * (4 * DEFAULT_INDENT_WIDTH))))

        section_tracker.end()

    section_tracker.end()


def render_view(args):
    render_file(args[0], documented_instructions = [])


def emit_line(s = ''):
    sys.stdout.write('{}\n'.format(s))

def render_toc(max_depth = None, title = 'TABLE OF CONTENTS'):
    emit_line('{}'.format(title.center(LINE_WIDTH)))
    emit_line()
    longest_index = max(map(len, map(lambda e: e[0], section_tracker.recorded_headings()))) + 1
    for index, heading, noise, extra, ref in section_tracker.recorded_headings():
        if noise:
            continue
        character = '.'
        if max_depth is not None and index.count('.') > max_depth:
            continue
        #if max_depth is not None and index.count('.') == 0:
        is_chapter = (index.count('.') == 0)
        if is_chapter:
            character = '_'
        if RENDERING_MODE == RENDERING_MODE_HTML_ASCII_ART:
            just = (character * (LINE_WIDTH - longest_index - 1 - len(heading)))
            heading_link = '{just} <a href="#{slug}">{text}</a>'.format(
                just = just,
                slug = section_tracker.slug(index, ref),
                text = (
                    '<strong>{}</strong>'.format(heading)
                    if is_chapter
                    else heading
                ),
            )
            emit_line('{}{}'.format(
                (index + ' ').ljust(longest_index, character),
                heading_link,
            ))
        else:
            emit_line('{}{}'.format(
                (index + ' ').ljust(longest_index, character),
                (' ' + heading).rjust((LINE_WIDTH - longest_index), character),
            ))
    emit_line()
    emit_line('{}'.format('-' * LINE_WIDTH))
    emit_line()

def render_toc_overview():
    render_toc(
        max_depth = 0,
        title = 'OVERVIEW OF CONTENTS',
    )

def render_toc_full():
    render_toc()

def main(args):
    if (not len(args)) or ('--help' in args) or ('-h' in args):
        sys.stdout.write('docs-formatter <source-file>\n')
        sys.stdout.write('\n')
        sys.stdout.write('OPTIONS\n')
        sys.stdout.write('\n')
        sys.stdout.write('    -h, --help    - display help\n')
        sys.stdout.write('        --version - display version information\n')
        sys.stdout.write('\n')
        sys.stdout.write('LICENSE\n')
        sys.stdout.write('\n')
        sys.stdout.write('    This program is Free Software published under GNU GPL v3 license.\n')
        exit(not len(args))

    if ('--version' in args):
        fmt = (
            'docs-formatter version {version} ({commit})'
            if ('--verbose' in args) else
            '{version}'
        )
        sys.stdout.write((fmt + '\n').format(
            version = __version__,
            commit = __commit__,
        ))
        exit(0)

    render_view(args)

    if RENDERING_MODE == RENDERING_MODE_HTML_ASCII_ART:
        sys.stdout.write('<!DOCTYPE html>\n')
        sys.stdout.write('<html>\n')
        sys.stdout.write('<head>\n')
        sys.stdout.write('<meta charset="utf-8">\n')
        sys.stdout.write('<style>\n')
        if os.environ.get('COLOR') != 'no':
            sys.stdout.write('body { color: #d0d0d0; background-color: #000; }\n')
            sys.stdout.write('a { color: #d0d0d0; }\n')
        else:
            sys.stdout.write('a { color: #000; }\n')
        if os.environ.get('PRETTY_LISTINGS') != 'no':
            sys.stdout.write(
                  'div.source_code_listing {'
                + ' color: #0a0a0a;'
                + ' background-color: #e0e0e0;'
                + ' margin-bottom: -1em;'
                + ' }\n'
            )
        sys.stdout.write('</style>\n')
        sys.stdout.write('<title>{}</title>\n'.format(TITLE))
        sys.stdout.write('</head>\n')
        sys.stdout.write('<body>\n')
        sys.stdout.write('<a id="0"></a>\n')
        sys.stdout.write('<pre>\n')

    timestamp_line = 'Generated {}'.format(
        datetime.datetime.now().astimezone().strftime('%FT%T %z')
    )
    if RENDER_TIMESTAMP == 'above':
        emit_line(timestamp_line)
        emit_line()
        emit_line('{}\n'.format('-' * LINE_WIDTH))

    if TITLE is not None:
        emit_line(TITLE.center(LINE_WIDTH).rstrip())
        emit_line(('-' * (len(TITLE) + 2)).center(LINE_WIDTH).rstrip())
        emit_line()
        emit_line()

    for each in RENDERED_LINES:
        if each == r'\toc{overview}':
            render_toc_overview()
            continue
        if each == r'\toc{full}':
            render_toc_full()
            continue
        emit_line('{}'.format(each))

    if RENDER_TIMESTAMP == 'below':
        emit_line('{}\n'.format('-' * LINE_WIDTH))
        emit_line(timestamp_line)

    if RENDERING_MODE == RENDERING_MODE_HTML_ASCII_ART:
        sys.stdout.write('</pre>\n')
        sys.stdout.write('</body>\n')
        sys.stdout.write('</html>\n')

    with open(REFS_FILE, 'w') as ofstream:
        ofstream.write(json.dumps(section_tracker.data(), indent=4))

    return 0


exit(main(sys.argv[1:]))
