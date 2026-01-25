run: main.py
	python3 main.py

seed: db/seed.py
	python3 db/seed.py

clean: comprobantes db/stock.db
	rm db/stock.db
	rm -r comprobantes

