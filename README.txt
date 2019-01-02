                                 Docs formatter                                 
                                ----------------                                


                              OVERVIEW OF CONTENTS                              

1 _______________________________________________________________________ README
2 _____________________________________________________________________ Features
3 ______________________________________________________________________ License

--------------------------------------------------------------------------------


                               TABLE OF CONTENTS                                

1 _______________________________________________________________________ README
1.1 ..................................................................... Output
1.2 ...................................................................... Input
2 _____________________________________________________________________ Features
2.1 ......................................................... Lists vs "listeds"
2.2 ................................................. Function call tree example
2.3 ....................................................... Features not present
3 ______________________________________________________________________ License

--------------------------------------------------------------------------------



  [1] README {readme}

  Docs formatter - a text formatter for documentation.


  [1.1] Output {readme.output}

  It  produces  a  preformatted  text output suitable for viewing on the command
  line and HTML output suitable for the Web. The HTML output is preformatted and
  looks  exactly  like  the  plain  text  output  for the command line; the only
  difference is the presence of hyperlinks and basic colourisation.


  [1.2] Input {readme.input}

  It takes source in LaTeX-like notation as input.


  [2] Features {features}

  Features of the formatter include:

  - automatic generation of Table of Contents
  - arbitrarily nested sections to express the necessary hierarchy
  - automatic text reflow
  - lists of items
  - "listeds"  displaying all possible values of certain kind (e.g. instructions
    of an architecture, packet types in a protocol)
  - automatic formatting of function call trees
  - references (forward and backward)
  - file inclusion


  [2.1] Lists vs "listeds"

  Here is an example of a list:

  - hello
  - world
  - lorem
  - ipsum

  Lists  may  not be nested. Descriptions of a list item may be arbitrarily long
  and include line breaks.

  Here is an example of a "listed":

    hello      world      foo        bar        baz        lorem      
    ipsum      alpha      beta       gamma      delta      epsilon    

  [2.2] Function call tree example

  An example of a formatted function call tree:

  main()
  ↳ open("/etc/example.conf")
  ↳ do_stuff(fd)
    Descriptions  may  be  present  at  each  level  of  the  call stack and are
    automatically  indented  to  be  just below and slightly to the right of the
    function call they describe.

    ↳ some_function_with_long_name(
                                     and_a = "pretty long"
                                   , list_of = "arguments"
                                   , that_it_needs_to = receive
      )

      Calls  whose  list  of arguments would exceed column limit if printed on a
      single line are automatically broken and reformatted.
    ↳ exit(1)

  This  feature  is  quite primitive and limited, and is only able to describe a
  single  call  tree  with  no  conditional calls. Any conditional calls must be
  marked as such in description.


  [2.3] Features not present

  Some  features  are  omitted  from the code to keep the formatter simple. Most
  notable  omissions  include lack of support for arbitrary levels of nesting of
  different  constructs  (e.g.  lists),  and lack of support for custom layouts.


  [3] License

  The code is published under GNU GPL v3.

