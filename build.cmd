create-version-file version.yaml --outfile version.txt
pyinstaller --onefile --noconsole --add-data "icons/*.png;icons" -n "HomeTray" -i icon.ico --version-file version.txt home_tray.py
