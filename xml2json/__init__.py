from collections import defaultdict
import logging

import lxml.etree

def cast(string):
    '''Cast a string to its proper JSON value.

    @param string: str
        The string to cast.'''

    if '' == string.strip():
        return None

    return string

def simplify(data):
    '''Simplify a dictionary of data. If a key maps to a list of length one,
    then have the key map to just that object.

    @param data: dict
        The dictionary to simplify.'''

    for k, v in data.iteritems():
        if isinstance(v, list) and 1 == len(v):
            v = v[0]

        yield k, v

def recurse_xml(iterator, parent_attributes=None):
    '''Recurse into the XML, building up a dictionary structure of accumulated
    data.

    @param iterator: lxml.etree.iterparse iterator
        The iterator over XML events.'''

    data = defaultdict(list)
    for action, element in iterator:
        if 'start' == action:
            # Get the attributes in the opening tag and pass them into the 
            # recursive call.
            attributes = dict(('@'+k, v) for k, v in element.attrib.iteritems())

            # Recurse into the XML structure
            data[element.tag].append(recurse_xml(iterator, attributes))
        
        if 'end' == action:
            # Get the text between the opening and closing tag and cast it to
            # its proper data type
            text = cast(element.text)

            # Clear the element - we are done with it
            element.clear()

            # Update the data dict with any attributes that was in the parent's
            # opening tag.
            data.update(parent_attributes)

            # If data has key/value pairs in it, then this element is not a leaf
            # node. Add the text (if it is present) to the key value pairs and
            # return a dict. Otherwise, return the text by itself if this is a
            # leaf node.
            if 0 < len(data):
                if text is not None:
                    data[''] = text
                return dict(simplify(data))
            return text

    # Return the structure at this XML node and all children
    return dict(simplify(data))

def parse_xml(xml):
    '''Convert an XML file to an arbitrary nesting of dict objects.

    @param xml: file-like object
        The file containing the XML data to parse.'''

    # Listen to the start and end events
    events = ('start', 'end')

    # Get an iterator over the XML file, and recurse into the XML structure
    iterator = lxml.etree.iterparse(xml, events=events)

    try:
        data = recurse_xml(iterator)
        return data, None
    except lxml.etree.XMLSyntaxError as se:
        return None, 'There is a syntax error in the XML file.'

