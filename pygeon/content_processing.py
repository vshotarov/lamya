"This module provides a few utility functions for processing content and front matter."
import re


def split_front_matter(source, front_matter_delimiter="+"):
    """Splits and evaluates the front matter from the content's source.

    This function assumes the front matter is actual python code, which gets
    `exec`-ed to give us a dictionary of values.

    :param source: the input raw source
    :param front_matter_delimiter: the delimiting character used for separating
        front matter from the rest of the content. The front matter should be
        surrounded by lines containing only delimiter characters.
    """
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
    exec(front_matter, {}, evaluated_front_matter) # pylint: disable=exec-used

    return evaluated_front_matter, content


def get_excerpt(content, remove_html_tags=True, # pylint: disable=too-many-arguments
        excerpt_start_tag="<!--excerpt-start-->",
        excerpt_end_tag="<!--excerpt-end-->",
        fallback_num_characters=250, suffix=""):
    """Extracts an excerpt from the provided content.

    The excerpt can be extracted either from excerpt tags if they exist in
    the content or by just taking the first ~150 characters of clean text,
    where clean means without any html tags.

    :param content: the content to grab the excerpt from. Can either be processed
        or raw markup
    :param remove_html_tags: whether or not to try removing html tags from
        the excerpt
    :param excerpt_start_tag: an optional piece of string that can be use for
        specifying the beginning of the excerpt
    :param excerpt_end_tag: an optional piece of string that can be use for
        specifying the ending of the excerpt
    :param fallback_num_characters: if no delimiting tags were specified,
        take everything up to the first space after `fallback_num_characters`
        as the excerpt
    :param suffix: optional suffix to add at the end of the excerpt. For when
        something like `...` is appropriate
    """
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
    """Uses regex to remove html tags.

    :param x: the string to try to rid of html
    """
    # https://stackoverflow.com/questions/9662346/python-code-to-remove-html-tags-from-a-string
    clean_re = re.compile('<.*?>|&([a-z0-9]+|#[0-9]{1,6}|#x[0-9a-f]{1,6});')
    return re.sub(clean_re, "", x).replace("\n"," ")
