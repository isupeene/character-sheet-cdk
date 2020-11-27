import string
import sys

from google.protobuf import descriptor_pb2 as descriptor
from google.protobuf.compiler import plugin_pb2 as plugin

import comment_tree


NON_REPEATED_FUNCTION_TEMPLATE = """
      {comments}
      public {type_name}.Builder mutable{field_name}() {{
        {type_name}.Builder result = {type_name}.newBuilder();
        return result._setInstance(get{field_name}());
      }}
"""

REPEATED_FUNCTION_TEMPLATE = """
      {comments}
      public {type_name}.Builder mutable{field_name}(int i) {{
        {type_name}.Builder result = {type_name}.newBuilder();
        return result._setInstance(get{field_name}(i));
      }}
      
      {comments}
      public java.util.stream.Stream<{type_name}.Builder> mutable{field_name}() {{
        return java.util.stream.IntStream.range(0, get{field_name}Count()).mapToObj(this::mutable{field_name});
      }}
"""

SNEAKY_PROTECTED_MEMBER_ACCESS_TEMPLATE = """
      // Prefix with underscore to avoid colliding with a hypothetical field named 'instance'.
      Builder _setInstance({type_name} instance) {{
        this.instance = instance;
        return this;
      }}
"""

# TODO: Deduplicate this comment code.
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


# TODO: Deduplicate this message handling code
def nested_message_types(message_descriptor: descriptor.DescriptorProto, prefix):
    nested_descriptors = {}
    for nested_type in message_descriptor.nested_type:
        qualified_name = '.'.join([prefix, nested_type.name])
        nested_descriptors[qualified_name] = nested_type
        nested_descriptors |= nested_message_types(nested_type, qualified_name)
    return nested_descriptors


def all_message_types(file_descriptor: descriptor.FileDescriptorProto):
    message_descriptors = {}
    for message_type in file_descriptor.message_type:
        message_descriptors[message_type.name] = message_type
        message_descriptors |= nested_message_types(message_type, message_type.name)
    return message_descriptors



def generate_mutable_functions(request_file, file_comment_tree, qualified_name, message_type):
    mutable_functions = []
    insertion_point = "builder_scope:{}.{}".format(request_file.package, qualified_name)

    mutable_functions.append(
        SNEAKY_PROTECTED_MEMBER_ACCESS_TEMPLATE.format(type_name=message_type.name)
    )

    for field in [f for f in message_type.field if f.type == descriptor.FieldDescriptorProto.TYPE_MESSAGE]:
        comment_node = file_comment_tree.at_path(qualified_name.split('.') + [field.name])
        CamelCaseName = string.capwords(field.name, "_").replace("_", "") if field.name != "class" else "Class_"
        simplified_type_name = field.type_name.replace(".ca.isupeene.charactersheet.cdk.", "")  # Switch from global scope to implicit 'Model' class scope for java.
        if field.label == descriptor.FieldDescriptorProto.LABEL_REPEATED:
            mutable_functions.append(
                REPEATED_FUNCTION_TEMPLATE.format(field_name=CamelCaseName, type_name=simplified_type_name,
                                                  comments=make_comments(comment_node.leading_comments.strip(), comment_node.trailing_comments.strip(),
                                                                         simplified_type_name, field.name, field.number)))
        else:
            mutable_functions.append(
                NON_REPEATED_FUNCTION_TEMPLATE.format(field_name=CamelCaseName, type_name=simplified_type_name,
                                                      comments=make_comments(comment_node.leading_comments.strip(), comment_node.trailing_comments.strip(),
                                                                             simplified_type_name, field.name, field.number)))

    return mutable_functions, insertion_point


def generate_code(request):
    response = plugin.CodeGeneratorResponse()
    for request_file in request.proto_file:
        java_file_path = "/".join(request_file.package.split(".") + [request_file.name.split("/")[-1].split(".")[0].capitalize() + ".java"])
        file_comment_tree = comment_tree.build_comment_tree(request_file)

        for qualified_name, message_type in all_message_types(request_file).items():
            mutable_functions, insertion_point = generate_mutable_functions(request_file, file_comment_tree, qualified_name, message_type)
            if mutable_functions:
                response_file = response.file.add()
                response_file.name = java_file_path
                response_file.insertion_point = insertion_point
                response_file.content = "\n\n".join(mutable_functions)
    return response

if __name__ == '__main__':
    # Parse request from stdin
    # https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/compiler/PluginProtos.CodeGeneratorRequest
    request = plugin.CodeGeneratorRequest()
    request.ParseFromString(sys.stdin.buffer.read())

    # Generate code and write to stdout
    # https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/compiler/PluginProtos.CodeGeneratorResponse
    sys.stdout.buffer.write(generate_code(request).SerializeToString())