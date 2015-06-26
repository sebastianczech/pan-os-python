#!/usr/bin/env python

# Copyright (c) 2014, Palo Alto Networks
#
# Permission to use, copy, modify, and/or distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

# Author: Brian Torres-Gil <btorres-gil@paloaltonetworks.com>


"""Base object classes for inheritence by other classes"""

import xml.etree.ElementTree as ET
import logging

import device
import errors as err

# set logging to nullhandler to prevent exceptions if logging not enabled
logger = logging.getLogger(__name__)


# PanObject type
class PanObject(object):
    XPATH = "/config"
    ENTRY = "/entry[@name='%s']"
    MEMBER = "/member[text()='%s']"

    def __init__(self, name=None):
        self.name = name
        self.parent = None
        self.children = []

    def add(self, child):
        child.parent = self
        self.children.append(child)
        return child

    def pop(self, index):
        child = self.children.pop(index)
        child.parent = None
        return child

    def remove_by_name(self, name, cls=None):
        index = PanObject.find(self.children, name, cls)
        if index is None:
            return None
        return self.pop(index)  # Just remove the first child that matches the name

    def xpath(self):
        return self.XPATH

    def element(self):
        return "<entry name=\"%s\"></entry>" % self.name

    def apply(self):
        self.pandevice().xapi.edit(self.xpath(), self.element())

    def create(self):
        # Remove the last part from the xpath
        xpath = self.xpath().rsplit("/", 1)[0]
        self.pandevice().xapi.set(xpath, self.element())

    def delete(self):
        self.pandevice().xapi.delete(self.xpath())
        if self.parent is not None:
            self.parent.remove_by_name(self.name, type(self))

    def pandevice(self):
        if issubclass(self.__class__, device.PanDevice):
            return self
        else:
            if self.parent is None:
                raise err.PanDeviceNotSet("No PanDevice set for object tree")
            else:
                return self.parent.pandevice()

    @classmethod
    def find(cls, list_of_panobjects, name, class_type=None):
        if class_type is None:
            class_type = cls
        indexes = [i for i, child in enumerate(list_of_panobjects) if
                   child.name == name and issubclass(type(child), class_type)]
        for index in indexes:
            return index  # Just return the first index that matches the name
        return None