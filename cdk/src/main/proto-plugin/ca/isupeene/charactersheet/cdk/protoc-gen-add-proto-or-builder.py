import string
import sys

from google.protobuf import descriptor_pb2 as descriptor
from google.protobuf import text_format  # DO NOT SUBMIT
from google.protobuf.compiler import plugin_pb2 as plugin

import comment_tree


FUNCTION_TEMPLATE = """
      {comments}
      public Builder add{field_name}({type_name}OrBuilder value) {{
        if (value instanceof {type_name}) {{
          add{field_name}(({type_name}) value);
        }}
        else {{
          add{field_name}(({type_name}.Builder) value);
        }}
        return this;
      }}
      
      {comments}
      public Builder addAll{field_name}({type_name}OrBuilder... values) {{
        for ({type_name}OrBuilder value : values) {{
          add{field_name}(value);
        }}
        return this;
      }}
"""


LEADING_AND_TRAILING_TEMPLATE = """
      /**
        <pre>
        {leading_comments}
        
        {trailing_comments}
        </pre>
        
        <code>repeated {type_name} {snake_field_name} = {tag_number};</code> 
      */"""


LEADING_ONLY_TEMPLATE = """
      /**
        <pre>
        {leading_comments}
        </pre>
        
        <code>repeated {type_name} {snake_field_name} = {tag_number};</code> 
      */"""


TRAILING_ONLY_TEMPLATE = """
      /**
        <pre>
        {trailing_comments}
        </pre>
        
        <code>repeated {type_name} {snake_field_name} = {tag_number};</code> 
      */"""


NEITHER_TEMPLATE = """
      /**
        <code>repeated {type_name} {snake_field_name} = {tag_number};</code> 
      */"""


def make_comments(leading_comments, trailing_comments, type_name, snake_field_name, tag_number):
    if leading_comments and trailing_comments:
        return LEADING_AND_TRAILING_TEMPLATE.format(
            leading_comments=leading_comments, trailing_comments=trailing_comments,
            type_name=type_name, snake_field_name=snake_field_name, tag_number=tag_number)
    elif leading_comments:
        return LEADING_ONLY_TEMPLATE.format(
            leading_comments=leading_comments,
            type_name=type_name, snake_field_name=snake_field_name, tag_number=tag_number)
    elif trailing_comments:
        return TRAILING_ONLY_TEMPLATE.format(
            trailing_comments=trailing_comments,
            type_name=type_name, snake_field_name=snake_field_name, tag_number=tag_number)
    else:
        return NEITHER_TEMPLATE.format(
            type_name=type_name, snake_field_name=snake_field_name, tag_number=tag_number)


def generate_add_proto_or_builder_functions(request_file, file_comment_tree, message_type):
    add_proto_or_builder_functions = []
    insertion_point = "builder_scope:{}.{}".format(request_file.package, message_type.name)

    for field in [f for f in message_type.field if f.label == descriptor.FieldDescriptorProto.LABEL_REPEATED and f.type == descriptor.FieldDescriptorProto.TYPE_MESSAGE]:
        comment_node = file_comment_tree.children[message_type.name].children[field.name]
        CamelCaseName = string.capwords(field.name, "_").replace("_", "") if field.name != "class" else "Class_"
        simplified_type_name = field.type_name.replace(".ca.isupeene.charactersheet.cdk.", "")  # TODO: Try using full type name?
        add_proto_or_builder_functions.append(
            FUNCTION_TEMPLATE.format(field_name=CamelCaseName, type_name=simplified_type_name,
                                     comments=make_comments(comment_node.leading_comments.strip(), comment_node.trailing_comments.strip(),
                                                            simplified_type_name, field.name, field.number)))

    return add_proto_or_builder_functions, insertion_point


def generate_code(request):
    response = plugin.CodeGeneratorResponse()
    for request_file in request.proto_file:
        java_file_path = "/".join(request_file.package.split(".") + [request_file.name.split("/")[-1].split(".")[0].capitalize() + ".java"])
        file_comment_tree = comment_tree.build_comment_tree(request_file)
        for message_type in request_file.message_type:
            add_proto_or_builder_functions, insertion_point = generate_add_proto_or_builder_functions(request_file, file_comment_tree, message_type)
            if add_proto_or_builder_functions:
                response_file = response.file.add()
                response_file.name = java_file_path
                response_file.insertion_point = insertion_point
                response_file.content = "\n\n".join(add_proto_or_builder_functions)
    return response


# TODO: Make sure this works on nested types.  Test this on Resource.Quantity.level_progression
if __name__ == '__main__':
    # Parse request from stdin
    # https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/compiler/PluginProtos.CodeGeneratorRequest
    request = plugin.CodeGeneratorRequest()
    request.ParseFromString(sys.stdin.buffer.read())

    # Generate code and write to stdout
    # https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/compiler/PluginProtos.CodeGeneratorResponse
    sys.stdout.buffer.write(generate_code(request).SerializeToString())