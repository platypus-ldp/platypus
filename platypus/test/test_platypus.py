# interact with existing cover object created in fedora4 tutorial
cover = LdpResource('http://localhost:4567/cover')
print cover.dc_publisher
print cover.dc_title
for t in cover.rdf_types:
    print t

cover.dc_publisher = 'platypus-ldp'
del cover.dc_title
print cover.dc_publisher
print cover.dc_title
print cover.graph_updates.serialize()
cover.create()

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
newfile = NonRdfResource(container='http://localhost:4567/cover')
with open('fixtures/images/SIPI_Jelly_Beans_4.1.07.tiff') as tiff:
    newfile.content = tiff
    newfile.filename = 'SIPI_Jelly_Beans_4.1.07.tiff'
    newfile.content_type = 'image/tiff'

    newfile.create()
