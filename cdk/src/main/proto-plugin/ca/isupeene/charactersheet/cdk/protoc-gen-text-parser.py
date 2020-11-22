import string
import sys

from google.protobuf import descriptor_pb2 as descriptor
from google.protobuf.compiler import plugin_pb2 as plugin

# Parameters:
#   parser_functions
#     The set of ParseMessage and ParseMessageImpl functions that actually do the parsing
FILE_TEMPLATE = """
package ca.isupeene.charactersheet.cdk;

import androidx.annotation.NonNull;
import androidx.core.util.Pair;
import android.util.Log;

import java.io.BufferedReader;
import java.io.IOException;
import java.io.InputStream;
import java.io.InputStreamReader;
import java.io.StreamTokenizer;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;
import java.util.Set;

/**
 * A simple text proto parser generated by the protoc-gen-text-parser plugin.
 * Parse<i>MessageType</i> functions are generated for each message type in the input. These
 * functions take an InputStream which should yield a text-format protocol buffer of the appropriate type.
 * 
 * If an error is encountered while parsing the message, the Parser raises a ParseException
 * indicating the error and the line number on which it occurred.
 */
public class Parser {{
    private static final String TAG = "Parser";
    private static final String LOG_FORMAT = "Line %d: %s";


	/**
	 * Signals that the input to the parser was not a legal message of the appropriate type.
	 * The error message will indicate the general nature of the error and the line on which
	 * it occurred.
	 */
    public static class ParseException extends Exception {{
		ParseException(String errorMessage, Throwable innerException) {{
			super(errorMessage, innerException);
		}}

		ParseException(String errorMessage) {{
			super(errorMessage);
		}}

		ParseException(String errorMessage, int lineNumber) {{
			this(errorMessage, lineNumber, null);
		}}

		ParseException(String errorMessage, int lineNumber, Throwable innerException) {{
			super(String.format(LOG_FORMAT, lineNumber, errorMessage), innerException);
		}}
	}}

    private static void info(int lineNumber, String message) {{
        // Log.d(TAG, String.format(LOG_FORMAT, lineNumber, message));
    }}

    private static void error(int lineNumber, String message) throws ParseException {{
        Log.e(TAG, String.format(LOG_FORMAT, lineNumber, message));
        throw new ParseException(message, lineNumber);
    }}
    
    interface FieldHandler {{
        void HandleField() throws IOException, ParseException;
    }}
	
	private static StreamTokenizer GetTokenizer(InputStream input) {{
        StreamTokenizer tokenizer = new StreamTokenizer(
                new BufferedReader(
                        new InputStreamReader(input)
                )
        );
        tokenizer.slashSlashComments(true);
        tokenizer.slashStarComments(true);
        tokenizer.commentChar('#');
        tokenizer.parseNumbers();
        tokenizer.wordChars('_', '_');

        return tokenizer;
	}}
	
	private static int ConsumeInt32(StreamTokenizer tokenizer) throws IOException, ParseException {{
		tokenizer.nextToken();
		if (tokenizer.ttype == StreamTokenizer.TT_NUMBER) {{
			info(tokenizer.lineno(), "Parsed a number.");
			return (int)tokenizer.nval;
		}}
		else {{
			error(tokenizer.lineno(), "Failed to parse a number.");
			return 0;
		}}
	}}
	
	private static long ConsumeInt64(StreamTokenizer tokenizer) throws IOException, ParseException {{
		tokenizer.nextToken();
		if (tokenizer.ttype == StreamTokenizer.TT_NUMBER) {{
			info(tokenizer.lineno(), "Parsed a number.");
			return (long)tokenizer.nval;
		}}
		else {{
			error(tokenizer.lineno(), "Failed to parse a number.");
			return 0L;
		}}
	}}
	
	private static float ConsumeFloat(StreamTokenizer tokenizer) throws IOException, ParseException {{
		tokenizer.nextToken();
		if (tokenizer.ttype == StreamTokenizer.TT_NUMBER) {{
			info(tokenizer.lineno(), "Parsed a number.");
			return (float)tokenizer.nval;
		}}
		else {{
			error(tokenizer.lineno(), "Failed to parse a number.");
			return 0.0f;
		}}
	}}
	
	private static double ConsumeDouble(StreamTokenizer tokenizer) throws IOException, ParseException {{
		tokenizer.nextToken();
		if (tokenizer.ttype == StreamTokenizer.TT_NUMBER) {{
			info(tokenizer.lineno(), "Parsed a number.");
			return tokenizer.nval;
		}}
		else {{
			error(tokenizer.lineno(), "Failed to parse a number.");
			return 0.0;
		}}
	}}
	
	private static boolean ConsumeBool(StreamTokenizer tokenizer) throws IOException, ParseException {{
		tokenizer.nextToken();
		if (tokenizer.ttype == StreamTokenizer.TT_WORD) {{
		    if (tokenizer.sval.toLowerCase().equals("true")) {{
				info(tokenizer.lineno(), "Parsed a true.");
				return true;
			}}
			else if (tokenizer.sval.toLowerCase().equals("false")) {{
				info(tokenizer.lineno(), "Parsed a false.");
				return false;
			}}
		}}
		error(tokenizer.lineno(), "Failed to parse a boolean.");
		return false;
	}}
	
	private static String ConsumeString(StreamTokenizer tokenizer) throws IOException, ParseException {{
		tokenizer.nextToken();
		if (tokenizer.ttype == '"' || tokenizer.ttype == '\\'') {{
			info(tokenizer.lineno(), "Parsed a quoted string.");
			StringBuilder stringValue = new StringBuilder();
			// Concatenate consecutive quoted strings (as in C).
			while (tokenizer.ttype == '"' || tokenizer.ttype == '\\'') {{
				stringValue.append(tokenizer.sval);
				tokenizer.nextToken();
			}}
			tokenizer.pushBack();
			return stringValue.toString();
		}}
		else {{
			error(tokenizer.lineno(), "Failed to parse a quoted string.");
			return "";
		}}
	}}
	
	// Since the generic Enum class's valueOf method is a little more expensive
	// than a specific enum's valueOf method, we shunt a bit of the logic back
	// to the sender where the actual Enum type is known.
	private static String ConsumeEnum(StreamTokenizer tokenizer) throws IOException {{
		tokenizer.nextToken();
		if (tokenizer.ttype == StreamTokenizer.TT_WORD) {{
			return tokenizer.sval;
		}}
		else {{
			return "";
		}}
	}}
	
	private static String ConsumeFieldNameOrEndOfMessage(StreamTokenizer tokenizer,  Set<String> messageFields, boolean expectEof) throws IOException, ParseException {{
		tokenizer.nextToken();
		if (tokenizer.ttype == StreamTokenizer.TT_WORD) {{
			String fieldName = tokenizer.sval;
			info(tokenizer.lineno(), "Parsed the field name '" + fieldName);
			tokenizer.nextToken();
			if (tokenizer.ttype == ':') {{
				if (messageFields.contains(fieldName)) {{
					error(tokenizer.lineno(), "Parsed a colon after '" + fieldName + "', when the start of a nested message '{{' was expected.");
					return "";
				}}
				else {{
					info(tokenizer.lineno(), "Parsed a colon.");
					return fieldName;
				}}
			}}
			else if (tokenizer.ttype == '{{') {{
				if (!messageFields.contains(fieldName)) {{
					error(tokenizer.lineno(), "Parsed an opening brace after '" + fieldName + "', when a colon was expected.");
					return "";
				}}
				else {{
					info(tokenizer.lineno(), "Parsed the start of a nested message.");
					return fieldName;
				}}
			}}
			else {{
				error(tokenizer.lineno(), "Failed to parse either a colon or the start of a nested message.");
				return "";
			}}
		}}
		else if (tokenizer.ttype == '}}') {{
			if (expectEof) {{
				error(tokenizer.lineno(), "Found an extra closing brace '}}' at the end of the file.");
				return "";
			}}
			else {{
				info(tokenizer.lineno(), "Parsed the end of a nested message.");
				return "";
			}}
		}}
		else if (tokenizer.ttype == StreamTokenizer.TT_EOF) {{
			if (!expectEof) {{
				error(tokenizer.lineno(), "Found the end-of-file when not all nested messages have been closed. Did you forget a '}}'?.");
				return "";
			}}
			else {{
				info(tokenizer.lineno(), "Parsed the end of the outermost message.");
				return "";
			}}
		}}
		else {{
			error(tokenizer.lineno(), "Failed to parse a field label.");
			return "";
		}}
	}}
	
	{parser_functions}
}}
"""

# Parameters:
#   message_type
#     The qualified type of the proto message to parse, e.g. 'Model.Character'.
#
#   simple_message_type
#     The unqualified type of the proto message to parse, e.g. 'Character'.
#
#   field_handlers
#	  The set of statements responsible for parsing each individual field.
FUNCTION_TEMPLATE = """
	/**
	 * Parse a text-format {{@link {message_type} {simple_message_type}}} from an {{@link java.io.InputStream InputStream}}.
	 */
    public static @NonNull {message_type}.Builder Parse{simple_message_type}(@NonNull InputStream input) throws ParseException {{
        Log.i(TAG, "Trying to parse a {message_type}");
        try {{
            return Parse{simple_message_type}Impl(GetTokenizer(input), true);
        }}
        catch (IOException ex) {{
            throw new ParseException("The input to Parse{simple_message_type} could not be read.", ex);
        }}
    }}
    
    private static @NonNull {message_type}.Builder Parse{simple_message_type}Impl(final StreamTokenizer tokenizer, boolean isOutermostMessage) throws ParseException, IOException {{
        final {message_type}.Builder builder = {message_type}.newBuilder();
        
        Map<String, Pair<? extends FieldHandler, Boolean>> fieldHandlers = new HashMap<>();
        Set<String> messageFields = new HashSet<>();
        {field_handlers}

		Set<String> foundFieldNames = new HashSet<>();

        for (String fieldName = ConsumeFieldNameOrEndOfMessage(tokenizer, messageFields, isOutermostMessage);
            !fieldName.isEmpty();
            fieldName = ConsumeFieldNameOrEndOfMessage(tokenizer, messageFields, isOutermostMessage))
        {{
            Pair<? extends FieldHandler, Boolean> pair = fieldHandlers.get(fieldName);
            if (pair == null) error(tokenizer.lineno(), "Parsed a bad field name: " + fieldName);

            FieldHandler handler = pair.first;
            boolean repeated = pair.second;
            if (!foundFieldNames.add(fieldName) && !repeated) error(tokenizer.lineno(), "Parsed a duplicate field name for a non-repeated field: " + fieldName);

            handler.HandleField();
        }}
        
        return builder;
    }}
"""


# Parameters:
#   field_name
#     The name of the field as it appears in the .asciipb files.
#
#   field_setter
#     The name of the method that sets the field in the proto object.
#     This could be a setter or an adder depending on whether the field is repeated.
#
#   repeated
#     'true' if the field is repeated, 'false' otherwise.
#     Make sure to pass in strings - Java can't understand capitalized 'True' and 'False'.
INT32_FIELD_TEMPLATE = """
            fieldHandlers.put(
                "{field_name}",
                Pair.create(
                    new FieldHandler() {{
                        public void HandleField() throws IOException, ParseException {{
                            builder.{field_setter}(ConsumeInt32(tokenizer));
                        }}
                    }},
                    {repeated}
                )
            );
"""


# Parameters:
#   field_name
#     The name of the field as it appears in the .asciipb files.
#
#   field_setter
#     The name of the method that sets the field in the proto object.
#     This could be a setter or an adder depending on whether the field is repeated.
#
#   repeated
#     'true' if the field is repeated, 'false' otherwise.
#     Make sure to pass in strings - Java can't understand capitalized 'True' and 'False'.
INT64_FIELD_TEMPLATE = """
            fieldHandlers.put(
                "{field_name}",
                Pair.create(
                    new FieldHandler() {{
                        public void HandleField() throws IOException, ParseException {{
                            builder.{field_setter}(ConsumeInt64(tokenizer));
                        }}
                    }},
                    {repeated}
                )
            );
"""


# Parameters:
#   field_name
#     The name of the field as it appears in the .asciipb files.
#
#   field_setter
#     The name of the method that sets the field in the proto object.
#     This could be a setter or an adder depending on whether the field is repeated.
#
#   repeated
#     'true' if the field is repeated, 'false' otherwise.
#     Make sure to pass in strings - Java can't understand capitalized 'True' and 'False'.
FLOAT_FIELD_TEMPLATE = """
            fieldHandlers.put(
                "{field_name}",
                Pair.create(
                    new FieldHandler() {{
                        public void HandleField() throws IOException, ParseException {{
                            builder.{field_setter}(ConsumeFloat(tokenizer));
                        }}
                    }},
                    {repeated}
                )
            );
"""


# Parameters:
#   field_name
#     The name of the field as it appears in the .asciipb files.
#
#   field_setter
#     The name of the method that sets the field in the proto object.
#     This could be a setter or an adder depending on whether the field is repeated.
#
#   repeated
#     'true' if the field is repeated, 'false' otherwise.
#     Make sure to pass in strings - Java can't understand capitalized 'True' and 'False'.
DOUBLE_FIELD_TEMPLATE = """
            fieldHandlers.put(
                "{field_name}",
                Pair.create(
                    new FieldHandler() {{
                        public void HandleField() throws IOException, ParseException {{
                            builder.{field_setter}(ConsumeDouble(tokenizer));
                        }}
                    }},
                    {repeated}
                )
            );
"""

# Parameters:
#   field_name
#     The name of the field as it appears in the .asciipb files.
#
#   field_setter
#     The name of the method that sets the field in the proto object.
#     This could be a setter or an adder depending on whether the field is repeated.
#
#   repeated
#     'true' if the field is repeated, 'false' otherwise.
#     Make sure to pass in strings - Java can't understand capitalized 'True' and 'False'.
BOOL_FIELD_TEMPLATE = """
            fieldHandlers.put(
                "{field_name}",
                Pair.create(
                    new FieldHandler() {{
                        public void HandleField() throws IOException, ParseException {{
                            builder.{field_setter}(ConsumeBool(tokenizer));
                        }}
                    }},
                    {repeated}
                )
            );
"""

# Parameters:
#   field_name
#     The name of the field as it appears in the .asciipb files.
#
#   field_setter
#     The name of the method that sets the field in the proto object.
#     This could be a setter or an adder depending on whether the field is repeated.
#
#   repeated
#     'true' if the field is repeated, 'false' otherwise.
#     Make sure to pass in strings - Java can't understand capitalized 'True' and 'False'.
STRING_FIELD_TEMPLATE = """
            fieldHandlers.put(
                "{field_name}",
                Pair.create(
                    new FieldHandler() {{
                        public void HandleField() throws IOException, ParseException {{
                            builder.{field_setter}(ConsumeString(tokenizer));
                        }}
                    }},
                    {repeated}
                )
            );
"""


# Parameters:
#   field_name
#     The name of the field as it appears in the .asciipb files.
#
#   field_setter
#     The name of the method that sets the field in the proto object.
#     This could be a setter or an adder depending on whether the field is repeated.
#
#   field_type
#	  The qualified type of the field, as in 'Model.Character' or 'Model.Item.Type'
#
#   repeated
#     'true' if the field is repeated, 'false' otherwise.
#     Make sure to pass in strings - Java can't understand capitalized 'True' and 'False'.
ENUM_FIELD_TEMPLATE = """
            fieldHandlers.put(
                "{field_name}",
                Pair.create(
                    new FieldHandler() {{
                        public void HandleField() throws IOException, ParseException {{
                            // Some of the logic that should properly be contained in ConsumeEnum is moved here
                            // so that we can use the faster valueOf function associated with a specific enum type.
                            String enumString = ConsumeEnum(tokenizer);
                            if (!enumString.isEmpty()) {{
                                try {{
                                    builder.{field_setter}({field_type}.valueOf(enumString));
                                    info(tokenizer.lineno(), "Parsed a {field_type}.");
                                }}
                                catch (IllegalArgumentException ex) {{
                                    error(tokenizer.lineno(), "Failed to parse a {field_type}.");
                                }}
                            }}
                            else {{
                                error(tokenizer.lineno(), "Failed to parse a {field_type}.");
                            }}
                        }}
                    }},
                    {repeated}
                )
            );
"""


# Parameters:
#   field_name
#     The name of the field as it appears in the .asciipb files.
#
#   field_setter
#     The name of the method that sets the field in the proto object.
#     This could be a setter or an adder depending on whether the field is repeated.
#
#   field_type
#	  The simplified name of the field's type, as in 'Character' or 'Item_Type'
#
#   repeated
#     'true' if the field is repeated, 'false' otherwise.
#     Make sure to pass in strings - Java can't understand capitalized 'True' and 'False'.
MESSAGE_FIELD_TEMPLATE = """
            fieldHandlers.put(
                "{field_name}",
                Pair.create(
                    new FieldHandler() {{
                        public void HandleField() throws IOException, ParseException {{
                            builder.{field_setter}(Parse{field_type}Impl(tokenizer, false));
                        }}
                    }},
                    {repeated}
                )
            );
            messageFields.add("{field_name}");
"""


def generate_field_handler(field):
	snake_case_name = field.name
	# Convert proto field names to java names. Note that the generated java code treats the word 'class' as a special case.
	CamelCaseName = string.capwords(snake_case_name, "_").replace("_", "") if field.name != "class" else "Class_"
	simplified_type_name = field.type_name.replace(".ca.isupeene.charactersheet.cdk.", "")

	repeated = field.label == descriptor.FieldDescriptorProto.LABEL_REPEATED
	repeatedString = "true" if repeated else "false"
	field_setter_string = "add{}".format(CamelCaseName) if repeated else "set{}".format(CamelCaseName)
	
	if field.type in {descriptor.FieldDescriptorProto.TYPE_INT32, descriptor.FieldDescriptorProto.TYPE_UINT32}:
		return INT32_FIELD_TEMPLATE.format(field_name=snake_case_name, field_setter=field_setter_string, repeated=repeatedString)
	elif field.type in {descriptor.FieldDescriptorProto.TYPE_INT64, descriptor.FieldDescriptorProto.TYPE_UINT64}:
		return INT64_FIELD_TEMPLATE.format(field_name=snake_case_name, field_setter=field_setter_string, repeated=repeatedString)
	elif field.type == descriptor.FieldDescriptorProto.TYPE_FLOAT:
		return FLOAT_FIELD_TEMPLATE.format(field_name=snake_case_name, field_setter=field_setter_string, repeated=repeatedString)
	elif field.type == descriptor.FieldDescriptorProto.TYPE_DOUBLE:
		return DOUBLE_FIELD_TEMPLATE.format(field_name=snake_case_name, field_setter=field_setter_string, repeated=repeatedString)
	elif field.type == descriptor.FieldDescriptorProto.TYPE_BOOL:
		return BOOL_FIELD_TEMPLATE.format(field_name=snake_case_name, field_setter=field_setter_string, repeated=repeatedString)
	elif field.type == descriptor.FieldDescriptorProto.TYPE_STRING:
		return STRING_FIELD_TEMPLATE.format(field_name=snake_case_name, field_setter=field_setter_string, repeated=repeatedString)
	elif field.type == descriptor.FieldDescriptorProto.TYPE_ENUM:
		return ENUM_FIELD_TEMPLATE.format(
			field_name=snake_case_name,
			field_setter=field_setter_string,
			field_type="Model.{}".format(simplified_type_name),
			repeated=repeatedString
		)
	elif field.type == descriptor.FieldDescriptorProto.TYPE_MESSAGE:
		return MESSAGE_FIELD_TEMPLATE.format(
			field_name=snake_case_name,
			field_setter=field_setter_string,
			field_type="_".join([s[0] + s[1:] for s in simplified_type_name.split(".")]),
            repeated=repeatedString
		)
	else:
		raise Exception("Unhandled field type: " + str(field.type))


def generate_outer_message_parser_function(message_type, parent_name):
	message_type_string = "{}.{}".format(parent_name, message_type.name)
	simple_message_type_string = '_'.join(parent_name.split('.')[1:] + [message_type.name])
	
	field_handlers = []
	
	for field in message_type.field:
		field_handlers.append(generate_field_handler(field))
	
	return FUNCTION_TEMPLATE.format(
		message_type=message_type_string,
		simple_message_type=simple_message_type_string,
		field_handlers="\n".join(field_handlers)
	)
	

# Returns a list of strings - parser functions for the given message type and
# each of its nested message types.
def generate_parser_functions(message_type, parent_name):
	new_parent_name = "{}.{}".format(parent_name, message_type.name) if parent_name else message_type.name
	return (
		[generate_outer_message_parser_function(message_type, parent_name)] +
		[function
		 for nested_type
		 in message_type.nested_type
		 for function
		 in generate_parser_functions(nested_type, new_parent_name)]
	)


def generate_code(request, response):
	parser_functions = []

	for request_file in request.proto_file:
		java_file_path = "/".join(request_file.package.split(".") + ["Parser.java"])
		class_name = string.capwords(request_file.name.split("/")[-1].split(".")[0], '_')
		for message_type in request_file.message_type:
			parser_functions += generate_parser_functions(message_type, class_name)

		response_file = response.file.add()
		response_file.name = java_file_path
		response_file.content = FILE_TEMPLATE.format(parser_functions="\n\n".join(parser_functions))


if __name__ == '__main__':
	# Parse request from stdin
	# https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/compiler/PluginProtos.CodeGeneratorRequest
	request = plugin.CodeGeneratorRequest()
	request.ParseFromString(sys.stdin.buffer.read())

	# Create response and generate code
	# https://developers.google.com/protocol-buffers/docs/reference/java/com/google/protobuf/compiler/PluginProtos.CodeGeneratorResponse
	response = plugin.CodeGeneratorResponse()
	generate_code(request, response)

	# Serialize and write to stdout
	sys.stdout.buffer.write(response.SerializeToString())