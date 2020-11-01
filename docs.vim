" Vim syntax file
" Language: Docs
" Maintainer: Marek Marecki <marekjm@ozro.pw>
" Last Change: 2020 May 14

"
" See https://git.sr.ht/~maelkum/docs-formatter for more information.
"

if exists("b:current_syntax")
    finish
endif

syntax keyword docsBeginEnd         contained begin end

syntax keyword docsTodo             contained FIXME TODO XXX
syntax match docsComment            "%%.*$" contains=docsTodo

syntax match docsTitleContent       contained "\v\{[^}]*\}"ms=s+1,me=e-1
syntax match docsHeadingRefLink     contained "ref=.*}"ms=s+4,me=e-1
syntax match docsHeadingRef         contained "{ref=.*}"
    \ contains=docsHeadingRefLink
syntax match docsHeadingRef         "\v^\{ref=.*\}"
    \ contains=docsHeadingRefLink
syntax match docsHeading            "\v^\\heading\{.*\}(\\)?$"
    \ contains=docsTitleContent,docsHeadingRef
syntax match docsTitle              "\v^\\title\{.*\}$"
    \ contains=docsTitleContent

syntax match docsIncludePath        contained "\v\{[^}]*\}"ms=s+1,me=e-1
syntax match docsInclude            "\v^\\include\{.*\}$"
    \ contains=docsIncludePath

syntax match docsTocFullOverview    contained "{\(full\|overview\)}"ms=s+1,me=e-1
syntax match docsToc                "\\toc{.*}" contains=docsTocFullOverview

syntax match docsSectionBegin       "\\section{begin}" contains=docsBeginEnd
syntax match docsSectionEnd         "\\section{end}" contains=docsBeginEnd

syntax match docsRefLink            contained "{.*}"ms=s+1,me=e-1
syntax match docsRef                "\v\\ref\{.*\}" contains=docsRefLink
syntax match docsNameRef            "\v\\nameref\{.*\}" contains=docsRefLink

syntax match docsSourceBegin        contained "\\source{begin}"
    \ contains=docsBeginEnd
syntax match docsSourceEnd          contained "\\source{end}"
    \ contains=docsBeginEnd
syntax region docsSourceListing     keepend start="\\source{begin}"
    \ end="\\source{end}"
    \ contains=docsSourceBegin,docsSourceEnd

syntax match docsTrueOrFalse        contained "=\(true\|false\)*"ms=s+1
syntax match docsListEnumerated     contained "{enumerated\(=\(true\|false\)\)*}"
    \ contains=docsTrueOrFalse
syntax match docsListItemsNo        contained "[0-9][0-9]*"
syntax match docsListItems          contained "{items=[0-9][0-9]*}"
    \ contains=docsListItemsNo
syntax match docsListBegin          "\\list{begin}.*"
    \ contains=docsBeginEnd,docsListEnumerated,docsListItems
syntax match docsListEnd            "\\list{end}" contains=docsBeginEnd
syntax match docsItem               "\\item"

syntax match docsHr                 "\\hr"
syntax match docsBreak              "\\break"


highlight link docsBeginEnd         Number

highlight link docsTodo             Todo
highlight link docsComment          Comment

highlight link docsTitleContent     Special
highlight link docsHeadingRefLink   Special
highlight link docsHeadingRef       Boolean
highlight link docsTitle            Statement
highlight link docsHeading          Statement

highlight link docsInclude          Statement

highlight link docsTocFullOverview  Number
highlight link docsToc              Statement

highlight link docsSectionBegin     Statement
highlight link docsSectionEnd       Statement

highlight link docsRefLink          Special
highlight link docsRef              Boolean
highlight link docsNameRef          Boolean

highlight link docsSourceBegin      Statement
highlight link docsSourceEnd        Statement
highlight link docsSourceListing    Comment

highlight link docsTrueOrFalse      Number
highlight link docsListEnumerated   Boolean
highlight link docsListItemsNo      Number
highlight link docsListItems        Boolean
highlight link docsListBegin        Statement
highlight link docsListEnd          Statement
highlight link docsItem             Statement

highlight link docsHr               Statement
highlight link docsBreak            Statement
