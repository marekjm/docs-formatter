\title{Docs formatter}

\toc{overview}

\toc{full}

\heading{README}{ref=readme}
\section{begin}

Docs formatter - a text formatter for documentation.

\heading{Output}{ref=readme.output}

It produces a preformatted text output suitable for viewing on the command line
and HTML output suitable for the Web. The HTML output is preformatted and looks
exactly like the plain text output for the command line; the only difference is
the presence of hyperlinks and basic colourisation.

\heading{Input}{ref=readme.input}

It takes source in LaTeX-like notation as input.

%% Docs formatter
\section{end}

\heading{Features}{ref=features}
\section{begin}

Features of the formatter include:

\list{begin}
\item
automatic generation of Table of Contents
\item
arbitrarily nested sections to express the necessary hierarchy
\item
automatic text reflow
\item
lists of items
\item
"listeds" displaying all possible values of certain kind (e.g. instructions of
an architecture, packet types in a protocol)
\item
automatic formatting of function call trees
\item
references (forward and backward)
\item
file inclusion
\list{end}

\heading{Lists vs "listeds"}

Here is an example of a list:

\list{begin}
\item
hello
\item
world
\item
lorem
\item
ipsum
\list{end}

Lists may not be nested. Descriptions of a list item may be arbitrarily long and
include line breaks.

Here is an example of a "listed":

\listed{begin}
hello
world
foo
bar
baz
lorem
ipsum
alpha
beta
gamma
delta
epsilon
\listed{end}

\heading{Function call tree example}

An example of a formatted function call tree:

\callof{main()}
\call{begin}
\callof{open("/etc/example.conf")}
\callof{do_stuff(fd)}
Descriptions may be present at each level of the call stack and are
automatically indented to be just below and slightly to the right of the
function call they describe.

\call{begin}
\callof{some_function_with_long_name(and_a = "pretty long", \
list_of = "arguments", that_it_needs_to = receive)}
Calls whose list of arguments would exceed column limit if printed on a single
line are automatically broken and reformatted.
\callof{exit(1)}
\call{end}
\call{end}

This feature is quite primitive and limited, and is only able to describe a
single call tree with no conditional calls. Any conditional calls must be marked
as such in description.

\heading{Features not present}

Some features are omitted from the code to keep the formatter simple.
Most notable omissions include lack of support for arbitrary levels of nesting
of different constructs (e.g. lists), and lack of support for custom layouts.

%% Features
\section{end}

\heading{License}

The code is published under GNU GPL v3.

%% vim:textwidth=80
