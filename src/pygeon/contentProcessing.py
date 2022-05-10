import re


def split_front_matter(source, front_matter_delimiter="+"):
	if not source:
		return {}, ""

	as_lines = source.splitlines()
	has_front_matter = set(as_lines[0]) == set([front_matter_delimiter])

	if not has_front_matter:
		return {}, source

	front_matter = ""
	content = ""
	for i, line in enumerate(as_lines[1:]):
		if set(line) == set(front_matter_delimiter):
			content = "\n".join(as_lines[i+2:])
			break
		front_matter += line + "\n"

	evaluated_front_matter = {}
	exec(front_matter, {}, evaluated_front_matter)

	return evaluated_front_matter, content


def get_excerpt(content, remove_html_tags=True, excerpt_start_tag="<!--excerpt-start-->",
		excerpt_end_tag="<!--excerpt-end-->", fallback_num_characters=250, suffix=""):
	if excerpt_start_tag in content or excerpt_end_tag in content:
		excerpt = str(content)
		if excerpt_start_tag in content:
			excerpt = excerpt.split(excerpt_start_tag, 1)[1]
		if excerpt_end_tag in content:
			excerpt = excerpt.split(excerpt_end_tag, 1)[0]
		excerpt = remove_html(excerpt) if remove_html_tags else excerpt
	else:
		clean_content = remove_html(content)
		i = 0
		for i, char in enumerate(clean_content[fallback_num_characters:]):
			if char == " ":
				break
		excerpt = str(clean_content[:fallback_num_characters+i])
	return "".join(excerpt.splitlines()) + suffix


def remove_html(x):
	# https://stackoverflow.com/questions/9662346/python-code-to-remove-html-tags-from-a-string
	CLEANR = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
	return re.sub(CLEANR, "", x).replace("\n"," ")
