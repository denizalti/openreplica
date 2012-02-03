VERSION := 1.0.0
CONCOORDDIR := src/concoord
CLIENTFILES := $(addprefix $(CONCOORDDIR)/,connection.py group.py clientproxy.py pvalue.py command.py message.py peer.py enums.py utils.py)
CONCOORDNAME := $(addsuffix -$(VERSION),concoord)
ALL := $(CONCOORDNAME).tar.gz

all:	$(ALL)

concoord.zip:src/*
	zip $(CONCOORDNAME).zip src/*

concoord.tar.gz:src/*
	tar czf $(CONCOORDNAME).tar.gz src/*

tar:src/*
	tar czf $(CONCOORDNAME).tar src/*

client:$(CLIENTFILES)
	tar czf clientbundle.tar.gz $(CLIENTFILES)

clean:
	rm -f *~

clobber: clean
	rm -f $(ALL)
	rm -f clientbundle.tar.gz
