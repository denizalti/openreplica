SERVERFILES := *.py
CLIENTFILES := connection.py blockingclientproxy.py batchclientproxy.py asyncclientproxy.py clientproxy.py pvalue.py message.py enums.py utils.py exception.py
ALL := concoordserver.tar.gz

all:	$(ALL)

concoordserver.zip:$(SERVERFILES)
	zip concoordserver.zip $(SERVERFILES)

concoordserver.tar.gz:$(SERVERFILES)
	tar czf concoordserver.tar.gz $(SERVERFILES)

tar:$(SERVERFILES)
	tar czf concoordserver.tar $(SERVERFILES)

server:$(SERVERFILES)
	tar czf concoordserver.tar.gz $(SERVERFILES)

client:$(CLIENTFILES)
	tar czf concoordclient.tar.gz $(CLIENTFILES)

clean:
	rm -f *~

clobber: clean
	rm -f $(ALL)
	rm -f concoordserver.zip
	rm -f concoordserver.tar
	rm -f concoordserver.tar.gz
	rm -f concoordclient.tar.gz
