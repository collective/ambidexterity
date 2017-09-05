# -*- coding: utf-8 -*-
"""
    Dexterity model manipulation
"""

from lxml import etree
from plone import api
import utilities

import re

SCHEMA_NAMESPACE = 'http://namespaces.plone.org/supermodel/schema'
FORM_NAMESPACE = 'http://namespaces.plone.org/supermodel/form'


def qname(tag, ns=SCHEMA_NAMESPACE):
    # return decorated tag
    return etree.QName(ns, tag).text


def efindall(e, tag, ns=SCHEMA_NAMESPACE):
    # element findall
    return e.findall(".//{}".format(qname(tag, ns)))


def efind(e, tag, ns=SCHEMA_NAMESPACE):
    return e.find(".//{}".format(qname(tag, ns)))


def usefulTypes():
    rez = []
    for fti in utilities.getSimpleDexterityFTIs():
        d = {}
        d['title'] = fti.title
        d['id'] = fti.getId()
        my_fields = []
        model_source = getattr(fti, 'model_source', None)
        if model_source is not None:
            root = etree.XML(model_source)
            for field in efindall(root, 'field'):
                df = dict(
                    id=field.attrib['name'],
                    ftype=field.attrib['type'],
                    validator=field.attrib.get(qname('validator', FORM_NAMESPACE)),
                )
                default = efind(field, 'defaultFactory')
                if default is not None:
                    default = default.text
                df['defaultFactory'] = default
                vocab_type = 'None'
                if efind(field, 'vocabulary') is not None:
                    vocab_type = 'vocabulary'
                if efind(field, 'values') is not None:
                    vocab_type = 'values'
                source = efind(field, 'source')
                if source is not None:
                    df['source'] = source.text
                    vocab_type = 'source'
                else:
                    df['source'] = None
                df['vocab_type'] = vocab_type
                my_fields.append(df)
        d['fields'] = my_fields
        rez.append(d)
    return rez


def getFTI(id):
    pt = api.portal.get_tool(name='portal_types')
    return getattr(pt, id)


def getModelSource(id):
    return getattr(getFTI(id), 'model_source')


def setModelSource(id, source):
    fti = getFTI(id)
    fti.manage_changeProperties(model_source=source)


def getModelRoot(id):
    return etree.XML(getModelSource(id))


def getFieldList(ctype_name):
    root = getModelRoot(ctype_name)
    rez = []
    for field in efindall(root, 'field'):
        rez.append(field.attrib['name'])
    return rez


def setModelSourceFromXML(id, root):
    source = etree.tostring(
        root,
        pretty_print=True,
        xml_declaration=True,
        encoding='utf8'
    )
    setModelSource(id, source)


def getFieldElement(root, field_name):
    for field in efindall(root, 'field'):
        if field.attrib['name'] == field_name:
            return field
    raise KeyError('Field "{}" not found'.format(field_name))


def setDefaultFactory(id, field_name):
    root = getModelRoot(id)
    field_element = getFieldElement(root, field_name)
    assert(efind(field_element, 'defaultFactory') is None)
    df = etree.SubElement(field_element, qname('defaultFactory'))
    df.text = 'collective.ambidexterity.default'
    setModelSourceFromXML(id, root)


def removeDefaultFactory(id, field_name):
    root = getModelRoot(id)
    field_element = getFieldElement(root, field_name)
    df = efind(field_element, 'defaultFactory')
    field_element.remove(df)
    setModelSourceFromXML(id, root)


def setVocabulary(id, field_name):
    root = getModelRoot(id)
    field_element = getFieldElement(root, field_name)
    assert(efind(field_element, 'source') is None)

    # remove values or vocabulary elements
    value_element = efind(field_element, 'values')
    if value_element is not None:
        field_element.remove(value_element)
    vocabulary_element = efind(field_element, 'vocabulary')
    if vocabulary_element is not None:
        field_element.remove(vocabulary_element)

    df = etree.SubElement(field_element, qname('source'))
    df.text = 'collective.ambidexterity.vocabulary'
    setModelSourceFromXML(id, root)


def removeVocabulary(id, field_name):
    root = getModelRoot(id)
    field_element = getFieldElement(root, field_name)
    df = efind(field_element, 'source')
    field_element.remove(df)
    etree.SubElement(field_element, qname('values'))
    setModelSourceFromXML(id, root)


def removeValidator(id, field_name):
    root = getModelRoot(id)
    field_element = getFieldElement(root, field_name)
    del field_element.attrib[qname('validator', FORM_NAMESPACE)]
    setModelSourceFromXML(id, root)


def setValidator(id, field_name):
    # etree in lxml 3.5.0 has problems setting namespace in attributes,
    # so we've got to do this via source.
    s = getModelSource(id)

    # make sure we have a "form" xmlns
    if s.find('xmlns:form="http://namespaces.plone.org/supermodel/form"') < 0:
        s.replace("<model", '<model xmlns:form="http://namespaces.plone.org/supermodel/form"')

    mo = re.search(r"""\<field.+?name="{}".+?\>""".format(field_name), s)
    assert(mo is not None)
    orig_tag = mo.group(0)
    # remove any existing form attribute
    tag = re.sub(r'form:validator=".+?"', '', orig_tag)
    tag = tag.replace('>', ' form:validator="collective.ambidexterity.validate">')
    s = s.replace(orig_tag, tag)
    setModelSource(id, s)


def setAmbidexterityView(id):
    fti = getFTI(id)
    fti.manage_changeProperties(view_methods=['@@ambidexterityview', ])
