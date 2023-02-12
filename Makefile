all: yafunc

test:
	@echo "Running unit-tests"
	pytest -q tests

yafunc: test
	@echo "Zipping into a function"
	rm yafunc.zip || true
	zip yafunc.zip index.py requirements.txt -r ./bot/*.py
	zip -T yafunc.zip