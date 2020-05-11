PREFIX=~/.local
BIN_PATH=$(PREFIX)/bin

EXECUTABLE=$(BIN_PATH)/docs-formatter

RENDER_COLUMNS=80

all: README.txt

README.txt: docs/README.txt
	RENDER_COLUMNS=$(RENDER_COLUMNS) COLOR=no ./view.py docs/README.txt > README.txt

README.html: docs/README.txt
	RENDER_COLUMNS=$(RENDER_COLUMNS) RENDERING_MODE=RENDERING_MODE_HTML_ASCII_ART COLOR=no ./view.py docs/README.txt > README.html

install:
	mkdir -p $(BIN_PATH)
	cp ./view.py $(EXECUTABLE)
	chmod +x $(EXECUTABLE)
	sed -i "s/__commit__ = '\<HEAD\>'/__commit__ = '$(shell git rev-parse HEAD)'/" $(EXECUTABLE)
