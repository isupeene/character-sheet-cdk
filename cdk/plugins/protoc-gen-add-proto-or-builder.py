import string
import sys

from google.protobuf import descriptor_pb2 as descriptor
from google.protobuf.compiler import plugin_pb2 as plugin

FUNCTION_TEMPLATE = """
      public Builder add{field_name}({type_name}OrBuilder value) {{
        if (value instanceof {type_name}) {{
          add{field_name}(({type_name}) value);
        }}
        else {{
          add{field_name}(({type_name}.Builder) value);
        }}
        return this;
      }}
      
      public Builder addAll{field_name}({type_name}OrBuilder... values) {{
        for ({type_name}OrBuilder value : values) {{
          add{field_name}(value);
        }}
        return this;
      }}
"""

def generate_add_proto_or_builder_functions(request_file, message_type):
    add_proto_or_builder_functions = []
    insertion_point = "builder_scope:{}.{}".format(request_file.package, message_type.name)

    for field in [f for f in message_type.field if f.label == descriptor.FieldDescriptorProto.LABEL_REPEATED and f.type == descriptor.FieldDescriptorProto.TYPE_MESSAGE]:
        CamelCaseName = string.capwords(field.name, "_").replace("_", "") if field.name != "class" else "Class_"
        simplified_type_name = field.type_name.replace(".ca.isupeene.charactersheet.proto.", "")  # TODO: Try using full type name?
        add_proto_or_builder_functions.append(FUNCTION_TEMPLATE.format(field_name=CamelCaseName, type_name=simplified_type_name))

    return add_proto_or_builder_functions, insertion_point


def generate_code(request):
    response = plugin.CodeGeneratorResponse()
    for request_file in request.proto_file:
        java_file_path = "/".join(request_file.package.split(".") + [request_file.name.split("/")[-1].split(".")[0].capitalize() + ".java"])
        for message_type in request_file.message_type:
            add_proto_or_builder_functions, insertion_point = generate_add_proto_or_builder_functions(request_file, message_type)
            if add_proto_or_builder_functions:
                response_file = response.file.add()
                response_file.name = java_file_path
                response_file.insertion_point = insertion_point
                response_file.content = "\n\n".join(add_proto_or_builder_functions)
    return response

if __name__ == '__main__':
    # Parse request from stdin
    # https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/compiler/PluginProtos.CodeGeneratorRequest
    request = plugin.CodeGeneratorRequest()
    request.ParseFromString(sys.stdin.buffer.read())

    # Generate code and write to stdout
    # https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/compiler/PluginProtos.CodeGeneratorResponse
    sys.stdout.buffer.write(generate_code(request).SerializeToString())