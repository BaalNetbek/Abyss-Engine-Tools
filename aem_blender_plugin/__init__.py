import bpy
import os
from bpy_extras.io_utils import ImportHelper, ExportHelper
from bpy.props import StringProperty, FloatProperty, EnumProperty, BoolProperty, CollectionProperty
from bpy.types import Operator
import struct
from numpy import float32, short
from enum import Enum


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

SCALE = 0.01
NORMALS_SCALE = 3.0517578126e-05 # 1>>15


AEMflags = {
    "uvs": 2,  # these are Texture Coordinates if you will
    "normals": 4,
    "animations": 8,  # guess
    "faces": 16
}

AEMVersion = {
    "AEMesh":0,
    "V2AEMesh":2,
    "V3AEMesh":3,
    "V4AEMesh":4,
    "V5AEMesh":5
}  

def sign_check(c, cs):
    if (cs==0xFFFF and c<0) or (cs==0x0 and c>= 0):
        return 1
    return 1

def read_floats(file, count=1):
    return [float32(struct.unpack('f', file.read(4))[0]) for _ in range(count)]
    
def read_float(file):
    return float32(struct.unpack('f', file.read(4))[0])

def read_shorts(file, count=1):
    return [short(struct.unpack('h', file.read(2))[0]) for _ in range(count)]
    
def read_short(file):
    return short(struct.unpack('h', file.read(2))[0])
    
  

    
def import_aem(file_path):
    file_aem = open(file_path, 'rb')
    magic = "" #file_aem.read(5).decode("utf-8")
    magic_len = 0
    while magic[-4:] != "Mesh": 
        magic += file_aem.read(1).decode("utf-8")
        magic_len += 1
        if magic_len>8:
            #self.report ...
            file_aem.close()
            print("Unsupported .aem file. Error reading header")
            return
    file_aem.read(1)
    flags = int.from_bytes(file_aem.read(1))
    if flags & AEMflags["normals"] != 0:
        normals_present = True
    else:
        normals_present = False
        
    if AEMVersion[magic] in (4,5):
        with file_aem:
            file_aem.seek(0x18)
            f_num = int(read_short(file_aem)/3)
            faces = [(read_short(file_aem), read_short(file_aem), read_short(file_aem)) for _ in range(f_num)]
            v_num = read_short(file_aem)

            vertices = [(read_float(file_aem) * SCALE, read_float(file_aem) * SCALE, read_float(file_aem) * SCALE) for _ in range(v_num)]
            vertices = [(x, -z, y) for x, y, z in vertices]
            uvs = [(read_float(file_aem), read_float(file_aem)) for _ in range(v_num)]
            normals = [(read_float(file_aem), read_float(file_aem), read_float(file_aem)) for _ in range(v_num)]
            normals = [(x, -z, y) for x, y, z in normals]
            
        obj_name = os.path.basename(file_path).split('.')[0]    
        mesh = bpy.data.meshes.new(name=obj_name + "_Mesh")
        obj = bpy.data.objects.new(obj_name, mesh)
        bpy.context.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)

        mesh.from_pydata(vertices, [], faces)
        mesh.update()

        uv_layer = mesh.uv_layers.new(name="UVMap")
        for i, uv in enumerate(uvs):
            uv_layer.data[i].uv = uv
        
        if normals_present == True:
            mesh.normals_split_custom_set_from_vertices(normals)
        
    elif AEMVersion[magic] in (0,2):
        with file_aem:
            if AEMVersion[magic] == 2:
            #    data_start_point = 0xA
                vertex_cord_size = 6
            if AEMVersion[magic] == 0:
            #    data_start_point = 0x8
                vertex_cord_size = 3
            #file_aem.seek(data_start_point)    
            f_num = int(read_short(file_aem)/3)
            print(hex(f_num))
            faces = [(read_short(file_aem), read_short(file_aem), read_short(file_aem)) for _ in range(f_num)]
            v_num = read_short(file_aem)
            v_block = [tuple(read_short(file_aem) for _ in range(vertex_cord_size)) for _ in range(v_num)]
            uvs = [(struct.unpack("h", file_aem.read(2))[0], struct.unpack("h", file_aem.read(2))[0]) for _ in range(v_num)]
            if normals_present == True:
                normals_block = [(read_short(file_aem), read_short(file_aem), read_short(file_aem)) for _ in range(v_num)]
                        
        if magic == "V2AEMesh":
            #if cord is not negative sign bytes are 0000 else they are FFFF
            vertices = [(x*SCALE * sign_check(x, xs), -z*SCALE * sign_check(z, zs), y*SCALE * sign_check(y, ys)) for x, xs, y, ys, z, zs in v_block]                  
        if magic == "AEMesh":
            vertices = [(x*SCALE, -z*SCALE, y*SCALE) for x, y, z in v_block] 
            
        if normals_present == True:
            normals = [(x*NORMALS_SCALE, -z*NORMALS_SCALE, y*NORMALS_SCALE) for x,y,z in normals_block]
        
        obj_name = os.path.basename(file_path).split('.')[0]    
        mesh = bpy.data.meshes.new(name=obj_name + "_Mesh")
        obj = bpy.data.objects.new(obj_name, mesh)
        bpy.context.collection.objects.link(obj)
        bpy.context.view_layer.objects.active = obj
        obj.select_set(True)
        
        mesh.from_pydata(vertices, [],faces)
        mesh.update()

        uv_layer = mesh.uv_layers.new(name="UVMap")
        
        for poly in mesh.polygons:
            for loop_index in poly.loop_indices:
                loop_vert_index = mesh.loops[loop_index].vertex_index
                uv_layer.data[loop_index].uv = uvs[loop_vert_index]
            
        for uv_data in uv_layer.data:
            uv_data.uv /= 4096
        
        if normals_present == True:
            mesh.normals_split_custom_set_from_vertices(normals)
        
    else:
        file_aem.close()
        print("Unsupported file AEM version.")
        return


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
            file_aem.write(struct.pack("f", v_x[v_id[i]] / SCALE))
            file_aem.write(struct.pack("f", v_y[v_id[i]] / SCALE))
            file_aem.write(struct.pack("f", v_z[v_id[i]] / SCALE))
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
        default=SCALE,
        min=0.001, max=1.0
    )

    def execute(self, context):
        global SCALE
        SCALE = self.scale
        
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
        default=SCALE,
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
        global SCALE
        SCALE = self.scale

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