VERSION := 1.0.0
CONCOORDDIR := concoord
CONCOORDFILES := $(CONCOORDDIR)/* *.txt *.py
CLIENTFILES := $(addprefix $(CONCOORDDIR)/,connection.py group.py clientproxy.py pvalue.py command.py message.py peer.py enums.py utils.py)
CONCOORDNAME := $(addsuffix -$(VERSION),concoord)
ALL := $(CONCOORDNAME).tar.gz

all:	$(ALL)

$(CONCOORDNAME).zip:$(CONCOORDFILES)
	zip $(CONCOORDNAME).zip $(CONCOORDFILES)

$(CONCOORDNAME).tar.gz:$(CONCOORDFILES)
	tar czf $(CONCOORDNAME).tar.gz $(CONCOORDFILES)

tar:$(CONCOORDFILES)
	tar czf $(CONCOORDNAME).tar $(CONCOORDFILES)

client:$(CLIENTFILES)
	tar czf clientbundle.tar.gz $(CLIENTFILES)

clean:
	rm -f *~

clobber: clean
	rm -f $(ALL)
	rm -f clientbundle.tar.gz
