VERSION := 0.1.0
CONCOORDDIR := concoord
CONCOORDFILES := $(CONCOORDDIR)/* *.txt *.py
CONCOORDNAME := $(addsuffix -$(VERSION),concoord)
ALL := $(CONCOORDNAME).tar.gz

all:	$(ALL)

$(CONCOORDNAME).tar.gz:$(CONCOORDFILES)
	tar czf $(CONCOORDNAME).tar.gz $(CONCOORDFILES)

zip:$(CONCOORDFILES)
	zip $(CONCOORDNAME).zip $(CONCOORDFILES)

bz2:$(CONCOORDFILES)
	tar cjf $(CONCOORDNAME).tar.bz2 $(CONCOORDFILES)

tar:$(CONCOORDFILES)	
	tar czf $(CONCOORDNAME).tar $(CONCOORDFILES)

clean:
	rm -f *~

clobber: clean
	rm -f $(ALL)
	rm -f $(CONCOORDNAME).zip
	rm -f $(CONCOORDNAME).tar
	rm -f $(CONCOORDNAME).tar.bz2