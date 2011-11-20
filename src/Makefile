ALL=concoord.tar.gz
all:	$(ALL)

concoord.zip:*.py
	zip concoord.zip *.py

concoord.tar.gz:*.py
	tar czf concoord.tar.gz *.py

clean:
	rm -f *~

clobber: clean
	rm -f $(ALL)
