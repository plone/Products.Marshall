# Marshall: A framework for pluggable marshalling policies
# Copyright (C) 2004-2006 Enfold Systems, LLC
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
"""
"""

import re
import difflib

# Load fixture
from plone.app.testing.bbb_at import PloneTestCase


def normalize_tabs(s):
    s = re.sub(r"[ \t]+", " ", s)
    return s


def normalize_space(s):
    s =  re.sub(r"[\r\n]+", r'\r\n', s)
    return s


class BaseTest(PloneTestCase):
    """Base Test"""

    def compare(self, one, two):
        diff = difflib.ndiff(one.splitlines(), two.splitlines())
        diff = '\n'.join(list(diff))
        return diff

    def assertEqualsDiff(self, one, two, normalize=True):
        if normalize:
            one, two = normalize_tabs(one), normalize_tabs(two)
        one, two = normalize_space(one), normalize_space(two)
        self.failUnless(one.splitlines() == two.splitlines(),
                        self.compare(one, two))
