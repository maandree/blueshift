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
LICENSEDIR ?= $(DATADIR)/licenses

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



.PHONY: all
all: command

.PHONY: command
command: bin/blueshift_randr.so bin/blueshift


bin/blueshift.zip: src/*.py
	@mkdir -p bin
	cd src && zip ../$@ *.py

bin/blueshift: bin/blueshift.zip
	echo '#!/usr/bin/python3' > $@
	cat $< >> $@
	chmod a+x $@


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


.PHONY: install
install: install-command install-license

.PHONY: install-command
install-command: bin/blueshift_randr.so bin/blueshift
	install -dm755 -- "$(DESTDIR)$(BINDIR)"
	install -m755 bin/blueshift -- "$(DESTDIR)$(BINDIR)/$(COMMAND)"
	install -dm755 -- "$(DESTDIR)$(LIBDIR)"
	install -m755 bin/blueshift_randr.so -- "$(DESTDIR)$(LIBDIR)/blueshift_randr.so"
	install -dm755 -- "$(DESTDIR)$(DATADIR)/$(PKGNAME)"
	install -m644 -- $(DATAFILES) "$(DESTDIR)$(DATADIR)/$(PKGNAME)"

.PHONY: install-license
install-license:
	install -dm755 -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)"
	install -m644 COPYING LICENSE -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)"


.PHONY: uninstall
uninstall:
	-rm -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)/COPYING"
	-rm -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)/LICENSE"
	-rmdir -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)"
	-rm -- $(foreach F,$(DATAFILES),"$(DESTDIR)$(DATADIR)/$(PKGNAME)/$(F)")
	-rmdir -- "$(DESTDIR)$(DATADIR)/$(PKGNAME)"
	-rm --"$(DESTDIR)$(LIBDIR)/blueshift_randr.so"
	-rm --"$(DESTDIR)$(BINDIR)/$(COMMAND)"


.PHONY: all
clean:
	-rm -r bin obj src/blueshift_randr.c

