Plugin support importing V4- and V5AEMs with UVs and normals but stripping animation and skeleton data.
Also it supports exporting V5AEMs with automatic traingulation (no animations yet) and some quality of nolife features like console import/export.


```python
bpy.ops.import_mesh.aem(filepath="", filter_glob="*.aem", files=[], scale_factor=0.01)
bpy.ops.export_mesh.aem(filepath="", check_existing=True, filter_glob="*.aem", scale_factor=0.01, triangulate_method='BEAUTY', add_prefix="", add_suffix="", overwrite=False)
```
I had to keep indirect export becouse using direct Blender object to AEM export with function as one below gives broken results for custom meshes but correct for meshes that were initialy imported from AEM.
Which I don't understand why is happening.   

```python
def export_aem(obj, file_path, scale):
    mesh = obj.data.copy()
    bpy.context.collection.objects.link(bpy.data.objects.new("temp", mesh))
    bpy.context.view_layer.objects.active = bpy.context.collection.objects['temp']
    bpy.ops.object.mode_set(mode='EDIT')
    bpy.ops.mesh.select_all(action='SELECT')
    bpy.ops.mesh.quads_convert_to_tris()
    bpy.ops.object.mode_set(mode='OBJECT')

    vertices = [v.co for v in mesh.vertices]
    uvs = [uv.uv for uv in mesh.uv_layers.active.data]
    normals = [v.normal for v in mesh.vertices]

    addon_directory = os.path.dirname(os.path.abspath(__file__))
    header_file_path = os.path.join(addon_directory, 'header.bin')
    
    with open(header_file_path, 'rb') as file_header, open(file_path, 'wb') as file_aem:
        header = file_header.read(24)
        file_aem.write(header)
        
        v_num = ushort(len(vertices))
        file_aem.write(struct.pack("H", v_num))
        for i in range(v_num):
            file_aem.write(struct.pack("H", ushort(i)))

        file_aem.write(struct.pack("H", v_num))
        for v in vertices:
            file_aem.write(struct.pack("f", v.x * scale))
            file_aem.write(struct.pack("f", v.y * scale))
            file_aem.write(struct.pack("f", v.z * scale))

        for uv in uvs:
            file_aem.write(struct.pack("f", uv.x))
            file_aem.write(struct.pack("f", uv.y))

        for n in normals:
            file_aem.write(struct.pack("f", n.x))
            file_aem.write(struct.pack("f", n.y))
            file_aem.write(struct.pack("f", n.z))

        header = file_header.read(56)
        file_aem.write(header)

    bpy.data.meshes.remove(mesh)
```
