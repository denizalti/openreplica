ALL := concoord.tar.gz clientbundle.tar.gz
CONCOORDDIR := src/concoord
CLIENTFILES := $(addprefix $(CONCOORDDIR)/,connection.py group.py clientproxy.py pvalue.py command.py message.py peer.py enums.py utils.py)

all:	$(ALL)

concoord.zip:src/*
	zip concoord.zip src/*

concoord.tar.gz:src/*
	tar czf concoord.tar.gz src/*

tar:src/*
	tar czf concoord.tar src/*

client:$(CLIENTFILES)
	tar czf clientbundle.tar.gz $(CLIENTFILES)

clean:
	rm -f *~

clobber: clean
	rm -f $(ALL)
