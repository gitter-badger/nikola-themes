#!/usr/bin/env python

"""Make sanity checks on the provided themes."""

from __future__ import unicode_literals, print_function
import codecs
import filecmp
import glob
import hashlib
import os
import sys
import re

import colorama

from nikola import utils

def error(msg):
    print(colorama.Fore.RED + "ERROR:" + msg)

def theme_list():
    return sorted(['base', 'base-jinja', 'bootstrap', 'bootstrap-jinja', 'bootstrap3', 'bootstrap3-jinja'] + [theme.split('/')[-1] for theme in glob.glob("v7/*")])

def sanity_check(theme=None):
    if theme is None:  # Check them all
        for theme in theme_list():
            sanity_check(theme)
        return
    themes = utils.get_theme_chain(theme, _themes_dir='v7')
    engine = utils.get_template_engine(themes, _themes_dir='v7')

    # Inheritance checks

    # All themes must inherit from base
    if themes[-1] != 'base':
        error("theme {0} doesn't inherit from base".format(theme))
    # All jinja themes must inherit from base-jinja
    if engine == "jinja" and "base-jinja" not in themes:
        error("theme {0} is jinja-based and doesn't inherit from base-jinja".format(theme))
    # All mako themes must NOT inherit from base-jinja
    if engine == "mako" and "base-jinja" in themes:
        error("theme {0} is mako-based and inherits from base-jinja".format(theme))

    # Detect exact asset duplication in theme chain
    for root, dirs, files in os.walk("v7/"+theme):
        for f in files:
            path = "/".join([root, f])
            asset = path.split("/",2)[-1]
            r, p1, p2 = is_asset_duplicated(asset, themes)
            if r:
                error("duplicated asset: {0} {1}".format(p1, p2))


    # Detect deprecated names and anonymous namespaces
    for root, dirs, files in os.walk("v7/"+theme+"/templates"):
        for f in files:
            path = "/".join([root, f])
            with codecs.open(path, "r", "utf8") as inf:
                data = inf.read()
            for k, exceptions in blacklist:
                if k in data and f not in exceptions:
                    error("theme '{0}' contains deprecated name '{1}' in {2}".format(theme, k, path))

    # Ensure the theme has a README.md
    if utils.get_asset_path('README.md', [theme], _themes_dir='v7') is None:
        error("theme '{0}' has no README.md".format(theme))

def is_asset_duplicated(path, themes):
    # First get the path for the asset with whole theme chain
    p1 = utils.get_asset_path(path, themes, _themes_dir='v7')
    # Get the path for asset with truncated theme chain
    p2 = utils.get_asset_path(path, themes[1:], _themes_dir='v7')
    # README.md is ok to duplicate
    if 'README.md' in path:
        return False, p1, p2
    # Compare
    if p1 and p2:
        return filecmp.cmp(p1, p2, False), p1, p2
    else:
        return False, p1, p2


blacklist = (
    ["${analytics}",[]],
    ["{{analytics}}",[]],
    ["disqus_",['comments_helper.tmpl', 'disqus_helper.tmpl']],
    ["addthis",[]],
    ["namespace file=",[]],
)

if __name__ == "__main__":
    colorama.init()
    if len(sys.argv) == 1:
        sanity_check()
    else:
        for a in sys.argv[1:]:
            sanity_check(a)
