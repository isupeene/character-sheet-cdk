import collections
import textwrap

from google.protobuf import descriptor_pb2


class CommentNode(object):
    def __init__(self, name, node_type, leading_comments, trailing_comments):
        self.name = name
        self.node_type = node_type
        self.leading_comments = leading_comments
        self.trailing_comments = trailing_comments
        self.children = {}

    def at_path(self, path):
        if not path:
            return self
        return self.children[path[0]].at_path(path[1:])

    def __str__(self):
        def child_string(child):
            return textwrap.indent(str(child), "    ")
        def children_string():
            return "\n".join([child_string(c) for c in self.children.values()])
        return ("CommentNode(\n" +
                f"  name='{self.name}'\n" +
                f"  node_type='{self.node_type}'\n" +
                f"  leading_comments='{self.leading_comments}'\n" +
                f"  trailing_comments='{self.trailing_comments}'\n" +
                "  children={\n" +
                children_string() + "\n"
                "  }\n" +
                ")")


class PathNode(object):
    def __init__(self):
        self.location = None
        self.children = collections.defaultdict(PathNode)

    def get_or_add_path(self, path, location: descriptor_pb2.SourceCodeInfo.Location):
        if not path:
            if not self.location:
                self.location = location
            return self
        if path[0] not in self.children:
            self.children[path[0]] = PathNode()
        return self.children[path[0]].get_or_add_path(path[1:], location)


def build_path_tree(source_code_info: descriptor_pb2.SourceCodeInfo):
    root = PathNode()
    for location in source_code_info.location:
        root.get_or_add_path(location.path, location)
    return root


# https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/DescriptorProtos.EnumValueDescriptorProto.html
def build_enum_value_node(value_descriptor: descriptor_pb2.EnumValueDescriptorProto, path_node: PathNode):
    return CommentNode(value_descriptor.name, 'EnumValueDescriptorProto',
                       path_node.location.leading_comments, path_node.location.trailing_comments)


# https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/DescriptorProtos.FieldDescriptorProto.html
def build_message_field_node(field_descriptor: descriptor_pb2.FieldDescriptorProto, path_node: PathNode):
    return CommentNode(field_descriptor.name, 'FieldDescriptorProto',
                       path_node.location.leading_comments, path_node.location.trailing_comments)


# https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/DescriptorProtos.EnumDescriptorProto.html
def build_enum_descriptor_node(enum_descriptor: descriptor_pb2.EnumDescriptorProto, path_node: PathNode):
    node = CommentNode(enum_descriptor.name, 'EnumDescriptorProto',
                       path_node.location.leading_comments, path_node.location.trailing_comments)
    enum_value_list_path_node = path_node.children[2]
    for i, enum_value_path_node in enum_value_list_path_node.children.items():
        enum_value_descriptor = enum_descriptor.value[i]
        node.children[enum_value_descriptor.name] = build_enum_value_node(enum_value_descriptor, enum_value_path_node)
    return node


# https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/DescriptorProtos.DescriptorProto.html
def build_message_descriptor_node(message_descriptor: descriptor_pb2.DescriptorProto, path_node: PathNode):
    node = CommentNode(message_descriptor.name, 'DescriptorProto',
                       path_node.location.leading_comments, path_node.location.trailing_comments)
    field_list_path_node = path_node.children[2]
    message_list_path_node = path_node.children[3]
    enum_list_path_node = path_node.children[4]
    for i, field_path_node in field_list_path_node.children.items():
        field_descriptor = message_descriptor.field[i]
        node.children[field_descriptor.name] = build_message_field_node(field_descriptor, field_path_node)
    for i, message_path_node in message_list_path_node.children.items():
        nested_message_descriptor = message_descriptor.nested_type[i]
        node.children[nested_message_descriptor.name] = build_message_descriptor_node(nested_message_descriptor, message_path_node)
    for i, enum_path_node in enum_list_path_node.children.items():
        enum_descriptor = message_descriptor.enum_type[i]
        node.children[enum_descriptor.name] = build_enum_descriptor_node(enum_descriptor, enum_path_node)
    return node


# https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/DescriptorProtos.FileDescriptorProto.html
def build_file_descriptor_node(file_descriptor: descriptor_pb2.FileDescriptorProto, path_node: PathNode):
    node = CommentNode(file_descriptor.name.split("/")[-1], 'FileDescriptorProto', '', '')
    # TODO: Look up these field numbers by name?
    message_list_path_node = path_node.children[4]
    enum_list_path_node = path_node.children[5]
    for i, message_path_node in message_list_path_node.children.items():
        message_descriptor = file_descriptor.message_type[i]
        node.children[message_descriptor.name] = build_message_descriptor_node(message_descriptor, message_path_node)
    for i, enum_path_node in enum_list_path_node.children.items():
        enum_descriptor = file_descriptor.enum_type[i]
        node.children[enum_descriptor.name] = build_enum_descriptor_node(enum_descriptor, enum_path_node)
    return node


# TODO: Handle One-Of messages, once I add some to the model
# https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/DescriptorProtos.OneofDescriptorProto.html
def build_comment_tree(file_descriptor: descriptor_pb2.FileDescriptorProto):
    return build_file_descriptor_node(file_descriptor, build_path_tree(file_descriptor.source_code_info))