import bpy
import os
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import StringProperty, FloatProperty, EnumProperty, BoolProperty, CollectionProperty
from bpy.types import Operator
import struct
from numpy import float32, ushort


bl_info = {
    "name": "AEM Blender Plugin",
    "author": "Chuck Norris",
    "version": (1, 1),
    "blender": (4, 1, 0),
    "location": "File > Import-Export",
    "description": "AByss Engine Mesh V4,V5 Import / V5 Export",
    "warning": "",
    "category": "Import-Export",
}

SCALE_FACTOR = 0.01

def read_floats(file, count):
    return [float32(struct.unpack("f", file.read(4))[0]) for _ in range(count)]

def import_aem(file_path):
    file_aem = open(file_path, 'rb')
    version = file_aem.read(5).decode("utf-8")
    if version != "V5AEM" and version != "V4AEM":
        file_aem.close()
        print("Unsupported file AEM version.")
    else:
        with open(file_path, 'rb') as file_aem:
            
            file_aem.seek(24)
            v_num = struct.unpack("H", file_aem.read(2))[0]
            file_aem.seek(v_num * 2 + 2, 1)

            vertices = [(read_floats(file_aem, 1)[0] * SCALE_FACTOR, read_floats(file_aem, 1)[0] * SCALE_FACTOR, read_floats(file_aem, 1)[0] * SCALE_FACTOR) for _ in range(v_num)]
            vertices = [(x, -z, y) for x, y, z in vertices]
            uvs = [(read_floats(file_aem, 1)[0], read_floats(file_aem, 1)[0]) for _ in range(v_num)]
            normals = [(read_floats(file_aem, 1)[0], read_floats(file_aem, 1)[0], read_floats(file_aem, 1)[0]) for _ in range(v_num)]
            normals = [(x, -z, y) for x, y, z in normals]
            
        obj_name = os.path.basename(file_path).split('.')[0]    
        mesh = bpy.data.meshes.new(name=obj_name + "_Mesh")
        obj = bpy.data.objects.new(obj_name, mesh)
        bpy.context.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        mesh.from_pydata(vertices, [], [(i, i + 1, i + 2) for i in range(0, v_num, 3)])
        mesh.update()

        uv_layer = mesh.uv_layers.new(name="UVMap")
        for i, uv in enumerate(uvs):
            uv_layer.data[i].uv = uv

        mesh.normals_split_custom_set_from_vertices(normals)

def convert_obj_to_aem(file_in,file_out):
    addon_directory = os.path.dirname(os.path.abspath(__file__))
    header_file_path = os.path.join(addon_directory, 'header.bin')
    file_header = open(header_file_path, 'rb')
    header = file_header.read(24)
    file_obj = open(file_in, 'r')
    file_aem = open(file_out, 'ab')
    file_aem.write(header)
    file_read = file_obj.readlines()
    v_x = []
    v_y = []
    v_z = []
    vt_x = []
    vt_y = []
    vn_x = []
    vn_y = []
    vn_z = []
    v_id = []
    vt_id = []
    vn_id = []
    print('\n', 'Analyzing obj file...')
    for i in range(len(file_read)):
        if file_read[i][0] == 'v' and file_read[i][1] == ' ':
            v_x.append(float32(file_read[i].split()[1]))
            v_y.append(float32(file_read[i].split()[2]))
            v_z.append(float32(file_read[i].split()[3]))
        elif file_read[i][0] == 'v' and file_read[i][1] == 't':
            vt_x.append(float32(file_read[i].split()[1]))
            vt_y.append(float32(file_read[i].split()[2]))
        elif file_read[i][0] == 'v' and file_read[i][1] == 'n':
            vn_x.append(float32(file_read[i].split()[1]))
            vn_y.append(float32(file_read[i].split()[2]))
            vn_z.append(float32(file_read[i].split()[3]))
        elif file_read[i][0] == 'f':
            for j in range(3):
                v_id.append(ushort(file_read[i].split()[j + 1].split('/')[0]) - 1)
                vt_id.append(ushort(file_read[i].split()[j + 1].split('/')[1]) - 1)
                vn_id.append(ushort(file_read[i].split()[j + 1].split('/')[2]) - 1)
    if v_x and vt_x and vn_x and v_id and len(vt_id) == len(v_id) and len(vn_id) == len(v_id) and len(v_id) < 65536:
        v_num = ushort(len(v_id))
        file_aem.write(struct.pack("H", v_num))
        print('\n', '# Faces', v_num // 3)
        for i in range(v_num):
            file_aem.write(struct.pack("H", ushort(i)))
        file_aem.write(struct.pack("H", v_num))
        print('\n', '# Vertices', v_num)
        for i in range(v_num):
            file_aem.write(struct.pack("f", v_x[v_id[i]] / SCALE_FACTOR))
            file_aem.write(struct.pack("f", v_y[v_id[i]] / SCALE_FACTOR))
            file_aem.write(struct.pack("f", v_z[v_id[i]] / SCALE_FACTOR))
        print('\n', '# UVs', v_num)
        for i in range(v_num):
            file_aem.write(struct.pack("f", vt_x[vt_id[i]]))
            file_aem.write(struct.pack("f", vt_y[vt_id[i]]))
        print('\n', '# Normals', v_num)
        for i in range(v_num):
            file_aem.write(struct.pack("f", vn_x[vn_id[i]]))
            file_aem.write(struct.pack("f", vn_y[vn_id[i]]))
            file_aem.write(struct.pack("f", vn_z[vn_id[i]]))
    elif len(v_id) > 65535:
        print('\n', 'Error: Too many vertices to convert, please use low-poly model')
    else:
        print('\n', 'Error: UVs or Normals data lost. Please check obj file')

    header = file_header.read(56)
    file_aem.write(header)
    file_header.close()
    file_aem.close()
    file_obj.close()
    print('\n', 'Done', '\n')

class ImportAEM(Operator, ImportHelper):
    bl_idname = "import_mesh.aem"
    bl_label = "Import AEM"
    bl_options = {'UNDO'}

    filename_ext = ".aem"
    filter_glob: StringProperty(default="*.aem", options={'HIDDEN'})
    
    files: CollectionProperty(type=bpy.types.PropertyGroup)
    scale: FloatProperty(
        name="Scale Factor",
        description="Scale factor for imported objects",
        default=SCALE_FACTOR,
        min=0.001, max=1.0
    )

    def execute(self, context):
        global SCALE_FACTOR
        SCALE_FACTOR = self.scale
        
        if len(self.filepath) < 1:
            print('No valid AEM provided.')
            return {'FINISHED'}
        if len(self.files) > 1:
            directory = os.path.dirname(self.filepath)
            for file in self.files:
                file_path = os.path.join(directory, file.name)
                import_aem(file_path)
        else:
            import_aem(self.filepath)
            
        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "scale")

class ExportAEM(Operator, ExportHelper):
    bl_idname = "export_mesh.aem"
    bl_label = "Export AEM"
    bl_options = {'UNDO'}

    filename_ext = ".aem"
    filter_glob: StringProperty(default="*.aem", options={'HIDDEN'})

    scale: FloatProperty(
        name="Scale Factor (inverted)",
        description="Scale factor for exported objects - set the same as in import",
        default=SCALE_FACTOR,
        min=0.001, max=1.0
    )

    triangulate_method: EnumProperty(
        name="Triangulation Method",
        description="Method used for triangulating mesh",
        items=[
            ('BEAUTY', "Beauty", "Use Beauty method"),
            ('FIXED', "Fixed", "Use Fixed method"),
            ('FIXED_ALTERNATE', "Fixed Alternate", "Use Fixed Alternate method"),
            ('FIXED_ALTERNATE', "Fixed Alternate", "Use Fixed Alternate method"),
            ('SHORTEST_DIAGONAL', "Shortest Diagonal", "Use Shortest Diagonal method"),
            ('LONGEST_DIAGONAL', "Longest Diagonal", "Use Longest Diagonal method")
        ],
        default='BEAUTY'
    )
    
    add_prefix: StringProperty(
        name="Prefix",
        description="Prefix to add to exported files",
        default=""
    )

    add_suffix: StringProperty(
        name="Suffix",
        description="Suffix to add to exported files",
        default=""
    )

    overwrite: BoolProperty(
        name="Overwrite",
        description="Overwrite existing files",
        default=False
    )

    def execute(self, context):
        global SCALE_FACTOR
        SCALE_FACTOR = self.scale

        directory = os.path.dirname(self.filepath)
        
        if not context.selected_objects:
            self.report({'ERROR'}, "No objects selected")
            return {'CANCELLED'}
    
        for obj in context.selected_objects:
            if not obj.data or not isinstance(obj.data, bpy.types.Mesh):
                self.report({'ERROR'}, f"Object {obj.name} does not have a mesh")
                continue
            
            temp_file = os.path.join(directory, obj.name + '_temp.obj')
            if len(context.selected_objects) == 1:
                file_out = os.path.join(directory, self.add_prefix + os.path.splitext(os.path.basename(self.filepath))[0] + self.add_suffix + '.aem')
            else:
                file_out = os.path.join(directory, self.add_prefix + obj.name + self.add_suffix + '.aem')
    
            # Select only the current object
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
        
            #AEM does't support quads nor higher n-gons
            bpy.ops.object.modifier_add(type='TRIANGULATE')
            bpy.context.object.modifiers["Triangulate"].quad_method = self.triangulate_method
            bpy.context.object.modifiers["Triangulate"].min_vertices = 4
            if self.triangulate_method == 'BEAUTY':
                bpy.context.object.modifiers["Triangulate"].ngon_method = 'BEAUTY'
            else:
                bpy.context.object.modifiers["Triangulate"].ngon_method = 'CLIP'       

            # Export the selected object to OBJ
            bpy.ops.wm.obj_export(filepath=temp_file,forward_axis='NEGATIVE_Z',up_axis='Y', export_materials=False, export_selected_objects=True)
            bpy.ops.object.select_all(action='DESELECT')

            if not self.overwrite and os.path.exists(file_out):
                self.report({'WARNING'}, f"File {file_out} already exists and overwrite is disabled.")
                os.remove(temp_file)
                continue

            convert_obj_to_aem(temp_file, file_out)
            os.remove(temp_file)
            bpy.context.object.modifiers["Triangulate"].min_vertices = 4

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "scale")
        layout.prop(self, "triangulate_method")
        layout.prop(self, "add_prefix")
        layout.prop(self, "add_suffix")
        layout.prop(self, "overwrite")

def menu_func_import(self, context):
    self.layout.operator(ImportAEM.bl_idname, text="AEM v4,v5 (.aem)")

def menu_func_export(self, context):
    self.layout.operator(ExportAEM.bl_idname, text="AEM v5(.aem)")

def register():
    bpy.utils.register_class(ImportAEM)
    bpy.utils.register_class(ExportAEM)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)

def unregister():
    bpy.utils.unregister_class(ImportAEM)
    bpy.utils.unregister_class(ExportAEM)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)

if __name__ == "__main__":
    register()