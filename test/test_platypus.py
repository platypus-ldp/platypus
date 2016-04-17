import pytest
import rdflib

from platypus.platypus import LdpResource, NonRdfResource
# TODO: figure out better naming/org for submodules

# vagrant fedora instance
ldp_server_uri = 'http://127.0.0.1:8080/fcrepo/rest/'
# derby-ldp
# ldp_server_uri = 'http://localhost:4567/'

# @pytest.fixture(scope="module")
# def ldp_server(request):
#     ldp_server_uri = 'http://127.0.0.1:8080/fcrepo/rest/'

#     def fin():
#         print ("teardown")
#     request.addfinalizer(fin)
#     return ldp_server_uri




@pytest.fixture
def ldp_resource(request):
    # todo: maybe create a test container, where all test
    # resources can be created and then removed in tear down

    res = LdpResource(container=ldp_server_uri)
    res.dc_title = 'Platypus test item'
    res.create()

    def fin():
        print ("deleting %s" % repr(res))
        res.delete()

    request.addfinalizer(fin)
    return res

class TestLdpResource:

    def test_create(self):
        res = LdpResource(container=ldp_server_uri)
        res.dc_title = 'Platypus test container'
        assert res.create()
        print res.uri
        assert res.uri, 'created LdpResource should have non-empty uri'


    def test_update(self, ldp_resource):
        assert isinstance(ldp_resource.uriref, rdflib.URIRef)
        print 'resource title = ', ldp_resource.dc_title
        # no changes - save should do nothing
        # todo: currently returning false
        # saved = ldp_resource.save()
        # print 'saved == ', saved
        # assert saved is None

        # make some changes
        ldp_resource.dc_title = 'A new title'
        ldp_resource.dc_publisher = 'platypus-ldp'
        saved = ldp_resource.save()
        print 'saved == ', saved

        # assert ldp_resource.save() == True,
        #    'save should return True on success'
        assert saved == True, 'save should return True on success'

    def test_delete(self, ldp_resource):
        print 'resource title = ', ldp_resource.dc_title


#     # interact with existing cover object created in fedora4 tutorial
# cover = LdpResource('http://localhost:4567/cover')
# print cover.dc_publisher
# print cover.dc_title
# for t in cover.rdf_types:
#     print t

# cover.dc_publisher = 'platypus-ldp'
# del cover.dc_title
# print cover.dc_publisher
# print cover.dc_title
# print cover.graph_updates.serialize()
# cover.create()

# print 'created ', cover.created
# print 'last modified ', cover.last_modified
# print 'created by', cover.created_by

# for m in cover.members:
#     print m.uri

# create a new object within the cover container
# newobj = LdpResource(container='http://localhost:8080/fcrepo/rest/cover')
# newobj.dc_title = 'create new'
# newobj.create()

# create a non-rdf resource within the cover container
# newfile = NonRdfResource(container='http://localhost:4567/cover')
# with open('fixtures/images/SIPI_Jelly_Beans_4.1.07.tiff') as tiff:
#     newfile.content = tiff
#     newfile.filename = 'SIPI_Jelly_Beans_4.1.07.tiff'
#     newfile.content_type = 'image/tiff'

#     newfile.create()
