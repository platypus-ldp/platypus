#!/usr/bin/env python

# fedora 4 test client
# NOTE: this is experimental / spike code!!
# (written to get a sense of  the fedora 4 LDP API)
import requests
import rdflib


DC = rdflib.Namespace('http://purl.org/dc/elements/1.1/')
XMLSchema = rdflib.Namespace('http:////www.w3.org/2001/XMLSchema#')
LDP = rdflib.Namespace('http://www.w3.org/ns/ldp#')

FEDORA4 = rdflib.Namespace('http://fedora.info/definitions/v4/repository#')

class Value(object):
    """A data descriptor that gets a rdf single value.
    """
    # break out into types by xmlschema type, like eulxml?
    # StringField, DateField, etc. then conversion is easy...
    # but do we always know what a field will contain?

    def __init__(self, predicate, datatype=None, normalize=False):
        self.predicate = predicate
        self.datatype = datatype
        self.normalize = normalize

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        return self.to_python(obj.graph.value(obj.uriref, self.predicate))

    def __set__(self, obj, value):

        # if any namespace prefixes were specified, bind them before adding the tuple
        # for prefix, ns in self.ns_prefix.iteritems():
            # obj.rels_ext.content.bind(prefix, ns)

        # TODO: do we need to check that subject matches self.object_type (if any)?

        if value == self.__get__(obj):
            print 'no change, returning'
            return


        if isinstance(value, rdflib.URIRef):
            uri = value
        elif hasattr(value, 'uriref'):
            uri = value.uriref
        elif self.datatype:
            uri = rdflib.Literal(value, datatype=self.datatype)
        else:
            print 'rdf literal'
            uri = rdflib.Literal(value, datatype=XMLSchema.string)

        # update requires delete/insert, so make a note of what we're replacing
        old_objs = list(obj.graph.objects(obj.uriref, self.predicate))
        if old_objs:
            #FIXME: doesn't match if one has datatype and the other doesn't
            print 'old objs = ', repr(old_objs[0]), ' new uri = ', repr(uri)
            print old_objs[0].__class__
            if old_objs[0] == uri:

                print 'no change, returning'
                return
            print 'marking ', old_objs[0], ' for deletion'
            obj.graph_deletes.set((obj.uriref, self.predicate, old_objs[0]))
        new_triple = (obj.uriref, self.predicate, uri)
        obj.graph.set(new_triple)
        obj.graph_updates.set(new_triple)

    def __delete__(self, obj):
        old_objs = list(obj.graph.objects(obj.uriref, self.predicate))
        if old_objs:
            #FIXME: doesn't match if one has datatype and the other doesn't
            print 'marking ', old_objs[0], ' for deletion'
            obj.graph_deletes.set((obj.uriref, self.predicate, old_objs[0]))
            obj.graph.remove((obj.uriref, self.predicate, old_objs[0]))


    def to_python(self, val):
        # NOTE: could check for and use val.toPython() ...


        # if we got a 'none' return as is (don't convert to "None")
        if val is None:
            return val
        if self.datatype is not None:
            val = rdflib.Literal(val, datatype=self.datatype).toPython()
        elif isinstance(val, rdflib.Literal):
            val = val.toPython()

        # NOTE: doesn't convert rdflib.uriref; should it?

        if self.normalize:
            val = normalize_whitespace(val)
        return val



class ValueList(Value):
    """A data descriptor that gets a list of rdf values.
    """

    def __init__(self, predicate, datatype=None, normalize=False):
        self.predicate = predicate
        self.datatype = datatype
        self.normalize = normalize

    def __get__(self, obj, objtype=None):
        if obj is None:
            return self

        results = [self.to_python(o) for o in obj.graph.objects(obj.uriref, self.predicate)]
        return results



class ResourceList(object):

    def __init__(self, predicate, resource_type):
        self.predicate = predicate
        self.resource_type = resource_type

    def __get__(self, obj, objtype):
        if obj is None:
            return self
        if self.resource_type == 'self':
            resource_type = obj.__class__
        else:
            resource_type = self.resource_type
        return [resource_type(o) for o in obj.graph.objects(obj.uriref, self.predicate)]


class DublinCoreMixin(object):
    dc_title = Value(DC.title)
    dc_creator = Value(DC.creator)
    dc_publisher = Value(DC.publisher)

class FedoraMixin(object):
    created = Value(FEDORA4.created)
    last_modified = Value(FEDORA4.lastModified)
    frozen_uuid = Value(FEDORA4.frozenUuid)
    frozen_primary_types = Value(FEDORA4.frozenPrimaryTypes)
    frozen_mixin_types = Value(FEDORA4.frozenMixinTypes)
    uuid = Value(FEDORA4.uuid)
    last_modified_by = Value(FEDORA4.lastModifiedBy)
    created_by = Value(FEDORA4.createdBy)

    # fedora-specific things would go here, e.g.
    # versions
    # fixity
    # transform
    # repo object: support transactions, define transforms (?)


class LdpResource(DublinCoreMixin, FedoraMixin):

    rdf_types = ValueList(rdflib.RDF.type)

    members = ResourceList(LDP.contains, 'self')


    def __init__(self, uri=None, container=None): # optional when creating new...
        self.container = container
        self.uri = uri

        # maybe a dynamic resource that figures out what kind of thing it is
        # at initialization?  make a head request and then initialize
        # as appropriate type (passing in data to avoid repeating the request)
        # response = requests.head(self.uri)
        # print response.headers
        # need requests to do content-negotiation, last modified, etc
        # load on demand

        self.graph = rdflib.Graph()
        # create a graph to hold updates so we can patch just the changes
        self.graph_updates = rdflib.Graph()
        self.graph_deletes = rdflib.Graph()

        if self.uri is not None:
            response = requests.get(self.uri, headers={"Accept" : 'application/rdf+xml'})
            print response.headers

        # NOTE: header says what kind of thing this is,
        # e.g. for container:
        #  'link': '<http://www.w3.org/ns/ldp#Resource>;rel="type",
        # <http://www.w3.org/ns/ldp#Container>;rel="type",
        # <http://www.w3.org/ns/ldp#BasicContainer>;rel="type"'
        # or for binary:
        #'link': '<http://www.w3.org/ns/ldp#Resource>;rel="type", <http://www.w3.org/ns/ldp#NonRDFSource>;rel="type",
        # <http://localhost:8080/fcrepo/rest/cover/cover2.jpg/fcr:metadata>; rel="describedby"',


        # don't try to load as rdf it isn't rdf!
            if response.headers['content-type'] == 'application/rdf+xml':

                # print response.content
                self.graph.parse(data=response.content)

        # for ns_prefix, ns in self.graph.namespaces():
        #     self.graph_updates.bind(ns_prefix, ns)

        # print rdflib.RDF.type
        # print '\n'.join(list(self.graph.objects(self.uriref, rdflib.RDF.type)))

    @property
    def uriref(self):
        if self.uri is not None:
            return rdflib.URIRef(self.uri)

        return rdflib.URIRef('')

    def create(self):
        # param opt
        # CHECKSUM (Optional) Provide a SHA-1 checksum which will be checked against the uploaded content to ensure error-free transfer.
        # headers
        # CONTENT-DISPOSITION (Optional) The filename provided in the content disposition header will be stored in a ebucore:filename property.
        # CONTENT-TYPE (Optional) MIME type of the uploaded binary or RDF content.
        # CONTENT-LOCATION (Optional) A URI to a resource to use instead of the request body
        #If the MIME type corresponds to a supported RDF format or SPARQL-Update, the uploaded content will be parsed as RDF and used to populate the child node properties.  RDF will be interpreted using the current resource as the base URI (e.g. <> will be expanded to the current URI). Namespaces must be declared in full.
        #        For other MIME types, the uploaded content will be used to create a binary resource.
        #SLUG - suggested name for new resource

        print self.graph.serialize()
        response = requests.post(self.container, headers={'content-type': 'application/rdf+xml'},
            data=self.graph.serialize())
        if response.status_code == requests.codes.created:
            # also returns etag
            self.uri = response.headers['location']
        print response
        print response.content

    def save(self):

        # for now, assuming patch update of rdf properties
        if not self.graph_deletes and not self.graph_updates:
            print 'no deletes or updates, returning'
            return

        prefixes = []
        # for ns_prefix, ns in self.graph_updates.namespaces():
        #     prefixes.append('PREFIX %s: <%s>' % (ns_prefix, ns))
        inserts = []
        for pred, obj in self.graph_updates.predicate_objects(self.uriref):
            inserts.append('<> <%s> "%s"' % (pred, obj))

        deletes = []
        for pred, obj in self.graph_deletes.predicate_objects(self.uriref):
            deletes.append('<> <%s> "%s"' % (pred, obj))

        delete = '''%(prefixes)s
        DELETE DATA
        { %(deletes)s }''' % {
            'prefixes': '\n'.join(prefixes),
            'inserts': ' .\n'.join(inserts),
            'deletes': ' .\n'.join(deletes)
        }

        print delete
        response = requests.patch(self.uri, delete,
            headers={"Content-Type": 'application/sparql-update'})
        print response

        update = '''%(prefixes)s
        INSERT DATA
        { %(inserts)s }
        ''' % {
            'uri': self.uri,
            'prefixes': '\n'.join(prefixes),
            'inserts': ' .\n'.join(inserts),
            'deletes': ' .\n'.join(deletes)
        }

        # INSERT {
        #   %(inserts)s
        # } WHERE {}
        # ''' % {
        #     'prefixes': '\n'.join(prefixes),
        #     'inserts': ' .\n'.join(inserts)
        # }

        print update
        response = requests.patch(self.uri, update,
            headers={"Content-Type": 'application/sparql-update'})
        print response.content


class NonRdfResource(object):
    content = None
    checksum = None # sha-1 checksum
    filename = None
    content_type = None

    def __init__(self, uri=None, container=None):
        # same as ldp resource
        self.container = container
        self.uri = uri

    def create(self):
        headers = {}
        if self.content_type:
            headers['Content-Type'] = self.content_type
        if self.filename:
            headers['Content-Disposition'] = self.filename

        print 'headers = ', headers

        response = requests.post(self.container,
            headers=headers, data=self.content)
        if response.status_code == requests.codes.created:
            # also returns etag
            self.uri = response.headers['location']
        print response
        print response.content


# interact with existing cover object created in fedora4 tutorial
cover = LdpResource('http://localhost:8080/fcrepo/rest/cover')
print cover.dc_publisher
print cover.dc_title
for t in cover.rdf_types:
    print t

cover.dc_publisher = 'emory'
del cover.dc_title
print cover.dc_publisher
print cover.dc_title
print cover.graph_updates.serialize()
cover.save()

print 'created ', cover.created
print 'last modified ', cover.last_modified
print 'created by', cover.created_by

for m in cover.members:
    print m.uri

# create a new object within the cover container
# newobj = LdpResource(container='http://localhost:8080/fcrepo/rest/cover')
# newobj.dc_title = 'create new'
# newobj.create()

# create a non-rdf resource within the cover container
newfile = NonRdfResource(container='http://localhost:8080/fcrepo/rest/cover')
with open('/Users/rsutton/Downloads/networks-book.pdf') as pdf:
    newfile.content = pdf
    newfile.filename = 'networks-book.pdf'
    newfile.content_type = 'application/pdf'

    newfile.create()
