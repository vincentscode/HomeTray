PYTHON_VERSION_MIN := 3.10

run: check-python-version
	python hometray

setup: check-python-version requirements.txt
	pip install -r requirements.txt

setup-dev: check-python-version requirements.dev.txt
	pip install -r requirements.txt

build: check-python-version hometray/* version.txt
	create-version-file version.yaml --outfile version.txt
	pyinstaller --onefile --noconsole --add-data "icons/*;icons" -n "HomeTray" -i icon.ico --version-file version.txt HomeTray/__main__.py
	cp config.ini dist/config.ini

clean:
	rm -rf __pycache__
	rm -rf build
	rm -rf dist
	rm -rf *.spec

rebuild: clean build

git-pull:
	git pull

confirm-action:
	@echo -n "Are you sure? [y/N] " && read ans && [ $${ans:-N} = y ]

COMMIT_MESSAGE ?= $(shell bash -c 'read -p "Commit message: " commit_message; echo $$commit_message')
git-commit:
	git add .
	git commit -m "$(COMMIT_MESSAGE)"

git-push: confirm-action
	git push

git-update: git-pull git-commit git-push

VERSION = $(shell cat version.yaml | grep Version | cut -f2 -d " ")
release: git-update rebuild
	echo $(VERSION)
	gh release create v$(VERSION) -t v$(VERSION) --generate-notes -d dist/HomeTray.exe

unchecked-release:
	echo $(VERSION)
	gh release create v$(VERSION) -t v$(VERSION) --generate-notes -d dist/HomeTray.exe

PYTHON_VERSION := $(shell python -c "import sys; print('%d.%d'% sys.version_info[:2])" )
PYTHON_VERSION_OK := $(shell python -c "import sys; print(int(sys.version_info[0] == int(\"$(PYTHON_VERSION_MIN)\".split('.')[0]) and sys.version_info[1] >= int(\"$(PYTHON_VERSION_MIN)\".split('.')[1]) or sys.version_info[0] > int(\"$(PYTHON_VERSION_MIN)\".split('.')[0])))")
check-python-version:
ifneq ($(PYTHON_VERSION_OK), 1)
	$(error Python $(PYTHON_VERSION_MIN) or higher is required. You are using Python $(PYTHON_VERSION))
endif
