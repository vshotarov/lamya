from pathlib import Path
import markdown
import shutil


def build(site_name, root_dir=None):
	root_dir = Path(root_dir or os.getcwd())

	# Read config file
	config_file = root_dir / (site_name + ".py")

	config_locals = {}
	with open(config_file) as f:
		exec(f.read(), {}, config_locals)
	
	# Build
	build_dir = root_dir / "build" # NOTE: I'm not keen on the name build

	if build_dir.exists():
		shutil.rmtree(build_dir)
	
	build_dir.mkdir()

	for path in (root_dir / "content").glob("**/*"):
		if not path.is_file():
			continue

		if path.suffix.lower() == ".md":
			with open(path) as f:
				source = f.read()

			# TODO: Process source
			html = markdown.markdown(source)
			# TODO: Process html

			with open(build_dir / (path.stem + ".html"), "w") as f:
				f.write(html)

		if path.suffix.lower() == ".html":
			raise NotImplementedError("No support for compiling .html files yet")
