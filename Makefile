# Copying and distribution of this file, with or without modification,
# are permitted in any medium without royalty provided the copyright
# notice and this notice are preserved.  This file is offered as-is,
# without any warranty.


# The package path prefix, if you want to install to another root, set DESTDIR to that root
PREFIX ?= /usr
# The command path excluding prefix
BIN ?= /bin
# The executable library path excluding prefix
LIBEXEC ?= /libexec
# The resource path excluding prefix
DATA ?= /share
# The command path including prefix
BINDIR ?= $(PREFIX)$(BIN)
# The executable library path including prefix
LIBEXECDIR ?= $(PREFIX)$(LIBEXEC)
# The resource path including prefix
DATADIR ?= $(PREFIX)$(DATA)
# The generic documentation path including prefix
DOCDIR ?= $(DATADIR)/doc
# The info manual documentation path including prefix
INFODIR ?= $(DATADIR)/info
# The license base path including prefix
LICENSEDIR ?= $(DATADIR)/licenses

# Python 3 command to use in shebangs
SHEBANG ?= /usr/bin/env python3
# The name of the command as it should be installed
COMMAND ?= blueshift
# The name of the package as it should be installed
PKGNAME ?= blueshift

# Executable bindings for display server access
EXECS ?= iccprofile

# Executable library files
EXECLIBS = $(foreach E,$(EXECS),blueshift_$(E))
# The installed pkg-config command
PKGCONFIG ?= pkg-config
# Optimisation settings for C code compilation
OPTIMISE ?= -O3 -g
# Warnings settings for C code compilation
WARN = -Wall -Wextra -pedantic -Wdouble-promotion -Wformat=2 -Winit-self -Wmissing-include-dirs      \
       -Wtrampolines -Wmissing-prototypes -Wmissing-declarations -Wnested-externs                    \
       -Wno-variadic-macros -Wsync-nand -Wunsafe-loop-optimizations -Wcast-align                     \
       -Wdeclaration-after-statement -Wundef -Wbad-function-cast -Wwrite-strings -Wlogical-op        \
       -Wstrict-prototypes -Wold-style-definition -Wpacked -Wvector-operation-performance            \
       -Wunsuffixed-float-constants -Wsuggest-attribute=const -Wsuggest-attribute=noreturn           \
       -Wsuggest-attribute=format -Wnormalized=nfkc -fstrict-aliasing -fipa-pure-const -ftree-vrp    \
       -fstack-usage -funsafe-loop-optimizations -Wshadow -Wredundant-decls -Winline -Wcast-qual     \
       -Wsign-conversion -Wstrict-overflow=5 -Wconversion -Wsuggest-attribute=pure -Wswitch-default  \
       -Wstrict-aliasing=1 -fstrict-overflow -Wfloat-equal
#not used: -Wtraditional (tranditional C function definitions are ridiculous),
#          -Wpadded (useless for this project), -Wc++-compat (bad practice)
#not used because of libxcb's API: -Waggregate-return, -Wtraditional-conversion (also useless)
# The C standard for C code compilation
STD = c99
LIBS_iccprofile = xcb
LD_iccprofile =
LIBS = $(foreach B,$(EXECS),$(LIBS_$(B)))
FLAGS = $$($(PKGCONFIG) --cflags $(LIBS)) -std=$(STD) $(WARN) $(OPTIMISE) \
        $(CFLAGS) $(LDFLAGS) $(CPPFLAGS)

# Resource files
DATAFILES = 2deg 10deg redshift redshift_old
# Python source files
PYFILES = __main__.py colour.py curve.py monitor.py solar.py icc.py adhoc.py  \
          backlight.py blackbody.py aux.py weather.py interpolation.py
# Configuration script example files
EXAMPLES = comprehensive sleepmode crtc-detection crtc-searching logarithmic  \
           xmobar xpybar stored-settings current-settings xmonad threaded     \
           backlight darkroom textconf textconf.conf modes weather battery    \
           icc-profile-atoms bedtime x-window-focus


# Build rules

.PHONY: default
default: command info shell

.PHONY: all
all: command doc shell

.PHONY: command
command: bin/blueshift $(foreach E,$(EXECLIBS),bin/$(E))


# Build rules for C source files

bin/blueshift_%: obj/blueshift_%.o
	@mkdir -p bin
	$(CC) $(FLAGS) $$($(PKGCONFIG) --libs $(LIBS_$*)) $(LD_$*) -o $@ $^

obj/%.o: src/%.c
	@mkdir -p obj
	$(CC) $(FLAGS) -c -o $@ $<


# Build rules for Python source files

bin/blueshift: obj/blueshift.zip
	@mkdir -p bin
	echo '#!$(SHEBANG)' > $@
	cat $< >> $@
	chmod a+x $@

obj/blueshift.zip: $(foreach F,$(PYFILES),obj/$(F))
	cd obj && zip ../$@ $(foreach F,$(PYFILES),$(F))

obj/%.py: src/%.py
	@mkdir -p obj
	cp $< $@
	sed -i '/^DATADIR *= /s#^.*$$#DATADIR = '\''$(DATADIR)/$(PKGNAME)'\''#' $@
	sed -i '/^LIBEXECDIR *= /s#^.*$$#LIBEXECDIR = '\''$(LIBEXECDIR)'\''#' $@


# Build rules for documentation

.PHONY: doc
doc: info pdf dvi ps

obj/%.texinfo: info/%.texinfo
	@mkdir -p obj
	cp $< $@
	sed -i 's:@set DOCDIR /usr/share/doc:@set DOCDIR $(DOCDIR):g' $@
	sed -i 's:@set PKGNAME blueshift:@set PKGNAME $(PKGNAME):g' $@

.PHONY: info
info: blueshift.info
%.info: obj/%.texinfo obj/fdl.texinfo
	makeinfo $<

.PHONY: pdf
pdf: blueshift.pdf
%.pdf: obj/%.texinfo obj/fdl.texinfo
	cd obj ; yes X | texi2pdf ../$<
	mv obj/$@ $@

.PHONY: dvi
dvi: blueshift.dvi
%.dvi: obj/%.texinfo obj/fdl.texinfo
	cd obj ; yes X | $(TEXI2DVI) ../$<
	mv obj/$@ $@

.PHONY: ps
ps: blueshift.ps
%.ps: obj/%.texinfo obj/fdl.texinfo
	cd obj ; yes X | texi2pdf --ps ../$<
	mv obj/$@ $@


# Build rules for shell auto-completion

.PHONY: shell
shell: bash zsh fish

.PHONY: bash
bash: bin/blueshift.bash
bin/blueshift.bash: src/completion
	@mkdir -p bin
	auto-auto-complete bash --output $@ --source $<

.PHONY: zsh
zsh: bin/blueshift.zsh
bin/blueshift.zsh: src/completion
	@mkdir -p bin
	auto-auto-complete zsh --output $@ --source $<

.PHONY: fish
fish: bin/blueshift.fish
bin/blueshift.fish: src/completion
	@mkdir -p bin
	auto-auto-complete fish --output $@ --source $<


# Install rules

.PHONY: install
install: install-base install-info install-examples install-shell

.PHONY: install
install-all: install-base install-doc install-shell

# Install base rules

.PHONY: install-base
install-base: install-command install-license

.PHONY: install-command
install-command: install-command-bin install-command-libexec install-command-share

.PHONY: install-command-bin
install-command-bin: bin/blueshift
	install -dm755 -- "$(DESTDIR)$(BINDIR)"
	install -m755 $< -- "$(DESTDIR)$(BINDIR)/$(COMMAND)"

.PHONY: install-command-libexec
install-command-libexec: $(foreach E,$(EXECLIBS),bin/$(E))
	install -dm755 -- "$(DESTDIR)$(LIBEXECDIR)"
	install -m755 $^ -- "$(DESTDIR)$(LIBEXECDIR)"

.PHONY: install-command-share
install-command-share: $(foreach D,$(DATAFILES),res/$(D))
	install -dm755 -- "$(DESTDIR)$(DATADIR)/$(PKGNAME)"
	install -m644 -- $^ "$(DESTDIR)$(DATADIR)/$(PKGNAME)"

.PHONY: install-license
install-license:
	install -dm755 -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)"
	install -m644 COPYING LICENSE.agpl3 LICENSE.gpl3 LICENSE.fdl1.3 -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)"

# Install documentation

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

# Install shell auto-completion

.PHONY: install-shell
install-shell: install-bash install-zsh install-fish

.PHONY: install-bash
install-bash: bin/blueshift.bash
	install -dm755 -- "$(DESTDIR)$(DATADIR)/bash-completion/completions"
	install -m644 $< -- "$(DESTDIR)$(DATADIR)/bash-completion/completions/$(COMMAND)"

.PHONY: install-zsh
install-zsh: bin/blueshift.zsh
	install -dm755 -- "$(DESTDIR)$(DATADIR)/zsh/site-functions"
	install -m644 $< -- "$(DESTDIR)$(DATADIR)/zsh/site-functions/_$(COMMAND)"

.PHONY: install-fish
install-fish: bin/blueshift.fish
	install -dm755 -- "$(DESTDIR)$(DATADIR)/fish/completions"
	install -m644 $< -- "$(DESTDIR)$(DATADIR)/fish/completions/$(COMMAND).fish"


# Uninstall rules

.PHONY: uninstall
uninstall:
	-rm -- "$(DESTDIR)$(BINDIR)/$(COMMAND)"
	-rm -- $(foreach E,$(EXECLIBS),"$(DESTDIR)$(LIBEXECDIR)/$(E)")
	-rmdir -- "$(DESTDIR)$(LIBEXECDIR)"
	-rm -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)/COPYING"
	-rm -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)/LICENSE.agpl3"
	-rm -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)/LICENSE.gpl3"
	-rm -- "$(DESTDIR)$(LICENSEDIR)/$(PKGNAME)/LICENSE.fdl1.3"
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


# Clean rules

.PHONY: all
clean:
	-rm -r bin obj blueshift.{info,pdf,ps,dvi} *.su src/*.su

