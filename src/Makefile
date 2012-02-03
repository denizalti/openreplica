ALL=concoord.tar.gz
all:	$(ALL)

concoord.zip:*.py
	zip concoord.zip concoord/*

concoord.tar.gz:*.py
	tar czf concoord.tar.gz concoord/*

client:*.py
	tar czf logger.tar.gz concoord/connection.py concoord/group.py concoord/clientproxy.py concoord/pvalue.py concoord/command.py concoord/message.py concoord/peer.py concoord/enums.py concoord/utils.py

clean:
	rm -f *~

clobber: clean
	rm -f $(ALL)
