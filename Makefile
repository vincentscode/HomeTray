run:
	python hometray

setup: requirements.txt
	pip install -r requirements.txt

setup-dev: requirements.dev.txt
	pip install -r requirements.txt

build: hometray/* version.txt
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
