PKGCONFIG = pkg-config
OPTIMISE = -Og -g
WARN = -Wall -Wextra -pedantic
LIBS = xcb-randr
STD = c90

FLAGS = $$($(PKGCONFIG) --cflags --libs $(LIBS)) -std=$(STD) $(WARN) $(OPTIMISE)


.PHONY: all
all: bin/blueshift_randr


bin/blueshift_randr: obj/blueshift_randr.o
	@mkdir -p bin
	$(CC) $(FLAGS) -o $@ $^

obj/%.o: src/%.c
	@mkdir -p obj
	$(CC) $(FLAGS) -c -o $@ $<


.PHONY: all
clean:
	-rm -r bin obj

