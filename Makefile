# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.  This file is offered as-is,
# without any warranty.


PREFIX ?= /usr
BIN ?= /bin
LIB ?= /lib
DATA ?= /share
BINDIR ?= $(PREFIX)$(BIN)
LIBDIR ?= $(PREFIX)$(LIB)
DATADIR ?= $(PREFIX)$(DATA)
DOCDIR ?= $(DATADIR)/doc
LICENSEDIR ?= $(DATADIR)/licenses
INFODIR ?= $(DATADIR)/info

SHEBANG ?= /usr/bin/python3
COMMAND ?= blueshift
PKGNAME ?= blueshift


PKGCONFIG ?= pkg-config
OPTIMISE ?= -Og -g
WARN = -Wall -Wextra -pedantic
LIBS = xcb-randr python3
STD = c99
FLAGS = $$($(PKGCONFIG) --cflags --libs $(LIBS)) -std=$(STD) $(WARN) $(OPTIMISE) -fPIC

DATAFILES = 2deg 10deg redshift redshift_old
PYFILES = __main__.py colour.py curve.py monitor.py solar.py icc.py
EXAMPLES = comprehensive sleepmode


.PHONY: default
default: command info shell

.PHONY: all
all: command doc shell

.PHONY: doc
doc: info pdf dvi ps

.PHONY: info
info: blueshift.info

.PHONY: pdf
pdf: blueshift.pdf

.PHONY: dvi
dvi: blueshift.dvi

.PHONY: ps
ps: blueshift.ps

.PHONY: command
command: bin/blueshift_randr.so bin/blueshift

.PHONY: shell
shell: bash zsh fish

.PHONY: bash
bash: blueshift.bash

.PHONY: zsh
zsh: blueshift.zsh

.PHONY: fish
fish: blueshift.fish


bin/blueshift: obj/blueshift.zip
	echo '#!/usr/bin/python3' > $@
	cat $< >> $@
	chmod a+x $@

obj/blueshift.zip: $(foreach F,$(PYFILES),obj/$(F))
	@mkdir -p bin
	cd obj && zip ../$@ $(foreach F,$(PYFILES),$(F))

obj/%.py: src/%.py
	cp $< $@
	sed -i '/^DATADIR *= /s#^.*$$#DATADIR = '\''$(DATADIR)/$(PKGNAME)'\''#' $@
	sed -i '/^LIBDIR *= /s#^.*$$#LIBDIR = '\''$(LIBDIR)'\''#' $@


bin/blueshift_randr.so: obj/blueshift_randr.o obj/blueshift_randr_c.o
	@mkdir -p bin
	$(CC) $(FLAGS) -shared -o $@ $^

obj/%.o: src/%.c
	@mkdir -p obj
	$(CC) $(FLAGS) -c -o $@ $<

obj/%.o: obj/%.c
	@mkdir -p obj
	$(CC) $(FLAGS) -c -o $@ $<

obj/blueshift_randr.c: src/blueshift_randr.pyx
	@mkdir -p obj
	if ! cython -3 -v $<; then src/blueshift_randr.c ; false ; fi
	mv src/blueshift_randr.c $@


%.info: info/%.texinfo
	makeinfo "$<"

%.pdf: info/%.texinfo
	@mkdir -p obj
	cd obj ; yes X | texi2pdf ../$<
	mv obj/$@ $@

%.dvi: info/%.texinfo
	@mkdir -p obj
	cd obj ; yes X | $(TEXI2DVI) ../$<
	mv obj/$@ $@

%.ps: info/%.texinfo
	@mkdir -p obj
	cd obj ; yes X | texi2pdf --ps ../$<
	mv obj/$@ $@


blueshift.bash: completion
	auto-auto-complete bash --output $@ --source $<

blueshift.zsh: completion
	auto-auto-complete zsh --output $@ --source $<

blueshift.fish: completion
	auto-auto-complete fish --output $@ --source $<



.PHONY: install
install: install-base install-info install-examples install-shell

.PHONY: install
install-all: install-base install-doc install-shell

.PHONY: install-base
install-base: install-command install-license

.PHONY: install-command
install-command: bin/blueshift_randr.so bin/blueshift $(foreach D,$(DATAFILES),res/$(D))
	install -dm755 -- "$(DESTDIR)$(BINDIR)"
	install -m755 bin/blueshift -- "$(DESTDIR)$(BINDIR)/$(COMMAND)"
	install -dm755 -- "$(DESTDIR)$(LIBDIR)"
	install -m755 bin/blueshift_randr.so -- "$(DESTDIR)$(LIBDIR)/blueshift_randr.so"
	install -dm755 -- "$(DESTDIR)$(DATADIR)/$(PKGNAME)"
	install -m644 -- $(foreach D,$(DATAFILES),res/$(D)) "$(DESTDIR)$(DATADIR)/$(PKGNAME)"

.PHONY: install-license
install-license:
	install -dm755 -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)"
	install -m644 COPYING LICENSE -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)"

.PHONY: install-doc
install-doc: install-info install-pdf install-ps install-dvi install-examples

.PHONY: install-examples
install-examples: $(foreach E,$(EXAMPLES),examples/$(E))
	install -dm755 -- "$(DESTDIR)$(DOCDIR)/$(PKGNAME)/examples"
	install -m644 $^ -- "$(DESTDIR)$(DOCDIR)/$(PKGNAME)/examples"

.PHONY: install-info
install-info: blueshift.info
	install -dm755 -- "$(DESTDIR)$(INFODIR)"
	install -m644 $< -- "$(DESTDIR)$(INFODIR)/$(PKGNAME).info"

.PHONY: install-pdf
install-pdf: blueshift.pdf
	install -dm755 -- "$(DESTDIR)$(DOCDIR)"
	install -m644 $< -- "$(DESTDIR)$(DOCDIR)/$(PKGNAME).pdf"

.PHONY: install-ps
install-ps: blueshift.ps
	install -dm755 -- "$(DESTDIR)$(DOCDIR)"
	install -m644 $< -- "$(DESTDIR)$(DOCDIR)/$(PKGNAME).ps"

.PHONY: install-dvi
install-dvi: blueshift.dvi
	install -dm755 -- "$(DESTDIR)$(DOCDIR)"
	install -m644 $< -- "$(DESTDIR)$(DOCDIR)/$(PKGNAME).dvi"

.PHONY: install-shell
install-shell: install-bash install-zsh install-fish

.PHONY: install-bash
install-bash: blueshift.bash
	install -dm755 -- "$(DESTDIR)$(DATADIR)/bash-completion/completions"
	install -m644 $< -- "$(DESTDIR)$(DATADIR)/bash-completion/completions/$(COMMAND)"

.PHONY: install-zsh
install-zsh: blueshift.zsh
	install -dm755 -- "$(DESTDIR)$(DATADIR)/zsh/site-functions"
	install -m644 $< -- "$(DESTDIR)$(DATADIR)/zsh/site-functions/_$(COMMAND)"

.PHONY: install-fish
install-fish: blueshift.fish
	install -dm755 -- "$(DESTDIR)$(DATADIR)/fish/completions"
	install -m644 $< -- "$(DESTDIR)$(DATADIR)/fish/completions/$(COMMAND).fish"


.PHONY: uninstall
uninstall:
	-rm -- "$(DESTDIR)$(BINDIR)/$(COMMAND)"
	-rm -- "$(DESTDIR)$(LIBDIR)/blueshift_randr.so"
	-rm -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)/COPYING"
	-rm -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)/LICENSE"
	-rmdir -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)"
	-rm -- $(foreach F,$(DATAFILES),"$(DESTDIR)$(DATADIR)/$(PKGNAME)/$(F)")
	-rmdir -- "$(DESTDIR)$(DATADIR)/$(PKGNAME)"
	-rm -- $(foreach E,$(EXAMPLES),"$(DESTDIR)$(DOCDIR)/$(PKGNAME)/examples/$(E)")
	-rmdir -- "$(DESTDIR)$(DOCDIR)/$(PKGNAME)/examples"
	-rmdir -- "$(DESTDIR)$(DOCDIR)/$(PKGNAME)"
	-rm -- "$(DESTDIR)$(INFODIR)/$(PKGNAME).info"
	-rm -- "$(DESTDIR)$(DOCDIR)/$(PKGNAME).pdf"
	-rm -- "$(DESTDIR)$(DOCDIR)/$(PKGNAME).ps"
	-rm -- "$(DESTDIR)$(DOCDIR)/$(PKGNAME).dvi"
	-rm -- "$(DESTDIR)$(DATADIR)/fish/completions/$(COMMAND).fish"
	-rmdir -- "$(DESTDIR)$(DATADIR)/fish/completions"
	-rmdir -- "$(DESTDIR)$(DATADIR)/fish"
	-rm -- "$(DESTDIR)$(DATADIR)/zsh/site-functions/_$(COMMAND)"
	-rmdir -- "$(DESTDIR)$(DATADIR)/zsh/site-functions"
	-rmdir -- "$(DESTDIR)$(DATADIR)/zsh"
	-rm -- "$(DESTDIR)$(DATADIR)/bash-completion/completions/$(COMMAND)"
	-rmdir -- "$(DESTDIR)$(DATADIR)/bash-completion/completions"
	-rmdir -- "$(DESTDIR)$(DATADIR)/bash-completion"


.PHONY: all
clean:
	-rm -r bin obj src/blueshift_randr.c blueshift.{ba,z,fi}sh

